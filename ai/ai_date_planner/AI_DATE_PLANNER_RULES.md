# 🤖 AI Date Planner - Rules & Considerations

## 📋 Overview

The AI Date Planner uses a **hybrid approach** combining:

- **Rule-based filtering** (deterministic)
- **RAG (Retrieval-Augmented Generation)** (AI-powered semantic search)
- **LLM integration** (Gemini for natural language output)

## 🎯 Core Planning Rules

### 1. **Duration-Based Activity Planning**

The system automatically suggests different numbers of activities based on date duration:

| Duration     | Activities     | Rules                                                                    |
| ------------ | -------------- | ------------------------------------------------------------------------ |
| **3+ hours** | 2 activities   | Basic food + 1 attraction/activity                                       |
| **4+ hours** | 3 activities   | Basic food + attraction + coffee break                                   |
| **6+ hours** | 3-4 activities | Basic food + attraction + coffee break + additional cultural/nature spot |

### 2. **Time-Based Meal Planning**

The system plans meals based on **actual time windows** with intelligent sequential planning:

#### 🍽️ **Meal Time Windows**

| Meal Type            | Time Window   | Duration  | Conditions                                                        |
| -------------------- | ------------- | --------- | ----------------------------------------------------------------- |
| **Coffee/Breakfast** | 6:00 - 11:00  | 1.0 hour  | If date starts between 6-11 AM                                    |
| **Lunch**            | 12:00 - 14:00 | 1.5 hours | If date spans lunch time (starts before 12:00, ends after 12:00)  |
| **Coffee Break**     | 14:00 - 16:00 | 1.0 hour  | If date spans 14:00-16:00 AND max 1 coffee break per date         |
| **Dinner**           | 17:00 - 20:00 | 2.0 hours | If date spans dinner time (starts before 20:00, ends after 17:00) |
| **Late Dinner**      | 21:00 - 02:00 | 2.0 hours | If date starts after 21:00 OR before 2 AM                         |

#### 🎯 **Smart Meal Logic**

- **Sequential planning** - Activities planned one after another with travel time
- **Flexible durations** - Meal durations adapt to available time (minimum 30 minutes)
- **Meal prioritization** - Meals are prioritized over activities when time windows align
- **Travel time integration** - Realistic travel time calculated between all locations
- **Coffee break limits** - Maximum 1 coffee break per date to prevent duplicates

#### 📅 **Example Scenarios**

- **7:00-10:00 (3 hours):** Coffee/Breakfast + Activities (no lunch - doesn't span 12:00-14:00)
- **9:00-13:00 (4 hours):** Coffee/Breakfast + Activities + Lunch (spans 12:00-14:00, lunch duration adapts to 0.6 hours)
- **14:00-17:00 (3 hours):** Lunch + Coffee Break (spans lunch and coffee break windows)
- **15:00-19:00 (4 hours):** Activities + Dinner (spans 17:00-20:00)
- **18:00-21:00 (3 hours):** Dinner + Activities (spans 17:00-20:00)
- **10:00-18:00 (8 hours):** Coffee/Breakfast + Activities + Lunch + Coffee Break + Activities (no dinner - doesn't span 17:00-20:00)
- **9:00-19:00 (10 hours):** Coffee/Breakfast + Activities + Lunch + Coffee Break + Activities (no dinner - doesn't span 17:00-20:00)
- **21:00-01:00 (4 hours):** Late Dinner + Activities (Late Dinner for night dates)
- **14:00-21:00 (7 hours):** Lunch + Coffee Break + Sports + Dinner (perfect sports date with all meals)

## 🔧 Hardcoded Elements

### **Activity Types (Partially Hardcoded)**

#### ✅ **Dynamic Activity Types:**

- **Sports Activity** - Based on location analysis (swimming, tennis, fitness, etc.)
- **Swimming** - For swimming pools/aquatic centers
- **Tennis** - For tennis courts
- **Fitness** - For gyms/fitness centers
- **Sports** - For stadiums/fields

#### ❌ **Hardcoded Activity Types:**

- `"Coffee/Breakfast"` - For 6:00-11:00 time window
- `"Lunch"` - For 11:00-15:00 time window
- `"Dinner"` - For 17:00-22:00 time window
- `"Late Dinner"` - For 21:00-02:00 time window
- `"Coffee Break"` - For 14:00-17:00 time window
- `"Walk"` - For park/nature attractions
- `"Cultural Visit"` - For museums/galleries
- `"Sports Activity"` - For sports facilities (dynamically categorized)

### **Duration Times (Flexible)**

| Activity Type    | Duration      | Time Window | Notes                                              |
| ---------------- | ------------- | ----------- | -------------------------------------------------- |
| Coffee/Breakfast | 1.0 hours     | 6:00-11:00  | Fixed                                              |
| Lunch            | 1.5 hours     | 12:00-14:00 | **Flexible** - adapts to available time (min 0.5h) |
| Dinner           | 2.0 hours     | 17:00-20:00 | Fixed                                              |
| Late Dinner      | 2.0 hours     | 21:00-02:00 | Fixed                                              |
| Coffee Break     | 1.0 hours     | 14:00-16:00 | Fixed                                              |
| Walk             | 0.5-2.0 hours | Any time    | Variable based on available time                   |
| Cultural Visit   | 0.5-3.0 hours | Any time    | Variable based on available time                   |
| Sports Activity  | 1.0-4.0 hours | Any time    | Variable based on available time                   |

### **Activity Sequencing (Dynamic)**

The system now uses **flexible sequencing** based on time windows:

1. **Food always comes first** (breakfast/lunch/dinner)
2. **Attractions come second** (walks, museums, parks)
3. **Activities come last** (sports, entertainment)

### **Budget Tiers (Hardcoded)**

| Budget Tier | Price Range         | Keywords                                       |
| ----------- | ------------------- | ---------------------------------------------- |
| `$`         | $20-$40 per person  | "budget", "affordable", "cheap", "casual"      |
| `$$`        | $40-$70 per person  | "moderate", "mid-range", "casual", "family"    |
| `$$$`       | $70-$100 per person | "upscale", "fine dining", "premium", "luxury"  |
| `$$$$`      | $100+ per person    | "high-end", "exclusive", "gourmet", "michelin" |

## 🎛️ User Input Considerations

### **Required Inputs:**

- `start_time` - When the date begins (HH:MM format)
- `start_latitude` & `start_longitude` - Starting location coordinates
- `budget_tier` - $, $$, $$$, or $$$$

### **Optional Inputs:**

- `end_time` - When the date ends (defaults to 4 hours after start)
- `interests` - Array of interests (defaults to ['food', 'culture', 'nature'])
- `date_type` - casual, romantic, adventurous, cultural (defaults to 'casual')
- `preferred_location_types` - Array of types (defaults to all types)

### **Auto-Detected:**

- `time_of_day` - Automatically detected from start_time:
  - 6:00-12:00 → "morning"
  - 12:00-17:00 → "afternoon"
  - 17:00-21:00 → "evening"
  - 21:00-02:00 → "night"

## 🔍 Filtering Rules

### **Rule-Based Filtering (Step 1)**

1. **Location Type Filter** - Filters by preferred types (food, attraction, activity, heritage)
2. **Interest Filter** - **Smart filtering** - If no interests specified, includes all locations. If interests specified, only includes matching locations (except food locations which are always included for meals)
3. **Budget Filter** - Filters by budget tier keywords
4. **Time Filter** - **Very lenient** - only excludes locations that explicitly conflict
5. **Date Type Filter** - **Very lenient** - only excludes locations that explicitly conflict

### **RAG-Based Relevance (Step 2)**

- Uses **Sentence-BERT embeddings** for semantic similarity
- Combines **70% semantic relevance** + **30% proximity score**
- Returns top 50 most relevant locations

### **Proximity Scoring**

- Calculates distance from `start_latitude`/`start_longitude`
- Uses **Haversine formula** for accurate distance calculation
- Scores range from 0-1 (higher = closer)

## 📍 Address System

### **Address Formatting:**

#### **Sports Facilities:**

```
"21, Evans Road, Singapore 259366"
```

#### **Restaurants:**

```
"Block 123, Main Street, #01-01, Singapore"
```

#### **Tourist Attractions:**

```
"MacRitchie Reservoir Park"
```

### **Address Sources:**

- **GeoJSON files** - Extracted from HTML description tables
- **KML files** - Extracted from ExtendedData fields
- **Restaurant data** - Built from BLK_HOUSE + STR_NAME + UNIT_NO

## ⏰ Travel Time & Timing System

### **Travel Time Calculation:**

The system now calculates **realistic travel time** between locations:

- **Distance Calculation**: Uses Haversine formula for accurate distance
- **Speed Assumption**: 30 km/h average in Singapore (including traffic/public transport)
- **Travel Time Range**: 6 minutes to 1 hour (capped for realism)
- **Default Fallback**: 15 minutes if coordinates missing

### **Timing Format:**

#### **Before (Unclear):**

```
• 10:00: Coffee/Breakfast at Restaurant
• 11:00: Morning Walk at Park
```

#### **After (Clear Start/End Times):**

```
• 10:00-11:00: Coffee/Breakfast at Restaurant
• 11:06-13:06: Morning Walk at Park (6 min travel time included)
```

### **Travel Time Examples:**

- **Same area**: 6-10 minutes travel time
- **Different districts**: 15-30 minutes travel time
- **Cross-island**: 30-60 minutes travel time

### **Real Examples from the System:**

#### **Morning Coffee Date (3 hours):**

```
• 09:00-10:00: Coffee/Breakfast at HUA FONG KEE FOOD COURT PTE LTD
• 10:06-12:06: Morning Walk at MacRitchie Singapore & Singapore Nature Reserve
  (6 minutes travel time from food court to nature reserve)
```

#### **Full Day Date (7 hours):**

```
• 10:00-11:00: Coffee/Breakfast at AH SIN FAMILY EATING HOUSE
• 11:06-13:06: Morning Walk at MacRitchie Singapore & Singapore Nature Reserve
  (6 minutes travel time from restaurant to nature reserve)
• 13:12-17:12: Light Activity at Co Curricular Activities Branch
  (6 minutes travel time from nature reserve to sports center)
```

### **Technical Implementation:**

- **Haversine Formula**: Accurate distance calculation between coordinates
- **Singapore-Specific**: 30 km/h average speed (realistic for traffic + public transport)
- **Fallback Handling**: 15 minutes default if coordinates missing
- **Time Capping**: Maximum 1 hour travel time (prevents unrealistic estimates)
- **Automatic Calculation**: No manual input needed - system calculates everything

### **Key Benefits:**

1. **Realistic Timing**: No more impossible back-to-back activities
2. **Clear Communication**: Users know exactly when each activity starts and ends
3. **Google Maps Ready**: Travel times are realistic for Singapore
4. **Automatic**: No manual input needed - system calculates everything
5. **Flexible**: Works for any location combination

## 🎯 What to Expect

### **Input:**

```json
{
  "start_time": "10:00",
  "end_time": "17:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "culture", "nature"],
  "budget_tier": "$$",
  "date_type": "romantic"
}
```

### **Output:**

```json
{
  "itinerary": [
    {
      "start_time": "10:00",
      "end_time": "11:00",
      "activity": "Coffee/Breakfast",
      "location": "AH SIN FAMILY EATING HOUSE",
      "address": "Block 123, Main Street, Singapore",
      "type": "food",
      "duration": 1.0,
      "description": "Start your day with..."
    },
    {
      "start_time": "11:06",
      "end_time": "13:06",
      "activity": "Morning Walk",
      "location": "MacRitchie Singapore & Singapore Nature Reserve",
      "address": "MacRitchie Reservoir Park",
      "type": "attraction",
      "duration": 2.0,
      "description": "Enjoy a peaceful walk at..."
    }
  ],
  "estimated_cost": "$70-$100 per person",
  "duration": 7.0,
  "summary": "Romantic 7-hour date with food, nature, and activities"
}
```

## ⚠️ Limitations

### **Current Limitations:**

1. **Fixed activity sequencing** - Cannot customize order
2. **Hardcoded durations** - Cannot adjust time per activity
3. **Limited activity types** - Some types are hardcoded
4. **No real-time data** - Uses static location database
5. **Singapore only** - Location data is Singapore-specific
6. **Basic travel time** - Uses average speed, not real-time traffic data

### **Future Improvements:**

1. **Dynamic activity types** - Analyze restaurant types for better categorization
2. **Flexible sequencing** - Allow custom activity orders
3. **Dynamic durations** - Base duration on location type and user preferences
4. **Real-time integration** - Connect to live restaurant/event APIs
5. **Multi-city support** - Expand beyond Singapore
6. **Real-time traffic data** - Integrate with Google Maps API for accurate travel times
7. **Transport mode selection** - Allow users to choose walking, driving, or public transport

## 🧪 Comprehensive Test Scenarios

The AI Date Planner has been thoroughly tested with 15 different scenarios covering all major use cases:

### **Time-Based Test Scenarios:**

#### **Morning Dates:**

1. **Early Morning (7:00-10:00)** - 3 hours

   - **Expected**: Coffee/Breakfast + Activities
   - **Meals**: 1 (Coffee/Breakfast only - doesn't span lunch time)

2. **Morning to Afternoon (9:00-13:00)** - 4 hours
   - **Expected**: Coffee/Breakfast + Lunch + Activities
   - **Meals**: 2 (spans lunch time 12:00-14:00)

#### **Afternoon Dates:**

3. **Afternoon Only (14:00-17:00)** - 3 hours

   - **Expected**: Activities only
   - **Meals**: 0 (doesn't span any meal times)

4. **Afternoon to Evening (15:00-19:00)** - 4 hours
   - **Expected**: Activities + Dinner
   - **Meals**: 1 (spans dinner time 17:00-19:30)

#### **Evening Dates:**

5. **Evening Only (18:00-21:00)** - 3 hours

   - **Expected**: Dinner + Activities
   - **Meals**: 1 (spans dinner time 17:00-19:30)

6. **Evening to Night (19:00-23:00)** - 4 hours
   - **Expected**: Dinner + Activities
   - **Meals**: 1 (spans dinner time 17:00-19:30)

#### **Night Dates:**

7. **Night Only (21:00-00:00)** - 3 hours

   - **Expected**: Late Dinner + Activities
   - **Meals**: 1 (Late Dinner for night dates)

8. **Night to Early Morning (22:00-02:00)** - 4 hours
   - **Expected**: Late Dinner + Activities
   - **Meals**: 1 (Late Dinner for night dates)

#### **Full Day Dates:**

9. **Full Day (10:00-18:00)** - 8 hours

   - **Expected**: Coffee/Breakfast + Lunch + Coffee Break + Activities
   - **Meals**: 3 (spans breakfast and lunch, but not dinner)

10. **Extended Day (9:00-19:00)** - 10 hours
    - **Expected**: Coffee/Breakfast + Lunch + Coffee Break + Activities
    - **Meals**: 3 (spans breakfast and lunch, but not dinner)

### **Budget Test Scenarios:**

11. **Low Budget ($)** - Budget-friendly options

    - **Price Range**: $20-$40 per person
    - **Keywords**: "budget", "affordable", "cheap", "casual"

12. **High Budget ($$$$)** - Luxury options
    - **Price Range**: $100+ per person
    - **Keywords**: "high-end", "exclusive", "gourmet", "michelin"

### **Interest Test Scenarios:**

13. **Sports Focused** - Activity and food interests

    - **Focus**: Sports facilities, active pursuits
    - **Activities**: Swimming, tennis, fitness, sports

14. **Culture Focused** - Culture and food interests
    - **Focus**: Museums, galleries, cultural sites
    - **Activities**: Cultural visits, museum tours

### **Edge Case Scenarios:**

15. **Very Short Date (12:00-14:00)** - 2 hours
    - **Expected**: Lunch + Activities
    - **Meals**: 1 (spans lunch time 12:00-14:00)

## ✅ Test Validation Rules

The test suite validates the following aspects of each date plan:

### **Meal Planning Validation:**

- ✅ **Correct meal types** - Coffee/Breakfast, Lunch, Dinner, Late Dinner, Coffee Break
- ✅ **Proper meal timing** - Meals planned only when date spans meal time windows
- ✅ **Meal sequencing** - Food activities come before other activities
- ✅ **Realistic durations** - 1-2 hours for meals, appropriate for activity type

### **Activity Sequencing Validation:**

- ✅ **Food first** - Meals always come before activities
- ✅ **Attractions second** - Walks, museums, parks after meals
- ✅ **Activities last** - Sports, entertainment after attractions
- ✅ **Logical flow** - Activities make sense for the time of day

### **Timing Validation:**

- ✅ **Start/End times** - Clear timing format (HH:MM-HH:MM)
- ✅ **Travel time** - Realistic gaps between activities (6-60 minutes)
- ✅ **Duration accuracy** - Total duration matches requested duration
- ✅ **No time conflicts** - Activities don't overlap

### **Address Validation:**

- ✅ **Complete addresses** - Google Maps ready format
- ✅ **Address format** - Proper Singapore address format
- ✅ **No missing addresses** - All locations have addresses
- ✅ **Address consistency** - Consistent formatting across all locations

### **Budget Validation:**

- ✅ **Budget filtering** - Appropriate cost ranges for budget tier
- ✅ **Cost estimation** - Realistic per-person costs
- ✅ **Budget consistency** - All activities match budget tier

### **Interest Validation:**

- ✅ **Smart interest matching** - If no interests specified, all activities included. If interests specified, only matching activities included
- ✅ **Food exception** - Food locations are always included (needed for meals)
- ✅ **Location type filtering** - Correct activity types selected based on interests
- ✅ **Relevance scoring** - Activities are relevant to user query and interests

### **Test Success Criteria:**

- **100% test pass rate** - All 15 scenarios must pass
- **No missing meals** - Expected meals must be present
- **No missing activities** - Expected activity types must be present
- **Proper timing** - All activities have valid start/end times
- **Complete addresses** - All locations have addresses
- **Realistic costs** - Cost estimates match budget tier

## 🧪 Testing & Configuration

### **Running Tests:**

#### **Quick Test (Recommended for Development):**

```bash
cd ai-dating-app-ai
python tests/quick_test.py
```

#### **Full Test Suite (Comprehensive):**

```bash
cd ai-dating-app-ai
python tests/test_date_planner.py
```

### **Test Configuration:**

#### **Default Test Location:**

- **Latitude:** 1.3521 (Singapore city center)
- **Longitude:** 103.8198 (Singapore city center)

#### **Test Budget Tiers:**

- **$** - $20-$40 per person
- **$$** - $40-$70 per person
- **$$$** - $70-$100 per person
- **$$$$** - $100+ per person

#### **Test Interests:**

- **food** - Restaurants, cafes, food courts
- **culture** - Museums, galleries, cultural sites
- **nature** - Parks, nature reserves, outdoor activities
- **activity** - Sports, entertainment, active pursuits

### **Test Output Examples:**

#### **Success Example:**

```
🧪 Testing: Morning Coffee Date
   Time: 09:00 - 12:00
   Duration: 3.0 hours
   Budget: $
   Type: casual
   ✅ PASSED: All validations passed! 2 activities planned

📋 Detailed Results for Morning Coffee Date:
   Total Duration: 3.0 hours
   Estimated Cost: $20-$40 per person
   Activities: 2

🗓️ Itinerary:
   1. 09:00-10:00 | Coffee/Breakfast
      Location: HUA FONG KEE FOOD COURT PTE LTD
      Address: Address not available
      Duration: 1.0 hours
   2. 10:06-12:06 | Morning Walk
      Location: MacRitchie Singapore & Singapore Nature Reserve
      Address: MacRitchie Reservoir Park
      Duration: 2.0 hours
```

#### **Failure Example:**

```
🧪 Testing: Evening Date
   ❌ FAILED: Issues found: Missing expected meal: Dinner, No travel time detected
```

### **Test Results Generated:**

- **Console output** with real-time results
- **JSON results file** with timestamp (e.g., `test_results_20241225_120000.json`)
- **Success/failure summary** with statistics
- **Detailed validation** for each test case

### **Troubleshooting Common Issues:**

#### **"No activities planned":**

- Check if embeddings are generated
- Verify data files are present
- Check budget filtering (might be too restrictive)

#### **"Missing addresses":**

- Some locations may not have complete address data
- This is expected for some test cases

#### **"No travel time detected":**

- Activities might be at the same location
- Travel time calculation might need adjustment

### **Setup Requirements:**

- AI Date Planner must be initialized
- Embeddings must be generated (`setup_date_planner_embeddings.py`)
- Data files must be present in `ai/ai_date_planner/data/`

### **Adding New Tests:**

To add a new test scenario:

1. **Add test case** in `test_date_planner.py`:

```python
tester.run_test(
    "Your Test Name",
    preferences,
    "user query",
    ["expected", "meals"],
    ["expected", "activity", "types"]
)
```

2. **Update validation** if needed in `validate_result()` method

3. **Run test** to verify it works correctly

### **Test Goals:**

The test suite ensures:

- ✅ **Reliability** - Consistent results across different scenarios
- ✅ **Accuracy** - Correct meal and activity planning
- ✅ **Completeness** - All required information is provided
- ✅ **Realism** - Travel times and costs are realistic
- ✅ **Flexibility** - Works with different time ranges and preferences

## 🚀 Usage Examples

### **Quick Coffee Date (3 hours):**

- **Input**: 09:00-12:00, $ budget
- **Output**:
  ```
  • 09:00-10:00: Coffee/Breakfast at HUA FONG KEE FOOD COURT PTE LTD
  • 10:06-12:06: Morning Walk at MacRitchie Singapore & Singapore Nature Reserve
  ```
- **Travel Time**: 6 minutes between locations

### **Full Day Date (7 hours):**

- **Input**: 10:00-17:00, $$ budget
- **Output**:
  ```
  • 10:00-11:00: Coffee/Breakfast at AH SIN FAMILY EATING HOUSE
  • 11:06-13:06: Morning Walk at MacRitchie Singapore & Singapore Nature Reserve
  • 13:12-17:12: Light Activity at Co Curricular Activities Branch
  ```
- **Travel Time**: 6 minutes between each location

### **Romantic Evening (4 hours):**

- **Input**: 18:00-22:00, $$$ budget
- **Output**:
  ```
  • 18:00-20:00: Dinner at JUMBO PREMIUM SEAFOOD
  • 20:06-22:06: Sunset Walk at MacRitchie Singapore & Singapore Nature Reserve
  • 22:12-23:12: Sports Activity at Co Curricular Activities Branch
  ```
- **Travel Time**: 6 minutes between each location

## 🧪 Sample API Inputs for Swagger Testing

Here are 3 sample inputs you can copy and paste into Swagger to test the AI Date Planner:

### **Sample 1: Morning Coffee Date (3 hours)**

```json
{
  "start_time": "09:00",
  "end_time": "12:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "nature"],
  "budget_tier": "$",
  "date_type": "casual",
  "user_query": "casual morning coffee and nature walk"
}
```

### **Sample 2: Romantic Evening Date (4 hours)**

```json
{
  "start_time": "18:00",
  "end_time": "22:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "culture"],
  "budget_tier": "$$$",
  "date_type": "romantic",
  "user_query": "romantic dinner with city views and cultural activity"
}
```

### **Sample 3: Full Day Adventure (8 hours)**

```json
{
  "start_time": "10:00",
  "end_time": "18:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "nature", "sports"],
  "budget_tier": "$$",
  "date_type": "adventurous",
  "user_query": "full day adventure with multiple activities and meals"
}
```

---

_This documentation covers the current state of the AI Date Planner. Rules and hardcoded elements may change as the system evolves._
