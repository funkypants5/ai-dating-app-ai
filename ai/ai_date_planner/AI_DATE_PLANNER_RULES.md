# 🤖 AI Date Planner - Complete System Documentation

## 📋 Overview

The AI Date Planner uses a **hybrid approach** combining:

- **Rule-based filtering** (deterministic exclusions and budget)
- **RAG (Retrieval-Augmented Generation)** (AI-powered semantic search with **70% semantic + 30% proximity**)
- **Fixed exclusion checkboxes** (max 2 exclusions)
- **Date type prioritization** (tailored food and activities for each date type)
- **Diversity sampling** (70 food + 30 non-food locations)

## ✅ Current Status

**🎉 FULLY FUNCTIONAL** - The AI Date Planner is production-ready with:

- ✅ **100% test pass rate** (comprehensive scenarios passing)
- ✅ **Sequential planning** with realistic travel times
- ✅ **Flexible meal durations** that adapt to available time
- ✅ **Smart interest filtering** with food exceptions
- ✅ **Complete address system** (Google Maps ready)
- ✅ **Fixed exclusion system** with max 2 exclusions
- ✅ **75% time usage validation** to ensure full dates
- ✅ **Enhanced breakfast filtering** for appropriate venues
- ✅ **Romantic date type enhancement** for better venue matching

## 🎛️ User Input System

### **Fixed Exclusion Checkboxes (Max 2)**

Users can exclude up to **2 activity types** from their date:

- **🏃 Sports** - Excludes: Gyms, fitness centers, swimming pools, tennis courts, sports stadiums
- **🎨 Cultural** - Excludes: Museums, art galleries, cultural sites, heritage locations, temples, churches, mosques
- **🌳 Nature** - Excludes: Parks, gardens, nature reserves, botanical gardens, scenic viewpoints, zoos

**Important Rules:**

- Maximum 2 exclusions allowed (prevents over-filtering)
- Food venues are **NEVER excluded** (meals always needed)
- Shopping areas are **always included** (not in exclusion list)

### **Required Inputs:**

- `start_time` - When the date begins (HH:MM format)
- `start_latitude` & `start_longitude` - Starting location coordinates (validated)
- `budget_tier` - $, $$, or $$$ (3 tiers)
- `date_type` - casual, romantic, adventurous, cultural
- `interests` - Array of interests (culture, sports, nature, food, etc.)

### **Optional Inputs:**

- `end_time` - When the date ends (defaults to 8 hours after start)
- `exclusions` - Array of exclusions (max 2: "sports", "cultural", "nature")

### **Auto-Detected:**

- `time_of_day` - Automatically detected from start_time:
  - 6:00-12:00 → "morning"
  - 12:00-17:00 → "afternoon"
  - 17:00-21:00 → "evening"
  - 21:00-02:00 → "night"

## 🎯 Core Planning Rules

### 1. **75% Time Usage Validation**

The system ensures at least **75% of requested time** is filled with activities:

- **Validation**: `(total_activity_time / requested_duration) * 100 >= 75%`
- **Applies to**: Dates longer than 2 hours
- **Error if failed**: "Unable to plan sufficient activities for X hours. Try selecting more interests, reducing exclusions, or choosing a shorter duration."
- **Dynamic max activities**: Scales with duration (`max(5, int(duration / 1.0) + 2)`)

**Examples:**

- 2-hour date: No validation (quick dates exempt)
- 4-hour date: Need at least 3 hours of activities
- 8-hour date: Need at least 6 hours of activities
- 8-hour with only breakfast: ❌ Fails validation (12.5% coverage)

### 2. **Time-Based Meal Planning**

The system plans meals based on **actual time windows** with intelligent sequential planning:

#### 🍽️ **Meal Time Windows**

| Meal Type            | Time Window   | Duration  | Cost          | Conditions                                                        |
| -------------------- | ------------- | --------- | ------------- | ----------------------------------------------------------------- |
| **Coffee/Breakfast** | 6:00 - 11:00  | 1.0 hour  | **$10**       | If date starts between 6-11 AM                                    |
| **Coffee Break**     | 14:00 - 16:00 | 1.0 hour  | **$10**       | If date spans 14:00-16:00 AND max 1 coffee break per date         |
| **Lunch**            | 12:00 - 14:00 | 1.5 hours | Budget × 80%  | If date spans lunch time (starts before 12:00, ends after 12:00)  |
| **Dinner**           | 17:00 - 20:00 | 2.0 hours | Budget × 100% | If date spans dinner time (starts before 20:00, ends after 17:00) |
| **Late Dinner**      | 21:00 - 02:00 | 2.0 hours | Budget × 100% | If date starts after 21:00 OR before 2 AM                         |

#### 🎯 **Enhanced Breakfast & Coffee Break Filtering**

**Strict Rules to Prevent Non-Breakfast Venues:**

```python
# POSITIVE: What we WANT for breakfast/coffee
breakfast_keywords = [
    'cafe', 'coffee', 'kopi', 'breakfast', 'brunch', 'bakery',
    'toast', 'western', 'bistro', 'patisserie', 'sandwich', 'bagel',
    'espresso', 'latte', 'cappuccino', 'americano', 'tea house'
]

# NEGATIVE: What we DON'T WANT for breakfast/coffee
non_breakfast_keywords = [
    'korean', 'chinese', 'indian', 'italian', 'french', 'japanese',
    'thai', 'vietnamese', 'malay', 'seafood', 'steakhouse', 'steak',
    'fine dining', 'asian cuisine', 'peranakan', 'vegetarian restaurant',
    'noodles', 'ramen', 'sushi', 'dim sum', 'hotpot', 'bbq', 'grill'
]
```

**Logic (Checks both name AND description):**

1. If has non-breakfast keywords AND no breakfast vibe:
   - If hawker/food court/kopitiam → ✅ Allowed (have breakfast options)
   - Else → ❌ Rejected
2. If has breakfast vibe → ✅ Allowed
3. If hawker/food court/kopitiam → ✅ Allowed
4. Otherwise → ❌ Rejected (conservative approach)

**Critical Safeguard:**

- If NO appropriate breakfast venues found → Use hawker centers as fallback
- If NO hawker centers → Return `None` (don't plan inappropriate meals)
- **Never falls back to full restaurants for breakfast/coffee**

**Examples:**

- ✅ Ya Kun Kaya Toast (has 'toast')
- ✅ Starbucks Coffee (has 'coffee')
- ✅ TWG Tea Salon (has 'tea house')
- ✅ Tiong Bahru Market (hawker center)
- ❌ Jumbo Seafood (has 'seafood', no breakfast vibe)
- ❌ Seoul Yummy Korean (has 'korean', no breakfast vibe)
- ❌ Indian Vegetarian Restaurant (has 'vegetarian restaurant', 'indian')

### **Budget Tiers (3 Tiers)**

| Budget Tier | Breakfast/Coffee | Lunch  | Dinner | Description                                 |
| ----------- | ---------------- | ------ | ------ | ------------------------------------------- |
| **$**       | $10              | $10-15 | $10-15 | Local favorites (hawker centers, kopitiams) |
| **$$**      | $10              | $16-32 | $20-40 | Casual dining (cafes, casual restaurants)   |
| **$$$**     | $10              | $40-56 | $50-70 | Upscale dining (fine restaurants, premium)  |

**Cost Calculation:**

- Breakfast & Coffee Break: **Always $10 per person**
- Lunch: Budget tier × 0.8 (80% of full cost)
- Dinner: Budget tier × 1.0 (full cost)
- **Default budget**: $$ (moderate pricing)

**CRITICAL: Budget ONLY Applies to Food**

- **Food locations**: Filtered by budget tier keywords
- **Attractions**: No budget filter (most are free or low-cost)
- **Activities**: No budget filter (sports facilities usually municipal/free)
- **Heritage**: No budget filter (museums have nominal fees)
- **Cafes**: ALWAYS kept regardless of budget tier (needed for breakfast/coffee)

## 🔍 Filtering Rules

### **Rule-Based Filtering (Step 1)**

1. **Exclusion Filter (First Priority)** - Removes excluded activity types:

   - Checks location name/description against exclusion keywords
   - **NEVER excludes food locations** (meals required)
   - Processed before all other filters

2. **Interest Filter** - Matches user interests:

   - If no interests specified, includes all locations
   - If interests specified, only includes matching locations
   - **Exception**: Food locations always included for meals
   - **Enhancement**: General attractions allowed if they don't match exclusions

3. **Budget Filter** - **ONLY applies to food locations:**

   - **Food locations**: Filtered by budget tier keywords (`upscale`, `premium`, `luxury`, etc.)
   - **Cafes/Coffee shops**: ALWAYS kept regardless of budget (needed for breakfast/coffee)
   - **Attractions/Activities/Heritage**: NO budget filter applied (most are free or low-cost)
   - **Keywords by tier:**
     - `$`: `cheap`, `budget`, `affordable`, `hawker`, `food court`
     - `$$`: `moderate`, `mid-range`, `casual`, `family`
     - `$$$`: `upscale`, `fine dining`, `premium`, `luxury`
   - **Cafe keywords (always kept)**: `cafe`, `coffee`, `kopi`, `bistro`, `bakery`, `patisserie`, `espresso`, `starbucks`, `toast`

4. **Time Filter** - Very lenient - only excludes locations that explicitly conflict

5. **Date Type Filter** - Enhanced for romantic dates:
   - **Romantic**: Excludes child-focused venues
   - **Cultural**: Excludes child-focused venues
   - All types: Age-appropriate filtering

### **RAG-Based Relevance (Step 2)**

- Uses **FAISS index** for fast semantic similarity search (k=200)
- **Graceful fallback** to cosine similarity if FAISS unavailable
- Combines **70% semantic relevance** + **30% proximity score** (prioritizes quality over convenience)
- Returns top **100** most relevant locations via diversity sampling
- **Diversity sampling**: Ensures 70 food + 10 attractions + 10 activities + 10 heritage minimum
- **Why?** Prevents RAG from returning 99 food + 1 attraction (was happening before)

### **Date Type Differentiation (3-Layer System)**

The system uses **THREE layers** to differentiate date types:

**Layer 1: RAG Semantic Search** (affects ALL locations)

- Each date type has rich keyword descriptions added to query
- RAG finds semantically similar venues

**Layer 2: Food Re-Ranking via RAG Semantic Similarity** (affects food locations only)

- After RAG, food venues are re-scored using **semantic similarity** to date type vibe
- Generates date-type-specific query embedding and compares to venue embeddings
- Captures "vibe" even without exact keywords (e.g., "sunset views" matches romantic without the word "romantic")

**Layer 3: Activity Selection** (affects non-food locations)

- Adventurous → Prioritizes sports (max 1) + nature walks
- Cultural → Prioritizes heritage sites + museums
- Romantic/Casual → Standard RAG-driven selection

### **Date Type Characteristics Summary:**

| Date Type       | Food Re-Ranking Query (RAG Semantic)                                                                  | Activity Priority                                   | Expected Venues                                                        | Max Sports |
| --------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------- | ---------- |
| **Casual**      | "casual relaxed friendly comfortable laid-back bistro cafe food court family-friendly"                | Standard flow                                       | Bistros, cafes, casual restaurants, shopping                           | 1          |
| **Romantic**    | "romantic intimate cozy candlelit elegant fine dining rooftop waterfront scenic wine couple-friendly" | Standard flow                                       | Fine dining, rooftop bars, waterfront, scenic walks                    | 1          |
| **Adventurous** | "outdoor adventure unique fusion experimental street food hawker food market outdoor seating"         | **1. Sports (max 1)** <br> **2. Nature walks**      | Hawker centers, fusion food, tennis/swimming + nature walks            | 1          |
| **Cultural**    | "traditional heritage cultural authentic peranakan historical traditional ambiance art cafe"          | **1. Heritage sites** <br> **2. Museums/galleries** | Peranakan food, traditional cuisine, museums, temples, heritage trails | 1          |

**How Re-Ranking Works:**

- Generate embedding for date type query (e.g., "romantic intimate cozy candlelit...")
- Compare to each food venue's embedding using cosine similarity
- Rank by similarity score (venues with romantic "vibe" rank higher, even without keyword "romantic")
- Example: "Sunset Bar with Panoramic Views" → High similarity to romantic query ✅

## ⏰ Travel Time & Timing System

### **Travel Time Calculation:**

The system calculates **realistic travel time** between locations:

- **Distance Calculation**: Uses Haversine formula
- **Speed Assumption**: 30 km/h average in Singapore (traffic + public transport)
- **Travel Time Range**: 6 minutes to 1 hour (capped for realism)
- **Default Fallback**: 15 minutes if coordinates missing
- **Formula**: `travel_time = max(0.1, min(distance_km / 30.0, 1.0))` hours

**Examples:**

- 0.5 km away → **6 minutes** (minimum)
- 15 km away → **30 minutes**
- 45 km away → **1 hour** (maximum)

### **Timing Format:**

```
• 10:00-11:00: Coffee/Breakfast at Ya Kun Kaya Toast
• 11:06-13:06: Morning Walk at MacRitchie Reserve (6 min travel)
• 13:12-14:42: Lunch at Hawker Center (6 min travel)
```

## 📍 Location Validation

### **Starting Location Requirement:**

- **Frontend Validation**: Checks if coordinates are present before submission
- **Backend Validation**: Throws error if coordinates are null/undefined
- **User Feedback**: "Starting location is required. Please select a location in Singapore..."
- **Geocoding**: OpenCage API with Singapore-specific filtering

### **Singapore-Specific Geocoding:**

```typescript
// Always append "Singapore" to queries
searchQuery = query.includes("Singapore") ? query : `${query}, Singapore`;

// Filter results
params: {
  countrycode: 'sg',
  bounds: '103.6,1.15,104.0,1.47'  // Singapore boundaries
}

// Verify results
if (result.components.country_code === 'sg')
```

## 🔧 Hardcoded Elements

### **Activity Types:**

#### ✅ **Dynamic Activity Types:**

- **Shopping** - Based on keywords: shopping, mall, orchard road, boutique, retail
- **Walk** - Based on keywords: walk, park, nature, reserve, garden, trail
- **Cultural Visit** - Based on keywords: museum, gallery, art, heritage, temple, church
- **Attraction Visit** - Default for general attractions

**Enhanced Logic:**

```python
def _get_attraction_activity_type(location, exclude_nature, exclude_cultural):
    # Check nature keywords
    if has_nature_keywords:
        return None if exclude_nature else 'Walk'

    # Check cultural keywords
    if has_cultural_keywords:
        return None if exclude_cultural else 'Cultural Visit'

    # Check shopping keywords
    if has_shopping_keywords:
        return 'Shopping'  # Always allowed

    # Default: general attraction
    return 'Attraction Visit'
```

#### ❌ **Hardcoded Activity Types:**

- `"Coffee/Breakfast"` - For 6:00-11:00 time window ($10 fixed)
- `"Coffee Break"` - For 14:00-16:00 time window ($10 fixed)
- `"Lunch"` - For 12:00-14:00 time window (budget × 0.8)
- `"Dinner"` - For 17:00-20:00 time window (budget × 1.0)
- `"Late Dinner"` - For 21:00-02:00 time window (budget × 1.0)

## 🎯 What to Expect

### **Input:**

```json
{
  "start_time": "10:00",
  "end_time": "18:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "culture", "nature"],
  "budget_tier": "$$",
  "date_type": "romantic",
  "exclusions": ["sports"]
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
      "location": "Ya Kun Kaya Toast",
      "address": "Block 123, Main Street, Singapore",
      "type": "food",
      "duration": 1.0,
      "description": "Start your day with traditional kaya toast..."
    },
    {
      "start_time": "11:06",
      "end_time": "13:06",
      "activity": "Morning Walk",
      "location": "MacRitchie Reservoir",
      "address": "MacRitchie Reservoir Park",
      "type": "attraction",
      "duration": 2.0,
      "description": "Enjoy a peaceful walk..."
    }
  ],
  "estimated_cost": "$46-78 per person",
  "duration": 8.0,
  "summary": "Romantic 8-hour date with food, nature, and activities"
}
```

## 🚀 Usage Examples

### **Sample 1: Morning Coffee Date with Max Exclusions**

```json
{
  "start_time": "09:00",
  "end_time": "12:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "nature"],
  "budget_tier": "$",
  "date_type": "casual",
  "exclusions": ["sports", "cultural"]
}
```

**Expected Output:**

- Breakfast at cafe ($10) - Early-opening (not Hoshino)
- Nature walk (sports/cultural excluded by user)
- Total: 3 hours, $10 per person (attractions are free)

### **Sample 2: Romantic Evening Date**

```json
{
  "start_time": "18:00",
  "end_time": "22:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "culture"],
  "budget_tier": "$$$",
  "date_type": "romantic",
  "exclusions": []
}
```

**Expected Output:**

- Romantic dinner at rooftop/waterfront restaurant ($50-70) - Re-ranked #1 by keywords
- Scenic walk or shopping (RAG prioritizes scenic/beautiful)
- Total: 4 hours, $50-70 per person (activities are free)

### **Sample 3: Full Day Date (8 hours)**

```json
{
  "start_time": "10:00",
  "end_time": "18:00",
  "start_latitude": 1.3521,
  "start_longitude": 103.8198,
  "interests": ["food", "culture", "nature"],
  "budget_tier": "$$",
  "date_type": "casual",
  "exclusions": ["sports"]
}
```

**Expected Output:**

- Breakfast at cafe ($10) - Not Toast Box/Ya Kun (reserved for breakfast only)
- Morning activity (shopping, walk, or cultural - based on date type)
- Lunch at restaurant ($16-32) - Not breakfast-only places
- Afternoon activity (based on date type priority)
- Coffee break at cafe ($10)
- Evening activity (final activity may be extended to hit 75% coverage)
- Dinner at restaurant ($20-40) - Date type appropriate
- Total: 8 hours, $56-92 per person (only food costs, activities free)

## ⚠️ Validation & Error Handling

### **Frontend Validation:**

- ✅ All required fields filled before "Plan Our Date" button enabled
- ✅ Location coordinates present (from geocoding)
- ✅ Max 2 exclusions enforced (alert shown if user tries to select 3rd)
- ✅ Time validation (end time after start time)

### **Backend Validation:**

- ✅ Location coordinates required (throws error if missing)
- ✅ 75% time usage validation (throws error if insufficient activities)
- ✅ Interest/exclusion conflict resolution
- ✅ Budget tier validation ($, $$, or $$$)

### **Error Messages:**

```
❌ "Location Required" - No coordinates provided
❌ "Maximum Exclusions Reached" - User tried to select 3+ exclusions
❌ "Unable to plan sufficient activities for 8.0 hours" - 75% validation failed
```

## 📊 System Features & Recent Changes

### **Key Features:**

1. ✅ **RAG Scoring**: 70% semantic relevance, 30% proximity (prioritizes quality)
2. ✅ **Diversity Sampling**: 70 food + 30 non-food minimum (prevents food-only results)
3. ✅ **Date Type Prioritization**: 3-layer system (RAG + food re-rank + activity selection)
4. ✅ **Max 1 Sports Activity**: Walks unlimited, sports limited
5. ✅ **Meal-Specific Filtering**: Breakfast-only excluded from lunch/dinner
6. ✅ **Late-Opening Filter**: Hoshino Coffee avoided for early breakfast
7. ✅ **Budget Scope**: ONLY food (attractions/activities/heritage always included)
8. ✅ **Auto-Extension**: Last activity extended to meet 75% coverage
9. ✅ **Address Format**: `Blk X Street, #floor-unit, Singapore postal`
10. ✅ **Interest Filter**: Always keeps attractions/activities/heritage (RAG prioritizes)
11. ✅ **Max 2 Exclusions**: Prevents over-filtering
12. ✅ **Location Validation**: Frontend and backend coordinate checks

### **Future Improvements:**

1. **Real-time integration** - Connect to live restaurant/event APIs
2. **Multi-city support** - Expand beyond Singapore
3. **Real-time traffic data** - Integrate with Google Maps API
4. **Transport mode selection** - Walking, driving, or public transport
5. **Weather integration** - Adjust outdoor activities based on forecast
6. **User feedback loop** - Learn from user preferences over time

---

_This documentation reflects the current state of the AI Date Planner as of the latest updates. The system is production-ready and fully functional._
