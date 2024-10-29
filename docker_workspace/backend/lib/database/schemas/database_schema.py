from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """
    @brief Represents the data required to create a new user.

    This model is used for validating the input data when a new user
    is being registered in the system.

    Attributes:
    - email (EmailStr): The email address of the user (must be a valid email format).
    - password (str): The password chosen by the user.
    """
    email: EmailStr  # User's email, validated to ensure it's in the correct format
    password: str  # User's password

class UserLogin(BaseModel):
    """
    @brief Represents the data required for a user login.

    This model is used for validating the input data when a user
    attempts to log in to the system.

    Attributes:
    - email (EmailStr): The email address of the user (must be a valid email format).
    - password (str): The password provided by the user.
    """
    email: EmailStr  # User's email, validated to ensure it's in the correct format
    password: str  # User's password