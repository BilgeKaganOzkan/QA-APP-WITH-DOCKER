import React from 'react';

const FileUpload = ({ handleFileUpload, fileInputRef, accept }) => (
    <form onSubmit={handleFileUpload} style={{ display: 'flex', width: '100%', maxWidth: '800px', marginBottom: '20px' }}>
        <input
            type="file"
            name="fileInput"
            multiple
            accept={accept}
            ref={fileInputRef}
            style={{
                flexGrow: 1,
                padding: '12px 15px',
                marginRight: '10px',
                backgroundColor: '#f1f1f1',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
            }}
        />
        <button type="submit">Upload</button>
    </form>
);

export default FileUpload;