import React, { useState } from 'react';

const QueryInput = ({ onSubmit }) => {
    const [query, setQuery] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(query);
        setQuery("");
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your query here"
                style={{ flexGrow: 1, padding: '10px', marginRight: '10px' }}
            />
            <button type="submit">Submit</button>
        </form>
    );
};

export default QueryInput;
