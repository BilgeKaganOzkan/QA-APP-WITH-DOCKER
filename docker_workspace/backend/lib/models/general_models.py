from pydantic import BaseModel

class InformationResponse(BaseModel):
    """
    @brief Represents a response containing information messages.

    This model is used to validate and structure output data
    that conveys information to the user, such as status messages,
    confirmations.

    Attributes:
    - informationMessage (str): A string containing the information message to be conveyed.
    """
    informationMessage: str