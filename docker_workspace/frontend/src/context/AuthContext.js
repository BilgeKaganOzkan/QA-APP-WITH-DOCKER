import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { CHECK_SESSION_URL } from '../config/constants';

// Create an AuthContext for managing authentication state
export const AuthContext = createContext();

/**
 * @brief Provider component for authentication context.
 *
 * This component manages the authentication state of the application, 
 * including user information and loading status. It checks the user's 
 * authentication status when the component mounts.
 *
 * @param {object} children - The child components to be rendered within this provider.
 * @return {JSX.Element} The AuthContext provider with the authentication state.
 */
export const AuthProvider = ({ children }) => {
    // State to track if the user is authenticated
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        return localStorage.getItem('isAuthenticated') === 'true'; // Check local storage for authentication status
    });
    
    // State to store user information
    const [user, setUser] = useState(null);
    
    // State to indicate loading status
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Function to check authentication status from the server
        const checkAuth = async () => {
            try {
                const response = await axios.get(CHECK_SESSION_URL, { withCredentials: true });
                if (response.status === 200) {
                    setIsAuthenticated(true); // Set authentication state to true
                    setUser(response.data.user); // Store user information
                    localStorage.setItem('isAuthenticated', 'true'); // Update local storage
                }
            } catch (error) {
                setIsAuthenticated(false); // Set authentication state to false on error
                setUser(null); // Clear user information
                localStorage.removeItem('isAuthenticated'); // Remove authentication from local storage
            } finally {
                setLoading(false); // Set loading to false after check
            }
        };

        checkAuth(); // Call the authentication check function
    }, []);

    return (
        <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated, user, setUser }}>
            {!loading && children} {/* Render children if loading is complete */}
        </AuthContext.Provider>
    );
};