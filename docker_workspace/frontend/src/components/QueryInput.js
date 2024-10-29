import React, { useState } from 'react';
import './QueryInput.css';

/**
 * @brief QueryInput component for handling user queries and file uploads.
 *
 * This component allows users to enter queries and upload files for processing.
 * It displays selected files and provides functionality to remove them.
 *
 * @param {Object} props - The props object.
 * @param {function} props.handleFileSelection - Function to handle file selection.
 * @param {function} props.removeSelectedFile - Function to remove a selected file.
 * @param {Array} props.selectedFiles - Array of currently selected files.
 * @param {function} props.handleSend - Function to handle sending the query.
 * @param {React.Ref} props.fileInputRef - Ref for accessing the file input element.
 * @param {string} props.accept - The types of files that can be uploaded (MIME types).
 * @param {boolean} props.isUploading - Indicates if files are currently being uploaded.
 * @param {string} props.selectedPanel - The currently selected panel (SQL/RAG).
 * @param {boolean} props.disabled - Indicates if the input is disabled.
 * @return {JSX.Element} The rendered QueryInput component.
 */
const QueryInput = ({
    handleFileSelection,
    removeSelectedFile,
    selectedFiles,
    handleSend,
    fileInputRef,
    accept,
    isUploading,
    selectedPanel,
    disabled
}) => {
    const [query, setQuery] = useState(""); // State for user query input

    /**
     * @brief Handles form submission for the query.
     *
     * This function prevents default form submission and calls the handleSend function
     * with the current query if the input is not disabled.
     *
     * @param {Event} e - The form submission event.
     */
    const handleSubmit = (e) => {
        e.preventDefault(); // Prevent default form submission
        if (!disabled) {
            handleSend(query); // Send the query
            setQuery(""); // Reset the query input
        }
    };

    /**
     * @brief Handles file input changes.
     *
     * This function processes the selected files and calls the handleFileSelection function.
     *
     * @param {Event} e - The change event from the file input.
     */
    const handleFileChange = (e) => {
        const files = e.target.files; // Get the selected files
        if (files && files.length > 0) {
            handleFileSelection(files); // Handle file selection
            e.target.value = null; // Reset the input value
        }
    };

    /**
     * @brief Returns the icon for the file based on its extension.
     *
     * @param {string} fileName - The name of the file.
     * @return {string} The URL of the corresponding file icon image.
     */
    const getFileIcon = (fileName) => {
        const extension = fileName.split('.').pop().toLowerCase();
        if (extension === 'csv') {
            return '/csv_logo.jpg'; // CSV file icon
        } else if (extension === 'pdf') {
            return '/pdf_logo.png'; // PDF file icon
        } else {
            return '/file_logo.png'; // Default file icon
        }
    };

    return (
        <div className="query-input-container">
            {selectedFiles.length > 0 && (
                <div className="selected-files-container">
                    {/* Display selected files with icons and remove button */}
                    {selectedFiles.map((file, index) => (
                        <div key={index} className="file-box">
                            <div className="file-icon">
                                <img src={getFileIcon(file.name)} alt="File Icon" />
                            </div>
                            <div className="file-name" title={file.name}>
                                {file.name.length > 15
                                    ? file.name.slice(0, 12) + '...' // Truncate long file names
                                    : file.name}
                            </div>
                            <button
                                type="button"
                                className="remove-file-button"
                                onClick={() => removeSelectedFile(index)} // Remove selected file
                                disabled={isUploading || disabled}
                            >
                                &times; {/* Remove file button */}
                            </button>
                        </div>
                    ))}
                </div>
            )}
            <form onSubmit={handleSubmit} className="query-input-form">
                <input
                    id='query-input'
                    type="text"
                    value={query} // Query input value
                    onChange={(e) => setQuery(e.target.value)} // Update query state
                    placeholder="Enter your query here" // Placeholder text
                    className="query-input"
                    disabled={isUploading || disabled} // Disable input if uploading or disabled
                />
                <div className="input-actions">
                    <label htmlFor="file-input" className="upload-icon">
                        {/* File upload icon */}
                        <svg width="24" height="24" viewBox="0 0 24 24">
                            <path fill="white" d="M5 20h14v-2H5v2zm7-18L5.33 9h3.34v4h6V9h3.33L12 2z"/>
                        </svg>
                    </label>
                    <input
                        type="file"
                        id="file-input"
                        data-testid="file-input"
                        name="fileInput"
                        multiple // Allow multiple file selection
                        accept={accept} // Restrict file types based on the accept prop
                        ref={fileInputRef} // Reference to the file input element
                        style={{ display: 'none' }} // Hide the file input
                        onChange={handleFileChange} // Handle file selection
                        disabled={isUploading || disabled} // Disable input if uploading or disabled
                    />
                    <button
                        id="submit-button"
                        type="submit"
                        className="submit-button"
                        disabled={isUploading || disabled} // Disable button if uploading or disabled
                    >
                        Send {/* Button to submit the query */}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default QueryInput;