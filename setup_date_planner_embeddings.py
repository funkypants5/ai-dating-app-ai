#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for AI Date Planner RAG embeddings.
Run this once to generate embeddings for all locations and test the date planning system.
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from ai.ai_date_planner.ai_date_planner import AIDatePlanner
from ai.ai_date_planner.rule_engine import UserPreferences

def main():
    """Setup and test the AI Date Planner system"""
    print("AI Date Planner - Setup & Test")
    print("=" * 50)
    
    # Initialize the AI Date Planner
    print("\n1. Initializing AI Date Planner...")
    planner = AIDatePlanner(data_dir="ai/ai_date_planner/data")
    
    # Check embeddings status
    print("\n2. Checking embeddings status...")
    status = planner.check_embeddings_status()
    print(f"Status: {status['message']}")
    
    if not status['embeddings_ready']:
        print("\n3. Generating embeddings...")
        embedding_result = planner.generate_embeddings()
        if not embedding_result['success']:
            print(f"❌ Failed to generate embeddings: {embedding_result['error']}")
            return
        print(f"✅ {embedding_result['message']}")
    
    # Create user preferences
    print("\n4. Creating user preferences...")
    preferences = UserPreferences(
        start_time="10:00",
        end_time="17:00",  # 7-hour date
        start_latitude=1.3521,  # Marina Bay area
        start_longitude=103.8198,
        interests=['food', 'culture', 'nature'],
        budget_tier="$$",
        date_type="romantic"
    )
    
    print(f"Preferences: {preferences.start_time} - {preferences.end_time}")
    print(f"Interests: {preferences.interests}")
    print(f"Budget: {preferences.budget_tier}")
    print(f"Date type: {preferences.date_type}")
    
    # Plan the date
    print("\n5. Planning the date...")
    user_query = "romantic date with city views and good food"
    
    try:
        result = planner.plan_date(preferences, user_query)
        
        # Display results
        print("\n6. Results:")
        print(planner.get_processing_summary(result))
        
        # Show detailed itinerary
        print("\n📅 Detailed Itinerary:")
        for i, activity in enumerate(result.date_plan.itinerary, 1):
            start_time = activity.get('start_time', activity.get('time', 'Unknown'))
            end_time = activity.get('end_time', 'Unknown')
            print(f"\n{i}. {start_time} - {end_time} | {activity['activity']}")
            print(f"   Location: {activity['location']}")
            print(f"   Address: {activity.get('address', 'Address not available')}")
            print(f"   Duration: {activity['duration']} hours")
            print(f"   Description: {activity['description']}")
        
        # Show alternatives
        if result.date_plan.alternative_suggestions:
            print(f"\n🔄 Alternative Suggestions:")
            for alt in result.date_plan.alternative_suggestions:
                print(f"   • {alt}")
        
        print(f"\n💰 Estimated Cost: {result.date_plan.estimated_cost}")
        
    except Exception as e:
        print(f"❌ Error planning date: {e}")
        import traceback
        traceback.print_exc()

def test_different_scenarios():
    """Test different date scenarios"""
    print("\n\n🧪 Testing Different Scenarios")
    print("=" * 50)
    
    planner = AIDatePlanner(data_dir="ai/ai_date_planner/data")
    
    # Check if embeddings are ready
    status = planner.check_embeddings_status()
    if not status['embeddings_ready']:
        print("Generating embeddings first...")
        planner.generate_embeddings()
    
    # Scenario 1: Morning coffee date
    print("\n🌅 Scenario 1: Morning Coffee Date")
    morning_prefs = UserPreferences(
        start_time="09:00",
        end_time="12:00",
        start_latitude=1.3521,
        start_longitude=103.8198,
        interests=['food', 'nature'],
        budget_tier="$",
        date_type="casual"
    )
    
    try:
        result = planner.plan_date(morning_prefs, "casual morning coffee and walk")
        print(f"Activities planned: {len(result.date_plan.itinerary)}")
        for activity in result.date_plan.itinerary:
            start_time = activity.get('start_time', activity.get('time', 'Unknown'))
            end_time = activity.get('end_time', 'Unknown')
            print(f"  • {start_time}-{end_time}: {activity['activity']} at {activity['location']}")
            print(f"    Address: {activity.get('address', 'Address not available')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Scenario 2: Evening romantic date
    print("\n🌆 Scenario 2: Evening Romantic Date")
    evening_prefs = UserPreferences(
        start_time="18:00",
        end_time="22:00",
        start_latitude=1.3521,
        start_longitude=103.8198,
        interests=['food', 'culture'],
        budget_tier="$$$",
        date_type="romantic"
    )
    
    try:
        result = planner.plan_date(evening_prefs, "romantic dinner with city views")
        print(f"Activities planned: {len(result.date_plan.itinerary)}")
        for activity in result.date_plan.itinerary:
            start_time = activity.get('start_time', activity.get('time', 'Unknown'))
            end_time = activity.get('end_time', 'Unknown')
            print(f"  • {start_time}-{end_time}: {activity['activity']} at {activity['location']}")
            print(f"    Address: {activity.get('address', 'Address not available')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
    test_different_scenarios()
