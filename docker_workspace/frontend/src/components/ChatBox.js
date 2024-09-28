// ChatBox.js
import React, { useEffect, useRef } from 'react';
import './ChatBox.css';

const ChatBox = ({ messages }) => {
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const getAvatar = (type) => {
        if (type === 'user') {
            return '/user_logo.png';
        } else if (type === 'ai') {
            return '/ai_logo.png';
        } else {
            return '/system_logo.png';
        }
    };

    return (
        <div className="chat-box">
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={`chat-message ${message.type === 'user' ? 'user-message' : 'ai-message'}`}
                >
                    {message.type !== 'user' && (
                        <img src={getAvatar(message.type)} alt={`${message.type} avatar`} className="avatar" />
                    )}
                    <div className="message-content">
                        {message.text}
                    </div>
                    {message.type === 'user' && (
                        <img src={getAvatar(message.type)} alt="User avatar" className="avatar" />
                    )}
                </div>
            ))}
            <div ref={chatEndRef} />
        </div>
    );
};

export default ChatBox;
