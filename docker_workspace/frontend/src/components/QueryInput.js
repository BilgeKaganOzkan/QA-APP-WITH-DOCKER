import React, { useState } from 'react';
import './QueryInput.css';

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
    const [query, setQuery] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!disabled) {
            handleSend(query);
            setQuery("");
        }
    };

    const handleFileChange = (e) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelection(files);
            e.target.value = null;
        }
    };

    const getFileIcon = (fileName) => {
        const extension = fileName.split('.').pop().toLowerCase();
        if (extension === 'csv') {
            return '/csv_logo.jpg';
        } else if (extension === 'pdf') {
            return '/pdf_logo.png';
        } else {
            return '/file_logo.png';
        }
    };

    return (
        <div className="query-input-container">
            {selectedFiles.length > 0 && (
                <div className="selected-files-container">
                    {selectedFiles.map((file, index) => (
                        <div key={index} className="file-box">
                            <div className="file-icon">
                                <img src={getFileIcon(file.name)} alt="File Icon" />
                            </div>
                            <div className="file-name" title={file.name}>
                                {file.name.length > 15
                                    ? file.name.slice(0, 12) + '...'
                                    : file.name}
                            </div>
                            <button
                                type="button"
                                className="remove-file-button"
                                onClick={() => removeSelectedFile(index)}
                                disabled={isUploading || disabled}
                            >
                                &times;
                            </button>
                        </div>
                    ))}
                </div>
            )}
            <form onSubmit={handleSubmit} className="query-input-form">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter your query here"
                    className="query-input"
                    disabled={isUploading || disabled}
                />
                <div className="input-actions">
                    <label htmlFor="file-input" className="upload-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24">
                            <path fill="white" d="M5 20h14v-2H5v2zm7-18L5.33 9h3.34v4h6V9h3.33L12 2z"/>
                        </svg>
                    </label>
                    <input
                        type="file"
                        id="file-input"
                        name="fileInput"
                        multiple
                        accept={accept}
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        onChange={handleFileChange}
                        disabled={isUploading || disabled}
                    />
                    <button
                        type="submit"
                        className="submit-button"
                        disabled={isUploading || disabled}
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
};

export default QueryInput;