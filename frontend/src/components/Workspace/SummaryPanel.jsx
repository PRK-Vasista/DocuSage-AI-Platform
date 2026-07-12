/**
 * Collapsible document summary panel with download action.
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
                        <p className="summary-muted">
                            {isFailed
                                ? (document.processing_error || 'Summary failed for this document.')
                                : 'Summary will appear when processing completes.'}
                        </p>
                    )}
                </div>
            )}
        </section>
    );
};

export default SummaryPanel;
