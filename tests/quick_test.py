#!/usr/bin/env python3
"""
Quick Test Runner for AI Date Planner

Run specific test scenarios quickly without the full test suite.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_date_planner.ai_date_planner import AIDatePlanner
from ai.ai_date_planner.rule_engine import UserPreferences

def quick_test():
    """Run a quick test of the date planner"""
    print("🚀 Quick Date Planner Test")
    print("="*50)
    
    # Initialize planner
    try:
        planner = AIDatePlanner(data_dir="ai/ai_date_planner/data")
        print("✅ AI Date Planner initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test 1: Morning Coffee Date
    print("\n🌅 Test 1: Morning Coffee Date (3 hours)")
    preferences = UserPreferences(
        start_time="09:00",
        end_time="12:00",
        start_latitude=1.3521,
        start_longitude=103.8198,
        interests=['food', 'nature'],
        budget_tier="$",
        date_type="casual"
    )
    
    try:
        result = planner.plan_date(preferences, "casual morning coffee and walk")
        print(f"✅ Success! {len(result.date_plan.itinerary)} activities planned")
        
        for i, activity in enumerate(result.date_plan.itinerary, 1):
            print(f"   {i}. {activity['start_time']}-{activity['end_time']}: {activity['activity']}")
            print(f"      Location: {activity['location']}")
            print(f"      Address: {activity['address']}")
        
        print(f"   Cost: {result.date_plan.estimated_cost}")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Evening Romantic Date
    print("\n🌆 Test 2: Evening Romantic Date (4 hours)")
    preferences = UserPreferences(
        start_time="18:00",
        end_time="22:00",
        start_latitude=1.3521,
        start_longitude=103.8198,
        interests=['food', 'culture'],
        budget_tier="$$$",
        date_type="romantic"
    )
    
    try:
        result = planner.plan_date(preferences, "romantic dinner with city views")
        print(f"✅ Success! {len(result.date_plan.itinerary)} activities planned")
        
        for i, activity in enumerate(result.date_plan.itinerary, 1):
            print(f"   {i}. {activity['start_time']}-{activity['end_time']}: {activity['activity']}")
            print(f"      Location: {activity['location']}")
            print(f"      Address: {activity['address']}")
        
        print(f"   Cost: {result.date_plan.estimated_cost}")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Full Day Date
    print("\n🌍 Test 3: Full Day Date (7 hours)")
    preferences = UserPreferences(
        start_time="10:00",
        end_time="17:00",
        start_latitude=1.3521,
        start_longitude=103.8198,
        interests=['food', 'culture', 'nature'],
        budget_tier="$$",
        date_type="romantic"
    )
    
    try:
        result = planner.plan_date(preferences, "full day romantic date with multiple activities")
        print(f"✅ Success! {len(result.date_plan.itinerary)} activities planned")
        
        for i, activity in enumerate(result.date_plan.itinerary, 1):
            print(f"   {i}. {activity['start_time']}-{activity['end_time']}: {activity['activity']}")
            print(f"      Location: {activity['location']}")
            print(f"      Address: {activity['address']}")
        
        print(f"   Cost: {result.date_plan.estimated_cost}")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    print("\n🎉 Quick test completed!")

if __name__ == "__main__":
    quick_test()
