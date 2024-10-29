// src/components/SignUp.js
import React, { useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import './SignUp.css';
import { SIGNUP_URL } from '../config/constants';
import Cookies from 'js-cookie';

/**
 * @brief SignUp component for user registration.
 *
 * This component allows users to create a new account by entering their email and password.
 * It handles form submission, validates input, and manages success/error messages.
 *
 * @return {JSX.Element} The rendered SignUp component.
 */
const SignUp = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const clearCookies = () => {
        const allCookies = Cookies.get() || {};
        Object.keys(allCookies).forEach(cookieName => Cookies.remove(cookieName));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');
        clearCookies();

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            setLoading(false);
            return;
        }

        try {
            const response = await axios.post(SIGNUP_URL, { email, password }, { withCredentials: true });
            if (response.status === 201) {
                setSuccess('SignUp successful! Please log in.');
                setTimeout(() => navigate('/login'), 700);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'SignUp failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <h2>Sign Up</h2>
            <form onSubmit={handleSubmit} className="auth-form">
                <label htmlFor="email">Email:</label>
                <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <label htmlFor="password">Password:</label>
                <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                <label htmlFor="confirmPassword">Confirm Password:</label>
                <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                />

                {error && <p className="error">{error}</p>}
                {success && <p className="success">{success}</p>}

                <button type="submit" disabled={loading} id='SignUp-button'>
                    {loading ? 'Signing up...' : 'SignUp'}
                </button>
            </form>
            <p>
                Already have an account? <Link to="/login">Login here</Link>
            </p>
        </div>
    );
};

export default SignUp;