// src/components/SideBar.js
import React, { useState, useEffect, useRef } from 'react';
import './SideBar.css';

/**
 * @brief SideBar component for navigating between panels.
 *
 * This component allows users to toggle between SQL Query and RAG panels.
 * It contains buttons for each panel and a toggle button to show or hide
 * the SideBar. It also handles clicks outside the SideBar to close it.
 *
 * @param {function} onPanelSelect - Callback function to handle panel selection.
 * @return {JSX.Element} The rendered SideBar component.
 */
const SideBar = ({ onPanelSelect }) => {
  const [isOpen, setIsOpen] = useState(false); // State to track SideBar open/close status
  const sidebarRef = useRef(null); // Reference to the SideBar container

  /**
   * @brief Handles clicks outside the SideBar to close it.
   *
   * @param {Event} event - The event triggered by a mouse click.
   */
  const handleClickOutside = (event) => {
    if (sidebarRef.current && !sidebarRef.current.contains(event.target)) {
      setIsOpen(false); // Close the SideBar if click is outside
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside); // Add event listener when SideBar is open
    } else {
      document.removeEventListener('mousedown', handleClickOutside); // Remove event listener when SideBar is closed
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside); // Cleanup event listener on unmount
    };
  }, [isOpen]);

  return (
    <>
      {isOpen && (
        <div ref={sidebarRef} className="SideBar-container">
          {/* Button to select SQL Query panel */}
          <button
            id='sql-selection-button'
            className="SideBar-button"
            onClick={() => {
              onPanelSelect('sql'); // Notify parent to switch to SQL panel
              setIsOpen(false); // Close SideBar
            }}
          >
            SQL Query Panel
          </button>
          {/* Button to select RAG panel */}
          <button
            id='rag-selection-button'
            className="SideBar-button"
            onClick={() => {
              onPanelSelect('rag'); // Notify parent to switch to RAG panel
              setIsOpen(false); // Close SideBar
            }}
          >
            RAG Panel
          </button>
        </div>
      )}
      {/* Button to toggle SideBar visibility */}
      <div
        id='side-bar-button'
        role="button"
        aria-label="Toggle SideBar"
        className="toggle-button-container"
        style={{ left: isOpen ? '220px' : '20px' }} // Inline styling for dynamic position
        onClick={() => setIsOpen(!isOpen)} // Toggle SideBar open/close state
      >
        {isOpen ? '<' : '>'} {/* Display toggle icon */}
      </div>
    </>
  );
};

export default SideBar;