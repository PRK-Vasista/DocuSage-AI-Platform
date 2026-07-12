/**
 * Left document rail for the DocuSage workspace.
 */

import React, { useRef } from 'react';
import {
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
} from '../../config/appConfig';
import { formatDateTime, formatFileSize } from '../../utils/formatters';
import {
    getProcessingStatusClass,
    getProcessingStatusLabel,
} from '../../utils/processingStatus';
import Button from '../shared/Button';
import './DocumentSidebar.css';

/**
 * Render document list, upload controls, trash filter, and storage quota.
 *
 * @param {object} props
 */
const DocumentSidebar = ({
    viewMode,
    onViewModeChange,
    documents,
    selectedDocumentId,
    onSelectDocument,
    storage,
    isFetching,
    isUploading,
    actionDocumentId,
    statusMessage,
    onUpload,
    onSoftDelete,
    onPermanentDelete,
    onDownloadOriginal,
}) => {
    const fileInputRef = useRef(null);

    const handleFilePicked = (event) => {
        const file = event.target.files?.[0];
        if (!file) {
            return;
        }
        onUpload(file);
        event.target.value = '';
    };

    return (
        <aside className="doc-sidebar">
            <div className="doc-sidebar-header">
                <h2 className="doc-sidebar-title">Documents</h2>
                <div className="doc-sidebar-tabs">
                    <button
                        type="button"
                        className={`rail-tab ${viewMode === 'active' ? 'is-active' : ''}`}
                        onClick={() => onViewModeChange('active')}
                    >
                        Active
                    </button>
                    <button
                        type="button"
                        className={`rail-tab ${viewMode === 'trash' ? 'is-active' : ''}`}
                        onClick={() => onViewModeChange('trash')}
                    >
                        Trash
                    </button>
                </div>
            </div>

            {viewMode === 'active' && (
                <div className="doc-upload-block">
                    <input
                        ref={fileInputRef}
                        type="file"
                        className="visually-hidden"
                        accept={ALLOWED_UPLOAD_EXTENSIONS}
                        onChange={handleFilePicked}
                        disabled={isUploading}
                    />
                    <Button
                        variant="primary"
                        size="sm"
                        fullWidth
                        disabled={isUploading}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        {isUploading ? 'Uploading...' : 'Add file'}
                    </Button>
                    <p className="doc-upload-hint">
                        Max {formatFileSize(MAX_UPLOAD_SIZE_BYTES)} · PDF, TXT, DOCX, MD...
                    </p>
                </div>
            )}

            {statusMessage && (
                <p className={`doc-sidebar-status doc-sidebar-status-${statusMessage.type}`}>
                    {statusMessage.message}
                </p>
            )}

            <div className="doc-list-scroll">
                {isFetching && <p className="doc-empty">Loading documents...</p>}

                {!isFetching && documents.length === 0 && (
                    <p className="doc-empty">
                        {viewMode === 'active'
                            ? 'No documents yet. Add a file to start.'
                            : 'Trash is empty.'}
                    </p>
                )}

                {!isFetching && documents.map((document) => {
                    const isSelected = document.id === selectedDocumentId;
                    return (
                        <article
                            key={document.id}
                            className={`doc-item ${isSelected ? 'is-selected' : ''}`}
                        >
                            <button
                                type="button"
                                className="doc-item-main"
                                onClick={() => onSelectDocument(document)}
                            >
                                <span className="doc-item-name">{document.filename}</span>
                                <span className="doc-item-meta">
                                    <span className={`status-badge ${getProcessingStatusClass(document.processing_status)}`}>
                                        {getProcessingStatusLabel(document.processing_status)}
                                    </span>
                                    <span>{formatFileSize(document.size_bytes)}</span>
                                </span>
                                <span className="doc-item-date">{formatDateTime(document.created_at)}</span>
                            </button>

                            <div className="doc-item-actions">
                                {viewMode === 'active' ? (
                                    <>
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            disabled={actionDocumentId === document.id}
                                            onClick={() => onDownloadOriginal(document)}
                                        >
                                            File
                                        </Button>
                                        <Button
                                            variant="red"
                                            size="sm"
                                            disabled={actionDocumentId === document.id}
                                            onClick={() => onSoftDelete(document.id)}
                                        >
                                            Remove
                                        </Button>
                                    </>
                                ) : (
                                    <Button
                                        variant="red"
                                        size="sm"
                                        disabled={actionDocumentId === document.id}
                                        onClick={() => onPermanentDelete(document.id)}
                                    >
                                        Delete forever
                                    </Button>
                                )}
                            </div>
                        </article>
                    );
                })}
            </div>

            {storage && (
                <footer className="doc-quota">
                    <div className="doc-quota-bar">
                        <div
                            className="doc-quota-fill"
                            style={{
                                width: `${Math.min(
                                    100,
                                    (storage.used_bytes / Math.max(storage.limit_bytes, 1)) * 100,
                                )}%`,
                            }}
                        />
                    </div>
                    <p className="doc-quota-text">
                        {formatFileSize(storage.used_bytes)} / {formatFileSize(storage.limit_bytes)}
                    </p>
                </footer>
            )}
        </aside>
    );
};

export default DocumentSidebar;
