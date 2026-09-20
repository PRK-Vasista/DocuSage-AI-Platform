/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * API service layer for DocuSage frontend.
 *
 * All HTTP communication with the backend is centralized here so UI
 * components remain decoupled from fetch details and endpoint paths.
 */

import { API_BASE_URL, BACKEND_ROOT_URL } from '../config/appConfig';

/**
 * Parse a FastAPI error response into a readable message.
 *
 * @param {object} errorData - Parsed JSON error payload.
 * @param {number} status - HTTP status code.
 * @param {string} fallback - Default message if detail is unavailable.
 * @returns {string} Human-readable error message.
 */
function extractErrorMessage(errorData, status, fallback) {
    if (!errorData) {
        return fallback;
    }

    if (typeof errorData.detail === 'string') {
        return errorData.detail;
    }

    if (Array.isArray(errorData.detail)) {
        return errorData.detail.map((item) => item.msg || JSON.stringify(item)).join(', ');
    }

    return `${fallback}: HTTP ${status}`;
}

/**
 * Build an authorized fetch request against the DocuSage API.
 *
 * @param {string} endpoint - API path suffix such as `/files/upload`.
 * @param {object} options - Standard fetch options.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<Response>} Raw fetch response.
 */
function authorizedFetch(endpoint, options = {}, token) {
    const config = {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            ...options.headers,
        },
    };

    return fetch(`${API_BASE_URL}${endpoint}`, config);
}

/**
 * Register a new user account.
 *
 * @param {string} email - User email address.
 * @param {string} password - Plain-text password.
 * @returns {Promise<object>} Token payload from the backend.
 */
export async function register(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Registration failed'));
    }

    return data;
}

/**
 * Log in an existing user and retrieve a JWT token.
 *
 * @param {string} email - User email address.
 * @param {string} password - Plain-text password.
 * @returns {Promise<object>} Token payload from the backend.
 */
export async function login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Login failed'));
    }

    return data;
}

/**
 * Request a password reset email (or development log link).
 *
 * @param {string} email - Account email.
 * @returns {Promise<object>} Message payload.
 */
export async function forgotPassword(email) {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Forgot password failed'));
    }

    return data;
}

/**
 * Reset password using a one-time token.
 *
 * @param {string} token - Reset token from email/link.
 * @param {string} newPassword - New password.
 * @returns {Promise<object>} Message payload.
 */
export async function resetPassword(token, newPassword) {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Reset password failed'));
    }

    return data;
}

/**
 * Change password for the authenticated user.
 *
 * @param {string} currentPassword - Current password.
 * @param {string} newPassword - New password.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Message payload.
 */
export async function changePassword(currentPassword, newPassword, token) {
    const response = await authorizedFetch('/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
        }),
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Change password failed'));
    }

    return data;
}

/**
 * Fetch backend aggregate health (DB + AI).
 *
 * @returns {Promise<object>} Health payload.
 */
export async function fetchBackendHealth() {
    const response = await fetch(`${BACKEND_ROOT_URL}/health`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Health check failed'));
    }
    return data;
}

/**
 * Upload a document for the authenticated user.
 *
 * @param {File} file - Browser File object.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Uploaded document metadata.
 */
export async function uploadFile(file, token) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await authorizedFetch('/files/upload', {
        method: 'POST',
        body: formData,
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Upload failed'));
    }

    return data;
}

/**
 * List documents for the authenticated user.
 *
 * @param {string} token - JWT bearer token.
 * @param {boolean} includeDeleted - Whether to include trashed documents.
 * @returns {Promise<object>} Document list and storage quota summary.
 */
export async function listFiles(token, includeDeleted = false) {
    const query = includeDeleted ? '?include_deleted=true' : '';
    const response = await authorizedFetch(`/files/${query}`, {
        method: 'GET',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Failed to fetch documents'));
    }

    return data;
}

/**
 * Soft-delete a document by moving it to trash.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Deletion confirmation payload.
 */
export async function softDeleteFile(documentId, token) {
    const response = await authorizedFetch(`/files/${documentId}`, {
        method: 'DELETE',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Soft delete failed'));
    }

    return data;
}

/**
 * Permanently delete a document that is already in trash.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Permanent deletion confirmation payload.
 */
export async function permanentlyDeleteFile(documentId, token) {
    const response = await authorizedFetch(`/files/${documentId}/permanent`, {
        method: 'DELETE',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Permanent delete failed'));
    }

    return data;
}

/**
 * Retry processing for a failed document.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Updated document metadata.
 */
export async function reprocessFile(documentId, token) {
    const response = await authorizedFetch(`/files/${documentId}/reprocess`, {
        method: 'POST',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Reprocess failed'));
    }

    return data;
}

/**
 * Fetches summarized text for a processed document.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Summary payload from the backend.
 */
export async function getDocumentSummary(documentId, token) {
    const response = await authorizedFetch(`/files/${documentId}/summary`, {
        method: 'GET',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Failed to fetch document summary'));
    }

    return data;
}

/**
 * Fetch chat history for a document.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Chat history payload.
 */
export async function getDocumentChatHistory(documentId, token) {
    const response = await authorizedFetch(`/chat/${documentId}`, {
        method: 'GET',
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Failed to fetch chat history'));
    }

    return data;
}

/**
 * Ask a question about a document and receive an AI answer.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} question - User question.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<object>} Chat ask response with updated history.
 */
export async function askDocumentChat(documentId, question, token) {
    const response = await authorizedFetch(`/chat/${documentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    }, token);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(extractErrorMessage(data, response.status, 'Chat request failed'));
    }

    return data;
}

/**
 * Download a document as a browser file save action.
 *
 * @param {number} documentId - Document identifier.
 * @param {string} filename - Filename to use for the downloaded file.
 * @param {string} token - JWT bearer token.
 * @returns {Promise<void>}
 */
export async function downloadFile(documentId, filename, token) {
    const response = await authorizedFetch(`/files/${documentId}/download`, {
        method: 'GET',
    }, token);

    if (!response.ok) {
        let message = 'Download failed';
        try {
            const data = await response.json();
            message = extractErrorMessage(data, response.status, message);
        } catch (error) {
            console.error('Failed to parse download error response:', error);
        }
        throw new Error(message);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}
