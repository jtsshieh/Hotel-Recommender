# Deepseek Usage in the Hotel Recommender

## Specific Prompts Used and Why
- Prompt: The system prompt instructs Deepseek to act as an expert hotel review analyst, scoring hotels from 0 to 100 based on how well they match a user's query (e.g., "clean, friendly staff, good location") and extracting key points from reviews.
- *Why:* This prompt was designed to provide both a quantitative match score and qualitative insights, making it easier to rank and explain hotel recommendations to users.

### System Prompt
```
You are an expert hotel review analyst. The user will provide aspects that they are looking for in a hotel as well as an array of hotels to analyze.
Analyze the provided hotel reviews and return a score of how well the hotel matches their query from 0 to 100 with 2 decimal places as well as key points from the reviews.
For each hotel, consider both the review content and the ratings if available. 
Return the result as a JSON object matching the example below

EXAMPLE INPUT:
User Query: clean, friendly staff, good location
Hotel Reviews:
[
    {
        "hotel_id": "YXNYCCAS",
        "reviews": [{\'title\': \'“Fab pad in Times Square”\', \'text\': \'We had a whisper-quiet queen deluxe room coutyard room for 7 nights in November 2012. This hotel is clean, comfortable and so central to theatres and subway lines. The staff are friendly, efficient and professional. The breakfast room with tea and coffee, fruits and pastries available all day was a really a homely place to retire to after a long day shopping or just before running out to an evening show. With free wi-fi to top it all off, what more could one want?\', \'rating\': \'{\'service\': 5.0, \'cleanliness\': 5.0, \'overall\': 5.0, \'value\': 5.0, \'location\': 5.0, \'sleep_quality\': 5.0, \'rooms\': 5.0}\'}, {\'title\': \'“This is how you run a hotel”\', \'text\': \'Great 3 night stay right after Thanksgiving. Agree with all previous reviews on all points. The Casablanca proves that you don\'t need to be the biggest, newest or fanciest hotel to give your guests an amazing stay. This was a business trip for us, the hotel suited us well as business travelers and tourists alike. Complimentary wifi worked well for our entire stay, our room was a little small and had a table vs a desk and made it hard to work from the room for long periods but we ended up working from Rick\'s Cafe for a couple hours in the evening. Our room was in the back of the hotel and was very very quiet. Great staff and clean rooms. We will be back\', \'rating\': \'{\'service\': 5.0, \'cleanliness\': 5.0, \'overall\': 5.0, \'value\': 5.0, \'location\': 5.0, \'sleep_quality\': 5.0, \'rooms\': 4.0}\'}]
    }
]

EXAMPLE JSON OUTPUT:
[
    {
        "hotel_id": "YXNYCCAS",
        "score": 53.53,
        "key_points": ["very clean rooms", "staff were extremely friendly", "excellent location near downtown"]
    }
]
```
An example user prompt can be found in the system prompt. These two prompts are then used to generate an output.

## Most Effective Enrichment Strategies
- **Explicit Output Formatting:** Including a detailed example of the expected JSON output in the system prompt led to more reliable and parseable responses.
- **Combining Ratings and Text:** Instructing Deepseek to consider both review content and ratings produced more nuanced and accurate hotel scores.
- **Key Point Extraction:** Asking for key points from reviews distilled large volumes of text into actionable insights for users.

## Challenges and Solutions
- **Inconsistent Output:**
  - *Challenge:* Occasionally, Deepseek would return outputs that did not match the expected JSON format.
  - *Solution:* Adding a clear example and explicit instructions in the system prompt improved consistency.
- **Hallucinated or Irrelevant Key Points:**
  - *Challenge:* Sometimes, key points were not directly supported by the review text.
  - *Solution:* Refined prompts to instruct Deepseek to only use information present in the provided reviews.
- **API Rate Limits and Batch Size:**
  - *Challenge:* Sending too many hotels at once could hit token or rate limits.
  - *Solution:* Implemented batching (default batch size 50) to keep requests within limits and ensure reliable responses.

## Creative Applications Discovered
- **Personalized Hotel Ranking:** The scoring system enables dynamic, user-driven hotel rankings based on any set of preferences.
- **Transparent Recommendations:** Extracted key points provide clear explanations for why a hotel is recommended, increasing user trust.
- **Flexible Querying:** The system can be adapted to new user queries (e.g., "quiet rooms, good breakfast") without code changes, simply by passing a new query string.
- **Review Summarization:** The key point extraction doubles as a review summarizer, making it easy to surface highlights for each hotel.
