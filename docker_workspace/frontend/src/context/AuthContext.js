// src/context/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { START_SESSION_URL } from '../config/constants'; // Importing from constants.js

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if the user is already authenticated by making a request to the server
        const checkAuth = async () => {
            try {
                const response = await axios.get(START_SESSION_URL, { withCredentials: true });
                if (response.status === 200) {
                    setIsAuthenticated(true);
                    setUser(response.data.user); // Adjust based on your backend response
                }
            } catch (error) {
                setIsAuthenticated(false);
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated, user, setUser }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
