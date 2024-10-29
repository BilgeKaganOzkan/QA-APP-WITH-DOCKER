// src/__tests__/ChatBox.test.js

import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatBox from '../../components/ChatBox';

/**
 * @brief Test suite for ChatBox Component.
 */
describe('ChatBox Component', () => {
  const messages = [
    { type: 'user', text: 'Hello!' },
    { type: 'ai', text: 'Hi, how can I help you?' },
    { type: 'system', text: 'Session started.' },
  ];

  // Mock `scrollIntoView` globally for the tests to simulate automatic scrolling behavior
  beforeAll(() => {
    window.HTMLElement.prototype.scrollIntoView = jest.fn();
  });

  /**
   * @test Verifies that messages are displayed with correct content and avatars.
   * Ensures message text, user avatar, AI avatar, and system avatar render accurately.
   */
  test('renders messages with correct content and avatars', () => {
    render(<ChatBox messages={messages} />);

    // Verify each message text appears in the chat box
    messages.forEach((message) => {
      expect(screen.getByText(message.text)).toBeInTheDocument();
    });

    // Verify the presence of the user avatar for user messages
    const userAvatars = screen.getAllByAltText('User avatar');
    expect(userAvatars[0].src).toContain('/user_logo.png');

    // Verify the presence of the AI avatar for AI messages
    const aiAvatar = screen.getByAltText('ai avatar');
    expect(aiAvatar.src).toContain('/ai_logo.png');

    // Verify the presence of the system avatar for system messages
    const systemAvatar = screen.getByAltText('system avatar');
    expect(systemAvatar.src).toContain('/system_logo.png');
  });

  /**
   * @test Verifies that the chat box automatically scrolls to the bottom when new messages are added.
   * Ensures that the latest message is visible after updates.
   */
  test('scrolls to the bottom when new messages are added', () => {
    // Initial render with a single message
    const { rerender } = render(<ChatBox messages={[{ type: 'user', text: 'Hello!' }]} />);
    
    // Rerender the component with additional messages to simulate new messages arriving
    rerender(<ChatBox messages={[...messages, { type: 'user', text: 'Another message' }]} />);
    
    // Verify that scrollIntoView is called to scroll to the latest message
    expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalled();
  });
});