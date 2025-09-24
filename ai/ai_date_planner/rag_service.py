from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .data_processor import Location
from .embedding_service import EmbeddingService
from .rule_engine import UserPreferences, FilterResult
import numpy as np

@dataclass
class RAGResult:
    """Result of RAG-based location retrieval"""
    relevant_locations: List[Location]
    relevance_scores: Dict[str, float]  # Location ID -> relevance score
    query_embedding: np.ndarray
    search_stats: Dict[str, Any]

class RAGService:
    """
    Retrieval-Augmented Generation service for finding relevant locations.
    
    This service takes filtered locations and user preferences to find the most
    relevant locations using semantic similarity search.
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        """Initialize RAG service with embedding service"""
        self.embedding_service = embedding_service
        self.max_results = 50  # Maximum locations to return
    
    def find_relevant_locations(self, filter_result: FilterResult, preferences: UserPreferences, user_query: str = None) -> RAGResult:
        """
        Find the most relevant locations using semantic similarity search.
        
        Args:
            filter_result: Result from rule-based filtering
            preferences: User preferences
            user_query: Optional specific user query (e.g., "romantic dinner with city view")
            
        Returns:
            RAGResult with relevant locations and scores
        """
        print(f"Starting RAG-based location retrieval with {len(filter_result.filtered_locations)} filtered locations...")
        
        # Generate query embedding
        query_text = self._build_query_text(preferences, user_query)
        query_embedding = self.embedding_service.generate_embedding(query_text)
        
        print(f"Generated query embedding for: '{query_text[:100]}...'")
        
        # Calculate relevance scores for all filtered locations
        relevance_scores = self._calculate_relevance_scores(
            filter_result.filtered_locations, 
            query_embedding,
            filter_result.location_scores
        )
        
        # Sort by combined relevance and proximity scores
        sorted_locations = self._rank_locations(
            filter_result.filtered_locations,
            relevance_scores,
            filter_result.location_scores
        )
        
        # Take top results
        top_locations = sorted_locations[:self.max_results]
        
        print(f"RAG retrieval complete: {len(top_locations)} most relevant locations selected")
        
        return RAGResult(
            relevant_locations=top_locations,
            relevance_scores=relevance_scores,
            query_embedding=query_embedding,
            search_stats={
                'total_filtered': len(filter_result.filtered_locations),
                'top_results': len(top_locations),
                'query_text': query_text
            }
        )
    
    def _build_query_text(self, preferences: UserPreferences, user_query: str = None) -> str:
        """Build a comprehensive query text from preferences and user input"""
        query_parts = []
        
        # Add user's specific query if provided
        if user_query:
            query_parts.append(user_query)
        
        # Add time-based context
        time_context = self._get_time_context(preferences)
        if time_context:
            query_parts.append(time_context)
        
        # Add interest-based context
        interest_context = self._get_interest_context(preferences.interests)
        if interest_context:
            query_parts.append(interest_context)
        
        # Add date type context
        date_type_context = self._get_date_type_context(preferences.date_type)
        if date_type_context:
            query_parts.append(date_type_context)
        
        # Add budget context
        budget_context = self._get_budget_context(preferences.budget_tier)
        if budget_context:
            query_parts.append(budget_context)
        
        # Add location type context
        location_type_context = self._get_location_type_context(preferences.preferred_location_types)
        if location_type_context:
            query_parts.append(location_type_context)
        
        return " ".join(query_parts)
    
    def _get_time_context(self, preferences: UserPreferences) -> str:
        """Generate time-based context for the query"""
        duration = preferences.get_duration_hours()
        
        if preferences.time_of_day == "morning":
            return f"morning activities for {duration:.1f} hours, breakfast and brunch options"
        elif preferences.time_of_day == "afternoon":
            return f"afternoon activities for {duration:.1f} hours, lunch and daytime attractions"
        elif preferences.time_of_day == "evening":
            return f"evening activities for {duration:.1f} hours, dinner and sunset views"
        else:  # night
            return f"night activities for {duration:.1f} hours, late night dining and entertainment"
    
    def _get_interest_context(self, interests: List[str]) -> str:
        """Generate interest-based context for the query"""
        if not interests:
            return ""
        
        interest_descriptions = {
            "food": "restaurants, cafes, food markets, local cuisine",
            "culture": "museums, galleries, cultural sites, heritage locations",
            "nature": "parks, gardens, outdoor spaces, scenic views",
            "sports": "sports facilities, fitness centers, active activities",
            "art": "art galleries, exhibitions, creative spaces, artistic venues",
            "shopping": "shopping malls, markets, boutiques, retail areas"
        }
        
        descriptions = [interest_descriptions.get(interest, interest) for interest in interests]
        return f"interested in {', '.join(descriptions)}"
    
    def _get_date_type_context(self, date_type: str) -> str:
        """Generate date type context for the query"""
        date_type_descriptions = {
            "casual": "casual and relaxed atmosphere, comfortable settings",
            "romantic": "romantic and intimate atmosphere, cozy and private spaces",
            "adventurous": "adventure and outdoor activities, exciting experiences",
            "cultural": "cultural and educational experiences, historical significance"
        }
        
        return date_type_descriptions.get(date_type, f"{date_type} atmosphere")
    
    def _get_budget_context(self, budget_tier: str) -> str:
        """Generate budget context for the query"""
        budget_descriptions = {
            "$": "budget-friendly, affordable, cheap options",
            "$$": "moderate pricing, mid-range, casual dining",
            "$$$": "upscale, fine dining, premium experiences",
            "$$$$": "high-end, luxury, exclusive venues"
        }
        
        return budget_descriptions.get(budget_tier, f"{budget_tier} budget range")
    
    def _get_location_type_context(self, location_types: List[str]) -> str:
        """Generate location type context for the query"""
        if not location_types:
            return ""
        
        type_descriptions = {
            "food": "restaurants and dining",
            "attraction": "tourist attractions and landmarks",
            "activity": "activities and experiences",
            "heritage": "heritage sites and cultural locations"
        }
        
        descriptions = [type_descriptions.get(loc_type, loc_type) for loc_type in location_types]
        return f"looking for {', '.join(descriptions)}"
    
    def _calculate_relevance_scores(self, locations: List[Location], query_embedding: np.ndarray, proximity_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate semantic relevance scores for locations"""
        relevance_scores = {}
        
        # Ensure embeddings are loaded (loads once for all locations)
        try:
            self.embedding_service.load_embeddings()
        except FileNotFoundError:
            print("⚠️ No embeddings found, falling back to proximity scores only")
            return {loc.id: proximity_scores.get(loc.id, 0.0) for loc in locations}
        
        for location in locations:
            # Get location embedding (now uses pre-loaded embeddings)
            location_embedding = self.embedding_service.get_location_embedding(location.id)
            
            if location_embedding is not None:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, location_embedding)
                relevance_scores[location.id] = float(similarity)
            else:
                # Fallback to proximity score if no embedding
                relevance_scores[location.id] = proximity_scores.get(location.id, 0.0)
        
        return relevance_scores
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _rank_locations(self, locations: List[Location], relevance_scores: Dict[str, float], proximity_scores: Dict[str, float]) -> List[Location]:
        """Rank locations by combined relevance and proximity scores"""
        # Combine relevance (70%) and proximity (30%) scores
        combined_scores = {}
        
        for location in locations:
            relevance = relevance_scores.get(location.id, 0.0)
            proximity = proximity_scores.get(location.id, 0.0)
            
            # Weighted combination
            combined_score = 0.7 * relevance + 0.3 * proximity
            combined_scores[location.id] = combined_score
        
        # Sort by combined score (descending)
        sorted_locations = sorted(locations, key=lambda loc: combined_scores[loc.id], reverse=True)
        
        return sorted_locations
    
    def get_rag_summary(self, result: RAGResult) -> str:
        """Get a human-readable summary of RAG results"""
        summary = f"RAG Retrieval Results:\n"
        summary += f"  Total filtered locations: {result.search_stats['total_filtered']}\n"
        summary += f"  Top relevant locations: {result.search_stats['top_results']}\n"
        summary += f"  Query: {result.search_stats['query_text'][:100]}...\n\n"
        
        summary += "Top 5 most relevant locations:\n"
        for i, location in enumerate(result.relevant_locations[:5], 1):
            relevance_score = result.relevance_scores.get(location.id, 0.0)
            summary += f"  {i}. {location.name} (relevance: {relevance_score:.3f})\n"
        
        return summary
    
    def explain_relevance(self, location: Location, query_embedding: np.ndarray) -> str:
        """Explain why a location is relevant to the query"""
        location_embedding = self.embedding_service.get_location_embedding(location.id)
        
        if location_embedding is None:
            return f"No embedding available for {location.name}"
        
        similarity = self._cosine_similarity(query_embedding, location_embedding)
        
        explanation = f"Location: {location.name}\n"
        explanation += f"Type: {location.location_type}\n"
        explanation += f"Description: {location.description[:100]}...\n"
        explanation += f"Relevance Score: {similarity:.3f}\n"
        
        if similarity > 0.8:
            explanation += "Status: Highly relevant to your query"
        elif similarity > 0.6:
            explanation += "Status: Moderately relevant to your query"
        elif similarity > 0.4:
            explanation += "Status: Somewhat relevant to your query"
        else:
            explanation += "Status: Low relevance to your query"
        
        return explanation
