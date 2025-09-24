import numpy as np
from uuid import uuid4
from typing import List, Dict, Any
from .models import Payload, Context, get_sbert_model
from .helpers import (
    _txt, _jaccard, _haversine_km, _distance_score, 
    _age_score, _soft_match, _reason_text, _mmr
)


def rank_recommendations(payload: Payload) -> Dict[str, Any]:
    """Rank candidate profiles based on compatibility with user."""
    u, ctx = payload.user, (payload.context or Context())
    
    # Get the embedding model
    sbert_model = get_sbert_model()
    
    # Generate embeddings
    user_text = _txt(u)
    cand_texts = [_txt(c) for c in payload.candidates]
    u_vec = sbert_model.encode([user_text])[0]
    C = sbert_model.encode(cand_texts)

    # Calculate cosine similarity
    cos = (C @ u_vec) / (np.linalg.norm(C, axis=1) * np.linalg.norm(u_vec) + 1e-9)

    # Calculate scores for each candidate
    rows = []
    for i, c in enumerate(payload.candidates):
        interSim = _jaccard(u.interests or [], c.interests or [])
        rel = _soft_match(u.relationshipPreference, c.relationshipPreference)
        inten = _soft_match(u.datingIntention, c.datingIntention)
        km = _haversine_km(u.coordinates, c.coordinates)
        distS = _distance_score(km, ctx.kmScale)
        ageS = _age_score(u.age, c.age, ctx.ageSpread)

        # Calculate composite compatibility score
        # Weights adjusted for new constants with more nuanced compatibility scoring
        score = (
            0.35 * float(cos[i])      # Semantic similarity (bio, interests, prompts)
            + 0.25 * interSim         # Interest overlap (Jaccard similarity)
            + 0.15 * inten            # Dating intention compatibility (life-partner vs short-term)
            + 0.10 * rel              # Relationship preference compatibility (monogamous vs non-monogamous)
            + 0.10 * distS            # Distance-based score (exponential decay)
            + 0.05 * ageS             # Age compatibility (inverse square relationship)
        )

        rows.append({
            "id": c.id,
            "score": float(score),
            "reason": _reason_text(u, c, interSim, km, rel, inten, ageS),
        })

    # Apply MMR for diversity
    base_scores = np.array([r["score"] for r in rows], dtype=float)
    lam = float(1.0 - max(0.0, min(0.4, ctx.diversityWeight)))  # λ ≈ 0.6..1.0
    topk = min(ctx.maxResults, len(rows))
    order = _mmr(base_scores, C, lam, topk=topk)

    ranked = [rows[i] for i in order]
    return {
        "recId": f"rec_{uuid4().hex[:12]}",
        "totalCandidates": len(payload.candidates),
        "requestedResults": ctx.maxResults,
        "returnedResults": len(ranked),
        "debug": {
            "topk": topk,
            "diversityWeight": ctx.diversityWeight,
            "lambda": lam,
            "totalRows": len(rows)
        },
        "ranked": [
            {
                "rank": i + 1,
                "id": r["id"], 
                "score": round(r["score"], 3), 
                "reason": r["reason"]
            }
            for i, r in enumerate(ranked)
        ],
    }
