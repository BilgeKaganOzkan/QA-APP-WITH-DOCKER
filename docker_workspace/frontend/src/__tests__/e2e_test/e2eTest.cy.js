import 'cypress-file-upload';

/**
 * @brief End-to-End Test Suite
 */
describe('End-to-End Test', () => {
  const email = 'testuser1@example.com';
  const password = 'testpassword';
  const sqlFilePath = './sqlfile.csv';
  const ragFilePath = './ragfile.pdf';
  const question = 'What is the oldest employee?';

  /**
   * @test Verifies that a new user can successfully sign up.
   * It confirms that the user is redirected to the login page upon successful sign-up.
   */
  it('Signs up a new user', () => {
    // Visit the signup page
    cy.visit('http://localhost:3000/signup');
    cy.screenshot('signup_page_loaded');

    // Fill out the signup form
    cy.get('#email').should('exist').type(email);
    cy.get('#password').should('exist').type(password);
    cy.get('#confirmPassword').should('exist').type(password);

    // Submit the form and verify redirection to the login page
    cy.get('#SignUp-button').should('exist').click();
    cy.screenshot('after_signup');
    cy.url({ timeout: 1000 }).should('include', '/login');
  });

  /**
   * @test Ensures that a registered user can log in successfully.
   * Verifies that the user is redirected to the homepage upon successful login.
   */
  it('Logs in the user', () => {
    // Visit the login page
    cy.visit('http://localhost:3000/login');
    cy.screenshot('login_page_loaded');

    // Fill out the login form
    cy.get('#email').should('exist').type(email);
    cy.get('#password').should('exist').type(password);
    cy.get('#login-button').should('exist').click();
    cy.screenshot('after_login');

    // Verify redirection to the homepage
    cy.url().should('include', '/');
  });

  /**
   * @test Verifies the ability to upload an SQL file and submit a question.
   * Ensures the file upload functionality works, and the query is sent and processed.
   */
  it('Uploads SQL file and asks a question', () => {
    // Log in before performing actions
    cy.visit('http://localhost:3000/login', { timeout: 1000 });

    cy.get('#email').should('exist').type(email);
    cy.get('#password').should('exist').type(password);
    cy.get('#login-button').should('exist').click();

    // Upload SQL file and wait for upload to complete
    cy.get('#file-input', { timeout: 1000 })
      .attachFile(sqlFilePath);
    cy.screenshot('before_sql_upload');

    cy.get('#submit-button', { timeout: 10000 }).should('exist').and('be.visible').click();
    cy.get('.progress-container', { timeout: 30000 }).should('not.exist');
    cy.screenshot('after_sql_upload');

    // Enter a question and submit
    cy.get('#query-input').should('exist').and('be.visible').type(question);
    cy.get('#submit-button').should('exist').and('be.visible').click();
    cy.screenshot('after_sql_question');

    // Verify that a response appears in the chat box
    cy.get('#chat-box', { timeout: 3000 }).should('contain.text', '');
    cy.screenshot('after_response');
  });

  /**
   * @test Validates navigation to the RAG panel via the SideBar and file upload functionality.
   * Ensures that the user can switch to the RAG panel and successfully upload a file.
   */
  it('Navigates to RAG panel through SideBar and uploads SQL file', () => {
    // Log in before accessing the sidebar
    cy.visit('http://localhost:3000/login', { timeout: 1000 });

    cy.get('#email').should('exist').type(email);
    cy.get('#password').should('exist').type(password);
    cy.get('#login-button').should('exist').click();

    cy.screenshot('before_panel_open');

    // Open the sidebar and switch to the RAG panel
    cy.get('#side-bar-button').should('exist').click();
    cy.screenshot('after_panel_open');

    cy.get('#rag-selection-button').should('exist').click();
    cy.screenshot('before_rag_upload');

    // Upload a file on the RAG panel
    cy.get('#file-input', { timeout: 10000 }).should('exist').attachFile(ragFilePath);
    cy.get('#submit-button', { timeout: 10000 }).should('exist').click();
    cy.screenshot('after_rag_upload');

    // Type a question and submit it on the RAG panel
    cy.get('#query-input', { timeout: 10000 }).should('not.be.disabled').type(question);
    cy.get('#submit-button', { timeout: 10000 }).should('exist').and('be.visible').click();
    cy.screenshot('after_rag_question');

    // Check for the presence of a response in the chat box
    cy.get('#chat-box', { timeout: 10000 }).should('contain.text', '');
    cy.screenshot('after_rag_response');
  });

  /**
   * @test Ensures that the user can log out successfully.
   * Verifies that the user is redirected to the login page upon logout.
   */
  it('Logs out the user', () => {
    // Log in before logging out
    cy.visit('http://localhost:3000/login', { timeout: 1000 });

    cy.get('#email').should('exist').type(email);
    cy.get('#password').should('exist').type(password);
    cy.get('#login-button').should('exist').click();

    // Click the logout button and verify redirection to the login page
    cy.get('#logout-button', { timeout: 3000 }).should('exist').click();
    cy.screenshot('after_logout');

    cy.url().should('include', '/login');
  });
});