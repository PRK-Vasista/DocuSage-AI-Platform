/**
 * Central frontend configuration for DocuSage.
 *
 * Environment-specific values should be injected here so components and API
 * services remain decoupled from hard-coded URLs and storage keys.
 */

/** Base URL for all backend API requests. */
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

/** Local storage key used for the JWT access token. */
export const AUTH_TOKEN_KEY = 'token';

/** Local storage key used for the authenticated user's email. */
export const AUTH_EMAIL_KEY = 'userEmail';

/** Local storage key for light/dark theme preference. */
export const THEME_STORAGE_KEY = 'docuSageTheme';

/** Maximum upload size exposed to the UI (must match backend policy). */
export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;

/** Maximum total storage per user exposed to the UI (must match backend policy). */
export const MAX_USER_STORAGE_BYTES = 1024 * 1024 * 1024;

/** Allowed upload extensions shown in the file picker. */
export const ALLOWED_UPLOAD_EXTENSIONS = '.pdf,.txt,.md,.markdown,.docx,.csv,.json,.xml,.html,.htm,.rtf,.log';
