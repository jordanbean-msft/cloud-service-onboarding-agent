from pydantic import BaseModel


class ChatGetFileNameInput(BaseModel):
    file_id: str


__all__ = ["ChatGetFileNameInput"]
