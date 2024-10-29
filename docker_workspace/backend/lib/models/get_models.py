from pydantic import BaseModel

class ProgressResponse(BaseModel):
    """
    @brief Represents the progress of a process.

    This model is used to validate and structure the output data
    related to the progress of a certain task, typically in a session
    or operation that requires tracking progress.
    
    Attributes:
    - progress (int): An integer representing the current progress percentage (0-100).
    """
    progress: int