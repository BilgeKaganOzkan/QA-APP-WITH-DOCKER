import React, { useContext } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import MainApp from './components/MainApp';
import { AuthContext } from './context/AuthContext';
import './App.css';

function App() {
    const { isAuthenticated } = useContext(AuthContext);

    return (
        <Router>
            <Routes>
                <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
                <Route path="/signup" element={!isAuthenticated ? <Signup /> : <Navigate to="/" />} />
                <Route path="/" element={isAuthenticated ? <MainApp /> : <Navigate to="/login" />} />
                <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} />} />
            </Routes>
        </Router>
    );
}

export default App;
