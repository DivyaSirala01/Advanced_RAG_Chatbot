from fastapi import FastAPI

from app.core.pipeline import run_pipeline
from app.schemas import ChatRequest

app = FastAPI()

@app.post("/chat")
def chat(request: ChatRequest):
    answer = run_pipeline(request.query, request.role)
    return {"answer": answer}
