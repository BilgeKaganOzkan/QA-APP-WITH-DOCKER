// Sidebar.js
import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';

const SidebarContainer = styled.div`
  position: fixed;
  top: 0;
  left: ${(props) => (props.isOpen ? '0' : '-220px')};
  width: 220px;
  height: 100%;
  background-color: #20232a;
  color: white;
  padding-top: 60px;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.5);
  transition: left 0.3s ease;
  z-index: 1000;
`;

const SidebarButton = styled.button`
  width: 180px;
  margin: 10px;
  padding: 12px;
  background-color: #61dafb;
  color: #20232a;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  &:hover {
    background-color: #21a1f1;
  }
`;

const ToggleButton = styled.div`
  position: fixed;
  top: 20px;
  left: ${(props) => (props.isOpen ? '220px' : '20px')};
  width: 30px;
  height: 30px;
  background-color: #61dafb;
  color: #20232a;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  transition: left 0.3s ease;
  z-index: 1100;
`;

const Sidebar = ({ onPanelSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const sidebarRef = useRef(null);

  const handleClickOutside = (event) => {
    if (sidebarRef.current && !sidebarRef.current.contains(event.target)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <>
      <SidebarContainer isOpen={isOpen} ref={sidebarRef}>
        <SidebarButton onClick={() => {
          onPanelSelect('sql');
          setIsOpen(false);
        }}>
          SQL Query Panel
        </SidebarButton>
        <SidebarButton onClick={() => {
          onPanelSelect('rag');
          setIsOpen(false);
        }}>
          RAG Panel
        </SidebarButton>
      </SidebarContainer>
      <ToggleButton isOpen={isOpen} onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '<' : '>'}
      </ToggleButton>
    </>
  );
};

export default Sidebar;
