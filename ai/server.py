"""FastAPI server for the AI Co-Pilot."""
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import Orchestrator

app = FastAPI(title="AI Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


class ChunkRequest(BaseModel):
    chunk: str
    chunkIndex: Optional[int] = 0
    totalChunks: Optional[int] = 0


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock" if os.getenv("MOCK_MODE", "true").lower() == "true" else "live"}


@app.post("/process")
def process_chunk(request: ChunkRequest):
    """Process a text chunk through the RAG + Agents pipeline."""
    if not request.chunk or not request.chunk.strip():
        raise HTTPException(status_code=400, detail="chunk cannot be empty")
    
    result = orchestrator.process(
        chunk=request.chunk,
        chunk_index=request.chunkIndex,
        total_chunks=request.totalChunks,
    )
    return result


@app.post("/reset")
def reset():
    """Reset all agent and RAG state."""
    orchestrator.reset()
    return {"status": "reset"}


@app.get("/stats")
def stats():
    """Get current stats."""
    return {
        "chunks_processed": orchestrator.chunk_count,
        "chunks_in_rag": orchestrator.rag.chunk_count(),
        "current_summary": orchestrator.summarizer.current_summary,
        "questions_count": len(orchestrator.question_generator.all_questions),
        "insights_count": len(orchestrator.insight_generator.all_insights),
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"[AI Server] Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
