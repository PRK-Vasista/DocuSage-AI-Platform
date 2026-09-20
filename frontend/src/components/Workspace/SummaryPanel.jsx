/**
 * Collapsible document summary panel with download and retry actions.
 */

import React from 'react';
import Button from '../shared/Button';
import './SummaryPanel.css';

/**
 * Render the summary section for the selected document.
 *
 * @param {object} props
 */
const SummaryPanel = ({
    document,
    summaryText,
    isLoading,
    isCollapsed,
    onToggleCollapse,
    onDownloadSummary,
    onRetryProcessing,
    isRetrying,
}) => {
    if (!document) {
        return null;
    }

    const isReady = document.processing_status === 'ready' && Boolean(summaryText);
    const isFailed = document.processing_status === 'failed';

    return (
        <section className={`summary-panel ${isCollapsed ? 'is-collapsed' : ''}`}>
            <div className="summary-panel-header">
                <div>
                    <h3 className="summary-panel-title">Summary</h3>
                    <p className="summary-panel-subtitle">{document.filename}</p>
                </div>
                <div className="summary-panel-actions">
                    {isFailed && (
                        <Button
                            variant="primary"
                            size="sm"
                            disabled={isRetrying}
                            onClick={onRetryProcessing}
                        >
                            {isRetrying ? 'Retrying...' : 'Retry processing'}
                        </Button>
                    )}
                    <Button
                        variant="secondary"
                        size="sm"
                        disabled={!isReady}
                        onClick={onDownloadSummary}
                    >
                        Download summary
                    </Button>
                    <Button variant="secondary" size="sm" onClick={onToggleCollapse}>
                        {isCollapsed ? 'Expand' : 'Collapse'}
                    </Button>
                </div>
            </div>

            {!isCollapsed && (
                <div className="summary-panel-body">
                    {isLoading && <p className="summary-muted">Loading summary...</p>}
                    {!isLoading && isReady && (
                        <p className="summary-text">{summaryText}</p>
                    )}
                    {!isLoading && !isReady && (
                        <div className="summary-failed-block">
                            <p className="summary-muted">
                                {isFailed
                                    ? (document.processing_error
                                        || 'Processing failed for this document.')
                                    : 'Summary will appear when processing completes.'}
                            </p>
                            {isFailed && (
                                <p className="summary-hint">
                                    You can retry processing without re-uploading the file.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            )}
        </section>
    );
};

export default SummaryPanel;
