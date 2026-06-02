/**
 * Authenticated user dashboard for document upload and management.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
    downloadFile,
    getDocumentSummary,
    listFiles,
    permanentlyDeleteFile,
    softDeleteFile,
    uploadFile,
} from '../../api/apiService';
import {
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
} from '../../config/appConfig';
import { formatDateTime, formatFileSize } from '../../utils/formatters';
import {
    getProcessingStatusClass,
    getProcessingStatusLabel,
    shouldPollDocuments,
} from '../../utils/processingStatus';
import Alert from '../shared/Alert';
import Button from '../shared/Button';
import './Dashboard.css';

const POLL_INTERVAL_MS = 3000;

/**
 * Render upload, active document list, trash management, and processing status.
 *
 * @param {object} props
 * @param {string} props.token - JWT bearer token for API calls.
 */
const Dashboard = ({ token }) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [activeDocuments, setActiveDocuments] = useState([]);
    const [trashedDocuments, setTrashedDocuments] = useState([]);
    const [storage, setStorage] = useState(null);
    const [viewMode, setViewMode] = useState('active');
    const [statusAlert, setStatusAlert] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [actionDocumentId, setActionDocumentId] = useState(null);
    const [selectedSummary, setSelectedSummary] = useState(null);
    const [isSummaryLoading, setIsSummaryLoading] = useState(false);

    /**
     * Load active and trashed documents from the backend.
     *
     * @param {boolean} showLoader - Whether to show the loading indicator.
     */
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

            setActiveDocuments(activeResponse.documents || []);
            setStorage(activeResponse.storage || null);
            setTrashedDocuments(
                (trashResponse.documents || []).filter((document) => document.is_deleted),
            );
        } catch (error) {
            console.error('[Dashboard] Failed to load documents:', error);
            setStatusAlert({ type: 'error', message: error.message });
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
        if (!shouldPollDocuments(activeDocuments)) {
            return undefined;
        }

        const intervalId = window.setInterval(() => {
            loadDocuments(false);
        }, POLL_INTERVAL_MS);

        return () => window.clearInterval(intervalId);
    }, [activeDocuments, loadDocuments]);

    const handleFileChange = (event) => {
        const file = event.target.files[0] || null;

        if (file && file.size > MAX_UPLOAD_SIZE_BYTES) {
            setStatusAlert({
                type: 'error',
                message: `Selected file exceeds the ${formatFileSize(MAX_UPLOAD_SIZE_BYTES)} upload limit.`,
            });
            event.target.value = '';
            setSelectedFile(null);
            return;
        }

        setSelectedFile(file);
        setStatusAlert(null);
    };

    const handleUpload = async (event) => {
        event.preventDefault();

        if (!selectedFile) {
            setStatusAlert({ type: 'error', message: 'Please select a file to upload.' });
            return;
        }

        setIsUploading(true);
        setStatusAlert({ type: 'info', message: 'Uploading document...' });

        try {
            const uploadedDocument = await uploadFile(selectedFile, token);
            setStatusAlert({
                type: 'success',
                message: `Uploaded '${uploadedDocument.filename}'. Processing has started.`,
            });
            setSelectedFile(null);
            event.target.reset();
            await loadDocuments(false);
        } catch (error) {
            console.error('[Dashboard] Upload failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setIsUploading(false);
        }
    };

    const handleSoftDelete = async (documentId) => {
        setActionDocumentId(documentId);
        setStatusAlert({ type: 'info', message: 'Moving document to trash...' });

        try {
            await softDeleteFile(documentId, token);
            setStatusAlert({ type: 'success', message: 'Document moved to trash.' });
            await loadDocuments(false);
        } catch (error) {
            console.error('[Dashboard] Soft delete failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handlePermanentDelete = async (documentId) => {
        setActionDocumentId(documentId);
        setStatusAlert({ type: 'info', message: 'Permanently deleting document...' });

        try {
            await permanentlyDeleteFile(documentId, token);
            setStatusAlert({ type: 'success', message: 'Document permanently deleted.' });
            await loadDocuments(false);
        } catch (error) {
            console.error('[Dashboard] Permanent delete failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handleDownload = async (document) => {
        setActionDocumentId(document.id);
        setStatusAlert({ type: 'info', message: `Downloading '${document.filename}'...` });

        try {
            await downloadFile(document.id, document.filename, token);
            setStatusAlert({ type: 'success', message: 'Download started.' });
        } catch (error) {
            console.error('[Dashboard] Download failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    const handleViewSummary = async (document) => {
        setActionDocumentId(document.id);
        setIsSummaryLoading(true);
        setSelectedSummary(null);
        setStatusAlert({ type: 'info', message: `Loading summary for '${document.filename}'...` });

        try {
            const summaryPayload = await getDocumentSummary(document.id, token);
            setSelectedSummary(summaryPayload);
            setStatusAlert(null);
        } catch (error) {
            console.error('[Dashboard] Summary fetch failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setIsSummaryLoading(false);
            setActionDocumentId(null);
        }
    };

    const visibleDocuments = viewMode === 'active' ? activeDocuments : trashedDocuments;

    return (
        <div className="dashboard-container">
            <h2 className="dashboard-title">Welcome to DocuSage!</h2>
            <p className="dashboard-intro">
                Upload documents for automatic text extraction and summarization.
            </p>

            {storage && (
                <div className="card storage-card">
                    <h3 className="card-title">Storage Usage</h3>
                    <p className="storage-summary">
                        {formatFileSize(storage.used_bytes)} used of {formatFileSize(storage.limit_bytes)}
                        {' '}({formatFileSize(storage.remaining_bytes)} remaining)
                    </p>
                </div>
            )}

            <div className="card upload-card">
                <h3 className="card-title">Upload New Document</h3>
                <Alert type={statusAlert?.type} message={statusAlert?.message} />

                <form onSubmit={handleUpload} className="upload-form">
                    <input
                        type="file"
                        id="file-input"
                        onChange={handleFileChange}
                        className="file-input"
                        accept={ALLOWED_UPLOAD_EXTENSIONS}
                        disabled={isUploading}
                    />
                    <Button
                        type="submit"
                        variant="secondary"
                        size="lg"
                        disabled={isUploading || !selectedFile}
                    >
                        {isUploading ? 'Uploading...' : 'Upload Document'}
                    </Button>
                </form>
            </div>

            {selectedSummary && (
                <div className="card summary-card">
                    <div className="summary-card-header">
                        <h3 className="card-title">Summary: {selectedSummary.filename}</h3>
                        <Button variant="secondary" size="sm" onClick={() => setSelectedSummary(null)}>
                            Close
                        </Button>
                    </div>
                    {selectedSummary.processing_status === 'ready' && selectedSummary.document_summary ? (
                        <p className="summary-text">{selectedSummary.document_summary}</p>
                    ) : (
                        <p className="summary-text muted">
                            {selectedSummary.processing_error || 'Summary is not available yet.'}
                        </p>
                    )}
                </div>
            )}

            <div className="card document-list-card">
                <div className="document-list-header">
                    <h3 className="card-title">
                        {viewMode === 'active' ? 'My Documents' : 'Trash'}
                    </h3>
                    <div className="view-toggle">
                        <Button
                            variant={viewMode === 'active' ? 'primary' : 'secondary'}
                            size="sm"
                            onClick={() => setViewMode('active')}
                        >
                            Active
                        </Button>
                        <Button
                            variant={viewMode === 'trash' ? 'primary' : 'secondary'}
                            size="sm"
                            onClick={() => setViewMode('trash')}
                        >
                            Trash ({trashedDocuments.length})
                        </Button>
                    </div>
                </div>

                {isFetching && <p className="text-center">Loading documents...</p>}

                {!isFetching && visibleDocuments.length === 0 && (
                    <div className="empty-state">
                        <p>
                            {viewMode === 'active'
                                ? 'No documents uploaded yet. Start by uploading a file above!'
                                : 'Trash is empty.'}
                        </p>
                    </div>
                )}

                {!isFetching && visibleDocuments.length > 0 && (
                    <ul className="document-list">
                        <li className="list-header">
                            <span className="header-name">File Name</span>
                            <span className="header-status">Status</span>
                            <span className="header-size">Size</span>
                            <span className="header-uploaded">Uploaded At</span>
                            <span className="header-actions">Actions</span>
                        </li>

                        {visibleDocuments.map((document) => (
                            <li key={document.id} className="document-item">
                                <span className="item-name">{document.filename}</span>
                                <span className={`status-badge ${getProcessingStatusClass(document.processing_status)}`}>
                                    {getProcessingStatusLabel(document.processing_status)}
                                </span>
                                <span className="item-size">{formatFileSize(document.size_bytes)}</span>
                                <span className="item-uploaded">{formatDateTime(document.created_at)}</span>
                                <span className="item-actions">
                                    {viewMode === 'active' ? (
                                        <>
                                            {document.processing_status === 'ready' && (
                                                <Button
                                                    variant="primary"
                                                    size="sm"
                                                    disabled={actionDocumentId === document.id || isSummaryLoading}
                                                    onClick={() => handleViewSummary(document)}
                                                >
                                                    View Summary
                                                </Button>
                                            )}
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                disabled={actionDocumentId === document.id}
                                                onClick={() => handleDownload(document)}
                                            >
                                                Download
                                            </Button>
                                            <Button
                                                variant="red"
                                                size="sm"
                                                disabled={actionDocumentId === document.id}
                                                onClick={() => handleSoftDelete(document.id)}
                                            >
                                                Delete
                                            </Button>
                                        </>
                                    ) : (
                                        <Button
                                            variant="red"
                                            size="sm"
                                            disabled={actionDocumentId === document.id}
                                            onClick={() => handlePermanentDelete(document.id)}
                                        >
                                            Delete Permanently
                                        </Button>
                                    )}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
