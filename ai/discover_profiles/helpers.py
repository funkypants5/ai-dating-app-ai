import numpy as np
from typing import List, Optional
from .models import Person, Point, REL_PREF, INTENT


def _txt(p: Person) -> str:
    """Convert person data to text representation for embedding."""
    parts = [
        p.bio or "",
        " ".join(p.interests or []),
        " ".join([(q.answer or "") for q in (p.prompts or [])]),
        f"relationship:{REL_PREF.get(p.relationshipPreference, '')}",
        f"intention:{INTENT.get(p.datingIntention, '')}",
    ]
    return " | ".join([x for x in parts if x])


def _jaccard(a: List[str], b: List[str]) -> float:
    """Calculate Jaccard similarity between two lists of strings."""
    A, B = set([x.strip().lower() for x in a]), set([x.strip().lower() for x in b])
    if not A and not B:
        return 0.0
    inter = len(A & B)
    uni = len(A | B)
    return inter / uni if uni else 0.0


def _haversine_km(a: Optional[Point], b: Optional[Point]) -> Optional[float]:
    """Calculate distance between two points using Haversine formula."""
    if not a or not b:
        return None
    lng1, lat1 = a.coordinates
    lng2, lat2 = b.coordinates
    if (lng1 == 0 and lat1 == 0) or (lng2 == 0 and lat2 == 0):
        return None
    R = 6371.0
    to_rad = np.pi / 180.0
    dlat = (lat2 - lat1) * to_rad
    dlng = (lng2 - lng1) * to_rad
    x = np.sin(dlat / 2) ** 2 + np.cos(lat1 * to_rad) * np.cos(lat2 * to_rad) * np.sin(dlng / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(x)))


def _distance_score(km: Optional[float], kmScale: float) -> float:
    """Calculate distance-based score."""
    if km is None:
        return 0.0
    return float(np.exp(-max(0.0, km) / kmScale))


def _age_score(a: Optional[int], b: Optional[int], spread: float) -> float:
    """Calculate age compatibility score."""
    if not a or not b:
        return 0.0
    gap = abs(a - b)
    x = gap / spread
    return float(1.0 / (1.0 + x * x))


def _soft_match(x: Optional[int], y: Optional[int]) -> float:
    """Calculate soft matching score for categorical values."""
    if x is None or y is None:
        return 0.0
    
    # Exact match gets full score
    if x == y:
        return 1.0
    
    # Handle no-preferences (0) - should be compatible with anything
    if x == 0 or y == 0:
        return 0.8
    
    # For relationship preferences, calculate compatibility
    if x in REL_PREF and y in REL_PREF:
        # Monogamous (1) and non-monogamous (2) are incompatible
        if (x == 1 and y == 2) or (x == 2 and y == 1):
            return 0.1
        # Figuring-it-out (3) is compatible with most things
        if x == 3 or y == 3:
            return 0.7
        # Other combinations get moderate score
        return 0.5
    
    # For dating intentions, calculate compatibility
    if x in INTENT and y in INTENT:
        # Life-partner (1) and short-term (5) are less compatible
        if (x == 1 and y == 5) or (x == 5 and y == 1):
            return 0.2
        # Long-term (2) and short-term (5) have some compatibility
        if (x == 2 and y == 5) or (x == 5 and y == 2):
            return 0.4
        # Open combinations (3, 4) are more flexible
        if x in [3, 4] or y in [3, 4]:
            return 0.6
        # Other combinations get moderate score
        return 0.5
    
    # Default fallback
    return 0.3


def _reason_text(u: Person, c: Person, interSim: float, km: Optional[float], rel: float, inten: float, ageS: float) -> str:
    """Generate human-readable reason for recommendation."""
    reasons = []
    
    # Interest similarity
    if interSim >= 0.34:
        common = list(set([s.lower() for s in u.interests or []]) & set([s.lower() for s in c.interests or []]))
        if common:
            reasons.append("Shared interests: " + ", ".join([w.capitalize() for w in common][:3]))
        else:
            reasons.append("Similar interests")
    
    # Location proximity
    if km is not None and km <= 8:
        reasons.append(f"near you{f' in {c.location}' if c.location else ''}")
    
    # Dating intention compatibility
    if inten >= 0.7 and c.datingIntention in INTENT:
        if inten >= 0.99:
            reasons.append(f"same dating intention ({INTENT[c.datingIntention]})")
        elif inten >= 0.8:
            reasons.append(f"compatible dating goals ({INTENT[c.datingIntention]})")
        else:
            reasons.append(f"flexible dating approach")
    
    # Relationship preference compatibility
    if rel >= 0.7 and c.relationshipPreference in REL_PREF:
        if rel >= 0.99:
            reasons.append(f"both prefer {REL_PREF[c.relationshipPreference]}")
        elif rel >= 0.8:
            reasons.append(f"compatible relationship style")
        else:
            reasons.append(f"open to different relationship styles")
    
    # Age compatibility
    if ageS >= 0.8:
        reasons.append("close in age")
    elif ageS >= 0.6:
        reasons.append("similar age range")
    
    return " • ".join(reasons[:2])


def _mmr(scores: np.ndarray, reps: np.ndarray, lam: float, topk: int) -> List[int]:
    """Maximal Marginal Relevance algorithm for diverse recommendations."""
    chosen, cand = [], list(range(len(scores)))
    lam = float(np.clip(lam, 0.0, 1.0))

    def sim(i, j):
        a, b = reps[i], reps[j]
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    while cand and len(chosen) < topk:
        best, best_val = None, -1e9
        for i in cand:
            redundancy = 0.0 if not chosen else max(sim(i, j) for j in chosen)
            val = lam * scores[i] - (1.0 - lam) * redundancy
            if val > best_val:
                best, best_val = i, val
        chosen.append(best)
        cand.remove(best)
    
    # Return only the chosen items, not chosen + remaining candidates
    return chosen
