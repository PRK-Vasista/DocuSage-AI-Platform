/**
 * Application top bar with brand, theme toggle, profile, and logout.
 */

import React, { useState } from 'react';
import Button from '../shared/Button';
import './TopBar.css';

/**
 * Render the DocuSage workspace header.
 *
 * @param {object} props
 * @param {boolean} props.isAuthenticated - Whether a session exists.
 * @param {string|null} props.userEmail - Authenticated user email.
 * @param {Function} props.logout - Logout handler.
 * @param {'light'|'dark'} props.theme - Active theme.
 * @param {Function} props.onToggleTheme - Theme toggle handler.
 */
const TopBar = ({
    isAuthenticated,
    userEmail,
    logout,
    theme,
    onToggleTheme,
}) => {
    const [profileOpen, setProfileOpen] = useState(false);

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
