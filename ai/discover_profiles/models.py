from typing import List, Optional
from pydantic import BaseModel, Field
import numpy as np
from sentence_transformers import SentenceTransformer

# Lightweight CPU embedding model (downloads on first run)
_sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------- Models ----------
class Point(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(default_factory=lambda: [0.0, 0.0])  # [lng, lat]


class Prompt(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


class Person(BaseModel):
    id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    bio: Optional[str] = ""
    prompts: List[Prompt] = Field(default_factory=list)
    relationshipPreference: Optional[int] = None
    datingIntention: Optional[int] = None
    coordinates: Optional[Point] = None
    location: Optional[str] = None


class Context(BaseModel):
    diversityWeight: float = 0.15  # 0..0.4
    kmScale: float = 12.0  # distance decay (km)
    ageSpread: float = 6.0  # age gap softness
    maxResults: int = Field(default=50, ge=1, le=500)  # maximum number of results to return (1-500)


class Payload(BaseModel):
    user: Person
    candidates: List[Person]
    context: Optional[Context] = Context()


# Constants
REL_PREF = {0: "no-preferences", 1: "monogamous", 2: "non-monogamous", 3: "figuring-it-out"}
INTENT = {0: "no-preferences", 1: "life-partner", 2: "long-term", 3: "long-term, open to short", 4: "short-term, open to long", 5: "short-term"}


def get_sbert_model():
    """Get the SentenceTransformer model instance."""
    return _sbert_model
