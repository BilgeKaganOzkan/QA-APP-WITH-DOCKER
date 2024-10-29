import React, { useEffect, useRef } from 'react';
import './ChatBox.css';

/**
 * @brief ChatBox component for displaying chat messages.
 *
 * This component renders a chat interface that displays messages from both
 * the user and the AI. It automatically scrolls to the latest message
 * when new messages are added.
 *
 * @param {Object} props - The props object.
 * @param {Array} props.messages - An array of message objects to be displayed in the chat.
 * @return {JSX.Element} The rendered ChatBox component.
 */
const ChatBox = ({ messages }) => {
    // Reference for scrolling to the end of the chat
    const chatEndRef = useRef(null);

    useEffect(() => {
        // Scroll to the bottom of the chat when new messages are added
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]); // Dependency array to trigger effect on messages change

    /**
     * @brief Returns the avatar image URL based on message type.
     *
     * @param {string} type - The type of message sender ('user', 'ai', or 'system').
     * @return {string} The URL of the corresponding avatar image.
     */
    const getAvatar = (type) => {
        if (type === 'user') {
            return '/user_logo.png'; // User avatar
        } else if (type === 'ai') {
            return '/ai_logo.png'; // AI avatar
        } else {
            return '/system_logo.png'; // Default system avatar
        }
    };

    return (
        <div className="chat-box" id='chat-box'>
            {/* Render each message in the chat */}
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={`chat-message ${message.type === 'user' ? 'user-message' : 'ai-message'}`}
                >
                    {/* Show avatar for AI and system messages */}
                    {message.type !== 'user' && (
                        <img src={getAvatar(message.type)} alt={`${message.type} avatar`} className="avatar" />
                    )}
                    <div className="message-content">
                        {message.text} {/* Display the message text */}
                    </div>
                    {/* Show avatar for user messages */}
                    {message.type === 'user' && (
                        <img src={getAvatar(message.type)} alt="User avatar" className="avatar" />
                    )}
                </div>
            ))}
            {/* Reference to scroll to the end of the chat */}
            <div ref={chatEndRef} />
        </div>
    );
};

export default ChatBox;