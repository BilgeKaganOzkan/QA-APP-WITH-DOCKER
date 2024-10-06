import React from 'react';

const StartSessionButton = ({ onStartSession }) => {
    return (
        <button onClick={onStartSession}>Start Session</button>
    );
};

export default StartSessionButton;
