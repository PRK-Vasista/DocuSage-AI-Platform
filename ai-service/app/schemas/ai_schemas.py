# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Pydantic request/response schemas for the AI service.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Request body for document summarization."""

    text: str = Field(..., description="Full extracted document text to summarize.")
    max_chars: Optional[int] = Field(
        None,
        description="Optional maximum summary length in characters.",
    )


class SummarizeResponse(BaseModel):
    """Response body for document summarization."""

    summary: str = Field(..., description="Generated document summary.")
    model: str = Field(..., description="Model used for generation.")
    provider: str = Field(default="ollama", description="AI provider identifier.")


class ChatMessage(BaseModel):
    """A single chat turn."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message role.")
    content: str = Field(..., description="Message text content.")


class ChatRequest(BaseModel):
    """Request body for document-grounded chat."""

    question: str = Field(..., description="User question about the document.")
    document_context: str = Field(
        ...,
        description="Document summary/context used to ground the answer.",
    )
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation turns for this document.",
    )


class ChatResponse(BaseModel):
    """Response body for document-grounded chat."""

    answer: str = Field(..., description="Assistant reply grounded in the document.")
    model: str = Field(..., description="Model used for generation.")
    provider: str = Field(default="ollama", description="AI provider identifier.")


class HealthResponse(BaseModel):
    """Health check payload for the AI service unit."""

    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="Service status.")
    ollama_reachable: bool = Field(..., description="Whether Ollama responded.")
    model: str = Field(..., description="Configured model name.")
    model_ready: bool = Field(
        default=False,
        description="Whether the configured model is present in Ollama.",
    )
    message: str = Field(
        default="",
        description="Short human-readable readiness hint.",
    )
