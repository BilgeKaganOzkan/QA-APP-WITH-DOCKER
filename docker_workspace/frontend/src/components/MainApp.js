// src/components/MainApp.js
import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import './MainApp.css'; // Create this CSS file for styling
import QueryInput from './QueryInput';
import Sidebar from './Sidebar';
import ChatBox from './ChatBox';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import {
    START_SESSION_URL,
    UPLOAD_CSV_URL,
    UPLOAD_PDF_URL,
    SQL_QUERY_URL,
    RAG_QUERY_URL,
    END_SESSION_URL,
    GET_PROGRESS_URL
} from '../config/constants';

const MainApp = () => {
    const { setIsAuthenticated, setUser } = useContext(AuthContext);
    const [messages, setMessages] = useState([]);
    const [selectedPanel, setSelectedPanel] = useState('sql');
    const fileInputRef = useRef(null);

    const isSessionInProgressRef = useRef(false);
    const isFirstLoadRef = useRef(true);

    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);

    const [selectedFiles, setSelectedFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);

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
        if (!window.sessionInitiated) {
            return;
        }
        try {
            await axios.delete(END_SESSION_URL, { withCredentials: true });
            window.sessionInitiated = false;
        } catch (error) {
            handleHttpError(error, "Failed to end session");
        }
    }, [handleHttpError]);

    const startSession = useCallback(async () => {
        if (window.sessionInitiated || isSessionInProgressRef.current) {
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
            if (response.status === 200) {
                window.sessionInitiated = true;

                if (isFirstLoadRef.current) {
                    setMessages(prevMessages => [
                        ...prevMessages,
                        { type: 'system', text: 'Session started.' }
                    ]);
                    isFirstLoadRef.current = false;
                }
            }
        } catch (error) {
            handleHttpError(error, "Failed to start session");
        } finally {
            isSessionInProgressRef.current = false;
        }
    }, [handleHttpError]);

    const switchPanel = useCallback(async (panel) => {
        if (panel === selectedPanel) {
            // If the user clicks the same panel, do nothing
            return;
        }

        await endSession();
        setSelectedPanel(panel);
        setSelectedFiles([]); // Clear selected files (boxes)
        setMessages([]); // Clear conversation
        await startSession();
        setMessages(prevMessages => [
            { type: 'system', text: `Switched to ${panel === 'sql' ? 'SQL Query' : 'RAG'} Panel` },
            { type: 'system', text: 'New session started.' }
        ]);
    }, [endSession, startSession, selectedPanel]);

    useEffect(() => {
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
            if (window.sessionInitiated) {
                endSession();
            }
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [startSession, endSession]);

    const handleFileSelection = (files) => {
        const errorMessages = [];
        const newFiles = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if ((selectedPanel === 'sql' && fileExtension !== 'csv') ||
                (selectedPanel === 'rag' && fileExtension !== 'pdf')) {
                errorMessages.push(`Invalid file type: ${file.name}. Please upload only ${selectedPanel === 'sql' ? '.csv' : '.pdf'} files.`);
            } else {
                newFiles.push(file);
            }
        }

        if (errorMessages.length > 0) {
            setMessages(prevMessages => [
                ...prevMessages,
                ...errorMessages.map(error => ({ type: 'system', text: error }))
            ]);
        }

        setSelectedFiles(prevFiles => [...prevFiles, ...newFiles]);
    };

    const removeSelectedFile = (index) => {
        setSelectedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
    };

    const handleFileUpload = async () => {
        if (selectedFiles.length === 0) {
            return true;
        }

        setIsUploading(true);
        setLoading(true);
        setProgress(0);

        const uploadUrl = selectedPanel === 'sql' ? UPLOAD_CSV_URL : UPLOAD_PDF_URL;

        try {
            let polling = true;

            const pollProgress = async () => {
                try {
                    const response = await axios.get(GET_PROGRESS_URL, { withCredentials: true });
                    const progressValue = parseInt(response.data.progress);
                    console.log("Progress value received:", progressValue);
                    setProgress(progressValue);

                    if (progressValue >= 100 || progressValue === -1) {
                        polling = false;
                    }
                } catch (error) {
                    console.error("Error polling progress:", error);
                    polling = false;
                }
            };

            const startPolling = () => {
                const pollInterval = 2000;
                const intervalId = setInterval(() => {
                    if (polling) {
                        pollProgress();
                    } else {
                        clearInterval(intervalId);
                    }
                }, pollInterval);
            };

            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append("files", file);
            });

            const uploadPromise = axios.post(uploadUrl, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                withCredentials: true
            });

            startPolling();

            await uploadPromise;

            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

            setSelectedFiles([]);
            return true;
        } catch (error) {
            handleHttpError(error, `Failed to upload ${selectedPanel === 'sql' ? 'CSV' : 'PDF'} files`);
            return false;
        } finally {
            setLoading(false);
            setProgress(0);
            setIsUploading(false);
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

    const handleSend = async (query) => {
        if (selectedFiles.length > 0) {
            const uploadSuccess = await handleFileUpload();
            if (!uploadSuccess) return;
        }
        if (query.trim() !== '') {
            await handleQuerySubmit(query);
        }
    };

    const handlePanelSelect = async (panel) => {
        await switchPanel(panel);
    };

    const logout = async () => {
        try {
            await axios.delete(END_SESSION_URL, { withCredentials: true });
            setIsAuthenticated(false);
            setUser(null);
        } catch (error) {
            handleHttpError(error, "Failed to logout");
        }
    };

    return (
        <div className="container">
            <Sidebar onPanelSelect={handlePanelSelect} />
            <header>
                <h1>Q&A with {selectedPanel === 'sql' ? 'SQL and Tabular Data' : 'RAG'}</h1>
                <button onClick={logout} className="logout-button">Logout</button>
            </header>
            <main className="main-content">
                <ChatBox messages={messages} />
                {loading && (
                    <div className="progress-container">
                        <p>Processing files... {progress}%</p>
                        <progress value={progress} max="100" />
                    </div>
                )}
            </main>
            <QueryInput
                handleSend={handleSend}
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={selectedFiles}
                fileInputRef={fileInputRef}
                accept={selectedPanel === 'sql' ? '.csv' : '.pdf'}
                isUploading={isUploading}
                selectedPanel={selectedPanel}
            />
            <footer>
                <p>Author: Bilge Kagan Ozkan</p>
            </footer>
        </div>
    );
};

export default MainApp;
