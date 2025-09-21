"""
Deepseek Enrichment Module

Enriches the data by using the deepseek AI API
"""
import json
from openai import OpenAI
import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

system_prompt = """
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
"""


def find_best_hotels(hotel_samples, user_query, batch_size=20):
    """
    Prompts the deepseek AI to analyze and hotel reviews and return the top 10 matching the user's query
    """
    try:
        res = []
        n = len(hotel_samples)
        for i in range(0, n, batch_size):
            batch = hotel_samples[i : i + batch_size]
            user_prompt = (
                f"User Query: {user_query}\nHotel Reviews:\n{json.dumps(batch)}"
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={"type": "json_object"},
            )

            res = res + json.loads(response.choices[0].message.content)
        return res
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return []
