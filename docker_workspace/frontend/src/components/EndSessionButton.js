import React from 'react';

const EndSessionButton = ({ onEndSession }) => (
    <button
        onClick={onEndSession}
        style={{
            padding: '10px 20px',
            backgroundColor: '#444',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
        }}
    >
        End Session
    </button>
);

export default EndSessionButton;
