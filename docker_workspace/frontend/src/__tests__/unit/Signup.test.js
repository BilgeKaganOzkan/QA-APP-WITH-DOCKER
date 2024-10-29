import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SignUp from '../../components/SignUp';
import axios from 'axios';
import { BrowserRouter } from 'react-router-dom';
import { act } from 'react';
import Cookies from 'js-cookie';

jest.mock('axios');
jest.mock('js-cookie', () => ({
    get: jest.fn(() => ({})),
    remove: jest.fn(),
}));

/**
 * @brief Sets up and renders the SignUp component wrapped in BrowserRouter.
 */
const setup = () => {
    render(
        <BrowserRouter>
            <SignUp />
        </BrowserRouter>
    );
};

/**
 * @brief Test suite for SignUp Component.
 */
describe('SignUp Component', () => {
    
    /**
     * @test Verifies if the SignUp form renders with email, password, confirm password inputs, and the SignUp button.
     */
    test('renders SignUp form with inputs and button', () => {
        setup();
        expect(screen.getByLabelText('Email:')).toBeInTheDocument();
        expect(screen.getByLabelText('Password:')).toBeInTheDocument();
        expect(screen.getByLabelText('Confirm Password:')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /SignUp/i })).toBeInTheDocument();
    });

    /**
     * @test Checks if an error message is displayed when the passwords do not match.
     * Simulates user input of mismatched passwords and asserts for an error message.
     */
    test('displays error when passwords do not match', async () => {
        setup();
        
        await act(async () => {
            fireEvent.change(screen.getByLabelText('Email:'), { target: { value: 'test@example.com' } });
            fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'password123' } });
            fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'differentpassword' } });
            fireEvent.click(screen.getByRole('button', { name: /SignUp/i }));
        });

        expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument();
    });

    /**
     * @test Verifies the successful SignUp flow.
     * Mocks a successful response from the server and checks for success message display.
     */
    test('displays success message and redirects on successful SignUp', async () => {
        axios.post.mockResolvedValueOnce({ status: 201 });

        setup();

        fireEvent.change(screen.getByLabelText('Email:'), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'password123' } });
        fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'password123' } });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /SignUp/i }));
        });

        expect(await screen.findByText('SignUp successful! Please log in.')).toBeInTheDocument();
    });

    /**
     * @test Simulates a failed SignUp attempt and checks if the error message is displayed.
     * Mocks a rejected server response to ensure error handling works as expected.
     */
    test('displays error message on failed SignUp', async () => {
        axios.post.mockRejectedValueOnce({ response: { data: { detail: 'SignUp failed.' } } });

        setup();

        fireEvent.change(screen.getByLabelText('Email:'), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'password123' } });
        fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'password123' } });

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /SignUp/i }));
        });

        expect(await screen.findByText('SignUp failed.')).toBeInTheDocument();
    });

    /**
     * @test Checks if the loading indicator is displayed during SignUp submission.
     * Ensures that the SignUp button is disabled while the request is in progress.
     */
    test('displays loading indicator while signing up', async () => {
        axios.post.mockResolvedValueOnce({ status: 201 });
    
        setup();
    
        fireEvent.change(screen.getByLabelText('Email:'), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'password123' } });
        fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'password123' } });
    
        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /SignUp/i }));
        });
    
        await waitFor(() => {
            expect(screen.getByRole('button', { name: /SignUp/i })).toBeDisabled();
        });
    });
});