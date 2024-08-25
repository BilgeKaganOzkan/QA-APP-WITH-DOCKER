import React from 'react';

const ChatBox = ({ chatHistory }) => {
    return (
        <div style={{ height: '400px', overflowY: 'scroll', padding: '10px', backgroundColor: '#333', color: '#fff' }}>
            {chatHistory.map((message, index) => (
                <div key={index}>
                    <strong>{message.user}</strong>: {message.text}
                </div>
            ))}
        </div>
    );
};

export default ChatBox;
