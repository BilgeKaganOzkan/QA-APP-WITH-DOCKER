// src/__tests__/QueryInput.test.js

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import QueryInput from '../../components/QueryInput';

/**
 * @brief Test suite for QueryInput Component.
 */
describe('QueryInput Component', () => {
    // Mock functions to handle file selection, file removal, and query submission
    const handleFileSelection = jest.fn();
    const removeSelectedFile = jest.fn();
    const handleSend = jest.fn();
    const fileInputRef = { current: null };  // Reference for file input element
    const accept = '.csv, .pdf'; // Accepted file types

    /**
     * @test Ensures the component renders with query input, file input, and submit button.
     * Verifies that the essential elements are present in the DOM.
     */
    test('renders input, upload icon, and submit button', () => {
        render(
            <QueryInput
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={[]}
                handleSend={handleSend}
                fileInputRef={fileInputRef}
                accept={accept}
                isUploading={false}
                disabled={false}
            />
        );

        // Verify the presence of the query input field
        const queryInput = screen.getByPlaceholderText(/Enter your query here/i);
        expect(queryInput).toBeInTheDocument();

        // Verify the presence of the file input (upload icon)
        const fileInput = screen.getByTestId('file-input');
        expect(fileInput).toBeInTheDocument();

        // Verify the presence of the submit button
        const submitButton = screen.getByRole('button', { name: /send/i });
        expect(submitButton).toBeInTheDocument();
    });

    /**
     * @test Ensures that selecting a file triggers the handleFileSelection callback.
     * Simulates file selection and verifies correct callback invocation with the selected file.
     */
    test('handles file selection', () => {
        render(
            <QueryInput
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={[]}
                handleSend={handleSend}
                fileInputRef={fileInputRef}
                accept={accept}
                isUploading={false}
                disabled={false}
            />
        );
    
        // Simulate file selection with a mock file
        const fileInput = screen.getByTestId('file-input');
        const file = new File(['sample'], 'sample.csv', { type: 'text/csv' });
        fireEvent.change(fileInput, { target: { files: [file] } });
    
        // Verify handleFileSelection was called with the correct file
        expect(handleFileSelection).toHaveBeenCalledTimes(1);
        expect(handleFileSelection).toHaveBeenCalledWith(
            expect.arrayContaining([
                expect.objectContaining({
                    name: 'sample.csv',
                    type: 'text/csv'
                })
            ])
        );
    });

    /**
     * @test Ensures that clicking the remove button removes the selected file.
     * Verifies the removeSelectedFile callback is called with the correct index.
     */
    test('removes selected file when remove button is clicked', () => {
        render(
            <QueryInput
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={[{ name: 'sample.csv' }]}
                handleSend={handleSend}
                fileInputRef={fileInputRef}
                accept={accept}
                isUploading={false}
                disabled={false}
            />
        );

        // Locate and click the remove file button
        const removeButton = screen.getByRole('button', { name: /×/i });
        fireEvent.click(removeButton);

        // Verify removeSelectedFile was called with the correct index
        expect(removeSelectedFile).toHaveBeenCalledWith(0);
    });

    /**
     * @test Ensures that submitting a query triggers the handleSend callback.
     * Simulates entering a query and clicking send, verifying correct callback invocation.
     */
    test('submits query', () => {
        render(
            <QueryInput
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={[]}
                handleSend={handleSend}
                fileInputRef={fileInputRef}
                accept={accept}
                isUploading={false}
                disabled={false}
            />
        );

        // Enter a query and submit
        const queryInput = screen.getByPlaceholderText(/Enter your query here/i);
        const submitButton = screen.getByRole('button', { name: /send/i });
        fireEvent.change(queryInput, { target: { value: 'test query' } });
        fireEvent.click(submitButton);

        // Verify handleSend was called with the correct query
        expect(handleSend).toHaveBeenCalledWith('test query');
    });

    /**
     * @test Ensures that input elements are disabled during uploading or when the component is disabled.
     * Verifies that query input, file input, and submit button are not interactable.
     */
    test('disables input elements when uploading or disabled', () => {
        render(
            <QueryInput
                handleFileSelection={handleFileSelection}
                removeSelectedFile={removeSelectedFile}
                selectedFiles={[]}
                handleSend={handleSend}
                fileInputRef={fileInputRef}
                accept={accept}
                isUploading={true}  // Simulate uploading state
                disabled={true}    // Simulate disabled state
            />
        );

        // Check that all input elements are disabled
        const queryInput = screen.getByPlaceholderText(/Enter your query here/i);
        const fileInput = screen.getByTestId('file-input');
        const submitButton = screen.getByRole('button', { name: /send/i });

        expect(queryInput).toBeDisabled();
        expect(fileInput).toBeDisabled();
        expect(submitButton).toBeDisabled();
    });
});