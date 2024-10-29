import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { AuthProvider } from './context/AuthContext';

/**
 * @brief The entry point of the React application.
 *
 * This script renders the main application component (<App />) 
 * within a context provider (<AuthProvider />) to manage 
 * authentication state across the application.
 *
 * @return {void}
 */
ReactDOM.render(
    <React.StrictMode>
        {/* Provide authentication context to the application */}
        <AuthProvider>
            <App /> {/* Main application component */}
        </AuthProvider>
    </React.StrictMode>,
    document.getElementById('root') // Target DOM element for rendering
);