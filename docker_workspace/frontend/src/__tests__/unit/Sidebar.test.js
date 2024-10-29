// src/__tests__/SideBar.test.js

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SideBar from '../../components/SideBar';

/**
 * @brief Test suite for SideBar Component.
 */
describe('SideBar Component', () => {
  const onPanelSelect = jest.fn();  // Mock function for panel selection

  beforeEach(() => {
    onPanelSelect.mockClear();  // Clear mock before each test to avoid test pollution
  });

  /**
   * @test Verifies that the toggle button renders and the SideBar is closed by default.
   * Ensures the initial state of SideBar is as expected.
   */
  test('renders toggle button and SideBar closed by default', () => {
    render(<SideBar onPanelSelect={onPanelSelect} />);
    
    // Verify the presence of the toggle button by its aria-label
    const toggleButton = screen.getByLabelText(/toggle SideBar/i);
    expect(toggleButton).toBeInTheDocument();

    // Verify the SideBar is initially closed
    expect(screen.queryByText(/sql query panel/i)).not.toBeInTheDocument();
  });

  /**
   * @test Verifies that the SideBar opens and closes when the toggle button is clicked.
   * Ensures toggle functionality correctly changes SideBar visibility.
   */
  test('opens and closes the SideBar when the toggle button is clicked', () => {
    render(<SideBar onPanelSelect={onPanelSelect} />);

    // Simulate clicking the toggle button to open the SideBar
    const toggleButton = screen.getByLabelText(/toggle SideBar/i);
    fireEvent.click(toggleButton);

    // Verify the SideBar content is displayed
    expect(screen.getByText(/sql query panel/i)).toBeInTheDocument();
    expect(screen.getByText(/rag panel/i)).toBeInTheDocument();

    // Simulate clicking the toggle button again to close the SideBar
    fireEvent.click(toggleButton);
    expect(screen.queryByText(/sql query panel/i)).not.toBeInTheDocument();
  });

  /**
   * @test Verifies that onPanelSelect is called with 'sql' and the SideBar closes after selecting SQL Query Panel.
   * Ensures the SQL Query Panel selection triggers onPanelSelect with the correct argument.
   */
  test('calls onPanelSelect and closes the SideBar when SQL Query Panel button is clicked', () => {
    render(<SideBar onPanelSelect={onPanelSelect} />);

    // Open SideBar
    const toggleButton = screen.getByLabelText(/toggle SideBar/i);
    fireEvent.click(toggleButton);

    // Simulate clicking the SQL Query Panel button
    const sqlButton = screen.getByText(/sql query panel/i);
    fireEvent.click(sqlButton);

    // Verify onPanelSelect was called with 'sql'
    expect(onPanelSelect).toHaveBeenCalledWith('sql');
    
    // Verify the SideBar closes after selection
    expect(screen.queryByText(/sql query panel/i)).not.toBeInTheDocument();
  });

  /**
   * @test Verifies that the SideBar closes when clicking outside of it.
   * Ensures clicking outside triggers the SideBar close functionality.
   */
  test('closes SideBar when clicking outside', () => {
    render(<SideBar onPanelSelect={onPanelSelect} />);

    // Open SideBar
    const toggleButton = screen.getByLabelText(/toggle SideBar/i);
    fireEvent.click(toggleButton);

    // Simulate clicking outside of the SideBar
    fireEvent.mouseDown(document);

    // Verify the SideBar closes when clicking outside
    expect(screen.queryByText(/sql query panel/i)).not.toBeInTheDocument();
  });
});