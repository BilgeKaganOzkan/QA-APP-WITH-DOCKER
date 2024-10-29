import React, { useContext } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './components/Login';
import SignUp from './components/SignUp';
import MainApp from './components/MainApp';
import { AuthContext } from './context/AuthContext';
import './App.css';

/**
 * @brief The main application component.
 *
 * This component sets up the routing for the application using React Router.
 * It checks the authentication status and conditionally renders the appropriate
 * components based on whether the user is authenticated.
 *
 * @return {JSX.Element} The rendered App component.
 */
function App() {
    // Use the AuthContext to access the authentication status
    const { isAuthenticated } = useContext(AuthContext);

    return (
        <Router>
            <Routes>
                {/* Route for the login page; redirects to MainApp if already authenticated */}
                <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
                
                {/* Route for the Signup page; redirects to MainApp if already authenticated */}
                <Route path="/signup" element={!isAuthenticated ? <SignUp /> : <Navigate to="/" />} />
                
                {/* Main application route; redirects to login if not authenticated */}
                <Route path="/" element={isAuthenticated ? <MainApp /> : <Navigate to="/login" />} />
                
                {/* Catch-all route; redirects to login or MainApp based on authentication status */}
                <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} />} />
            </Routes>
        </Router>
    );
}

export default App;