import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const SidebarContainer = styled.div`
    position: fixed;
    top: 0;
    left: ${(props) => (props.isOpen ? '0' : '-200px')};
    width: 200px;
    height: 100%;
    background-color: #333;
    color: white;
    padding: 20px;
    box-shadow: 2px 0 5px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: left 0.3s ease;
`;

const SidebarButton = styled.button`
    width: 100%;
    margin: 10px 0;
    padding: 10px;
    background-color: #555;
    color: white;
    border: none;
    cursor: pointer;
    &:hover {
        background-color: #777;
    }
`;

const Sidebar = ({ onPanelSelect }) => {
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        const handleMouseMove = (event) => {
            if (event.clientX < 50) {
                setIsOpen(true);
            } else if (event.clientX > 200) {
                setIsOpen(false);
            }
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, []);

    return (
        <SidebarContainer isOpen={isOpen}>
            <SidebarButton onClick={() => onPanelSelect('sql')}>Open SQL Query Panel</SidebarButton>
            <SidebarButton onClick={() => onPanelSelect('rag')}>Open RAG Panel</SidebarButton>
        </SidebarContainer>
    );
};

export default Sidebar;
