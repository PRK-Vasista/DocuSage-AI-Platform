// Dashboard.jsx - Component logic without styles

import React, { useState, useEffect, useCallback } from 'react';
// import './Dashboard.css'; // Will be imported once created
// import { uploadFile, listFiles } from '../../api/apiService'; // Conceptual import

// NOTE: We assume API_BASE_URL is available from a configuration or imported service.
const API_BASE_URL = 'http://localhost:8000/api/v1';

const Dashboard = ({ token, setAlert }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [fetchLoading, setFetchLoading] = useState(false);

    // Handler for file input change
    const handleFileChange = (e) => {
        setFile(e.target.files[0] || null);
    };

    /**
     * Fetches the list of files uploaded by the current user.
     * This function should ideally be imported from apiService.
     */
    const listFiles = useCallback(async () => {
        if (!token) return;

        setFetchLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/files/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to fetch files with status ${response.status}`);
            }
            
            const files = await response.json();
            setUploadedFiles(files);

        } catch (error) {
            console.error("API Fetch Files Error:", error);
            setAlert({ message: `Failed to load files: ${error.message}`, type: 'error' });
            setUploadedFiles([]);
        } finally {
            setFetchLoading(false);
        }
    }, [token, setAlert]);
    
    /**
     * Handles the file upload process.
     * This function should ideally be imported from apiService.
     */
    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) {
            setAlert({ message: 'Please select a file to upload.', type: 'error' });
            return;
        }
        setLoading(true);
        setAlert({ message: 'Uploading file...', type: 'info' });
        setUploadStatus(null);
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/files/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            const data = await response.json();
            
            if (response.ok) {
                setAlert({ message: `File '${data.filename}' uploaded successfully!`, type: 'success' });
                setUploadStatus({ 
                    success: true, 
                    filename: data.filename,
                    message: `Saved to: ${data.path}` 
                });
                setFile(null); 
                // Refresh the list after successful upload
                listFiles(); 
            } else {
                const detail = data.detail || "Server failed to process the file.";
                setAlert({ message: `Upload Failed: ${detail}`, type: 'error' });
                setUploadStatus({ success: false, message: detail });
            }
        } catch (error) {
            console.error("Upload fetch error:", error);
            setAlert({ message: `Network Error: Could not reach backend server.`, type: 'error' });
            setUploadStatus({ success: false, message: 'Network connection failed.' });
        } finally {
            setLoading(false);
        }
    };


    // Fetch files on component mount or token change
    useEffect(() => {
        listFiles();
    }, [listFiles]);


    const uploadButtonClasses = `btn upload-btn ${
        (loading || !file) ? 'btn-disabled' : 'btn-green'
    }`;


    return (
        <div className="dashboard-container">
            
            {/* --- Document Upload Card --- */}
            <div className="card upload-card">
                <h2 className="upload-card-title">Document Upload</h2>
                <form onSubmit={handleUpload} className="upload-form">
                    <div className="form-group">
                        <label className="form-label">Select Document</label>
                        <input
                            type="file"
                            onChange={handleFileChange}
                            accept=".pdf,.txt,.docx"
                            className="file-input"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading || !file}
                        className={uploadButtonClasses}
                    >
                        {loading ? 'Uploading...' : `Upload Document (${file ? file.name : 'No file selected'})`}
                    </button>
                </form>
                
                {uploadStatus && (
                    <div className={`upload-status mt-4 ${uploadStatus.success ? 'alert-success' : 'alert-error'}`}>
                        <p className="status-title">{uploadStatus.success ? 'Upload Complete' : 'Upload Failed'}</p>
                        <p className="status-message">{uploadStatus.message}</p>
                    </div>
                )}
            </div>

            {/* --- Uploaded Files List --- */}
            <div className="card file-list-card">
                <h2 className="file-list-title">Your Uploaded Documents</h2>
                {fetchLoading ? (
                    <p className="loading-message">Loading files...</p>
                ) : uploadedFiles.length === 0 ? (
                    <p className="empty-message">
                        You have not uploaded any documents yet.
                    </p>
                ) : (
                    <ul className="file-list">
                        {uploadedFiles.map((f) => (
                            <li key={f.file_id} className="file-list-item">
                                <div className="file-details">
                                    {/* SVG Icon Placeholder */}
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="file-icon"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><line x1="10" y1="9" x2="10" y2="9"></line></svg>
                                    <div>
                                        <p className="file-name">{f.filename}</p>
                                        <p className="file-id">ID: {f.file_id}</p>
                                    </div>
                                </div>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => alert(`Starting AI Chat with: ${f.filename}`)}
                                >
                                    Start Chat
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default Dashboard;

