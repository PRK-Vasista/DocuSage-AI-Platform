/**
 * Authentication form for login and registration views.
 */

import React, { useState } from 'react';
import Alert from '../shared/Alert';
import Button from '../shared/Button';
import './AuthForm.css';

/**
 * Render the login/register form and delegate authentication to the parent hook.
 *
 * @param {object} props
 * @param {{authError: string|null, isLoading: boolean}} props.authState - Auth state from useAuth.
 * @param {Function} props.authenticate - Authentication handler from useAuth.
 */
const AuthForm = ({ authState, authenticate }) => {
    const [isLoginView, setIsLoginView] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [successMessage, setSuccessMessage] = useState(null);

    /**
     * Submit the login or registration form.
     *
     * @param {Event} event - Form submit event.
     */
    const handleSubmit = async (event) => {
        event.preventDefault();
        setSuccessMessage(null);

        const mode = isLoginView ? 'login' : 'register';
        const result = await authenticate(mode, email, password);

        if (result.success && !isLoginView) {
            setSuccessMessage('Registration successful! Please log in.');
            setIsLoginView(true);
            setPassword('');
        }
    };

    /**
     * Toggle between login and registration views.
     */
    const toggleView = () => {
        setIsLoginView((current) => !current);
        setEmail('');
        setPassword('');
        setSuccessMessage(null);
    };

    const title = isLoginView ? 'Sign In' : 'Register Account';

    return (
        <div className="form-container">
            <h2 className="form-title">{title}</h2>

            <Alert type="error" message={authState.authError} />
            <Alert type="success" message={successMessage} />

            <form onSubmit={handleSubmit} className="auth-form">
                <div className="form-group">
                    <label htmlFor="email">Email address</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        required
                        placeholder="you@example.com"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        required
                        placeholder="••••••••"
                    />
                </div>

                <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    fullWidth
                    disabled={authState.isLoading}
                >
                    {authState.isLoading
                        ? (isLoginView ? 'Logging In...' : 'Registering...')
                        : (isLoginView ? 'Log In' : 'Register')}
                </Button>
            </form>

            <div className="form-footer">
                <Button variant="link" onClick={toggleView}>
                    {isLoginView
                        ? "Don't have an account? Register"
                        : 'Already have an account? Log In'}
                </Button>
            </div>
        </div>
    );
};

export default AuthForm;
