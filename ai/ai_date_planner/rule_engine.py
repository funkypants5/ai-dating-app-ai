from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .data_processor import Location
import math

@dataclass
class UserPreferences:
    """User preferences for date planning"""
    budget_tier: str = "$$"  # $, $$, $$$, $$$$
    start_latitude: Optional[float] = None  # Where the date starts
    start_longitude: Optional[float] = None  # Where the date starts
    preferred_location_types: List[str] = None  # ['food', 'attraction', 'activity', 'heritage']
    start_time: str = "10:00"  # Start time in HH:MM format (24-hour)
    end_time: Optional[str] = None  # End time in HH:MM format (24-hour), optional
    time_of_day: str = "afternoon"  # morning, afternoon, evening, night
    date_type: str = "casual"  # casual, romantic, adventurous, cultural
    interests: List[str] = None  # ['food', 'culture', 'nature', 'sports', 'art', 'shopping']
    
    def __post_init__(self):
        if self.preferred_location_types is None:
            self.preferred_location_types = ['food', 'attraction', 'activity', 'heritage']
        if self.interests is None:
            self.interests = ['food', 'culture', 'nature']
        
        # Auto-detect time_of_day based on start_time if not explicitly set
        if self.time_of_day == "afternoon":  # Default value
            self.time_of_day = self._detect_time_of_day(self.start_time)
    
    def _detect_time_of_day(self, start_time: str) -> str:
        """Detect time of day based on start time"""
        try:
            hour = int(start_time.split(':')[0])
            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 17:
                return "afternoon"
            elif 17 <= hour < 21:
                return "evening"
            else:
                return "night"
        except:
            return "afternoon"  # Default fallback
    
    def get_duration_hours(self) -> float:
        """Calculate duration in hours from start and end time"""
        if not self.end_time:
            return 4.0  # Default 4 hours if no end time specified
        
        try:
            start_hour, start_min = map(int, self.start_time.split(':'))
            end_hour, end_min = map(int, self.end_time.split(':'))
            
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            # Handle overnight dates (end time next day)
            if end_minutes < start_minutes:
                end_minutes += 24 * 60  # Add 24 hours
            
            duration_minutes = end_minutes - start_minutes
            return duration_minutes / 60.0
        except:
            return 4.0  # Default fallback

@dataclass
class FilterResult:
    """Result of filtering locations"""
    filtered_locations: List[Location]
    location_scores: Dict[str, float]  # Location ID -> proximity score
    filter_stats: Dict[str, Any]
    excluded_count: int

class RuleEngine:
    """
    Rule-based filtering engine for date planning.
    
    ACTIVITY PLANNING RULES (Duration-Based):
    - 3+ hours: Basic activities + 1 extra activity
    - 4+ hours: Basic activities + coffee break
    - 6+ hours: Basic activities + additional cultural/nature spot
    
    These rules are implemented in the suggest_date_plan() method.
    """
    
    def __init__(self):
        """Initialize the rule engine with filtering rules"""
        self.budget_mapping = {
            "$": {"max_price": 20, "keywords": ["cheap", "budget", "affordable", "hawker", "food court"]},
            "$$": {"max_price": 50, "keywords": ["moderate", "mid-range", "casual", "family"]},
            "$$$": {"max_price": 100, "keywords": ["upscale", "fine dining", "premium", "luxury"]},
            "$$$$": {"max_price": 200, "keywords": ["high-end", "exclusive", "gourmet", "michelin"]}
        }
        
        self.time_preferences = {
            "morning": ["breakfast", "coffee", "brunch", "early", "morning"],
            "afternoon": ["lunch", "afternoon", "daytime", "casual"],
            "evening": ["dinner", "evening", "romantic", "sunset", "night"],
            "night": ["late night", "nightlife", "bar", "club", "night"]
        }
        
        self.date_type_preferences = {
            "casual": ["casual", "relaxed", "friendly", "comfortable"],
            "romantic": ["romantic", "intimate", "candlelight", "cozy", "private"],
            "adventurous": ["adventure", "outdoor", "active", "exciting", "thrilling"],
            "cultural": ["cultural", "heritage", "museum", "art", "historical", "traditional"]
        }
        
        self.interest_mapping = {
            "food": ["restaurant", "cafe", "dining", "cuisine", "food", "eat", "drink"],
            "culture": ["museum", "gallery", "art", "cultural", "heritage", "historical", "traditional"],
            "nature": ["park", "garden", "nature", "outdoor", "scenic", "botanical", "zoo"],
            "sports": ["sports", "gym", "fitness", "swimming", "tennis", "football", "basketball"],
            "art": ["art", "gallery", "museum", "creative", "exhibition", "sculpture", "painting"],
            "shopping": ["shopping", "mall", "market", "retail", "boutique", "store"]
        }
    
    def filter_locations(self, locations: List[Location], preferences: UserPreferences, exclusions: List[str] = None) -> FilterResult:
        """
        Apply all filtering rules to locations and score by proximity to start location
        
        Args:
            locations: List of all locations
            preferences: User preferences for filtering
            exclusions: Optional list of what user does NOT want
            
        Returns:
            FilterResult with filtered locations, proximity scores, and statistics
        """
        print(f"Starting rule-based filtering with {len(locations)} locations...")
        
        filtered_locations = locations.copy()
        filter_stats = {}
        excluded_count = 0
        
        # Apply each filter
        filtered_locations, excluded = self._filter_by_location_type(filtered_locations, preferences.preferred_location_types)
        excluded_count += excluded
        filter_stats['location_type'] = {'excluded': excluded, 'remaining': len(filtered_locations)}
        
        filtered_locations, excluded = self._filter_by_interests(filtered_locations, preferences.interests, exclusions or [])
        excluded_count += excluded
        filter_stats['interests'] = {'excluded': excluded, 'remaining': len(filtered_locations)}
        
        filtered_locations, excluded = self._filter_by_budget(filtered_locations, preferences.budget_tier)
        excluded_count += excluded
        filter_stats['budget'] = {'excluded': excluded, 'remaining': len(filtered_locations)}
        
        # Make time and date type filters more lenient - they should be suggestions, not strict filters
        filtered_locations, excluded = self._filter_by_time_preference(filtered_locations, preferences.time_of_day)
        excluded_count += excluded
        filter_stats['time'] = {'excluded': excluded, 'remaining': len(filtered_locations)}
        
        filtered_locations, excluded = self._filter_by_date_type(filtered_locations, preferences.date_type)
        excluded_count += excluded
        filter_stats['date_type'] = {'excluded': excluded, 'remaining': len(filtered_locations)}
        
        # Calculate proximity scores (no filtering, just scoring)
        location_scores = self._calculate_proximity_scores(filtered_locations, preferences)
        
        print(f"Filtering complete: {len(filtered_locations)} locations remaining ({excluded_count} excluded)")
        
        return FilterResult(
            filtered_locations=filtered_locations,
            location_scores=location_scores,
            filter_stats=filter_stats,
            excluded_count=excluded_count
        )
    
    def _filter_by_location_type(self, locations: List[Location], allowed_types: List[str]) -> Tuple[List[Location], int]:
        """Filter locations by type (food, attraction, activity, heritage)"""
        if not allowed_types:
            return locations, 0
        
        original_count = len(locations)
        filtered = [loc for loc in locations if loc.location_type in allowed_types]
        excluded = original_count - len(filtered)
        
        print(f"  Location type filter: {excluded} excluded, {len(filtered)} remaining")
        return filtered, excluded
    
    def _filter_by_interests(self, locations: List[Location], interests: List[str], exclusions: List[str] = None) -> Tuple[List[Location], int]:
        """Filter locations by user interests with exclusion awareness"""
        if not interests:
            print("  Interest filter: No interests specified, keeping all")
            return locations, 0
        
        exclusions = exclusions or []
        original_count = len(locations)
        filtered = []
        
        for location in locations:
            if self._matches_interests(location, interests, exclusions):
                filtered.append(location)
        
        excluded = original_count - len(filtered)
        print(f"  Interest filter: {excluded} excluded, {len(filtered)} remaining")
        return filtered, excluded
    
    def _calculate_proximity_scores(self, locations: List[Location], preferences: UserPreferences) -> Dict[str, float]:
        """Calculate proximity scores for locations (higher = closer to start location)"""
        if not preferences.start_latitude or not preferences.start_longitude:
            print("  Proximity scoring: No start location provided, using equal scores")
            return {location.id: 1.0 for location in locations}
        
        scores = {}
        max_distance = 0
        
        # First pass: calculate distances and find max
        for location in locations:
            distance = self._calculate_distance(
                preferences.start_latitude, preferences.start_longitude,
                location.coordinates[1], location.coordinates[0]  # lat, lon
            )
            scores[location.id] = distance
            max_distance = max(max_distance, distance)
        
        # Second pass: convert to proximity scores (closer = higher score)
        for location_id in scores:
            # Invert distance so closer locations get higher scores
            # Normalize to 0-1 range
            scores[location_id] = 1.0 - (scores[location_id] / max_distance) if max_distance > 0 else 1.0
        
        print(f"  Proximity scoring: Calculated scores for {len(locations)} locations")
        return scores
    
    def _filter_by_budget(self, locations: List[Location], budget_tier: str) -> Tuple[List[Location], int]:
        """Filter locations by budget tier"""
        if budget_tier not in self.budget_mapping:
            print(f"  Budget filter: Invalid budget tier '{budget_tier}', skipping")
            return locations, 0
        
        budget_info = self.budget_mapping[budget_tier]
        original_count = len(locations)
        filtered = []
        
        for location in locations:
            # For now, we'll use keyword matching since we don't have actual price data
            # In a real system, you'd have price information from external APIs
            if self._matches_budget_keywords(location, budget_info['keywords']):
                filtered.append(location)
        
        excluded = original_count - len(filtered)
        print(f"  Budget filter: {excluded} excluded, {len(filtered)} remaining (tier: {budget_tier})")
        return filtered, excluded
    
    def _filter_by_time_preference(self, locations: List[Location], time_of_day: str) -> Tuple[List[Location], int]:
        """Filter locations by time of day preference (very lenient - keeps almost all locations)"""
        if time_of_day not in self.time_preferences:
            print(f"  Time filter: Invalid time '{time_of_day}', skipping")
            return locations, 0
        
        # Make time filtering very lenient - only exclude locations that explicitly conflict
        time_keywords = self.time_preferences[time_of_day]
        original_count = len(locations)
        filtered = []
        
        for location in locations:
            # Keep location if it matches time keywords OR if it's a general location type
            # OR if it doesn't explicitly conflict with the time preference
            if (self._matches_time_keywords(location, time_keywords) or 
                self._is_general_location_type(location) or
                not self._conflicts_with_time(location, time_of_day)):
                filtered.append(location)
        
        excluded = original_count - len(filtered)
        print(f"  Time filter: {excluded} excluded, {len(filtered)} remaining (time: {time_of_day})")
        return filtered, excluded
    
    def _filter_by_date_type(self, locations: List[Location], date_type: str) -> Tuple[List[Location], int]:
        """Filter locations by date type preference (very lenient - keeps almost all locations)"""
        if date_type not in self.date_type_preferences:
            print(f"  Date type filter: Invalid type '{date_type}', skipping")
            return locations, 0
        
        # Make date type filtering very lenient - only exclude locations that explicitly conflict
        type_keywords = self.date_type_preferences[date_type]
        original_count = len(locations)
        filtered = []
        
        for location in locations:
            # Keep location if it matches date type keywords OR if it's a general location type
            # OR if it doesn't explicitly conflict with the date type preference
            if (self._matches_date_type_keywords(location, type_keywords) or 
                self._is_general_location_type(location) or
                not self._conflicts_with_date_type(location, date_type)):
                filtered.append(location)
        
        excluded = original_count - len(filtered)
        print(f"  Date type filter: {excluded} excluded, {len(filtered)} remaining (type: {date_type})")
        return filtered, excluded
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    def _matches_budget_keywords(self, location: Location, budget_keywords: List[str]) -> bool:
        """Check if location matches budget keywords"""
        text_to_search = f"{location.name} {location.description} {location.address or ''}".lower()
        
        # For food places, be more strict about budget matching
        if location.location_type == "food":
            return any(keyword in text_to_search for keyword in budget_keywords)
        
        # For other types, be more lenient (they don't have clear budget indicators)
        return True
    
    def _matches_time_keywords(self, location: Location, time_keywords: List[str]) -> bool:
        """Check if location matches time of day keywords"""
        text_to_search = f"{location.name} {location.description}".lower()
        
        # Check if any time keywords match
        return any(keyword in text_to_search for keyword in time_keywords)
    
    def _is_general_location_type(self, location: Location) -> bool:
        """Check if location is a general type that works for any time/date type"""
        general_types = ['food', 'attraction', 'activity', 'heritage']
        return location.location_type in general_types
    
    def _conflicts_with_time(self, location: Location, time_of_day: str) -> bool:
        """Check if location explicitly conflicts with time preference"""
        text_to_search = f"{location.name} {location.description}".lower()
        
        # Only exclude if location explicitly mentions conflicting times
        conflicts = {
            "morning": ["late night", "nightclub", "bar", "evening only"],
            "afternoon": ["breakfast only", "morning only"],
            "evening": ["breakfast", "morning", "lunch only"],
            "night": ["breakfast", "morning", "lunch", "daytime"]
        }
        
        conflicting_keywords = conflicts.get(time_of_day, [])
        return any(keyword in text_to_search for keyword in conflicting_keywords)
    
    def _conflicts_with_date_type(self, location: Location, date_type: str) -> bool:
        """Check if location explicitly conflicts with date type preference"""
        text_to_search = f"{location.name} {location.description}".lower()
        
        # Only exclude if location explicitly mentions conflicting date types
        conflicts = {
            "casual": ["formal", "dress code", "black tie", "elegant"],
            "romantic": ["family", "kids", "children", "group"],
            "adventurous": ["quiet", "peaceful", "relaxing", "calm"],
            "cultural": ["party", "nightclub", "bar", "entertainment"]
        }
        
        conflicting_keywords = conflicts.get(date_type, [])
        return any(keyword in text_to_search for keyword in conflicting_keywords)
    
    def _matches_date_type_keywords(self, location: Location, type_keywords: List[str]) -> bool:
        """Check if location matches date type keywords"""
        text_to_search = f"{location.name} {location.description}".lower()
        
        # Check if any date type keywords match
        return any(keyword in text_to_search for keyword in type_keywords)
    
    def _matches_interests(self, location: Location, interests: List[str], exclusions: List[str] = None) -> bool:
        """Check if location matches user interests and doesn't match exclusions"""
        if not interests:
            return True
        
        exclusions = exclusions or []
        text_to_search = f"{location.name} {location.description}".lower()
        
        # For attractions, check if they match excluded categories
        if location.location_type == 'attraction':
            # Check if it's a cultural attraction and cultural is excluded
            if 'cultural' in exclusions:
                cultural_keywords = self.interest_mapping.get('culture', [])
                if any(keyword in text_to_search for keyword in cultural_keywords):
                    return False  # Exclude cultural attractions
            
            # Check if it's a nature attraction and nature is excluded
            if 'nature' in exclusions:
                nature_keywords = self.interest_mapping.get('nature', [])
                if any(keyword in text_to_search for keyword in nature_keywords):
                    return False  # Exclude nature attractions
            
            # If attraction doesn't match excluded categories, allow it
            # This lets shopping areas like Orchard Road through
        
        # Check if any interest keywords match
        for interest in interests:
            if interest in self.interest_mapping:
                interest_keywords = self.interest_mapping[interest]
                if any(keyword in text_to_search for keyword in interest_keywords):
                    return True
        
        # If no specific interests match, be more selective
        # Only allow if it's a food location (since meals are always needed)
        if location.location_type == 'food':
            return True
        
        # For attractions that don't match interests but also don't match exclusions, allow them
        # This handles general attractions like shopping streets
        if location.location_type == 'attraction':
            # Check if it matches any excluded category
            matches_exclusion = False
            if 'cultural' in exclusions:
                cultural_keywords = self.interest_mapping.get('culture', [])
                if any(keyword in text_to_search for keyword in cultural_keywords):
                    matches_exclusion = True
            if 'nature' in exclusions:
                nature_keywords = self.interest_mapping.get('nature', [])
                if any(keyword in text_to_search for keyword in nature_keywords):
                    matches_exclusion = True
            
            # If it doesn't match any exclusion, allow it (e.g., shopping areas)
            if not matches_exclusion:
                return True
            
        # For non-food locations, require interest match
        return False
    
    def get_filter_summary(self, result: FilterResult) -> str:
        """Get a human-readable summary of filtering results"""
        summary = f"Filtering Results:\n"
        summary += f"  Total locations: {len(result.filtered_locations) + result.excluded_count}\n"
        summary += f"  Remaining: {len(result.filtered_locations)}\n"
        summary += f"  Excluded: {result.excluded_count}\n\n"
        
        summary += "Filter breakdown:\n"
        for filter_name, stats in result.filter_stats.items():
            summary += f"  {filter_name}: {stats['excluded']} excluded, {stats['remaining']} remaining\n"
        
        # Show proximity scoring info
        if result.location_scores:
            avg_score = sum(result.location_scores.values()) / len(result.location_scores)
            summary += f"\nProximity scoring: Average score {avg_score:.3f} (higher = closer to start location)\n"
        
        return summary
    
    def get_activity_planning_rules(self) -> str:
        """
        Returns the activity planning rules based on duration.
        
        ACTIVITY PLANNING RULES:
        - 3+ hours: Basic activities + 1 extra activity
        - 4+ hours: Basic activities + coffee break
        - 6+ hours: Basic activities + additional cultural/nature spot
        
        These rules are implemented in suggest_date_plan() method.
        """
        return """
        ACTIVITY PLANNING RULES (Duration-Based):
        
        🌅 MORNING DATES:
        - Base: Coffee/brunch + park walk
        - 3+ hours: + Light shopping or cultural activity
        
        ☀️ AFTERNOON DATES:
        - Base: Lunch + museum/attraction
        - 4+ hours: + Coffee break or light activity
        - 6+ hours: + Additional cultural or nature spot
        
        🌆 EVENING DATES:
        - Base: Dinner + sunset walk
        - 3+ hours: + Drinks or entertainment
        
        🌙 NIGHT DATES:
        - Base: Late dinner + nightlife
        - 3+ hours: + Additional night activities
        """

    def suggest_date_plan(self, preferences: UserPreferences) -> str:
        """
        Suggest a date plan based on preferences.
        
        ACTIVITY PLANNING RULES IMPLEMENTED:
        - 3+ hours: Basic activities + 1 extra activity
        - 4+ hours: Basic activities + coffee break  
        - 6+ hours: Basic activities + additional cultural/nature spot
        """
        duration = preferences.get_duration_hours()
        end_time_display = preferences.end_time if preferences.end_time else "flexible"
        
        plan = f"Suggested date plan ({preferences.start_time} - {end_time_display}, {duration:.1f} hours):\n\n"
        
        # Time-based suggestions with actual times
        # RULE: 3+ hours = Basic activities + 1 extra
        if preferences.time_of_day == "morning":
            plan += f"🌅 Morning ({preferences.start_time}):\n"
            plan += "  • Coffee/brunch at a cozy cafe\n"
            plan += "  • Walk in a nearby park or garden\n"
            if duration > 3:  # RULE: 3+ hours = +1 extra activity
                plan += "  • Light shopping or cultural activity\n"
                
        elif preferences.time_of_day == "afternoon":
            plan += f"☀️ Afternoon ({preferences.start_time}):\n"
            plan += "  • Lunch at a restaurant\n"
            plan += "  • Visit a museum or attraction\n"
            if duration > 4:  # RULE: 4+ hours = + coffee break
                plan += "  • Coffee break or light activity\n"
            if duration > 6:  # RULE: 6+ hours = + additional cultural/nature spot
                plan += "  • Additional cultural or nature spot\n"
                
        elif preferences.time_of_day == "evening":
            plan += f"🌆 Evening ({preferences.start_time}):\n"
            plan += "  • Dinner at a nice restaurant\n"
            plan += "  • Sunset walk or romantic spot\n"
            if duration > 3:  # RULE: 3+ hours = +1 extra activity
                plan += "  • Drinks or entertainment\n"
                
        else:  # night
            plan += f"🌙 Night ({preferences.start_time}):\n"
            plan += "  • Late dinner or drinks\n"
            plan += "  • Nightlife or entertainment\n"
            if duration > 3:  # RULE: 3+ hours = +1 extra activity
                plan += "  • Additional night activities\n"
        
        # Interest-based suggestions
        plan += f"\nBased on your interests ({', '.join(preferences.interests)}):\n"
        for interest in preferences.interests:
            if interest == "food":
                plan += "  • Food: Try local cuisine, food markets, or specialty restaurants\n"
            elif interest == "culture":
                plan += "  • Culture: Visit museums, galleries, or cultural sites\n"
            elif interest == "nature":
                plan += "  • Nature: Explore parks, gardens, or scenic spots\n"
            elif interest == "sports":
                plan += "  • Sports: Active activities like hiking, sports centers, or fitness\n"
            elif interest == "art":
                plan += "  • Art: Art galleries, exhibitions, or creative spaces\n"
            elif interest == "shopping":
                plan += "  • Shopping: Markets, boutiques, or shopping districts\n"
        
        return plan
