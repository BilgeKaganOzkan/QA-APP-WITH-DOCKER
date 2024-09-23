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

if (typeof window !== 'undefined' && window.sessionInitiated === undefined) {
    window.sessionInitiated = false;
}

function App() {
    const [messages, setMessages] = useState([]);
    const [selectedPanel, setSelectedPanel] = useState('sql');
    const fileInputRef = useRef(null);

    const isSessionInProgressRef = useRef(false);
    const isFirstLoadRef = useRef(true);

    const handleHttpError = useCallback((error, defaultMessage) => {
        const errorMessages = [];
        console.error('Error response:', error.response?.data);

        if (error.response) {
            errorMessages.push(`HTTP ${error.response.status}: ${error.response.statusText}`);
            if (error.response.data && typeof error.response.data === 'object') {
                for (const [key, value] of Object.entries(error.response.data)) {
                    errorMessages.push(`${key}: ${JSON.stringify(value)}`);
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
    }, []);

    const endSession = useCallback(async () => {
        console.log('endSession called');
        if (!window.sessionInitiated) {
            console.log('endSession aborted: session not started');
            return;
        }
        try {
            await axios.delete(END_SESSION_URL, { withCredentials: true });
            window.sessionInitiated = false;
            console.log('endSession: session ended');
        } catch (error) {
            handleHttpError(error, "Failed to end session");
        }
    }, [handleHttpError]);

    const startSession = useCallback(async () => {
        console.log('startSession called');
        if (window.sessionInitiated || isSessionInProgressRef.current) {
            console.log('Session already initiated or in progress.');
            return;
        }
        isSessionInProgressRef.current = true;

        if (isFirstLoadRef.current) {
            setMessages(prevMessages => [
                ...prevMessages,
                { type: 'system', text: 'Session starting...' }
            ]);
        }

        try {
            const response = await axios.get(START_SESSION_URL, { withCredentials: true });
            window.sessionInitiated = true;
            console.log('startSession: session started');

            if (isFirstLoadRef.current) {
                setMessages(prevMessages => [
                    ...prevMessages,
                    { type: 'system', text: 'Session started.' }
                ]);
                isFirstLoadRef.current = false;
            }
        } catch (error) {
            handleHttpError(error, "Failed to start session");
        } finally {
            isSessionInProgressRef.current = false;
        }
    }, [handleHttpError]);

    const switchPanel = useCallback(async (panel) => {
        console.log(`switchPanel called with panel: ${panel}`);
        await endSession();
        setSelectedPanel(panel);
        await startSession();
        setMessages(prevMessages => [
            ...prevMessages, 
            { type: 'system', text: `Switched to ${panel === 'sql' ? 'SQL Query' : 'RAG'} Panel` },
            { type: 'system', text: 'New session started.' }
        ]);
    }, [endSession, startSession]);

    useEffect(() => {
        console.log('useEffect called');
        startSession();
    
        const handleBeforeUnload = () => {
            if (window.sessionInitiated) {
                const url = END_SESSION_URL;
                const data = new Blob([], { type: 'application/json' });
                navigator.sendBeacon(url, data);
            }
        };
    
        window.addEventListener('beforeunload', handleBeforeUnload);
    
        return () => {
            console.log('cleanup: unmounting');
            if (window.sessionInitiated) {
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
                    'Content-Type': 'multipart/form-data',
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

            const payload = { humanMessage: query };

            const response = await axios.post(queryUrl, payload, {
                headers: {
                    'Content-Type': 'application/json',
                },
                withCredentials: true
            });

            setMessages(prevMessages => [...prevMessages, { type: 'ai', text: response.data.aiMessage }]);
        } catch (error) {
            handleHttpError(error, "Failed to process query");
        }
    };

    const handlePanelSelect = async (panel) => {
        console.log(`handlePanelSelect called with panel: ${panel}`);
        await switchPanel(panel);
    };

    return (
        <div className="container">
            <Sidebar onPanelSelect={handlePanelSelect} />
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
