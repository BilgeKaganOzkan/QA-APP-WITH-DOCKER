from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Create a base class for declarative class definitions
Base = declarative_base()

class User(Base):
    """
    @brief Represents a user in the database.

    This class defines the User model, which maps to the 'User' table
    in the database and includes fields for user information.

    Attributes:
    - id (int): Unique identifier for each user (primary key).
    - email (str): The user's email address (must be unique and not null).
    - hashed_password (str): The user's hashed password (must not be null).
    """
    __tablename__ = 'User'  # Name of the table in the database
    
    # Define the columns in the User table
    id = Column(Integer, primary_key=True, index=True)  # Unique identifier for each user
    email = Column(String, unique=True, index=True, nullable=False)  # User's email, must be unique
    hashed_password = Column(String, nullable=False)  # User's hashed password