from unittest.mock import patch
from lib.database.securities.security import getPasswordHash, verifyPassword

@patch("lib.database.securities.security.pwd_context.hash")
def test_db_security_get_password_success(mock_hash):
    """
    Test to verify that getPasswordHash successfully hashes a password.
    Ensures the hash function is called with the correct password and returns expected hash.
    """
    mock_hash.return_value = "hashedpassword"  # Mocked hash result

    # Call getPasswordHash and check result
    result = getPasswordHash("mysecretpassword")
    
    # Ensure hash was called once with the correct password
    mock_hash.assert_called_once_with("mysecretpassword")
    
    # Validate the result is the expected mocked hash
    assert result == "hashedpassword"

@patch("lib.database.securities.security.pwd_context.verify")
def test_db_security_verify_password_success(mock_verify):
    """
    Test to verify that verifyPassword correctly validates a plain password against a hash.
    Ensures the verify function is called with correct arguments and returns True for a match.
    """
    mock_verify.return_value = True  # Mock verification result as True

    # Call verifyPassword and check result
    result = verifyPassword("mysecretpassword", "hashedpassword")

    # Ensure verify was called with correct password and hash
    mock_verify.assert_called_once_with("mysecretpassword", "hashedpassword")

    # Confirm that the result indicates a successful match
    assert result == True