/**
 * Per-document chat panel that talks to the backend chat API.
 */

import React, { useEffect, useState } from 'react';
import { askDocumentChat, getDocumentChatHistory } from '../../api/apiService';
import Button from '../shared/Button';
import './DocumentChat.css';

/**
 * Render a chat UI for a ready document.
 *
 * @param {object} props
 * @param {number} props.documentId - Document identifier.
 * @param {string} props.filename - Document filename for display.
 * @param {string} props.token - JWT bearer token.
 * @param {Function} props.onClose - Close handler.
 */
const DocumentChat = ({ documentId, filename, token, onClose }) => {
    const [messages, setMessages] = useState([]);
    const [question, setQuestion] = useState('');
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [errorMessage, setErrorMessage] = useState(null);

    useEffect(() => {
        let cancelled = false;

        const loadHistory = async () => {
            setIsLoadingHistory(true);
            setErrorMessage(null);
            try {
                const history = await getDocumentChatHistory(documentId, token);
                if (!cancelled) {
                    setMessages(history.messages || []);
                }
            } catch (error) {
                console.error('[DocumentChat] Failed to load history:', error);
                if (!cancelled) {
                    setErrorMessage(error.message);
                }
            } finally {
                if (!cancelled) {
                    setIsLoadingHistory(false);
                }
            }
        };

        loadHistory();
        return () => {
            cancelled = true;
        };
    }, [documentId, token]);

    const handleSend = async (event) => {
        event.preventDefault();
        const trimmed = question.trim();
        if (!trimmed || isSending) {
            return;
        }

        setIsSending(true);
        setErrorMessage(null);

        try {
            const response = await askDocumentChat(documentId, trimmed, token);
            setMessages(response.messages || []);
            setQuestion('');
        } catch (error) {
            console.error('[DocumentChat] Ask failed:', error);
            setErrorMessage(error.message);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="card chat-card">
            <div className="chat-card-header">
                <h3 className="card-title">Chat: {filename}</h3>
                <Button variant="secondary" size="sm" onClick={onClose}>
                    Close
                </Button>
            </div>

            <p className="chat-hint">
                Ask questions about this document. Answers come from the local AI unit (Ollama).
            </p>

            {errorMessage && <p className="chat-error">{errorMessage}</p>}

            <div className="chat-messages">
                {isLoadingHistory && <p className="muted">Loading conversation...</p>}
                {!isLoadingHistory && messages.length === 0 && (
                    <p className="muted">No messages yet. Ask the first question below.</p>
                )}
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`chat-bubble chat-bubble-${message.role}`}
                    >
                        <span className="chat-role">{message.role === 'user' ? 'You' : 'DocuSage'}</span>
                        <p className="chat-content">{message.content}</p>
                    </div>
                ))}
            </div>

            <form className="chat-form" onSubmit={handleSend}>
                <input
                    type="text"
                    className="chat-input"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask a question about this document..."
                    disabled={isSending}
                />
                <Button type="submit" variant="primary" size="sm" disabled={isSending || !question.trim()}>
                    {isSending ? 'Thinking...' : 'Send'}
                </Button>
            </form>
        </div>
    );
};

export default DocumentChat;
