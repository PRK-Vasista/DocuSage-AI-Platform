// Navbar.jsx - Component logic without styles

import React from 'react';

const Navbar = ({ isLoggedIn, email, handleLogout, setView }) => {
    return (
        <header className="navbar-header">
            <div className="navbar-container">
                <h1 className="app-title">DocuSage AI</h1>
                
                {isLoggedIn ? (
                    // --- Logged In View ---
                    <nav className="nav-menu">
                        <span className="user-email">
                            Hello, {email}!
                        </span>
                        <button 
                            onClick={handleLogout}
                            className="btn btn-red" // Placeholder for btn-red style
                        >
                            Logout
                        </button>
                    </nav>
                ) : (
                    // --- Logged Out View ---
                    <nav className="nav-menu">
                        <button
                            onClick={() => setView('login')}
                            className="btn btn-secondary" // Placeholder for btn-secondary style
                        >
                            Login
                        </button>
                        <button
                            onClick={() => setView('register')}
                            className="btn btn-primary"
                        >
                            Register
                        </button>
                    </nav>
                )}
            </div>
        </header>
    );
};

export default Navbar;

