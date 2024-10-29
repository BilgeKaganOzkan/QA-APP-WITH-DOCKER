// src/__tests__/Login.test.js

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../components/Login';
import { AuthContext } from '../../context/AuthContext';
import axios from 'axios';

// Mock axios to simulate HTTP requests in tests
jest.mock('axios');

/**
 * @brief Test suite for Login Component.
 */
describe('Login Component', () => {
  // Mock functions to simulate AuthContext actions
  const mockSetIsAuthenticated = jest.fn();
  const mockSetUser = jest.fn();

  // Suppress console error and log output for cleaner test results
  let consoleErrorSpy, consoleLogSpy;

  beforeEach(() => {
    // Mock console.error and console.log to avoid cluttering test output
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    // Render the Login component within AuthContext and BrowserRouter
    render(
      <AuthContext.Provider value={{ setIsAuthenticated: mockSetIsAuthenticated, setUser: mockSetUser }}>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthContext.Provider>
    );
  });

  afterEach(() => {
    // Restore original console methods after each test
    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  /**
   * @test Verifies that the login form renders with expected elements.
   * Ensures email input, password input, and login button are present.
   */
  test('renders login form', () => {
    // Check for email, password input fields, and login button
    expect(screen.getByLabelText(/Email:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password:/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  /**
   * @test Verifies that email and password fields update correctly when typed into.
   * Simulates user input in both fields and checks for value updates.
   */
  test('updates email and password fields', () => {
    // Select email and password inputs
    const emailInput = screen.getByLabelText(/Email:/i);
    const passwordInput = screen.getByLabelText(/Password:/i);

    // Simulate typing into the email and password fields
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    // Check if the values were updated
    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });

  /**
   * @test Verifies that a loading indicator appears, and login button disables on submit.
   * Checks if the authentication state updates upon a successful login.
   */
  test('displays loading indicator and disables button on submit', async () => {
    const emailInput = screen.getByLabelText(/Email:/i);
    const passwordInput = screen.getByLabelText(/Password:/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Enter valid credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    // Mock successful login response
    axios.post.mockResolvedValueOnce({ status: 200, data: { user: { name: 'Test User' } } });

    // Click login button to submit
    fireEvent.click(loginButton);

    // Expect button to show "Logging in..." and be disabled
    expect(loginButton).toHaveTextContent('Logging in...');
    expect(loginButton).toBeDisabled();

    // Wait for authentication actions to be called and verify their arguments
    await waitFor(() => expect(mockSetIsAuthenticated).toHaveBeenCalledWith(true));
    expect(mockSetUser).toHaveBeenCalledWith({ name: 'Test User' });
  });

  /**
   * @test Verifies that an error message is displayed when login fails.
   * Simulates a failed login attempt with incorrect credentials and checks for error display.
   */
  test('displays error message on failed login', async () => {
    const emailInput = screen.getByLabelText(/Email:/i);
    const passwordInput = screen.getByLabelText(/Password:/i);
    const loginButton = screen.getByRole('button', { name: /login/i });

    // Enter invalid credentials
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

    // Mock failed login response with an error message
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Invalid credentials' } },
    });

    // Click login button to submit
    fireEvent.click(loginButton);

    // Wait for error message to be displayed
    await waitFor(() => expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument());
  });
});