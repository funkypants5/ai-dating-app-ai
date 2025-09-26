#!/usr/bin/env python3

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

@dataclass
class ActivityRequirement:
    """Represents a specific activity requirement parsed from user query"""
    activity_type: str  # 'sports', 'food', 'cultural', 'nature', 'entertainment'
    count: int  # Number of activities of this type requested
    priority: str  # 'high', 'medium', 'low'
    specific_activities: List[str]  # Specific activities mentioned (e.g., ['tennis', 'swimming'])

@dataclass
class ExclusionRequirement:
    """Represents an exclusion requirement parsed from user query"""
    activity_type: str  # 'sports', 'food', 'cultural', 'nature', 'entertainment'
    confidence: float  # 0.0 to 1.0 confidence in the exclusion
    reason: str  # Why this exclusion was detected

@dataclass
class ParsedQuery:
    """Result of LLM query parsing"""
    inclusions: List[ActivityRequirement]
    exclusions: List[ExclusionRequirement]
    total_activities_requested: int
    meal_preferences: Dict[str, Any]  # Specific meal requirements
    time_preferences: Dict[str, Any]  # Time-specific requirements
    confidence_score: float  # Overall confidence in parsing

class LLMQueryParser:
    """Service for parsing user queries using GPT-3.5 Turbo"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,  # Low temperature for consistent parsing
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Let the LLM be smart about categorizing activities
        # We just provide basic guidance
    
    def parse_query(self, user_query: str, preferences: Dict[str, Any]) -> ParsedQuery:
        """Parse user query using LLM to extract inclusions and exclusions"""
        
        # Load system message from markdown file
        system_message = self._load_system_message()
        
        # Create the user prompt
        user_prompt = self._create_parsing_prompt(user_query, preferences)
        
        try:
            # Call the LLM with system message
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content)
            
            # Convert to our dataclasses
            return self._convert_to_parsed_query(result)
            
        except Exception as e:
            print(f"Error parsing query with LLM: {e}")
            # Fallback to simple keyword-based parsing
            return self._fallback_parsing(user_query)
    
    def _load_system_message(self) -> str:
        """Load the system message from the markdown file"""
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        md_file_path = os.path.join(current_dir, 'date_planner_llm.md')
        
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to basic instructions if file not found
            return """You are an expert at parsing user queries for a date planning AI system. 
            Extract inclusions and exclusions from user queries and respond with valid JSON."""
    
    def _create_parsing_prompt(self, user_query: str, preferences: Dict[str, Any]) -> str:
        """Create a detailed prompt for the LLM"""
        
        return f"""
USER QUERY: "{user_query}"

USER PREFERENCES:
- Start Time: {preferences.get('start_time', 'Not specified')}
- End Time: {preferences.get('end_time', 'Not specified')}
- Interests: {preferences.get('interests', [])}
- Budget: {preferences.get('budget_tier', 'Not specified')}
- Date Type: {preferences.get('date_type', 'Not specified')}

Please parse this query according to the instructions above and respond with valid JSON only.
"""
    
    def _convert_to_parsed_query(self, llm_result: Dict[str, Any]) -> ParsedQuery:
        """Convert LLM result to ParsedQuery dataclass"""
        
        inclusions = []
        for inc in llm_result.get('inclusions', []):
            inclusions.append(ActivityRequirement(
                activity_type=inc['activity_type'],
                count=inc['count'],
                priority=inc['priority'],
                specific_activities=inc.get('specific_activities', [])
            ))
        
        exclusions = []
        for exc in llm_result.get('exclusions', []):
            exclusions.append(ExclusionRequirement(
                activity_type=exc['activity_type'],
                confidence=exc['confidence'],
                reason=exc['reason']
            ))
        
        return ParsedQuery(
            inclusions=inclusions,
            exclusions=exclusions,
            total_activities_requested=llm_result.get('total_activities_requested', 0),
            meal_preferences=llm_result.get('meal_preferences', {}),
            time_preferences=llm_result.get('time_preferences', {}),
            confidence_score=llm_result.get('confidence_score', 0.5)
        )
    
    def _fallback_parsing(self, user_query: str) -> ParsedQuery:
        """Simple fallback parsing when LLM fails"""
        
        query_lower = user_query.lower()
        inclusions = []
        exclusions = []
        
        # Very basic keyword detection
        if 'walk' in query_lower:
            inclusions.append(ActivityRequirement(
                activity_type='nature',
                count=1,
                priority='high',
                specific_activities=['walk']
            ))
        
        if 'sport' in query_lower:
            inclusions.append(ActivityRequirement(
                activity_type='sports',
                count=1,
                priority='high',
                specific_activities=[]
            ))
        
        return ParsedQuery(
            inclusions=inclusions,
            exclusions=exclusions,
            total_activities_requested=len(inclusions),
            meal_preferences={'include_meals': True},
            time_preferences={},
            confidence_score=0.6
        )
    
    def get_activity_requirements(self, parsed_query: ParsedQuery) -> Dict[str, int]:
        """Get a simple dict of activity type -> count requirements"""
        requirements = {}
        for inclusion in parsed_query.inclusions:
            requirements[inclusion.activity_type] = inclusion.count
        return requirements
    
    def get_exclusion_flags(self, parsed_query: ParsedQuery, threshold: float = 0.7) -> Dict[str, bool]:
        """Get exclusion flags for activity types above confidence threshold"""
        exclusions = {}
        for exclusion in parsed_query.exclusions:
            if exclusion.confidence >= threshold:
                exclusions[exclusion.activity_type] = True
        return exclusions
