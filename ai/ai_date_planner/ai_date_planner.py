from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .data_processor import DataProcessor, Location
from .embedding_service import EmbeddingService
from .rule_engine import RuleEngine, UserPreferences, FilterResult
from .rag_service import RAGService, RAGResult
from .llm_query_parser import LLMQueryParser, ParsedQuery
import json
import os

@dataclass
class DatePlan:
    """Final date plan with specific locations and timing"""
    itinerary: List[Dict[str, Any]]  # List of activities with times and locations
    total_duration: float
    estimated_cost: str
    summary: str
    alternative_suggestions: List[str]

@dataclass
class DatePlanResult:
    """Complete result of date planning process"""
    date_plan: DatePlan
    filter_result: FilterResult
    rag_result: RAGResult
    processing_stats: Dict[str, Any]

class AIDatePlanner:
    """
    Main AI Date Planner that orchestrates the entire date planning process.
    
    This is the main class that combines:
    1. Data processing (loading and parsing location data)
    2. Rule-based filtering (applying user preferences)
    3. RAG-based retrieval (AI-powered relevance search)
    4. Itinerary generation (creating specific date plans)
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the AI Date Planner with all required services"""
        self.data_dir = data_dir
        
        # Initialize services
        print("Initializing AI Date Planner services...")
        self.data_processor = DataProcessor(data_dir)
        self.embedding_service = EmbeddingService()
        self.rule_engine = RuleEngine()
        self.rag_service = RAGService(self.embedding_service)
        self.llm_query_parser = LLMQueryParser()
        
        # Cache for processed data
        self._locations_cache = None
        self._embeddings_ready = False
        
        print("AI Date Planner initialized successfully!")
    
    def plan_date(self, preferences: UserPreferences, user_query: str = None) -> DatePlanResult:
        """
        Plan a complete date based on user preferences and optional query.
        
        Args:
            preferences: User preferences for the date
            user_query: Optional specific user query (e.g., "romantic dinner with city view")
            
        Returns:
            DatePlanResult with complete date plan and processing details
        """
        print(f"\n🎯 Starting AI Date Planning...")
        print(f"User Query: {user_query or 'None'}")
        print(f"Preferences: {preferences.start_time} - {preferences.end_time or 'flexible'}")
        
        # Step 0: Parse user query with LLM for intelligent requirements extraction
        parsed_query = None
        if user_query:
            print("\n🤖 Step 0: LLM query parsing...")
            try:
                preferences_dict = {
                    'start_time': preferences.start_time,
                    'end_time': preferences.end_time,
                    'interests': preferences.interests,
                    'budget_tier': preferences.budget_tier,
                    'date_type': preferences.date_type
                }
                parsed_query = self.llm_query_parser.parse_query(user_query, preferences_dict)
                print(f"LLM Parsing: {len(parsed_query.inclusions)} inclusions, {len(parsed_query.exclusions)} exclusions")
                print(f"Confidence: {parsed_query.confidence_score:.2f}")
            except Exception as e:
                print(f"LLM parsing failed, using fallback: {e}")
                parsed_query = None
        
        # Step 1: Load and process location data
        locations = self._get_locations()
        
        # Step 2: Apply rule-based filtering
        print("\n📋 Step 1: Rule-based filtering...")
        filter_result = self.rule_engine.filter_locations(locations, preferences)
        
        # Step 3: RAG-based relevance search
        print("\n🧠 Step 2: AI-powered relevance search...")
        rag_result = self.rag_service.find_relevant_locations(filter_result, preferences, user_query)
        
        # Step 4: Generate specific itinerary with LLM-enhanced planning
        print("\n📅 Step 3: Generating specific itinerary...")
        date_plan = self._generate_itinerary(rag_result, preferences, user_query, parsed_query)
        
        # Compile processing statistics
        processing_stats = {
            'total_locations': len(locations),
            'filtered_locations': len(filter_result.filtered_locations),
            'relevant_locations': len(rag_result.relevant_locations),
            'final_activities': len(date_plan.itinerary),
            'embeddings_ready': self._embeddings_ready,
            'llm_parsing_used': parsed_query is not None,
            'llm_confidence': parsed_query.confidence_score if parsed_query else 0.0
        }
        
        print(f"\n✅ Date planning complete!")
        print(f"Final itinerary: {len(date_plan.itinerary)} activities planned")
        
        return DatePlanResult(
            date_plan=date_plan,
            filter_result=filter_result,
            rag_result=rag_result,
            processing_stats=processing_stats
        )
    
    def _get_locations(self) -> List[Location]:
        """Get locations from cache or load from data files"""
        if self._locations_cache is None:
            print("Loading location data...")
            self._locations_cache = self.data_processor.process_all_files()
            print(f"Loaded {len(self._locations_cache)} locations")
        
        return self._locations_cache
    
    def _generate_itinerary(self, rag_result: RAGResult, preferences: UserPreferences, user_query: str = None, parsed_query: ParsedQuery = None) -> DatePlan:
        """Generate a specific itinerary from relevant locations"""
        duration = preferences.get_duration_hours()
        relevant_locations = rag_result.relevant_locations
        
        # Group locations by type
        location_groups = self._group_locations_by_type(relevant_locations)
        
        # Generate itinerary based on time of day and duration
        itinerary = self._create_time_based_itinerary(
            location_groups, 
            preferences, 
            duration,
            user_query,
            parsed_query
        )
        
        # Calculate estimated cost
        estimated_cost = self._estimate_cost(itinerary, preferences.budget_tier)
        
        # Generate summary
        summary = self._generate_summary(itinerary, preferences)
        
        # Generate alternative suggestions
        used_locations = [item['location_obj'] for item in itinerary if 'location_obj' in item]
        alternatives = self._generate_alternatives(location_groups, preferences, used_locations)
        
        return DatePlan(
            itinerary=itinerary,
            total_duration=duration,
            estimated_cost=estimated_cost,
            summary=summary,
            alternative_suggestions=alternatives
        )
    
    def _group_locations_by_type(self, locations: List[Location]) -> Dict[str, List[Location]]:
        """Group locations by type for itinerary planning"""
        groups = {
            'food': [],
            'attraction': [],
            'activity': [],
            'heritage': []
        }
        
        for location in locations:
            if location.location_type in groups:
                groups[location.location_type].append(location)
        
        return groups
    
    def _create_time_based_itinerary(self, location_groups: Dict[str, List[Location]], preferences: UserPreferences, duration: float, user_query: str = None, parsed_query: ParsedQuery = None) -> List[Dict[str, Any]]:
        """Create itinerary based on actual time ranges and duration"""
        itinerary = []
        current_time = self._parse_time(preferences.start_time)
        if preferences.end_time:
            end_time = self._parse_time(preferences.end_time)
        else:
            end_time = self._add_hours(current_time, duration)
        
        # Sequential planning: plan each activity/meal after the previous one
        max_activities = 5  # Reasonable limit for date planning
        activity_count = 0
        
        while self._time_difference(current_time, end_time) > 0.5 and activity_count < max_activities:  # At least 30 minutes remaining
            next_activity = self._plan_next_activity(location_groups, current_time, end_time, itinerary, preferences, user_query, parsed_query)
            if next_activity:
                # Check if this activity would exceed the end time
                if self._time_after_or_equal(next_activity['end_time'], end_time):
                    # Adjust the activity to end at the end time
                    next_activity['end_time'] = end_time
                    next_activity['duration'] = self._time_difference(next_activity['start_time'], end_time)
                    itinerary.append(next_activity)
                    break  # Stop planning after this activity
                else:
                    itinerary.append(next_activity)
                    current_time = next_activity['end_time']
                    activity_count += 1
            else:
                break  # No more activities can be planned
        
        return itinerary
    
    
    def _plan_next_activity(self, location_groups: Dict[str, List[Location]], current_time: str, end_time: str, existing_itinerary: List[Dict[str, Any]], preferences: UserPreferences, user_query: str = None, parsed_query: ParsedQuery = None) -> Optional[Dict[str, Any]]:
        """Plan the next activity/meal sequentially with proper travel time"""
        time_remaining = self._time_difference(current_time, end_time)
        if time_remaining < 0.5:  # Less than 30 minutes
            return None
        
        current_hour = int(current_time.split(':')[0])
        
        # PRIORITIZE MEALS: Always check if we should plan a meal first
        if self._should_plan_meal(current_time, existing_itinerary, preferences, user_query, parsed_query):
            meal_result = self._plan_next_meal(location_groups, current_time, time_remaining, existing_itinerary)
            if meal_result:  # If we can plan a meal, do it
                return meal_result
        
        # If no meal needed or couldn't plan meal, plan activity
        return self._plan_next_activity_only(location_groups, current_time, time_remaining, existing_itinerary, preferences, user_query, parsed_query)
    
    def _should_plan_meal(self, current_time: str, existing_itinerary: List[Dict[str, Any]], preferences: UserPreferences, user_query: str = None, parsed_query: ParsedQuery = None) -> bool:
        """Determine if we should plan a meal at this time"""
        current_hour = int(current_time.split(':')[0])
        
        # Check if user wants to exclude food activities (using LLM or fallback)
        if self._should_exclude_activity_type(user_query, 'food', parsed_query):
            return False
        
        # Count existing meals and check for specific meal types
        meal_count = 0
        existing_meal_types = set()
        if existing_itinerary:
            for activity in existing_itinerary:
                if activity.get('type') == 'food':
                    meal_count += 1
                    existing_meal_types.add(activity.get('activity', ''))
        
        # Plan meals based on time windows and avoid duplicates
        if 6 <= current_hour <= 11 and 'Coffee/Breakfast' not in existing_meal_types:  # Breakfast/Coffee
            return True
        elif 12 <= current_hour <= 14 and 'Lunch' not in existing_meal_types:  # Lunch (12:00-14:00)
            return True
        elif 14 <= current_hour <= 16 and 'Coffee Break' not in existing_meal_types:  # Coffee Break (14:00-16:00)
            return True
        elif 17 <= current_hour <= 20 and 'Dinner' not in existing_meal_types:  # Dinner (17:00-20:00)
            return True
        elif current_hour >= 21 and 'Late Dinner' not in existing_meal_types:  # Late Dinner (after 21:00)
            return True
        
        return False
    
    def _plan_next_meal(self, location_groups: Dict[str, List[Location]], current_time: str, time_remaining: float, existing_itinerary: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Plan the next meal with travel time"""
        if not location_groups['food']:
            return None
        
        current_hour = int(current_time.split(':')[0])
        
        # Choose meal type and duration based on time and existing meals
        existing_meal_types = set()
        if existing_itinerary:
            for activity in existing_itinerary:
                if activity.get('type') == 'food':
                    existing_meal_types.add(activity.get('activity', ''))
        
        if 6 <= current_hour <= 11 and 'Coffee/Breakfast' not in existing_meal_types:
            meal_type = "Coffee/Breakfast"
            duration = 1.0
            food_index = 0
        elif 12 <= current_hour <= 14 and 'Lunch' not in existing_meal_types:
            meal_type = "Lunch"
            duration = 1.5  # Lunch duration (time window is 12:00-14:00)
            food_index = min(1, len(location_groups['food']) - 1)
        elif 14 <= current_hour <= 16 and 'Coffee Break' not in existing_meal_types:
            meal_type = "Coffee Break"
            duration = 1.0
            food_index = min(2, len(location_groups['food']) - 1)
        elif 17 <= current_hour <= 20 and 'Dinner' not in existing_meal_types:
            meal_type = "Dinner"
            duration = 2.0
            food_index = min(3, len(location_groups['food']) - 1)
        elif current_hour >= 21 and 'Late Dinner' not in existing_meal_types:
            meal_type = "Late Dinner"
            duration = 2.0
            food_index = 0
        else:
            return None  # Don't plan duplicate meal types
        
        # Adjust meal duration if not enough time remaining
        if duration > time_remaining:
            duration = max(0.5, time_remaining)  # Minimum 30 minutes for any meal
        
        # Get food location (avoid duplicates, prefer cafes for coffee breaks)
        used_location_ids = set()
        for a in existing_itinerary:
            if isinstance(a, dict) and 'location_obj' in a:
                used_location_ids.add(a['location_obj'].id)
            elif hasattr(a, 'id'):  # Direct Location object
                used_location_ids.add(a.id)
        available_food = [loc for loc in location_groups['food'] if loc.id not in used_location_ids]
        
        if not available_food:
            # If all food locations used, allow reuse but prefer different ones
            available_food = location_groups['food']
        
        if meal_type == "Coffee Break":
            # Prefer cafes, but use any food location if no cafes found
            cafe_keywords = ['cafe', 'coffee', 'kopi', 'kopitiam', 'bistro', 'brunch', 'breakfast']
            cafe_locations = [loc for loc in available_food 
                            if any(keyword in loc.name.lower() for keyword in cafe_keywords)]
            if cafe_locations:
                food_location = cafe_locations[min(food_index, len(cafe_locations) - 1)]
            else:
                # Fallback to regular food locations if no cafes found
                food_location = available_food[min(food_index, len(available_food) - 1)]
        else:
            food_location = available_food[min(food_index, len(available_food) - 1)]
        
        # Add travel time if there are previous activities
        start_time = current_time
        if existing_itinerary:
            last_location = existing_itinerary[-1].get('location_obj')
            if last_location:
                travel_time = self._calculate_travel_time(last_location, food_location)
                start_time = self._add_hours(current_time, travel_time)
        
        end_time = self._add_hours(start_time, duration)
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'activity': meal_type,
            'location': food_location.name,
            'address': food_location.address or 'Address not available',
            'type': 'food',
            'duration': duration,
            'description': f"{food_location.description[:100]}...",
            'location_obj': food_location
        }
    
    def _plan_next_activity_only(self, location_groups: Dict[str, List[Location]], current_time: str, time_remaining: float, existing_itinerary: List[Dict[str, Any]], preferences: UserPreferences = None, user_query: str = None, parsed_query: ParsedQuery = None) -> Optional[Dict[str, Any]]:
        """Plan the next non-meal activity with travel time"""
        # Count existing activities to avoid too many of the same type
        activity_count = len([a for a in existing_itinerary if a.get('type') != 'food'])
        
        # Check for user exclusions
        exclude_sports = self._should_exclude_sports(user_query, parsed_query)
        
        # Get used location IDs to avoid duplicates
        used_location_ids = set()
        for a in existing_itinerary:
            if isinstance(a, dict) and 'location_obj' in a:
                used_location_ids.add(a['location_obj'].id)
            elif hasattr(a, 'id'):  # Direct Location object
                used_location_ids.add(a.id)
        
        # Find available locations (not used before)
        available_activities = [loc for loc in location_groups.get('activity', []) if loc.id not in used_location_ids]
        available_attractions = [loc for loc in location_groups.get('attraction', []) if loc.id not in used_location_ids]
        available_heritage = [loc for loc in location_groups.get('heritage', []) if loc.id not in used_location_ids]
        
        # Check for other exclusions
        exclude_cultural = self._should_exclude_activity_type(user_query, 'cultural', parsed_query)
        exclude_nature = self._should_exclude_activity_type(user_query, 'nature', parsed_query)
        
        # Check if user explicitly wants walks despite cultural exclusion
        wants_walks = user_query and any(word in user_query.lower() for word in ['walk', 'walking', 'stroll', 'hike'])
        
        # Use LLM requirements to prioritize activities
        if parsed_query:
            activity_requirements = self.llm_query_parser.get_activity_requirements(parsed_query)
            # If user wants sports and we haven't planned any sports yet, prioritize sports
            if activity_requirements.get('sports', 0) > 0 and available_activities and not exclude_sports:
                location = available_activities[0]
                activity_duration = min(2.0, time_remaining)
                activity_type = self._get_simple_activity_type(location)
                return self._create_activity_dict(location, current_time, activity_duration, activity_type, existing_itinerary)
        
        # Choose activity type based on remaining time and what's available
        if time_remaining >= 2.0 and available_attractions and not exclude_sports and (not exclude_cultural or wants_walks):
            # Prefer attractions for cultural dates, or allow walks if explicitly requested
            location = available_attractions[0]
            activity_duration = min(2.0, time_remaining)
            # Check if it's a nature activity and if nature is excluded
            if 'walk' in location.name.lower() or 'park' in location.name.lower() or 'nature' in location.name.lower() or 'reserve' in location.name.lower() or 'garden' in location.name.lower():
                if exclude_nature and not wants_walks:
                    activity_type = 'Cultural Visit'  # Force cultural instead of nature
                else:
                    activity_type = 'Walk'  # Allow walks if explicitly requested
            else:
                activity_type = 'Cultural Visit'
        elif time_remaining >= 2.0 and available_activities and activity_count < 1 and not exclude_sports:  # Max 1 sports activity, only if not excluded
            location = available_activities[0]
            activity_duration = min(2.0, time_remaining)
            activity_type = self._get_simple_activity_type(location)
        elif time_remaining >= 1.5 and available_heritage and (not exclude_cultural or wants_walks):
            location = available_heritage[0]
            activity_duration = min(1.5, time_remaining)
            activity_type = 'Heritage Walk'
        elif time_remaining >= 1.0 and available_attractions and (not exclude_cultural or wants_walks):
            location = available_attractions[0]
            activity_duration = min(1.5, time_remaining)
            # Check if it's a nature activity and if nature is excluded
            if 'walk' in location.name.lower() or 'park' in location.name.lower() or 'nature' in location.name.lower() or 'reserve' in location.name.lower() or 'garden' in location.name.lower():
                if exclude_nature and not wants_walks:
                    activity_type = 'Cultural Visit'  # Force cultural instead of nature
                else:
                    activity_type = 'Walk'  # Allow walks if explicitly requested
            else:
                activity_type = 'Cultural Visit'
        elif time_remaining >= 1.0 and available_activities and activity_count < 1 and not exclude_sports:  # Max 1 sports activity, only if not excluded
            location = available_activities[0]
            activity_duration = min(1.5, time_remaining)
            activity_type = self._get_simple_activity_type(location)
        else:
            return None
        
        # Add travel time if there are previous activities
        start_time = current_time
        if existing_itinerary:
            last_location = existing_itinerary[-1].get('location_obj')
            if last_location:
                travel_time = self._calculate_travel_time(last_location, location)
                start_time = self._add_hours(current_time, travel_time)
        
        end_time = self._add_hours(start_time, activity_duration)
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'activity': activity_type,
            'location': location.name,
            'address': location.address or 'Address not available',
            'type': location.location_type,
            'duration': activity_duration,
            'description': f"{location.description[:100]}...",
            'location_obj': location
        }
    
    def _plan_meals_by_time(self, location_groups: Dict[str, List[Location]], start_time: str, duration: float) -> List[Dict[str, Any]]:
        """Plan meals based on actual time ranges"""
        meals = []
        current_time = start_time
        
        if not location_groups['food']:
            return meals
        
        # Parse start time to get hour
        start_hour = int(start_time.split(':')[0])
        
        # Breakfast/Coffee: 6:00 - 11:00
        if 6 <= start_hour <= 11:
            if location_groups['food']:
                food_location = location_groups['food'][0]  # Use first available food location
                end_time = self._add_hours(current_time, 1.0)
                meals.append({
                    'start_time': current_time,
                    'end_time': end_time,
                    'activity': 'Coffee/Breakfast',
                    'location': food_location.name,
                    'address': food_location.address or 'Address not available',
                    'type': 'food',
                    'duration': 1.0,
                    'description': f"Start your day with {food_location.description[:100]}...",
                    'location_obj': food_location
                })
                current_time = end_time
        
        # Lunch: 12:00 - 14:00 (if date spans this time)
        date_end_time = self._add_hours(start_time, duration)
        if start_hour <= 12 and self._time_after_or_equal(date_end_time, "12:00"):  # Date spans lunch time
            if len(location_groups['food']) > 1:
                lunch_location = location_groups['food'][1]  # Use second food location to avoid duplicate
                # Add travel time
                if meals:
                    travel_time = self._calculate_travel_time(meals[-1]['location_obj'], lunch_location)
                    current_time = self._add_hours(current_time, travel_time)
                
                end_time = self._add_hours(current_time, 1.5)
                meals.append({
                    'start_time': current_time,
                    'end_time': end_time,
                    'activity': 'Lunch',
                    'location': lunch_location.name,
                    'address': lunch_location.address or 'Address not available',
                    'type': 'food',
                    'duration': 1.5,
                    'description': f"{lunch_location.description[:100]}...",
                    'location_obj': lunch_location
                })
                current_time = end_time
        
        # Coffee Break: 14:00 - 17:00 (for extended dates)
        if start_hour <= 14 and duration > 6:  # Date starts before 2pm and is long enough
            if len(location_groups['food']) > 2:
                coffee_location = location_groups['food'][2]  # Use third food location to avoid duplicate
                # Add travel time
                if meals:
                    travel_time = self._calculate_travel_time(meals[-1]['location_obj'], coffee_location)
                    current_time = self._add_hours(current_time, travel_time)
                
                end_time = self._add_hours(current_time, 1.0)
                meals.append({
                    'start_time': current_time,
                    'end_time': end_time,
                    'activity': 'Coffee Break',
                    'location': coffee_location.name,
                    'address': coffee_location.address or 'Address not available',
                    'type': 'food',
                    'duration': 1.0,
                    'description': f"Relax with coffee at {coffee_location.description[:100]}...",
                    'location_obj': coffee_location
                })
                current_time = end_time
        
        # Dinner: 17:00 - 19:30 (if date spans this time)
        if (start_hour <= 17 and self._time_after_or_equal(date_end_time, "17:01")) or (start_hour >= 17 and self._time_after_or_equal(date_end_time, "17:00")):  # Date spans dinner time
            # Use different food location to avoid duplicates
            dinner_index = 3 if len(location_groups['food']) > 3 else min(2, len(location_groups['food']) - 1)
            if len(location_groups['food']) > dinner_index:
                dinner_location = location_groups['food'][dinner_index]
                
                # Plan dinner for the evening time slot (19:00-21:00 for 7-hour dates)
                dinner_start_time = "19:00" if duration >= 7 else self._add_hours(start_time, duration - 2.0)
                
                # Add travel time if there are previous meals
                if meals:
                    travel_time = self._calculate_travel_time(meals[-1]['location_obj'], dinner_location)
                    dinner_start_time = self._add_hours(dinner_start_time, travel_time)
                
                dinner_end_time = self._add_hours(dinner_start_time, 2.0)
                
                meals.append({
                    'start_time': dinner_start_time,
                    'end_time': dinner_end_time,
                    'activity': 'Dinner',
                    'location': dinner_location.name,
                    'address': dinner_location.address or 'Address not available',
                    'type': 'food',
                    'duration': 2.0,
                    'description': f"{dinner_location.description[:100]}...",
                    'location_obj': dinner_location
                })
        
        # Late Dinner: 21:00 - 02:00 (if date spans this time)
        if start_hour >= 21 or (start_hour <= 2 and duration > 2):  # Date starts after 9pm or before 2am
            late_dinner_index = 0
            if len(location_groups['food']) > late_dinner_index:
                late_dinner_location = location_groups['food'][late_dinner_index]
                # Add travel time
                if meals:
                    travel_time = self._calculate_travel_time(meals[-1]['location_obj'], late_dinner_location)
                    current_time = self._add_hours(current_time, travel_time)
                
                end_time = self._add_hours(current_time, 2.0)
                meals.append({
                    'start_time': current_time,
                    'end_time': end_time,
                    'activity': 'Late Dinner',
                    'location': late_dinner_location.name,
                    'address': late_dinner_location.address or 'Address not available',
                    'type': 'food',
                    'duration': 2.0,
                    'description': f"Late night dining at {late_dinner_location.description[:100]}...",
                    'location_obj': late_dinner_location
                })
                current_time = end_time
        
        return meals
    
    def _plan_activities_by_time(self, location_groups: Dict[str, List[Location]], start_time: str, duration: float, meals_planned: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Plan activities to fill remaining time between meals"""
        activities = []
        current_time = start_time
        
        if not meals_planned:
            # No meals planned, fill entire duration with activities
            # Plan multiple activities to fill the duration
            remaining_duration = duration
            activity_count = 0
            
            while remaining_duration > 0.5 and activity_count < 3:  # Max 3 activities
                # Choose activity type based on remaining time and what's available
                if remaining_duration >= 2.0 and location_groups['attraction'] and activity_count < 1:
                    # Long activity - use attraction (max 1)
                    activity_duration = min(2.0, remaining_duration)
                    location = location_groups['attraction'][activity_count]  # Use different attraction each time
                    activity_type = 'Walk' if 'walk' in location.name.lower() or 'park' in location.name.lower() else 'Cultural Visit'
                elif remaining_duration >= 1.0 and location_groups['activity'] and activity_count < 1:
                    # Medium activity - use sports/activity (max 1)
                    activity_duration = min(2.0, remaining_duration)
                    location = location_groups['activity'][activity_count]  # Use different activity each time
                    activity_type = self._get_simple_activity_type(location)
                elif location_groups['attraction'] and activity_count < 2:
                    # Short activity - use attraction
                    activity_duration = min(1.0, remaining_duration)
                    location = location_groups['attraction'][activity_count]  # Use different attraction each time
                    activity_type = 'Walk' if 'walk' in location.name.lower() or 'park' in location.name.lower() else 'Cultural Visit'
                else:
                    break
                
                # Add travel time if there are previous activities
                if activities:
                    travel_time = self._calculate_travel_time(activities[-1]['location_obj'], location)
                    current_time = self._add_hours(current_time, travel_time)
                
                end_time = self._add_hours(current_time, activity_duration)
                activities.append({
                    'start_time': current_time,
                    'end_time': end_time,
                    'activity': activity_type,
                    'location': location.name,
                    'address': location.address or 'Address not available',
                    'type': location.location_type,
                    'duration': activity_duration,
                    'description': f"{location.description[:100]}...",
                    'location_obj': location
                })
                
                current_time = end_time
                remaining_duration -= activity_duration
                activity_count += 1
        else:
            # Fill gaps between meals with activities
            for i, meal in enumerate(meals_planned):
                # Add activity before meal if there's time
                time_until_meal = self._time_difference(current_time, meal['start_time'])
                if time_until_meal > 0.5:  # At least 30 minutes
                    activity = self._create_activity_for_duration(location_groups, current_time, time_until_meal)
                    if activity:
                        activities.append(activity)
                        current_time = activity['end_time']
                
                # Move to after meal
                current_time = meal['end_time']
            
            # Add final activity if there's remaining time
            # Calculate the actual end time of the date
            actual_end_time = self._add_hours(start_time, duration)
            time_remaining = self._time_difference(current_time, actual_end_time)
            if time_remaining > 0.5:
                # Add travel time if there are previous meals/activities
                if meals_planned or activities:
                    # Get the last location (either from last meal or last activity)
                    last_location = None
                    if activities:
                        last_location = activities[-1]['location_obj']
                    elif meals_planned:
                        last_location = meals_planned[-1]['location_obj']
                    
                    if last_location:
                        # Find the next activity location
                        if location_groups['activity']:
                            next_location = location_groups['activity'][0]
                            travel_time = self._calculate_travel_time(last_location, next_location)
                            current_time = self._add_hours(current_time, travel_time)
                
                final_activity = self._create_activity_for_duration(location_groups, current_time, time_remaining)
                if final_activity:
                    activities.append(final_activity)
        
        return activities
    
    def _create_activity_for_duration(self, location_groups: Dict[str, List[Location]], start_time: str, duration: float) -> Optional[Dict[str, Any]]:
        """Create an appropriate activity for the given duration"""
        if duration < 0.5:  # Less than 30 minutes
            return None
        
        # Prefer attractions for shorter durations, activities for longer ones
        if duration <= 2.0 and location_groups['attraction']:
            location = location_groups['attraction'][0]
            activity_type = 'Walk' if 'walk' in location.name.lower() or 'park' in location.name.lower() else 'Cultural Visit'
        elif duration > 2.0 and location_groups['activity']:
            location = location_groups['activity'][0]
            activity_type = self._get_simple_activity_type(location)
        elif location_groups['attraction']:
            location = location_groups['attraction'][0]
            activity_type = 'Walk' if 'walk' in location.name.lower() or 'park' in location.name.lower() else 'Cultural Visit'
        else:
            return None
        
        end_time = self._add_hours(start_time, duration)
        return {
            'start_time': start_time,
            'end_time': end_time,
            'activity': activity_type,
            'location': location.name,
            'address': location.address or 'Address not available',
            'type': location.location_type,
            'duration': duration,
            'description': f"{location.description[:100]}...",
            'location_obj': location
        }
    
    def _time_difference(self, start_time: str, end_time: str) -> float:
        """Calculate time difference in hours between two time strings"""
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        start_total_min = start_hour * 60 + start_min
        end_total_min = end_hour * 60 + end_min
        
        # Handle overnight times
        if end_total_min < start_total_min:
            end_total_min += 24 * 60
        
        return (end_total_min - start_total_min) / 60.0
    
    def _time_after_or_equal(self, time1: str, time2: str) -> bool:
        """Check if time1 is after or equal to time2 (same day)"""
        hour1, min1 = map(int, time1.split(':'))
        hour2, min2 = map(int, time2.split(':'))
        
        total_min1 = hour1 * 60 + min1
        total_min2 = hour2 * 60 + min2
        
        return total_min1 >= total_min2
    
        return itinerary
    
    def _parse_time(self, time_str: str) -> str:
        """Parse time string (basic implementation)"""
        return time_str
    
    def _add_hours(self, time_str: str, hours: float) -> str:
        """Add hours to time string (basic implementation)"""
        try:
            hour, minute = map(int, time_str.split(':'))
            total_minutes = hour * 60 + minute + int(hours * 60)
            new_hour = (total_minutes // 60) % 24
            new_minute = total_minutes % 60
            return f"{new_hour:02d}:{new_minute:02d}"
        except:
            return time_str
    
    def _calculate_travel_time(self, location1: Location, location2: Location) -> float:
        """Calculate travel time between two locations in hours"""
        if not location1.coordinates or not location2.coordinates:
            return 0.25  # Default 15 minutes if coordinates missing
        
        # Extract coordinates (longitude, latitude)
        lon1, lat1 = location1.coordinates
        lon2, lat2 = location2.coordinates
        
        # Calculate distance using Haversine formula
        import math
        
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c  # Earth's radius in km
        
        # Estimate travel time based on distance
        # Assume average speed of 30 km/h in Singapore (including traffic, public transport)
        travel_time_hours = distance_km / 30.0
        
        # Add minimum travel time and cap maximum
        travel_time_hours = max(0.1, min(travel_time_hours, 1.0))  # 6 minutes to 1 hour
        
        return round(travel_time_hours, 2)
    
    def _should_exclude_activity_type(self, user_query: str = None, activity_type: str = None, parsed_query: ParsedQuery = None) -> bool:
        """Check if user explicitly wants to exclude specific activity types using LLM parsing"""
        if not user_query or not activity_type:
            return False
        
        # Use LLM parsing if available
        if parsed_query:
            exclusion_flags = self.llm_query_parser.get_exclusion_flags(parsed_query)
            return exclusion_flags.get(activity_type.lower(), False)
        
        # Simple fallback for basic exclusions
        user_query_lower = user_query.lower()
        return f"no {activity_type}" in user_query_lower or f"avoid {activity_type}" in user_query_lower
    
    def _should_exclude_sports(self, user_query: str = None, parsed_query: ParsedQuery = None) -> bool:
        """Check if user explicitly wants to exclude sports activities"""
        return self._should_exclude_activity_type(user_query, 'sports', parsed_query)
    
    def _create_activity_dict(self, location: Location, current_time: str, duration: float, activity_type: str, existing_itinerary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create activity dictionary with travel time"""
        # Add travel time if there are previous activities
        start_time = current_time
        if existing_itinerary:
            last_location = existing_itinerary[-1].get('location_obj')
            if last_location:
                travel_time = self._calculate_travel_time(last_location, location)
                start_time = self._add_hours(current_time, travel_time)
        
        end_time = self._add_hours(start_time, duration)
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'activity': activity_type,
            'location': location.name,
            'address': location.address or 'Address not available',
            'type': location.location_type,
            'duration': duration,
            'description': f"{location.description[:100]}...",
            'location_obj': location
        }
    
    def _get_simple_activity_type(self, location: Location) -> str:
        """Simple activity type determination - let the LLM handle the details"""
        # Just return a basic type based on location type
        if location.location_type == 'activity':
            return 'Sports Activity'
        elif location.location_type == 'attraction':
            return 'Cultural Visit'
        elif location.location_type == 'heritage':
            return 'Heritage Site'
        else:
            return 'Activity'
    
    def _estimate_cost(self, itinerary: List[Dict[str, Any]], budget_tier: str) -> str:
        """Estimate total cost based on budget tier and activities"""
        cost_per_person = {
            "$": 20,
            "$$": 50,
            "$$$": 100,
            "$$$$": 200
        }
        
        base_cost = cost_per_person.get(budget_tier, 50)
        activity_count = len(itinerary)
        
        if activity_count <= 2:
            return f"${base_cost}-${base_cost + 20} per person"
        elif activity_count <= 4:
            return f"${base_cost + 20}-${base_cost + 50} per person"
        else:
            return f"${base_cost + 50}-${base_cost + 100} per person"
    
    def _generate_summary(self, itinerary: List[Dict[str, Any]], preferences: UserPreferences) -> str:
        """Generate a summary of the date plan"""
        summary = f"Your {preferences.get_duration_hours():.1f}-hour {preferences.date_type} date:\n\n"
        
        for activity in itinerary:
            start_time = activity.get('start_time', activity.get('time', 'Unknown'))
            summary += f"• {start_time}: {activity['activity']} at {activity['location']}\n"
        
        summary += f"\nPerfect for a {preferences.date_type} experience with {', '.join(preferences.interests)} interests!"
        
        return summary
    
    def _generate_alternatives(self, location_groups: Dict[str, List[Location]], preferences: UserPreferences, used_locations: List[Location]) -> List[str]:
        """Generate alternative suggestions that don't repeat itinerary locations"""
        alternatives = []
        used_location_ids = {loc.id for loc in used_locations}
        
        for location_type, locations in location_groups.items():
            # Find locations of this type that weren't used in the itinerary
            unused_locations = [loc for loc in locations if loc.id not in used_location_ids]
            
            if unused_locations:
                # Take the first unused location of this type
                alt_location = unused_locations[0]
                address = alt_location.address or "Address not available"
                alternatives.append(f"Alternative {location_type}: {alt_location.name} - {address}")
        
        return alternatives[:3]  # Limit to 3 alternatives
    
    def get_processing_summary(self, result: DatePlanResult) -> str:
        """Get a comprehensive summary of the entire planning process"""
        summary = "🎯 AI Date Planning Summary\n"
        summary += "=" * 50 + "\n\n"
        
        # Processing stats
        stats = result.processing_stats
        summary += f"📊 Processing Statistics:\n"
        summary += f"  • Total locations loaded: {stats['total_locations']}\n"
        summary += f"  • After rule filtering: {stats['filtered_locations']}\n"
        summary += f"  • After AI relevance: {stats['relevant_locations']}\n"
        summary += f"  • Final activities: {stats['final_activities']}\n"
        summary += f"  • Embeddings ready: {stats['embeddings_ready']}\n\n"
        
        # Date plan
        plan = result.date_plan
        summary += f"📅 Your Date Plan:\n"
        summary += f"  • Duration: {plan.total_duration:.1f} hours\n"
        summary += f"  • Estimated cost: {plan.estimated_cost}\n"
        summary += f"  • Activities: {len(plan.itinerary)}\n\n"
        
        # Itinerary
        summary += "🗓️ Itinerary:\n"
        for activity in plan.itinerary:
            start_time = activity.get('start_time', activity.get('time', 'Unknown'))
            summary += f"  • {start_time}: {activity['activity']} at {activity['location']}\n"
        
        # Alternatives
        if plan.alternative_suggestions:
            summary += f"\n🔄 Alternative Suggestions:\n"
            for alt in plan.alternative_suggestions:
                summary += f"  • {alt}\n"
        
        return summary
    
    def check_embeddings_status(self) -> Dict[str, Any]:
        """Check if embeddings are ready and provide status"""
        status = {
            'embeddings_ready': self._embeddings_ready,
            'embedding_service_initialized': hasattr(self.embedding_service, 'model'),
            'locations_loaded': self._locations_cache is not None,
            'total_locations': len(self._locations_cache) if self._locations_cache else 0
        }
        
        if self._locations_cache and not self._embeddings_ready:
            status['message'] = "Embeddings need to be generated. Run generate_embeddings() first."
        elif self._embeddings_ready:
            status['message'] = "Embeddings are ready! You can plan dates now."
        else:
            status['message'] = "Load locations first, then generate embeddings."
        
        return status
    
    def generate_embeddings(self) -> Dict[str, Any]:
        """Generate embeddings for all locations"""
        if not self._locations_cache:
            locations = self._get_locations()
        else:
            locations = self._locations_cache
        
        print(f"Generating embeddings for {len(locations)} locations...")
        
        try:
            self.embedding_service.generate_embeddings(locations)
            self._embeddings_ready = True
            print("✅ Embeddings generated successfully!")
            
            return {
                'success': True,
                'total_embeddings': len(locations),
                'message': 'Embeddings generated successfully!'
            }
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate embeddings. Check your setup.'
            }
