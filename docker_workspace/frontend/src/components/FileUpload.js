import React from 'react';

const FileUpload = ({ onFileUpload }) => (
    <div style={{ marginBottom: '10px' }}>
        <input
            type="file"
            onChange={onFileUpload}
            style={{ padding: '10px', backgroundColor: '#fff', color: '#000' }}
        />
    </div>
);

export default FileUpload;
