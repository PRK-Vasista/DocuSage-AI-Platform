/**
 * Authentication hook for DocuSage.
 *
 * Centralizes JWT persistence, login/register actions, and auth state so UI
 * components remain presentation-focused.
 */

import { useCallback, useEffect, useState } from 'react';
import { login as apiLogin, register as apiRegister } from '../api/apiService';
import { AUTH_EMAIL_KEY, AUTH_TOKEN_KEY } from '../config/appConfig';

/**
 * Manage authentication state and actions for the application shell.
 *
 * @returns {object} Authentication state and helper functions.
 */
const useAuth = () => {
    const initialToken = localStorage.getItem(AUTH_TOKEN_KEY);
    const initialEmail = localStorage.getItem(AUTH_EMAIL_KEY);

    const [token, setToken] = useState(initialToken);
    const [userEmail, setUserEmail] = useState(initialEmail);
    const [isAuthenticated, setIsAuthenticated] = useState(Boolean(initialToken));
    const [authError, setAuthError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    /**
     * Clear authentication state and remove persisted credentials.
     */
    const logout = useCallback(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(AUTH_EMAIL_KEY);
        setToken(null);
        setUserEmail(null);
        setIsAuthenticated(false);
        setAuthError(null);
        console.info('[useAuth] User logged out.');
    }, []);

    /**
     * Authenticate the user via login or registration.
     *
     * @param {'login'|'register'} mode - Authentication mode.
     * @param {string} email - User email address.
     * @param {string} password - Plain-text password.
     * @returns {Promise<{success: boolean, message?: string}>}
     */
    const authenticate = useCallback(async (mode, email, password) => {
        setIsLoading(true);
        setAuthError(null);

        try {
            const authFn = mode === 'login' ? apiLogin : apiRegister;
            const data = await authFn(email, password);

            localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
            localStorage.setItem(AUTH_EMAIL_KEY, email);
            setToken(data.access_token);
            setUserEmail(email);
            setIsAuthenticated(true);

            console.info(`[useAuth] ${mode} successful for ${email}`);
            return { success: true };
        } catch (error) {
            const message = error.message || 'Authentication failed.';
            setAuthError(message);
            console.error(`[useAuth] ${mode} failed:`, error);
            return { success: false, message };
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        console.debug(
            `[useAuth] Authentication status changed: ${isAuthenticated ? 'authenticated' : 'guest'}`,
        );
    }, [isAuthenticated]);

    return {
        token,
        userEmail,
        isAuthenticated,
        authError,
        isLoading,
        authenticate,
        logout,
    };
};

export default useAuth;
