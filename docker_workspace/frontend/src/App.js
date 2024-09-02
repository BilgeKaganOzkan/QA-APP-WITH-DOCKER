import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import QueryInput from './components/QueryInput';
import Sidebar from './components/Sidebar';
import axios from 'axios';

const START_SESSION_URL = "http://localhost:8000/start_session"; 
const UPLOAD_CSV_URL = "http://localhost:8000/upload_csv";
const UPLOAD_PDF_URL = "http://localhost:8000/upload_pdf";
const SQL_QUERY_URL = "http://localhost:8000/sql_query";
const RAG_QUERY_URL = "http://localhost:8000/rag_query";
const END_SESSION_URL = "http://localhost:8000/end_session";

function App() {
    const [messages, setMessages] = useState([]);
    const [selectedPanel, setSelectedPanel] = useState('sql'); // Default to SQL panel
    const sessionStartedRef = useRef(false);
    const isUnmounted = useRef(false);
    const fileInputRef = useRef(null);

    const endSession = useCallback(async () => {
        if (!sessionStartedRef.current || isUnmounted.current) return;
        try {
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: 'Ending current session...' }]);
            const response = await axios.delete(END_SESSION_URL, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to end session");
        }
        sessionStartedRef.current = false;
    }, []);

    const startSession = useCallback(async () => {
        if (isUnmounted.current) return;
        try {
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: 'Starting new session...' }]);
            const response = await axios.get(START_SESSION_URL, { withCredentials: true });
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
            sessionStartedRef.current = true;
        } catch (error) {
            handleHttpError(error, "Failed to start session");
        }
    }, []);

    const switchPanel = useCallback(async (panel) => {
        if (sessionStartedRef.current) {
            await endSession(); // End the current session first
        }
        setSelectedPanel(panel); // Set the new panel
        await startSession(); // Start a new session
        setMessages(prevMessages => [
            ...prevMessages, 
            { type: 'system', text: `Switched to ${panel === 'sql' ? 'SQL Query' : 'RAG'} Panel` }
        ]);
    }, [endSession, startSession]);

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
    
            if ((selectedPanel === 'sql' && fileExtension !== 'csv') || 
                (selectedPanel === 'rag' && fileExtension !== 'pdf')) {
                errorMessages.push(`Invalid file type: ${file.name}. Please upload only ${selectedPanel === 'sql' ? '.csv' : '.pdf'} files.`);
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
            const uploadUrl = selectedPanel === 'sql' ? UPLOAD_CSV_URL : UPLOAD_PDF_URL;
            const response = await axios.post(uploadUrl, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',  // Ensure correct content type for file upload
                },
                withCredentials: true
            });
    
            setMessages(prevMessages => [...prevMessages, { type: 'system', text: response.data.informationMessage }]);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        } catch (error) {
            handleHttpError(error, `Failed to upload ${selectedPanel === 'sql' ? 'CSV' : 'PDF'} files`);
        }
    };
    
    const handleQuerySubmit = async (query) => {
        setMessages(prevMessages => [...prevMessages, { type: 'user', text: query }]);
    
        try {
            const queryUrl = selectedPanel === 'sql' ? SQL_QUERY_URL : RAG_QUERY_URL;
    
            // Ensure the payload matches the expected structure in the backend
            const payload = { humanMessage: query };
    
            const response = await axios.post(queryUrl, payload, {
                headers: {
                    'Content-Type': 'application/json',  // Ensure correct content type
                },
                withCredentials: true
            });
    
            setMessages(prevMessages => [...prevMessages, { type: 'ai', text: response.data.aiMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to process query");
        }
    };

    const handleHttpError = (error, defaultMessage) => {
        const errorMessages = [];
        console.error('Error response:', error.response?.data); // Log the detailed error response

        if (error.response) {
            errorMessages.push(`HTTP ${error.response.status}: ${error.response.statusText}`);
            if (error.response.data && typeof error.response.data === 'object') {
                for (const [key, value] of Object.entries(error.response.data)) {
                    errorMessages.push(`${key}: ${JSON.stringify(value)}`); // Stringify object details
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
            <Sidebar onPanelSelect={switchPanel} />
            <header>
                <h1>Q&A with {selectedPanel === 'sql' ? 'SQL and Tabular Data' : 'RAG'}</h1>
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
                        accept={selectedPanel === 'sql' ? '.csv' : '.pdf'}
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
