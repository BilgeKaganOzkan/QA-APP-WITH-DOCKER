import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { CHECK_SESSION_URL } from '../config/constants';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        return localStorage.getItem('isAuthenticated') === 'true';
    });
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await axios.get(CHECK_SESSION_URL, { withCredentials: true });
                if (response.status === 200) {
                    setIsAuthenticated(true);
                    setUser(response.data.user);
                    localStorage.setItem('isAuthenticated', 'true');
                }
            } catch (error) {
                setIsAuthenticated(false);
                setUser(null);
                localStorage.removeItem('isAuthenticated');
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
