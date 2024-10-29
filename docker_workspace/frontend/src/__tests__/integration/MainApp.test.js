import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MainApp from '../../components/MainApp';
import { AuthContext } from '../../context/AuthContext';
import axios from 'axios';

// Mock axios for API calls
jest.mock('axios');

// Mock authentication context values
const mockAuthContextValue = {
    isAuthenticated: true,
    setIsAuthenticated: jest.fn(),
    setUser: jest.fn(),
};

describe('MainApp Integration Test', () => {
    // Suppress console error output for cleaner test results
    let consoleErrorSpy;

    beforeEach(() => {
        jest.clearAllMocks();
        consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        consoleErrorSpy.mockRestore();
    });

    /**
     * @description Test case to verify session state rendering and logout functionality
     * It checks if the session starts as expected and handles logout correctly by clearing authentication state.
     */
    test('renders session state and handles logout', async () => {
        render(
            <AuthContext.Provider value={mockAuthContextValue}>
                <BrowserRouter>
                    <MainApp />
                </BrowserRouter>
            </AuthContext.Provider>
        );

        // Check if the session initialization message is displayed
        await waitFor(() => {
            expect(screen.getByText(/session starting/i)).toBeInTheDocument();
        });

        // Locate and click the logout button
        const logoutButton = screen.getByRole('button', { name: /logout/i });
        await act(async () => {
            fireEvent.click(logoutButton);
        });

        // Validate that the authentication state is cleared after logout
        await waitFor(() => {
            expect(mockAuthContextValue.setIsAuthenticated).toHaveBeenCalledWith(false);
            expect(mockAuthContextValue.setUser).toHaveBeenCalledWith(null);
            expect(screen.queryByText(/session started/i)).not.toBeInTheDocument();
        });
    });

    /**
     * @description Test case to switch panels and start a new session
     * It verifies the SideBar functionality for switching to the RAG panel and starting a new session.
     */
    test('switches panel and starts a new session', async () => {
        render(
            <AuthContext.Provider value={mockAuthContextValue}>
                <BrowserRouter>
                    <MainApp />
                </BrowserRouter>
            </AuthContext.Provider>
        );

        // Confirm initial panel text
        expect(screen.getByText(/Q&A with Tabular Data/i)).toBeInTheDocument();

        // Open the SideBar
        const sidebarButton = screen.getByRole('button', { name: /toggle SideBar/i });
        await act(async () => {
            fireEvent.click(sidebarButton);
        });

        // Ensure the SideBar and "RAG" panel button are rendered
        await waitFor(() => {
            expect(screen.getByText(/RAG/i)).toBeInTheDocument();
        });

        // Click the "RAG" panel button
        await act(async () => {
            fireEvent.click(screen.getByText(/RAG/i));
        });

        // Verify that a new session has started for the RAG panel
        await waitFor(() => {
            expect(screen.getByText(/Switched to RAG Panel/i)).toBeInTheDocument();
            expect(screen.getByText(/New session started/i)).toBeInTheDocument();
        });
    });

    /**
     * @description Test case to handle file upload and show progress
     * It simulates a file upload and verifies that the upload progress and completion messages are displayed.
     */
    test('handles file upload and shows progress', async () => {
        // Mock API responses for file upload and progress polling
        axios.put.mockResolvedValueOnce({
            data: { informationMessage: 'Files uploaded successfully.' },
        });
        axios.get.mockResolvedValueOnce({ data: { progress: 100 } });

        render(
            <AuthContext.Provider value={mockAuthContextValue}>
                <BrowserRouter>
                    <MainApp />
                </BrowserRouter>
            </AuthContext.Provider>
        );

        // Simulate selecting a file
        const file = new File(['dummy content'], 'test.csv', { type: 'text/csv' });
        const fileInput = screen.getByTestId('file-input');
        fireEvent.change(fileInput, { target: { files: [file] } });

        // Trigger file upload by clicking the send button
        const sendButton = screen.getByRole('button', { name: /send/i });
        fireEvent.click(sendButton);

        // Check for upload progress message
        await waitFor(() => {
            expect(screen.getByText(/uploading files/i)).toBeInTheDocument();
        });

        // Verify final success message after upload completes
        await waitFor(() => {
            expect(screen.getByText(/files uploaded successfully/i)).toBeInTheDocument();
        });
    });

    /**
     * @description Test case to handle query submission and display AI response
     * It sends a query to the server and checks if the AI's response is displayed in the chat box.
     */
    test('handles query submission and displays AI response', async () => {
        // Mock the API response for the AI query
        axios.post.mockResolvedValueOnce({ data: { aiMessage: 'This is the AI response.' } });

        render(
            <AuthContext.Provider value={mockAuthContextValue}>
                <BrowserRouter>
                    <MainApp />
                </BrowserRouter>
            </AuthContext.Provider>
        );

        // Enter a query in the input field
        const queryInput = screen.getByPlaceholderText(/Enter your query/i);
        await act(async () => {
            fireEvent.change(queryInput, { target: { value: 'Sample query' } });
        });

        // Submit the query
        const sendButton = screen.getByRole('button', { name: /send/i });
        await act(async () => {
            fireEvent.click(sendButton);
        });

        // Verify that both the query and the AI's response are displayed
        await waitFor(() => {
            expect(screen.getByText(/sample query/i)).toBeInTheDocument();
            expect(screen.getByText(/this is the ai response/i)).toBeInTheDocument();
        });
    });
});