// useAuth.js - Custom hook for managing authentication state and actions.

import { useState, useEffect, useCallback } from 'react';

// Central API configuration (Conceptual: In a real app, this would come from a config file)
const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Custom hook to handle JWT-based authentication state and actions.
 * @returns {object} Auth state and functions.
 */
const useAuth = () => {
    // Check local storage for an existing token on initialization
    const initialToken = localStorage.getItem('token');
    
    // State to track if the user is authenticated (based on token presence)
    const [isAuthenticated, setIsAuthenticated] = useState(!!initialToken);
    
    // State to hold any authentication-related error messages
    const [authError, setAuthError] = useState(null);
    
    // State to track loading status during login/register attempts
    const [isLoading, setIsLoading] = useState(false);

    /**
     * Clears local storage and resets the authentication state.
     */
    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setAuthError(null);
        // Optionally, force a refresh or redirect here if needed
        console.log("User logged out.");
    }, []);

    /**
     * Handles the authentication request (login or register).
     * @param {string} endpoint - 'login' or 'register'.
     * @param {string} email - User's email.
     * @param {string} password - User's password.
     */
    const authenticate = useCallback(async (endpoint, email, password) => {
        setIsLoading(true);
        setAuthError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok && data.access_token) {
                // Successful authentication
                localStorage.setItem('token', data.access_token);
                setIsAuthenticated(true);
                setAuthError(null);
                return { success: true };
            } else {
                // Failed authentication (e.g., wrong password, user exists)
                const errorMessage = data.detail || `Authentication failed: ${response.statusText}`;
                setAuthError(errorMessage);
                return { success: false, message: errorMessage };
            }
        } catch (error) {
            // Network or parsing error
            const errorMessage = "A network error occurred. Please check your connection.";
            setAuthError(errorMessage);
            console.error("Authentication fetch error:", error);
            return { success: false, message: errorMessage };
        } finally {
            setIsLoading(false);
        }
    }, []);
    
    // Simple effect to log authentication status changes (optional)
    useEffect(() => {
        console.log(`Authentication status changed: ${isAuthenticated ? 'Authenticated' : 'Not Authenticated'}`);
    }, [isAuthenticated]);

    return {
        isAuthenticated,
        authError,
        isLoading,
        authenticate,
        logout
    };
};

export default useAuth;

