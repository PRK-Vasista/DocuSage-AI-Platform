/**
 * Top navigation bar for DocuSage.
 */

import React from 'react';
import Button from '../shared/Button';
import './Navbar.css';

/**
 * Render the application header and authenticated user actions.
 *
 * @param {object} props
 * @param {boolean} props.isAuthenticated - Whether a valid session exists.
 * @param {string|null} props.userEmail - Authenticated user's email.
 * @param {Function} props.logout - Logout handler.
 */
const Navbar = ({ isAuthenticated, userEmail, logout }) => (
    <header className="navbar-header">
        <div className="navbar-container">
            <h1 className="app-title">DocuSage AI</h1>

            {isAuthenticated ? (
                <nav className="nav-menu">
                    <span className="user-email">Hello, {userEmail}</span>
                    <Button variant="red" onClick={logout}>
                        Logout
                    </Button>
                </nav>
            ) : (
                <nav className="nav-menu">
                    <span className="user-email">Secure document analysis platform</span>
                </nav>
            )}
        </div>
    </header>
);

export default Navbar;
