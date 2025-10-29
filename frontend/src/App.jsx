// This file combines all modular logic (AuthForm, Dashboard, Navbar, Alert, Button, useAuth)
// It now relies on an external stylesheet (app.css) for all presentation.

import React, { useState, useEffect, useCallback } from 'react';
import './app.css';

// --- API Service Logic (Conceptual: src/api/apiService.js) ---
const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Handles fetching the list of documents for the authenticated user.
 * @param {string} token - The user's JWT token.
 * @returns {Array} List of document objects or an empty array on failure.
 */
const fetchDocuments = async (token) => {
    try {
        const response = await fetch(`${API_BASE_URL}/files/list`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            // Log and return empty array if authentication or server fails
            console.error("Failed to fetch documents:", response.status, response.statusText);
            return [];
        }

        const data = await response.json();
        return data; // Expects an array of file metadata
    } catch (error) {
        console.error("Network error during document list fetch:", error);
        return [];
    }
};

/**
 * Handles the secure file upload to the backend.
 * @param {File} file - The file to upload.
 * @param {string} token - The user's JWT token.
 * @returns {object} Success status and message.
 */
const uploadFile = async (file, token) => {
    if (!file) return { success: false, message: "Please select a file." };

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/files/upload`, {
            method: 'POST',
            headers: {
                // IMPORTANT: Do NOT set Content-Type header when sending FormData; 
                // the browser sets it automatically (multipart/form-data)
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            return { success: true, message: data.message || "File uploaded successfully!" };
        } else {
            return { success: false, message: data.detail || `Upload failed: ${response.statusText}` };
        }
    } catch (error) {
        console.error("Network error during file upload:", error);
        return { success: false, message: "Network error during upload." };
    }
};


// --- useAuth Hook Logic (Conceptual: src/hooks/useAuth.js) ---

/**
 * Custom hook to handle JWT-based authentication state and actions.
 */
const useAuth = () => {
    const initialToken = localStorage.getItem('token');
    
    const [isAuthenticated, setIsAuthenticated] = useState(!!initialToken);
    const [authError, setAuthError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setAuthError(null);
        console.log("User logged out.");
    }, []);

    const authenticate = useCallback(async (endpoint, email, password) => {
        setIsLoading(true);
        setAuthError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok && data.access_token) {
                localStorage.setItem('token', data.access_token);
                setIsAuthenticated(true);
                setAuthError(null);
                return { success: true };
            } else {
                const errorMessage = data.detail || `Authentication failed: ${response.statusText}`;
                setAuthError(errorMessage);
                return { success: false, message: errorMessage };
            }
        } catch (error) {
            const errorMessage = "A network error occurred. Please check your connection.";
            setAuthError(errorMessage);
            console.error("Authentication fetch error:", error);
            return { success: false, message: errorMessage };
        } finally {
            setIsLoading(false);
        }
    }, []);
    
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


// --- Shared Components (Conceptual: src/components/shared/Alert.jsx & src/components/shared/Button.jsx) ---

/**
 * Reusable component to display alert messages.
 */
const Alert = ({ type = 'info', message }) => {
    if (!message) {
        return null;
    }
    const alertClasses = `alert alert-${type}`;
    return (
        <div className={alertClasses} role="alert">
            <span className="alert-message">{message}</span>
        </div>
    );
};

/**
 * Reusable button component.
 */
const Button = ({
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    disabled = false,
    className = '',
    children,
    onClick,
    type = 'button',
    ...rest
}) => {
    const baseClasses = `btn btn-${variant} btn-${size}`;
    const widthClass = fullWidth ? 'w-full' : '';
    const finalClasses = `${baseClasses} ${widthClass} ${className}`.trim();

    return (
        <button
            type={type}
            className={finalClasses}
            onClick={onClick}
            disabled={disabled}
            {...rest}
        >
            {children}
        </button>
    );
};


// --- Component: AuthForm (Conceptual: src/components/AuthForm/AuthForm.jsx) ---

const AuthForm = ({ authState, authenticate }) => {
    const [isLoginView, setIsLoginView] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [successMessage, setSuccessMessage] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSuccessMessage(null); // Clear success message on new attempt
        
        const endpoint = isLoginView ? 'login' : 'register';
        const result = await authenticate(endpoint, email, password);

        if (result.success && !isLoginView) {
            // Registration success, switch to login view
            setSuccessMessage("Registration successful! Please log in.");
            setIsLoginView(true);
        }
        // Auth hook handles error message and login success (isAuthenticated state change)
    };

    const toggleView = () => {
        setIsLoginView(!isLoginView);
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
                        onChange={(e) => setEmail(e.target.value)}
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
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        placeholder="••••••••"
                    />
                </div>
                
                <Button 
                    type="submit" 
                    variant="primary" 
                    size="lg" 
                    fullWidth={true}
                    disabled={authState.isLoading}
                >
                    {authState.isLoading ? (isLoginView ? 'Logging In...' : 'Registering...') : (isLoginView ? 'Log In' : 'Register')}
                </Button>
            </form>
            
            <div className="form-footer">
                <Button variant="link" onClick={toggleView}>
                    {isLoginView ? "Don't have an account? Register" : "Already have an account? Log In"}
                </Button>
            </div>
        </div>
    );
};


// --- Component: Dashboard (Conceptual: src/components/Dashboard/Dashboard.jsx) ---

const Dashboard = ({ token, logout }) => {
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState(null); // {type: 'success'/'error', message: '...'}
    const [isUploading, setIsUploading] = useState(false);
    const [documents, setDocuments] = useState([]);
    const [isFetching, setIsFetching] = useState(true); // Initial fetch state

    const loadDocuments = useCallback(async () => {
        setIsFetching(true);
        const docs = await fetchDocuments(token);
        setDocuments(docs);
        setIsFetching(false);
    }, [token]);

    useEffect(() => {
        // Load documents on mount and whenever the token changes (i.e., on successful login)
        if (token) {
            loadDocuments();
        }
    }, [token, loadDocuments]);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        setUploadStatus(null);

        if (!file) {
            setUploadStatus({ type: 'error', message: "Please select a file to upload." });
            return;
        }

        setIsUploading(true);
        const result = await uploadFile(file, token);
        setIsUploading(false);

        setUploadStatus(result);

        if (result.success) {
            // Clear the file input and reload the document list
            setFile(null);
            document.getElementById('file-input').value = '';
            loadDocuments(); 
        }
    };

    return (
        <div className="dashboard-container">
            <h2 className="dashboard-title">Welcome to DocuSage!</h2>
            <p className="dashboard-intro">Securely upload documents for processing.</p>

            {/* File Upload Section */}
            <div className="card upload-card">
                <h3 className="card-title">Upload New Document</h3>
                
                <Alert type={uploadStatus?.type} message={uploadStatus?.message} />

                <form onSubmit={handleUpload} className="upload-form">
                    <input 
                        type="file" 
                        id="file-input"
                        onChange={handleFileChange} 
                        className="file-input"
                        disabled={isUploading}
                    />
                    <Button 
                        type="submit" 
                        variant="secondary" 
                        size="lg" 
                        disabled={isUploading || !file}
                    >
                        {isUploading ? 'Uploading...' : 'Upload Document'}
                    </Button>
                </form>
            </div>

            {/* Document List Section */}
            <div className="card document-list-card">
                <h3 className="card-title">My Documents</h3>
                
                {isFetching && <p className="text-center">Loading documents...</p>}
                
                {!isFetching && documents.length === 0 && (
                    <div className="empty-state">
                        <p>No documents uploaded yet. Start by uploading a file above!</p>
                    </div>
                )}
                
                {!isFetching && documents.length > 0 && (
                    <ul className="document-list">
                        <li className="list-header">
                            <span className="header-name">File Name</span>
                            <span className="header-size">Size</span>
                            <span className="header-uploaded">Uploaded At</span>
                        </li>
                        {documents.map(doc => (
                            <li key={doc.file_id} className="document-item">
                                <span className="item-name">{doc.filename}</span>
                                <span className="item-size">{(doc.size / 1024).toFixed(2)} KB</span>
                                <span className="item-uploaded">
                                    {new Date(doc.upload_time).toLocaleDateString()}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            
            <div className="text-center mt-6">
                <Button variant="red" onClick={logout}>
                    Logout
                </Button>
            </div>
        </div>
    );
};


// --- Component: Navbar (Conceptual: src/components/Navbar/Navbar.jsx) ---

const Navbar = ({ isAuthenticated, logout }) => {
    return (
        <header className="navbar-header">
            <div className="app-title">DocuSage AI</div>
            <nav className="nav-links">
                {isAuthenticated ? (
                    <Button variant="red" onClick={logout}>
                        Logout
                    </Button>
                ) : (
                    <div className="auth-buttons">
                        {/* AuthForm handles its own view toggle, so we don't need a separate button here */}
                    </div>
                )}
            </nav>
        </header>
    );
};


// --- Main App Component ---

const App = () => {
    // Retrieve authentication logic and state from the custom hook
    const { isAuthenticated, authError, isLoading, authenticate, logout } = useAuth();
    
    // Get the current token to pass to API services
    const token = localStorage.getItem('token');

    // --- Main Rendering Logic ---
    return (
        <div className="app-main-layout">
            {/* The CSS for the entire application will now be in frontend/src/app.css */}
            
            <Navbar 
                isAuthenticated={isAuthenticated} 
                logout={logout} 
            />
            
            <main className="main-content">
                {isAuthenticated ? (
                    <Dashboard 
                        token={token} 
                        logout={logout} 
                    />
                ) : (
                    <AuthForm 
                        authState={{isAuthenticated, authError, isLoading}} 
                        authenticate={authenticate} 
                    />
                )}
            </main>
        </div>
    );
};

export default App;

