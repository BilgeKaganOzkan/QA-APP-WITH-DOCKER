import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import './MainApp.css';
import QueryInput from './QueryInput';
import SideBar from './SideBar';
import ChatBox from './ChatBox';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import {
    START_SESSION_URL,
    UPLOAD_CSV_URL,
    UPLOAD_PDF_URL,
    SQL_QUERY_URL,
    RAG_QUERY_URL,
    CLEAR_SESSION_URL,
    END_SESSION_URL,
    GET_PROGRESS_URL
} from '../config/constants';
import Cookies from 'js-cookie';

/**
 * @brief Main application component for user interaction.
 *
 * This component serves as the main interface for users to interact with
 * the system. It allows users to send queries, upload files, and view
 * responses from the AI. It manages the authentication state and session
 * operations while displaying chat messages and progress.
 *
 * @return {JSX.Element} The rendered MainApp component.
 */
const MainApp = () => {
    const { isAuthenticated, setIsAuthenticated, setUser } = useContext(AuthContext);
    const [messages, setMessages] = useState([]); // State for chat messages
    const [selectedPanel, setSelectedPanel] = useState('sql'); // State for selected panel (SQL/RAG)
    const fileInputRef = useRef(null); // Reference for the file input element

    const isSessionInProgressRef = useRef(false); // Reference to track session state
    const isFirstLoadRef = useRef(true); // Reference to track first load state

    const [selectedFiles, setSelectedFiles] = useState([]); // State for selected files
    const [progress, setProgress] = useState(0); // State for file upload progress
    const [uploading, setUploading] = useState(false); // State for upload status

    const [thinking, setThinking] = useState(false); // State for AI thinking status
    const navigate = useNavigate(); // Hook for navigation

    /**
     * @brief Clears all cookies stored in the browser.
     *
     * This function iterates over all cookies and removes them.
     */
    const clearCookies = useCallback(() => {
        const allCookies = Cookies.get();
        Object.keys(allCookies).forEach(cookieName => {
            Cookies.remove(cookieName);
        });
    }, []);

    /**
     * @brief Handles HTTP errors and sets error messages in the chat.
     *
     * @param {Object} error - The error object from the HTTP request.
     * @param {string} defaultMessage - Default message to show if no specific error message is available.
     */
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
    
            if (error.response.status === 401) {
                alert("UNAUTHENTICATION SESSION: You must login again");
                const data = new Blob([], { type: 'application/json' });
                navigator.sendBeacon(END_SESSION_URL, data);
                setIsAuthenticated(false);
                setUser(null);
                clearCookies();
                setMessages([]);
                navigate('/login');
                return;
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
    }, [navigate, setIsAuthenticated, setUser, clearCookies]);

    /**
     * @brief Clears the current session on the server.
     *
     * This function sends a request to clear the session and resets session initiation state.
     */
    const clearSession = useCallback(async () => {
        if (!window.sessionInitiated) {
            return;
        }
        try {
            await axios.delete(CLEAR_SESSION_URL, { withCredentials: true });
            window.sessionInitiated = false;
        } catch (error) {
            handleHttpError(error, "Failed to clear session");
        }
    }, [handleHttpError]);

    /**
     * @brief Starts a new session for the user.
     *
     * This function initializes a session by sending a request to the server
     * and updating the chat messages accordingly.
     */
    const startSession = useCallback(async () => {
        if (window.sessionInitiated || isSessionInProgressRef.current) {
            return;
        }
        isSessionInProgressRef.current = true;

        setMessages(prevMessages => [
            ...prevMessages,
            { type: 'system', text: 'Session starting...' }
        ]);

        try {
            const response = await axios.get(START_SESSION_URL, { withCredentials: true });
            if (response.status === 200) {
                window.sessionInitiated = true;

                setMessages(prevMessages => [
                    ...prevMessages,
                    { type: 'system', text: 'Session started.' }
                ]);

                setMessages(prevMessages => [
                    ...prevMessages,
                    { type: 'ai', text: response.data.informationMessage }
                ]);

                isFirstLoadRef.current = false;
            }
        } catch (error) {
            handleHttpError(error, "Failed to start session");
        } finally {
            isSessionInProgressRef.current = false;
        }
    }, [handleHttpError]);

    /**
     * @brief Switches between SQL and RAG panels.
     *
     * This function clears the current session and starts a new one for the selected panel.
     *
     * @param {string} panel - The panel to switch to ('sql' or 'rag').
     */
    const switchPanel = useCallback(async (panel) => {
        if (panel === selectedPanel) {
            return;
        }

        await clearSession();
        setSelectedPanel(panel);
        setSelectedFiles([]);
        setMessages([]);
        await startSession();
        setMessages(prevMessages => [
            { type: 'system', text: `Switched to ${panel === 'sql' ? 'SQL Query' : 'RAG'} Panel` },
            { type: 'system', text: 'New session started.' }
        ]);
    }, [clearSession, startSession, selectedPanel]);

    /**
     * @brief Handles file selection and validates file types.
     *
     * This function checks the selected files and ensures they are of the correct type.
     *
     * @param {FileList} files - The files selected by the user.
     */
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

    /**
     * @brief Removes a selected file from the list.
     *
     * @param {number} index - The index of the file to remove.
     */
    const removeSelectedFile = (index) => {
        setSelectedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
    };

    /**
     * @brief Handles file upload to the server.
     *
     * This function uploads selected files to the server and manages progress tracking.
     *
     * @return {Promise<boolean>} Indicates whether the upload was successful.
     */
    const handleFileUpload = async () => {
        if (selectedFiles.length === 0) {
            return true;
        }

        const uploadUrl = selectedPanel === 'sql' ? UPLOAD_CSV_URL : UPLOAD_PDF_URL;

        try {
            setUploading(true);
            setProgress(0);

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

            const uploadPromise = axios.put(uploadUrl, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                withCredentials: true
            });

            startPolling();

            const uploadResponse = await uploadPromise;

            if (uploadResponse.data.informationMessage) {
                setMessages(prevMessages => [
                    ...prevMessages,
                    { type: 'system', text: uploadResponse.data.informationMessage }
                ]);
            }

            setSelectedFiles([]);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

            return true;
        } catch (error) {
            handleHttpError(error, `Failed to upload ${selectedPanel === 'sql' ? 'CSV' : 'PDF'} files`);
            return false;
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    /**
     * @brief Handles submission of user queries.
     *
     * This function sends user queries to the server and updates the chat with responses.
     *
     * @param {string} query - The user query to send.
     */
    const handleQuerySubmit = async (query) => {
        setMessages(prevMessages => [...prevMessages, { type: 'user', text: query }]);
        setThinking(true);
    
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
            setThinking(false);
        } catch (error) {
            handleHttpError(error, "Failed to process query");
            setThinking(false);
        }
    };
    
    /**
     * @brief Handles sending the query and managing file uploads.
     *
     * This function uploads files if selected, then sends the user's query.
     *
     * @param {string} query - The user query to send.
     */
    const handleSend = async (query) => {
        if (selectedFiles.length > 0) {
            const uploadSuccess = await handleFileUpload();
            if (!uploadSuccess) return;
        }
        if (query.trim() !== '') {
            await handleQuerySubmit(query);
        }
    };

    /**
     * @brief Handles panel selection for switching views.
     *
     * @param {string} panel - The panel to switch to ('sql' or 'rag').
     */
    const handlePanelSelect = async (panel) => {
        await switchPanel(panel);
    };

    /**
     * @brief Logs out the user and clears session data.
     */
    const logout = async () => {
        try {
            await axios.delete(END_SESSION_URL, { withCredentials: true });
            setIsAuthenticated(false);
            setUser(null);
            clearCookies();
            window.sessionInitiated = false;
            setMessages([]);
        } catch (error) {
            handleHttpError(error, "Failed to logout");
        }
    };

    useEffect(() => {
        const handleBeforeUnload = (event) => {
            if (isAuthenticated) {
                event.preventDefault();
                event.returnValue = '';
            }
        };
    
        const handleUnload = async () => {
            if (isAuthenticated) {
                const data = new Blob([], { type: 'application/json' });
                navigator.sendBeacon(END_SESSION_URL, data);
                setIsAuthenticated(false);
                setUser(null);
                clearCookies();
                window.sessionInitiated = false;
                setMessages([]);
            }
        };
    
        window.addEventListener('beforeunload', handleBeforeUnload);
        window.addEventListener('unload', handleUnload);
    
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
            window.removeEventListener('unload', handleUnload);
        };
    }, [isAuthenticated, navigate, setIsAuthenticated, setUser, clearCookies]);

    useEffect(() => {
        if (isAuthenticated) {
            startSession();
        }
    }, [isAuthenticated, startSession]);    

    return (
        <div className="container">
            <SideBar onPanelSelect={handlePanelSelect} />
            <header>
                <h1>Q&A with {selectedPanel === 'sql' ? 'Tabular Data' : 'RAG'}</h1>
                <button onClick={logout} className="logout-button" id='logout-button'>Logout</button>
            </header>
            <main className="main-content">
                <ChatBox
                    messages={[
                        ...messages,
                        ...(thinking
                            ? [
                                {
                                    type: 'ai',
                                    text: (
                                        <div className="thinking-message">
                                            <span className="thinking-text">Thinking</span>
                                            <span className="dots"></span>
                                        </div>
                                    ),
                                },
                            ]
                            : []),
                    ]}
                />
                {uploading && (
                    <div className="progress-container">
                        <p>Uploading files... {progress}%</p>
                        <progress value={progress} max="100"></progress>
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
                selectedPanel={selectedPanel}
                disabled={thinking || uploading}
            />
            <footer>
                <p>Author: Bilge Kagan Ozkan</p>
            </footer>
        </div>
    );    
};

export default MainApp;