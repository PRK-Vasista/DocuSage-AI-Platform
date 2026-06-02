/**
 * Helpers for document processing status display.
 */

/** Maps backend processing status codes to user-facing labels. */
const STATUS_LABELS = {
    uploaded: 'Uploaded',
    processing: 'Processing',
    ready: 'Ready',
    failed: 'Failed',
};

/** Maps backend processing status codes to CSS badge class suffixes. */
const STATUS_BADGE_CLASSES = {
    uploaded: 'status-uploaded',
    processing: 'status-processing',
    ready: 'status-ready',
    failed: 'status-failed',
};

/**
 * Resolve a human-readable label for a processing status code.
 *
 * @param {string} status - Backend processing status value.
 * @returns {string} Display label.
 */
export function getProcessingStatusLabel(status) {
    return STATUS_LABELS[status] || status;
}

/**
 * Resolve a CSS class suffix for a processing status badge.
 *
 * @param {string} status - Backend processing status value.
 * @returns {string} CSS class suffix.
 */
export function getProcessingStatusClass(status) {
    return STATUS_BADGE_CLASSES[status] || 'status-unknown';
}

/**
 * Determine whether the UI should poll for processing updates.
 *
 * @param {Array<object>} documents - Document list from the API.
 * @returns {boolean} True when at least one document is still processing.
 */
export function shouldPollDocuments(documents) {
    return documents.some(
        (document) => document.processing_status === 'uploaded'
            || document.processing_status === 'processing',
    );
}
