import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import QueryInput from './components/QueryInput';
import axios from 'axios';

const START_SESSION_URL = "http://172.18.0.22:8000/start_session"; 
const UPLOAD_CSV_URL = "http://172.18.0.22:8000/upload_csv";
const QUERY_URL = "http://172.18.0.22:8000/query";
const END_SESSION_URL = "http://172.18.0.22:8000/end_session";

function App() {
    const [messages, setMessages] = useState([]);
    const sessionStartedRef = useRef(false);
    const isUnmounted = useRef(false);
    const fileInputRef = useRef(null);

    const startSession = useCallback(async () => {
        if (sessionStartedRef.current || isUnmounted.current) return;
        sessionStartedRef.current = true;
        setMessages(prevMessages => [...prevMessages, { type: 'system', text: 'Starting session...' }]);
        try {
            const response = await axios.get(START_SESSION_URL, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to start session");
        }
    }, []);

    const endSession = useCallback(async () => {
        if (!sessionStartedRef.current || isUnmounted.current) return;
        try {
            const response = await axios.delete(END_SESSION_URL, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to end session");
        }
        sessionStartedRef.current = false;
    }, []);

    useEffect(() => {
        if (!sessionStartedRef.current && !isUnmounted.current) {
            startSession();
        }

        const handleBeforeUnload = () => {
            if (sessionStartedRef.current) {
                const xhr = new XMLHttpRequest();
                xhr.open('DELETE', END_SESSION_URL, false);
                xhr.withCredentials = true;
                xhr.send(null);
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        return () => {
            isUnmounted.current = true;
            if (sessionStartedRef.current) {
                endSession();
            }
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [startSession, endSession]);

    const handleFileUpload = async (event) => {
        event.preventDefault();
        const files = event.target.elements.fileInput.files;
        const errorMessages = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (fileExtension !== 'csv') {
                errorMessages.push(`Invalid file type: ${file.name}. Please upload only .csv files.`);
            }
        }

        if (errorMessages.length > 0) {
            setMessages(prevMessages => [
                ...prevMessages,
                ...errorMessages.map(error => ({ type: 'system', text: error }))
            ]);
            return;
        }

        const formData = new FormData();
        
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        try {
            const response = await axios.post(UPLOAD_CSV_URL, formData, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        } catch (error) {
            handleHttpError(error, "Failed to upload CSV files");
        }
    };

    const handleQuerySubmit = async (query) => {
        setMessages(prevMessages => [...prevMessages, { type: 'user', text: query }]);

        try {
            const response = await axios.post(QUERY_URL, { humanMessage: query }, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'ai', text: response.data.aiMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to process query");
        }
    };

    const handleHttpError = (error, defaultMessage) => {
        const errorMessages = [];

        if (error.response) {
            errorMessages.push(`HTTP ${error.response.status}: ${error.response.statusText}`);
            if (error.response.data && typeof error.response.data === 'object') {
                for (const [key, value] of Object.entries(error.response.data)) {
                    errorMessages.push(`${key}: ${value}`);
                }
            } else if (error.response.data) {
                errorMessages.push(error.response.data);
            }
        } else if (error.request) {
            errorMessages.push("No response received from the server.");
        } else {
            errorMessages.push(`Error: ${error.message}`);
        }

        if (errorMessages.length === 0) {
            errorMessages.push(defaultMessage);
        }

        setMessages(prevMessages => [
            ...prevMessages,
            ...errorMessages.map(message => ({ type: 'system', text: message }))
        ]);
    };

    return (
        <div className="container">
            <header>
                <h1>Q&A with SQL and Tabular Data</h1>
            </header>
            <main className="main-content">
                <div className="system-messages">
                    {messages.map((message, index) => (
                        <p key={index}><strong>{message.type === 'system' ? 'System:' : message.type === 'user' ? 'You:' : 'AI:'}</strong> {message.text}</p>
                    ))}
                </div>
                <form onSubmit={handleFileUpload}>
                    <input
                        type="file"
                        name="fileInput"
                        multiple
                        accept=".csv"
                        ref={fileInputRef}
                    />
                    <button type="submit">Upload</button>
                </form>
                <QueryInput onSubmit={handleQuerySubmit} />
            </main>
            <footer>
                <p>Author: Bilge Kagan Ozkan</p>
            </footer>
        </div>
    );
}

export default App;
