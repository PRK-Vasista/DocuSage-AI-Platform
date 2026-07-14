/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * Document chat panel for the workspace right pane.
 */

import React, { useEffect, useRef, useState } from 'react';
import { askDocumentChat, getDocumentChatHistory } from '../../api/apiService';
import Button from '../shared/Button';
import './ChatPanel.css';

/**
 * Render grounded chat for a selected ready document.
 *
 * @param {object} props
 */
const ChatPanel = ({ documentId, token, enabled }) => {
    const [messages, setMessages] = useState([]);
    const [question, setQuestion] = useState('');
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [errorMessage, setErrorMessage] = useState(null);
    const listRef = useRef(null);

    useEffect(() => {
        let cancelled = false;

        const loadHistory = async () => {
            if (!enabled || !documentId || !token) {
                setMessages([]);
                return;
            }

            setIsLoadingHistory(true);
            setErrorMessage(null);
            try {
                const history = await getDocumentChatHistory(documentId, token);
                if (!cancelled) {
                    setMessages(history.messages || []);
                }
            } catch (error) {
                console.error('[ChatPanel] Failed to load history:', error);
                if (!cancelled) {
                    setErrorMessage(error.message);
                    setMessages([]);
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
    }, [documentId, token, enabled]);

    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [messages, isSending]);

    const handleSend = async (event) => {
        event.preventDefault();
        const trimmed = question.trim();
        if (!trimmed || isSending || !enabled) {
            return;
        }

        setIsSending(true);
        setErrorMessage(null);

        try {
            const response = await askDocumentChat(documentId, trimmed, token);
            setMessages(response.messages || []);
            setQuestion('');
        } catch (error) {
            console.error('[ChatPanel] Ask failed:', error);
            setErrorMessage(error.message);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <section className="chat-panel">
            <div className="chat-panel-header">
                <h3 className="chat-panel-title">Chat</h3>
                <p className="chat-panel-hint">
                    Ask questions about this document. Answers use the local AI unit.
                </p>
            </div>

            {!enabled && (
                <p className="chat-disabled">
                    Chat unlocks when this document is Ready.
                </p>
            )}

            {errorMessage && (
                <div className="chat-error-row">
                    <p className="chat-error">{errorMessage}</p>
                    <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={isSending || !enabled}
                        onClick={() => {
                            setErrorMessage(null);
                        }}
                    >
                        Dismiss
                    </Button>
                    {question.trim() && (
                        <Button
                            type="button"
                            variant="primary"
                            size="sm"
                            disabled={isSending || !enabled}
                            onClick={(event) => handleSend(event)}
                        >
                            Retry
                        </Button>
                    )}
                </div>
            )}

            <div className="chat-messages" ref={listRef}>
                {enabled && isLoadingHistory && (
                    <p className="chat-muted">Loading conversation...</p>
                )}
                {enabled && !isLoadingHistory && messages.length === 0 && (
                    <p className="chat-muted">No messages yet. Ask the first question below.</p>
                )}
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`chat-bubble chat-bubble-${message.role}`}
                    >
                        <span className="chat-role">
                            {message.role === 'user' ? 'You' : 'DocuSage'}
                        </span>
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
                    placeholder={enabled ? 'Ask about this document...' : 'Waiting for Ready status...'}
                    disabled={!enabled || isSending}
                />
                <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={!enabled || isSending || !question.trim()}
                >
                    {isSending ? 'Thinking...' : 'Send'}
                </Button>
            </form>
        </section>
    );
};

export default ChatPanel;
