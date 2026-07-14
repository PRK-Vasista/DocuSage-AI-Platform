/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * Application top bar with brand, theme toggle, profile, and logout.
 */

import React, { useState } from 'react';
import { changePassword } from '../../api/apiService';
import Button from '../shared/Button';
import './TopBar.css';

/**
 * Render the DocuSage workspace header.
 *
 * @param {object} props
 * @param {boolean} props.isAuthenticated - Whether a session exists.
 * @param {string|null} props.userEmail - Authenticated user email.
 * @param {string|null} props.token - JWT bearer token.
 * @param {Function} props.logout - Logout handler.
 * @param {'light'|'dark'} props.theme - Active theme.
 * @param {Function} props.onToggleTheme - Theme toggle handler.
 */
const TopBar = ({
    isAuthenticated,
    userEmail,
    token,
    logout,
    theme,
    onToggleTheme,
}) => {
    const [profileOpen, setProfileOpen] = useState(false);
    const [showChangePassword, setShowChangePassword] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [passwordMessage, setPasswordMessage] = useState(null);
    const [passwordError, setPasswordError] = useState(null);
    const [savingPassword, setSavingPassword] = useState(false);

    const handleChangePassword = async (event) => {
        event.preventDefault();
        setPasswordError(null);
        setPasswordMessage(null);
        setSavingPassword(true);
        try {
            const data = await changePassword(currentPassword, newPassword, token);
            setPasswordMessage(data.message);
            setCurrentPassword('');
            setNewPassword('');
        } catch (error) {
            setPasswordError(error.message);
        } finally {
            setSavingPassword(false);
        }
    };

    return (
        <header className="topbar">
            <div className="topbar-inner">
                <div className="topbar-brand">
                    <span className="topbar-mark" aria-hidden="true" />
                    <h1 className="topbar-title">DocuSage</h1>
                </div>

                <div className="topbar-actions">
                    <button
                        type="button"
                        className="theme-toggle"
                        onClick={onToggleTheme}
                        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                    >
                        {theme === 'dark' ? 'Light' : 'Dark'}
                    </button>

                    {isAuthenticated ? (
                        <div className="profile-menu">
                            <button
                                type="button"
                                className="profile-trigger"
                                onClick={() => setProfileOpen((open) => !open)}
                                aria-expanded={profileOpen}
                            >
                                <span className="profile-avatar" aria-hidden="true">
                                    {(userEmail || 'U').charAt(0).toUpperCase()}
                                </span>
                                <span className="profile-email">{userEmail}</span>
                            </button>

                            {profileOpen && (
                                <div className="profile-dropdown">
                                    <p className="profile-dropdown-label">Signed in as</p>
                                    <p className="profile-dropdown-email">{userEmail}</p>

                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        fullWidth
                                        onClick={() => {
                                            setShowChangePassword((value) => !value);
                                            setPasswordError(null);
                                            setPasswordMessage(null);
                                        }}
                                    >
                                        Change password
                                    </Button>

                                    {showChangePassword && (
                                        <form className="profile-password-form" onSubmit={handleChangePassword}>
                                            <input
                                                type="password"
                                                placeholder="Current password"
                                                value={currentPassword}
                                                onChange={(event) => setCurrentPassword(event.target.value)}
                                                required
                                            />
                                            <input
                                                type="password"
                                                placeholder="New password (min 8)"
                                                value={newPassword}
                                                onChange={(event) => setNewPassword(event.target.value)}
                                                required
                                                minLength={8}
                                            />
                                            {passwordError && <p className="profile-password-error">{passwordError}</p>}
                                            {passwordMessage && <p className="profile-password-ok">{passwordMessage}</p>}
                                            <Button
                                                type="submit"
                                                variant="primary"
                                                size="sm"
                                                fullWidth
                                                disabled={savingPassword}
                                            >
                                                {savingPassword ? 'Saving...' : 'Update password'}
                                            </Button>
                                        </form>
                                    )}

                                    <Button
                                        variant="red"
                                        size="sm"
                                        fullWidth
                                        onClick={() => {
                                            setProfileOpen(false);
                                            logout();
                                        }}
                                    >
                                        Log out
                                    </Button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <span className="topbar-subtitle">Document workspace</span>
                    )}
                </div>
            </div>
        </header>
    );
};

export default TopBar;
