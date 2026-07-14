/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * Authentication form for login, registration, and password reset views.
 */

import React, { useEffect, useState } from 'react';
import { forgotPassword, resetPassword } from '../../api/apiService';
import Alert from '../shared/Alert';
import Button from '../shared/Button';
import './AuthForm.css';

/**
 * Render the login/register/forgot/reset forms.
 *
 * @param {object} props
 * @param {{authError: string|null, isLoading: boolean}} props.authState - Auth state from useAuth.
 * @param {Function} props.authenticate - Authentication handler from useAuth.
 */
const AuthForm = ({ authState, authenticate }) => {
    const [mode, setMode] = useState('login'); // login | register | forgot | reset
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [resetToken, setResetToken] = useState('');
    const [successMessage, setSuccessMessage] = useState(null);
    const [localError, setLocalError] = useState(null);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const tokenFromUrl = params.get('reset_token');
        if (tokenFromUrl) {
            setResetToken(tokenFromUrl);
            setMode('reset');
        }
    }, []);

    const clearMessages = () => {
        setSuccessMessage(null);
        setLocalError(null);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        clearMessages();

        if (mode === 'login' || mode === 'register') {
            const result = await authenticate(mode, email, password);
            if (result.success && mode === 'register') {
                setSuccessMessage('Registration successful! Please log in.');
                setMode('login');
                setPassword('');
            }
            return;
        }

        setBusy(true);
        try {
            if (mode === 'forgot') {
                const data = await forgotPassword(email);
                setSuccessMessage(data.message);
            } else if (mode === 'reset') {
                const data = await resetPassword(resetToken, newPassword);
                setSuccessMessage(data.message);
                setMode('login');
                setNewPassword('');
                setResetToken('');
                window.history.replaceState({}, '', window.location.pathname);
            }
        } catch (error) {
            setLocalError(error.message);
        } finally {
            setBusy(false);
        }
    };

    const titles = {
        login: 'Sign In',
        register: 'Register Account',
        forgot: 'Forgot Password',
        reset: 'Reset Password',
    };

    return (
        <div className="form-container">
            <h2 className="form-title">{titles[mode]}</h2>

            <Alert type="error" message={authState.authError || localError} />
            <Alert type="success" message={successMessage} />

            <form onSubmit={handleSubmit} className="auth-form">
                {(mode === 'login' || mode === 'register' || mode === 'forgot') && (
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
                )}

                {(mode === 'login' || mode === 'register') && (
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
                )}

                {mode === 'reset' && (
                    <>
                        <div className="form-group">
                            <label htmlFor="resetToken">Reset token</label>
                            <input
                                id="resetToken"
                                type="text"
                                value={resetToken}
                                onChange={(event) => setResetToken(event.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="newPassword">New password</label>
                            <input
                                id="newPassword"
                                type="password"
                                value={newPassword}
                                onChange={(event) => setNewPassword(event.target.value)}
                                required
                                minLength={8}
                                placeholder="At least 8 characters"
                            />
                        </div>
                    </>
                )}

                <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    fullWidth
                    disabled={authState.isLoading || busy}
                >
                    {mode === 'login' && (authState.isLoading ? 'Logging In...' : 'Log In')}
                    {mode === 'register' && (authState.isLoading ? 'Registering...' : 'Register')}
                    {mode === 'forgot' && (busy ? 'Sending...' : 'Send reset link')}
                    {mode === 'reset' && (busy ? 'Updating...' : 'Set new password')}
                </Button>
            </form>

            <div className="form-footer">
                {mode === 'login' && (
                    <>
                        <Button variant="link" onClick={() => { clearMessages(); setMode('forgot'); }}>
                            Forgot password?
                        </Button>
                        <Button variant="link" onClick={() => { clearMessages(); setMode('register'); setPassword(''); }}>
                            Don't have an account? Register
                        </Button>
                    </>
                )}
                {mode === 'register' && (
                    <Button variant="link" onClick={() => { clearMessages(); setMode('login'); setPassword(''); }}>
                        Already have an account? Log In
                    </Button>
                )}
                {(mode === 'forgot' || mode === 'reset') && (
                    <Button variant="link" onClick={() => { clearMessages(); setMode('login'); }}>
                        Back to Sign In
                    </Button>
                )}
            </div>
        </div>
    );
};

export default AuthForm;
