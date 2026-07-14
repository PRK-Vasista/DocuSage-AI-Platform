/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * Cursor-style DocuSage workspace: document rail + summary/chat pane.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
    downloadFile,
    fetchBackendHealth,
    getDocumentSummary,
    listFiles,
    permanentlyDeleteFile,
    softDeleteFile,
    uploadFile,
} from '../../api/apiService';
import { MAX_UPLOAD_SIZE_BYTES } from '../../config/appConfig';
import { downloadTextFile } from '../../utils/downloadText';
import { formatFileSize } from '../../utils/formatters';
import { shouldPollDocuments } from '../../utils/processingStatus';
import ChatPanel from './ChatPanel';
import DocumentSidebar from './DocumentSidebar';
import SummaryPanel from './SummaryPanel';
import './Workspace.css';

const POLL_INTERVAL_MS = 3000;

/**
 * Authenticated workspace shell for document management and AI views.
 *
 * @param {object} props
 * @param {string} props.token - JWT bearer token.
 */
const Workspace = ({ token }) => {
    const [viewMode, setViewMode] = useState('active');
    const [activeDocuments, setActiveDocuments] = useState([]);
    const [trashedDocuments, setTrashedDocuments] = useState([]);
    const [storage, setStorage] = useState(null);
    const [selectedDocumentId, setSelectedDocumentId] = useState(null);
    const [summaryText, setSummaryText] = useState('');
    const [isSummaryLoading, setIsSummaryLoading] = useState(false);
    const [summaryCollapsed, setSummaryCollapsed] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [isUploading, setIsUploading] = useState(false);
    const [actionDocumentId, setActionDocumentId] = useState(null);
    const [statusMessage, setStatusMessage] = useState(null);
    const [mobileShowDocs, setMobileShowDocs] = useState(true);
    const [aiHealthBanner, setAiHealthBanner] = useState(null);

    const loadDocuments = useCallback(async (showLoader = true) => {
        if (!token) {
            return;
        }

        if (showLoader) {
            setIsFetching(true);
        }

        try {
            const [activeResponse, trashResponse] = await Promise.all([
                listFiles(token, false),
                listFiles(token, true),
            ]);

            const active = activeResponse.documents || [];
            const trash = (trashResponse.documents || []).filter((doc) => doc.is_deleted);

            setActiveDocuments(active);
            setTrashedDocuments(trash);
            setStorage(activeResponse.storage || null);
        } catch (error) {
            console.error('[Workspace] Failed to load documents:', error);
            setStatusMessage({ type: 'error', message: error.message });
            setActiveDocuments([]);
            setTrashedDocuments([]);
        } finally {
            if (showLoader) {
                setIsFetching(false);
            }
        }
    }, [token]);

    useEffect(() => {
        loadDocuments();
    }, [loadDocuments]);

    useEffect(() => {
        let cancelled = false;

        const pollHealth = async () => {
            try {
                const health = await fetchBackendHealth();
                if (cancelled) {
                    return;
                }
                if (health.ai_service === 'ok' || health.ai_service === 'disabled') {
                    setAiHealthBanner(null);
                } else if (health.ai_service === 'degraded') {
                    setAiHealthBanner(
                        'AI is warming up or partially available. Summaries may use a simpler fallback; chat may be slow.',
                    );
                } else {
                    setAiHealthBanner(
                        'AI unit is unreachable right now. Chat may fail until the local model is ready.',
                    );
                }
            } catch (error) {
                if (!cancelled) {
                    setAiHealthBanner('Could not reach backend health endpoint.');
                }
            }
        };

        pollHealth();
        const intervalId = window.setInterval(pollHealth, 15000);
        return () => {
            cancelled = true;
            window.clearInterval(intervalId);
        };
    }, []);

    useEffect(() => {
        if (!shouldPollDocuments(activeDocuments)) {
            return undefined;
        }

        const intervalId = window.setInterval(() => {
            loadDocuments(false);
        }, POLL_INTERVAL_MS);

        return () => window.clearInterval(intervalId);
    }, [activeDocuments, loadDocuments]);

    const visibleDocuments = viewMode === 'active' ? activeDocuments : trashedDocuments;

    const selectedDocument = useMemo(
        () => visibleDocuments.find((doc) => doc.id === selectedDocumentId)
            || activeDocuments.find((doc) => doc.id === selectedDocumentId)
            || null,
        [visibleDocuments, activeDocuments, selectedDocumentId],
    );

    useEffect(() => {
        let cancelled = false;

        const loadSummary = async () => {
            if (!selectedDocument || selectedDocument.processing_status !== 'ready') {
                setSummaryText(selectedDocument?.document_summary || '');
                return;
            }

            if (selectedDocument.document_summary) {
                setSummaryText(selectedDocument.document_summary);
            }

            setIsSummaryLoading(true);
            try {
                const payload = await getDocumentSummary(selectedDocument.id, token);
                if (!cancelled) {
                    setSummaryText(payload.document_summary || '');
                }
            } catch (error) {
                console.error('[Workspace] Summary fetch failed:', error);
                if (!cancelled) {
                    setStatusMessage({ type: 'error', message: error.message });
                }
            } finally {
                if (!cancelled) {
                    setIsSummaryLoading(false);
                }
            }
        };

        loadSummary();
        return () => {
            cancelled = true;
        };
    }, [selectedDocument, token]);

    const handleSelectDocument = (document) => {
        setSelectedDocumentId(document.id);
        setSummaryCollapsed(false);
        setMobileShowDocs(false);
        setStatusMessage(null);
    };

    const handleUpload = async (file) => {
        if (file.size > MAX_UPLOAD_SIZE_BYTES) {
            setStatusMessage({
                type: 'error',
                message: `Selected file exceeds the ${formatFileSize(MAX_UPLOAD_SIZE_BYTES)} upload limit.`,
            });
            return;
        }

        setIsUploading(true);
        setStatusMessage({ type: 'info', message: `Uploading '${file.name}'...` });

        try {
            const uploaded = await uploadFile(file, token);
            setStatusMessage({
                type: 'success',
                message: `Uploaded '${uploaded.filename}'. Processing started.`,
            });
            setSelectedDocumentId(uploaded.id);
            setViewMode('active');
            await loadDocuments(false);
        } catch (error) {
            console.error('[Workspace] Upload failed:', error);
            setStatusMessage({ type: 'error', message: error.message });
        } finally {
            setIsUploading(false);
        }
    };

    const handleSoftDelete = async (documentId) => {
        setActionDocumentId(documentId);
        try {
            await softDeleteFile(documentId, token);
            if (selectedDocumentId === documentId) {
                setSelectedDocumentId(null);
                setSummaryText('');
            }
            setStatusMessage({ type: 'success', message: 'Moved to trash.' });
            await loadDocuments(false);
        } catch (error) {
            setStatusMessage({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handlePermanentDelete = async (documentId) => {
        setActionDocumentId(documentId);
        try {
            await permanentlyDeleteFile(documentId, token);
            if (selectedDocumentId === documentId) {
                setSelectedDocumentId(null);
                setSummaryText('');
            }
            setStatusMessage({ type: 'success', message: 'Permanently deleted.' });
            await loadDocuments(false);
        } catch (error) {
            setStatusMessage({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handleDownloadOriginal = async (document) => {
        setActionDocumentId(document.id);
        try {
            await downloadFile(document.id, document.filename, token);
            setStatusMessage({ type: 'success', message: 'Download started.' });
        } catch (error) {
            setStatusMessage({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handleDownloadSummary = () => {
        if (!selectedDocument || !summaryText) {
            return;
        }
        const baseName = selectedDocument.filename.replace(/\.[^/.]+$/, '');
        downloadTextFile(`${baseName}-summary.txt`, summaryText);
    };

    const chatEnabled = Boolean(
        selectedDocument
        && !selectedDocument.is_deleted
        && selectedDocument.processing_status === 'ready'
        && summaryText,
    );

    return (
        <div className="workspace">
            {aiHealthBanner && (
                <div className="workspace-health-banner" role="status">
                    {aiHealthBanner}
                </div>
            )}
            <div className="workspace-mobile-toggle">
                <button
                    type="button"
                    className={`mobile-pane-btn ${mobileShowDocs ? 'is-active' : ''}`}
                    onClick={() => setMobileShowDocs(true)}
                >
                    Documents
                </button>
                <button
                    type="button"
                    className={`mobile-pane-btn ${!mobileShowDocs ? 'is-active' : ''}`}
                    onClick={() => setMobileShowDocs(false)}
                    disabled={!selectedDocument}
                >
                    Workspace
                </button>
            </div>

            <div className={`workspace-shell ${mobileShowDocs ? 'show-docs' : 'show-detail'}`}>
                <div className="workspace-left">
                    <DocumentSidebar
                        viewMode={viewMode}
                        onViewModeChange={setViewMode}
                        documents={visibleDocuments}
                        selectedDocumentId={selectedDocumentId}
                        onSelectDocument={handleSelectDocument}
                        storage={storage}
                        isFetching={isFetching}
                        isUploading={isUploading}
                        actionDocumentId={actionDocumentId}
                        statusMessage={statusMessage}
                        onUpload={handleUpload}
                        onSoftDelete={handleSoftDelete}
                        onPermanentDelete={handlePermanentDelete}
                        onDownloadOriginal={handleDownloadOriginal}
                    />
                </div>

                <div className="workspace-right">
                    {!selectedDocument ? (
                        <div className="workspace-empty">
                            <h2>Select a document</h2>
                            <p>
                                Choose a file from the left rail to view its summary and chat.
                            </p>
                        </div>
                    ) : (
                        <>
                            <SummaryPanel
                                document={selectedDocument}
                                summaryText={summaryText}
                                isLoading={isSummaryLoading}
                                isCollapsed={summaryCollapsed}
                                onToggleCollapse={() => setSummaryCollapsed((value) => !value)}
                                onDownloadSummary={handleDownloadSummary}
                            />
                            <ChatPanel
                                documentId={selectedDocument.id}
                                token={token}
                                enabled={chatEnabled}
                            />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Workspace;
