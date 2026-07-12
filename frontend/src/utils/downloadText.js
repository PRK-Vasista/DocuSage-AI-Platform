/**
 * Client-side helpers for downloading text content as a file.
 */

/**
 * Trigger a browser download for plain-text content.
 *
 * @param {string} filename - Suggested download filename.
 * @param {string} text - File body content.
 * @returns {void}
 */
export function downloadTextFile(filename, text) {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}
