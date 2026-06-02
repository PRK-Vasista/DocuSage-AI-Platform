/**
 * Shared formatting helpers for the DocuSage frontend.
 */

/**
 * Convert a byte count into a human-readable string.
 *
 * @param {number} bytes - Number of bytes.
 * @returns {string} Human-readable size such as "1.25 MB".
 */
export function formatFileSize(bytes) {
    if (bytes === 0) {
        return '0 B';
    }

    const units = ['B', 'KB', 'MB', 'GB'];
    const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / (1024 ** exponent);
    return `${value.toFixed(exponent === 0 ? 0 : 2)} ${units[exponent]}`;
}

/**
 * Format an ISO timestamp for display in the UI.
 *
 * @param {string|Date} value - Date value from the API.
 * @returns {string} Localized date/time string.
 */
export function formatDateTime(value) {
    if (!value) {
        return '-';
    }

    return new Date(value).toLocaleString();
}
