from pydantic import BaseModel

class InformationResponse(BaseModel):
    informationMessage: str