from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    role: str = Field(default="RAG", description="RAG or Agentic")
