from passlib.context import CryptContext

# Create a CryptContext instance for password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def getPasswordHash(password: str) -> str:
    """
    @brief Hashes a plaintext password.

    This function takes a plaintext password and returns its hashed version
    using the bcrypt algorithm for secure storage.

    @param password The plaintext password to be hashed.
    @return The hashed password as a string.
    """
    return pwd_context.hash(password)  # Hash the password using the defined context

def verifyPassword(plain_password: str, hashed_password: str) -> bool:
    """
    @brief Verifies a plaintext password against a hashed password.

    This function checks if the provided plaintext password matches the
    stored hashed password, returning True if they match and False otherwise.

    @param plain_password The plaintext password to verify.
    @param hashed_password The previously hashed password to compare against.
    @return True if the passwords match, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)  # Verify the plaintext password against the hashed password