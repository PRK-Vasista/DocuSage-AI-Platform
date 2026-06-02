/**
 * Authenticated user dashboard for document upload and management.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
    downloadFile,
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
import Alert from '../shared/Alert';
import Button from '../shared/Button';
import './Dashboard.css';

/**
 * Render upload, active document list, and trash management views.
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

    /**
     * Load active and trashed documents from the backend.
     */
    const loadDocuments = useCallback(async () => {
        if (!token) {
            return;
        }

        setIsFetching(true);
        setStatusAlert(null);

        try {
            const [activeResponse, trashResponse] = await Promise.all([
                listFiles(token, false),
                listFiles(token, true),
            ]);

            setActiveDocuments(activeResponse.documents || []);
            setStorage(activeResponse.storage || null);

            const trashedOnly = (trashResponse.documents || []).filter((doc) => doc.is_deleted);
            setTrashedDocuments(trashedOnly);

            console.info('[Dashboard] Documents loaded successfully.');
        } catch (error) {
            console.error('[Dashboard] Failed to load documents:', error);
            setStatusAlert({ type: 'error', message: error.message });
            setActiveDocuments([]);
            setTrashedDocuments([]);
        } finally {
            setIsFetching(false);
        }
    }, [token]);

    useEffect(() => {
        loadDocuments();
    }, [loadDocuments]);

    /**
     * Handle file input changes and perform client-side size validation.
     *
     * @param {Event} event - File input change event.
     */
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

    /**
     * Upload the selected file to the backend.
     *
     * @param {Event} event - Form submit event.
     */
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
                message: `Uploaded '${uploadedDocument.filename}' successfully.`,
            });
            setSelectedFile(null);
            event.target.reset();
            await loadDocuments();
        } catch (error) {
            console.error('[Dashboard] Upload failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setIsUploading(false);
        }
    };

    /**
     * Soft-delete a document by moving it to trash.
     *
     * @param {number} documentId - Document identifier.
     */
    const handleSoftDelete = async (documentId) => {
        setActionDocumentId(documentId);
        setStatusAlert({ type: 'info', message: 'Moving document to trash...' });

        try {
            await softDeleteFile(documentId, token);
            setStatusAlert({ type: 'success', message: 'Document moved to trash.' });
            await loadDocuments();
        } catch (error) {
            console.error('[Dashboard] Soft delete failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    /**
     * Permanently delete a trashed document.
     *
     * @param {number} documentId - Document identifier.
     */
    const handlePermanentDelete = async (documentId) => {
        setActionDocumentId(documentId);
        setStatusAlert({ type: 'info', message: 'Permanently deleting document...' });

        try {
            await permanentlyDeleteFile(documentId, token);
            setStatusAlert({ type: 'success', message: 'Document permanently deleted.' });
            await loadDocuments();
        } catch (error) {
            console.error('[Dashboard] Permanent delete failed:', error);
            setStatusAlert({ type: 'error', message: error.message });
        } finally {
            setActionDocumentId(null);
        }
    };

    /**
     * Download a document through the backend download endpoint.
     *
     * @param {object} document - Document metadata object.
     */
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

    const visibleDocuments = viewMode === 'active' ? activeDocuments : trashedDocuments;

    return (
        <div className="dashboard-container">
            <h2 className="dashboard-title">Welcome to DocuSage!</h2>
            <p className="dashboard-intro">Securely upload and manage your text-based documents.</p>

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
                            <span className="header-size">Size</span>
                            <span className="header-uploaded">Uploaded At</span>
                            <span className="header-actions">Actions</span>
                        </li>

                        {visibleDocuments.map((document) => (
                            <li key={document.id} className="document-item">
                                <span className="item-name">{document.filename}</span>
                                <span className="item-size">{formatFileSize(document.size_bytes)}</span>
                                <span className="item-uploaded">{formatDateTime(document.created_at)}</span>
                                <span className="item-actions">
                                    {viewMode === 'active' ? (
                                        <>
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
