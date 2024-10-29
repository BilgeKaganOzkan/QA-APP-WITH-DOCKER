// src/components/Login.js

import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import './Login.css';
import { LOGIN_URL } from '../config/constants';

/**
 * @brief Login component for user authentication.
 *
 * This component provides a login form for users to enter their email
 * and password. It handles form submission, communicates with the backend
 * to authenticate the user, and manages authentication state using context.
 *
 * @return {JSX.Element} The rendered Login component.
 */
const Login = () => {
    const { setIsAuthenticated, setUser } = useContext(AuthContext); // Access authentication context
    const [email, setEmail] = useState(''); // State for email input
    const [password, setPassword] = useState(''); // State for password input
    const [error, setError] = useState(''); // State for error messages
    const [loading, setLoading] = useState(false); // State to manage loading status
    const navigate = useNavigate(); // Hook to programmatically navigate

    /**
     * @brief Handles form submission for login.
     *
     * This function prevents the default form submission, sends the login
     * request to the server, and manages the response and potential errors.
     *
     * @param {Event} e - The form submission event.
     */
    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevent default form submission
        setLoading(true); // Set loading to true while waiting for response
        setError(''); // Clear previous error messages

        try {
            const response = await axios.post(LOGIN_URL, {
                email,
                password
            }, {
                withCredentials: true // Include credentials in the request
            });
            if (response.status === 200) {
                console.log(response.data.informationMessage); 
                setIsAuthenticated(true); // Update authentication state
                setUser(response.data.user); // Set user data in context
                navigate('/'); // Navigate to the main application page
            }
        } catch (err) {
            console.error('Login error:', err);
            // Set error message based on server response or default message
            if (err.response && err.response.data) {
                setError(err.response.data.detail || 'Login failed.');
            } else {
                setError('Login failed. Please try again.');
            }
        } finally {
            setLoading(false); // Reset loading state after request completion
        }
    };

    return (
        <div className="auth-container">
            <h2>Login</h2>
            <form onSubmit={handleSubmit} className="auth-form">
                <label htmlFor="email">Email:</label>
                <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)} // Update email state
                    required // Require email input
                />

                <label htmlFor="password">Password:</label>
                <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)} // Update password state
                    required // Require password input
                />

                {error && <p className="error">{error}</p>} {/* Display error message if any */}

                <button type="submit" disabled={loading} id='login-button'> {/* Disable button while loading */}
                    {loading ? 'Logging in...' : 'Login'} {/* Change button text based on loading state */}
                </button>
            </form>
            <p>
                Don't have an account? <Link to="/signup">SignUp here</Link> {/* Link to SignUp page */}
            </p>
        </div>
    );
};

export default Login;