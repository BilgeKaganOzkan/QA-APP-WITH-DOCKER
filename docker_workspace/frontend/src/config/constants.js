// Base URL for the API
export const API_BASE_URL = "http://localhost:8000"; // The base URL for the API server

/**
 * @brief API endpoint for user SignUp.
 *
 * This URL is used to send requests for user registration.
 */
export const SIGNUP_URL = `${API_BASE_URL}/signup`;

/**
 * @brief API endpoint for user login.
 *
 * This URL is used to send requests for user authentication.
 */
export const LOGIN_URL = `${API_BASE_URL}/login`;

/**
 * @brief API endpoint for starting a user session.
 *
 * This URL is used to initiate a session for an authenticated user.
 */
export const START_SESSION_URL = `${API_BASE_URL}/start_session`;

/**
 * @brief API endpoint for uploading CSV files.
 *
 * This URL is used to send requests for uploading CSV files to the server.
 */
export const UPLOAD_CSV_URL = `${API_BASE_URL}/upload_csv`;

/**
 * @brief API endpoint for uploading PDF files.
 *
 * This URL is used to send requests for uploading PDF files to the server.
 */
export const UPLOAD_PDF_URL = `${API_BASE_URL}/upload_pdf`;

/**
 * @brief API endpoint for executing SQL queries.
 *
 * This URL is used to send SQL queries to the server for execution.
 */
export const SQL_QUERY_URL = `${API_BASE_URL}/sql_query`;

/**
 * @brief API endpoint for executing RAG queries.
 *
 * This URL is used to send RAG (Retrieval-Augmented Generation) queries to the server.
 */
export const RAG_QUERY_URL = `${API_BASE_URL}/rag_query`;

/**
 * @brief API endpoint for ending a user session.
 *
 * This URL is used to terminate an active session for the user.
 */
export const END_SESSION_URL = `${API_BASE_URL}/end_session`;

/**
 * @brief API endpoint for retrieving the progress of ongoing operations.
 *
 * This URL is used to check the current progress of tasks performed by the server.
 */
export const GET_PROGRESS_URL = `${API_BASE_URL}/get_progress`;

/**
 * @brief API endpoint for checking the current session status.
 *
 * This URL is used to verify if the user is still authenticated and their session is active.
 */
export const CHECK_SESSION_URL = `${API_BASE_URL}/check_session`;

/**
 * @brief API endpoint for clearing a session.
 *
 * This URL is used to remove session data and clear any stored information.
 */
export const CLEAR_SESSION_URL = `${API_BASE_URL}/clear_session`;