from pydantic import BaseModel

class ProgressResponse(BaseModel):
    progress: int