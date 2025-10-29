// Alert.jsx - Reusable component for displaying status messages.

import React from 'react';
// import './Alert.css'; // Assume styles are imported from a shared file or defined globally

/**
 * A reusable component to display alert messages.
 *
 * @param {object} props
 * @param {string} props.type - The type of alert: 'error', 'success', 'warning', or 'info'.
 * @param {string} props.message - The message content to display.
 */
const Alert = ({ type = 'info', message }) => {
    if (!message) {
        return null; // Don't render if there's no message
    }

    // Determine the primary class based on the type
    // We assume global CSS or a shared CSS file handles the styling for these classes
    const alertClasses = `alert alert-${type}`;

    return (
        <div className={alertClasses} role="alert">
            <span className="alert-message">{message}</span>
        </div>
    );
};

export default Alert;

