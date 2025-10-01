# 🤖 AI Date Planner - LLM Instructions

## ⚠️ DEPRECATED - This file is no longer in use

**As of the latest update, the AI Date Planner no longer uses LLM-based query parsing.**

### What Changed?

The system previously used **GPT-3.5 Turbo** to parse free-text user queries like:

- "I want a walk and sports"
- "no cultural activities"
- "romantic dinner with museums"

This approach was removed because:

1. **Unpredictable results** - LLM parsing could misinterpret user intent
2. **Cost concerns** - GPT API calls added unnecessary expense
3. **Latency issues** - Extra API call slowed down planning
4. **User confusion** - Free-text input was unclear

### Current System

The system now uses **fixed exclusion checkboxes**:

- **🏃 Sports** - Excludes sports facilities, gyms, tennis courts
- **🎨 Cultural** - Excludes museums, galleries, heritage sites, temples
- **🌳 Nature** - Excludes parks, gardens, nature reserves

**Benefits:**

- ✅ Predictable filtering (no AI misinterpretation)
- ✅ Faster planning (no LLM API call)
- ✅ Lower cost (no GPT usage)
- ✅ Better UX (clear checkboxes)
- ✅ Max 2 exclusions (prevents over-filtering)

### Migration Guide

**Old API Format:**

```json
{
  "user_query": "I want sports but no cultural activities"
}
```

**New API Format:**

```json
{
  "exclusions": ["cultural"]
}
```

**Old Frontend:**

```tsx
<TextInput
  placeholder="Additional requests (e.g., no sports, want cultural)"
  value={userQuery}
/>
```

**New Frontend:**

```tsx
<Checkbox label="Sports" onToggle={handleExclusionToggle} />
<Checkbox label="Cultural" onToggle={handleExclusionToggle} />
<Checkbox label="Nature" onToggle={handleExclusionToggle} />
```

### Related Files

- **LLMQueryParser class** - Removed from `ai_date_planner.py`
- **`llm_query_parser.py`** - Deleted
- **User query parameter** - Removed from API

### See Also

- **AI_DATE_PLANNER_RULES.md** - Current system documentation
- **Frontend: date-planner.tsx** - Exclusion checkboxes implementation
- **Backend: rule_engine.py** - Exclusion filtering logic

---

_This file is kept for historical reference. Refer to AI_DATE_PLANNER_RULES.md for current system documentation._
