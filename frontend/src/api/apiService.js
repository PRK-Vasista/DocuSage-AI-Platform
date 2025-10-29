import { API_BASE_URL } from '../config'; // Assuming you have a config file or define it here

// Fallback definition if no config.js exists
const API_BASE_URL_FALLBACK = 'http://localhost:8000/api/v1'; 
const BASE_URL = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : API_BASE_URL_FALLBACK;

/**
 * Helper to construct authorized fetch calls.
 * @param {string} endpoint - The API endpoint suffix (e.g., '/files/upload').
 * @param {object} options - Fetch options (method, body, headers).
 * @param {string} token - JWT access token.
 * @returns {Promise<Response>}
 */
const authorizedFetch = (endpoint, options = {}, token) => {
    const defaultHeaders = {
        'Authorization': `Bearer ${token}`,
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    return fetch(`${BASE_URL}${endpoint}`, config);
};


// --- AUTHENTICATION API CALLS ---

/**
 * Registers a new user.
 * @param {string} email - User email.
 * @param {string} password - User password.
 * @returns {Promise<object>} - Parsed JSON response (User data and token).
 */
export async function register(email, password) {
    try {
        const response = await fetch(`${BASE_URL}/auth/register`, { // Use BASE_URL
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();
        
        if (!response.ok) {
            // FastAPI error responses have a 'detail' field
            throw new Error(data.detail || `Registration failed with status ${response.status}`);
        }

        return data; // Should contain { access_token, token_type }
    } catch (error) {
        console.error("API Register Error:", error);
        throw error;
    }
}

/**
 * Logs in a user and retrieves a JWT token.
 * @param {string} email - User email.
 * @param {string} password - User password.
 * @returns {Promise<object>} - Parsed JSON response (Token data).
 */
export async function login(email, password) {
    try {
        const response = await fetch(`${BASE_URL}/auth/login`, { // Use BASE_URL
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        
        const data = await response.json();

        if (!response.ok) {
            // Throw the error detail from the server for display in the UI
            throw new Error(data.detail || `Login failed with status ${response.status}`);
        }

        return data; // Should contain { access_token, token_type }
    } catch (error) {
        console.error("API Login Error:", error);
        throw error;
    }
}


// --- FILE MANAGEMENT API CALLS (Existing Code) ---

/**
 * Uploads a file to the backend.
 * @param {File} file - The file object to upload.
 * @param {string} token - JWT access token.
 * @returns {Promise<object>} - Parsed JSON response from the server.
 */
export async function uploadFile(file, token) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await authorizedFetch('/files/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Crucial for FormData
        }, token);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("API Upload Error:", error);
        throw error;
    }
}

/**
 * Fetches the list of files uploaded by the current user.
 * @param {string} token - JWT access token.
 * @returns {Promise<Array<object>>} - List of files.
 */
export async function listFiles(token) {
    try {
        const response = await authorizedFetch('/files/', {
            method: 'GET',
        }, token);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to fetch files with status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("API Fetch Files Error:", error);
        throw error;
    }
}
