// src/components/Login.js
import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import './Auth.css'; // Create this CSS file for styling
import { LOGIN_URL } from '../config/constants'; // Importing from constants.js

const Login = () => {
    const { setIsAuthenticated, setUser } = useContext(AuthContext);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await axios.post(LOGIN_URL, { email, password }, { withCredentials: true });
            if (response.status === 200) {
                setIsAuthenticated(true);
                setUser(response.data.user); // Adjust based on your backend response
                navigate('/'); // Redirect to main app
            }
        } catch (err) {
            if (err.response && err.response.data) {
                setError(err.response.data.detail || 'Login failed.');
            } else {
                setError('Login failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <h2>Login</h2>
            <form onSubmit={handleSubmit} className="auth-form">
                <label>Email:</label>
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <label>Password:</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                {error && <p className="error">{error}</p>}

                <button type="submit" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>
            <p>
                Don't have an account? <Link to="/signup">Signup here</Link>
            </p>
        </div>
    );
};

export default Login;
