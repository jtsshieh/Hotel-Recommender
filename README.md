# Hotel Recommender

## Overview

Hotel Recommender is a python project that uses reviews of hotels in a metro area and DeepSeek AI to rank hotels based on user preferences. The project integrates data from TripAdvisor and the Amadeus API to provide a comprehensive hotel recommendation system with price information.

## Data Sources and Purpose

| File Name                                       | Description                                                                     |
|-------------------------------------------------|---------------------------------------------------------------------------------|
| `offerings.csv`                                 | Hotels offerings with address and metadata from Tripadvisor.                    |
| `reviews.csv`                                   | Reviews for those selected Tripadvisor hotels, including ratings and text.      |
| Amadeus Hotel Search API / `amadeus_hotels.csv` | (Generated when program is run) Hotel list from the Amadeus API for specific city. |
| Amadeus Hotel Offers API                        | Shows current price offers for hotels for a specific date.                      |

### **Purpose**:  
  The project processes and cleans these datasets, then uses AI to analyze hotel reviews and match hotels to user preferences, providing a ranked list of best-fit hotels.


## DeepSeek Enhancements

DeepSeek AI is used to:
- Analyze hotel reviews and ratings in context of user-specified preferences (e.g., "clean, friendly staff, good location").
- Score each hotel (0-100) for how well it matches the query.
- Extract key points from reviews to justify the score.

## Before/After Example

See example outputs in the examples folder

**Before (Raw Data):**
- User sees a list of hotels and unstructured reviews.
- No clear ranking or summary for specific preferences.
- Example hotel listing:
- ```
    {
        "hotel_id": "KCBOSONX",
        "reviews": [
            {    
                "title": "\u201cquiet elegance on Beacon Hill\u201d",
                "text": "Boston's elegance and accessible scale is matched by the Kimpton Group's primary offer just behind Beacon Hill. The Onyx is nestled just below this historic access-way to the city's jewel public-space, Boston Common which can be reached with a 10minute walk.\nThe Onyx captures what you expect from the boutique attention to detail and fine design Kimpton brings so well throughout the US - along with its people (and pet) -friendly staff, always willing to assist with a smile. The only caveat here being breakfast quality not quite at the level it needs to be - the old adage of \u00e1 decent cup of coffee' harder to find than it should be - but minor quibble in the context of a thoroughly enjoyable, classically comfortable stay - enjoy!",
                "rating": "{'service': 5.0, 'cleanliness': 4.0, 'overall': 4.0, 'value': 5.0, 'location': 4.0, 'sleep_quality': 5.0, 'rooms': 5.0}"
            },
            ...
        ]
    }
  ```

**After (With DeepSeek):**
- User provides a query:  
  _"clean, friendly staff, good location"_
- Output:
  ```
  [
      {
        "hotel_id": "RZBOSRTZ",
        "score": 100.0,
        "key_points": [
          "completely perfect in all aspects",
          "excellent location and service",
          "favorite city Boston"
        ]
      },
    ...
  ]
  ```
- Hotels are ranked and summarized for the user’s needs.
- Then, prices are fetched using the Amadeus API and outputted to the user in a pretty format
## Installation

1. Clone the repository:
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file with your API keys:
     ```
     AMADEUS_CLIENT_ID=your_amadeus_client_id
     AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
     DEEPSEEK_API_KEY=your_deepseek_api_key
     KAGGLE_USERNAME=your_kaggle_username
     KAGGLE_KEY=your_kaggle_api_key
     ```

## Usage

1. Prepare your raw data in `data/raw/`.
2. Run the main script:
   ```sh
   python main.py
   ```
3. Follow the prompts to select a locality and enter your hotel preferences.
4. The script will output a ranked list of hotels with AI-generated scores and key review points.

## Limitations

The free/trial tier of the Amadeus API is limited. It does not provide real-time data and only has a subset of the total data available. This means that if a free API key is inputted, less hotels will be matched and less hotels will have prices attached to them. 