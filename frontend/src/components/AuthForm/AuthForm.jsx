// AuthForm.jsx - Component logic for Login and Register forms

import React, { useState } from 'react';

/**
 * Handles both the Login and Register forms, managing input state and submission logic.
 *
 * @param {string} view - 'login' or 'register' to determine which form is visible.
 * @param {function} handleLogin - Function to call on successful login/registration.
 * @param {function} setView - Function to switch the parent's view state.
 */
const AuthForm = ({ view, handleLogin, setView }) => {
    const isLogin = view === 'login';
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    // Determines the API endpoint based on the current view
    const apiEndpoint = isLogin ? 'login' : 'register';

    // Clear state when switching views
    const toggleView = (newView) => {
        setEmail('');
        setPassword('');
        setError(null);
        setView(newView);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        // Basic validation
        if (!email || !password) {
            setError('Email and password are required.');
            setIsLoading(false);
            return;
        }

        try {
            const response = await fetch(`/api/v1/auth/${apiEndpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                // Handle API errors (e.g., user exists, invalid credentials)
                const message = data.detail || `Authentication failed: ${response.statusText}`;
                setError(message);
                return;
            }

            // Success: Store token and update parent state
            localStorage.setItem('docuSageToken', data.access_token);
            localStorage.setItem('docuSageEmail', email);

            // Notify parent component (App.jsx) of successful login
            handleLogin(email);

        } catch (err) {
            console.error('Network or API call error:', err);
            setError('Could not connect to the server or process the request.');
        } finally {
            setIsLoading(false);
        }
    };

    const title = isLogin ? 'Sign In' : 'Register';
    const primaryButtonText = isLogin ? 'Log In' : 'Register';
    const togglePrompt = isLogin ? "Don't have an account? Register" : "Already have an account? Log In";

    return (
        <div className="auth-container">
            <div className="card auth-card">
                <h2 className="auth-title">{title}</h2>
                
                {/* Form Status Message */}
                {error && <div className="auth-alert alert-error">{error}</div>}
                {isLoading && <div className="auth-alert alert-loading">Processing request...</div>}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="email">Email address</label>
                        <input
                            type="email"
                            id="email"
                            className="form-input"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="you@example.com"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            className="form-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary auth-btn-submit"
                        disabled={isLoading}
                    >
                        {primaryButtonText}
                    </button>
                </form>

                <div className="auth-toggle-box">
                    <button
                        type="button"
                        onClick={() => toggleView(isLogin ? 'register' : 'login')}
                        className="btn btn-link" // Placeholder for simple link style
                    >
                        {togglePrompt}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AuthForm;
