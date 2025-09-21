# Hotel Recommender AI Usage

## AI Usage Summary
Most of the code was written by AI, however, many prompts were used to achieve this result.

The entire deepseek_enrichment prompt was written by human and AI was used to batch requests to prevent token overflow.

In main.py, almost all the code was written by AI and errors were solved by AI as well. The human (me) was used to tweak the code to ensure that it matched the requirements and was wired together correcrtly.

## Prompts
```
write code to load offerings.csv into a pandas dataframe and create an array of all localities
prompt the user to enter one of the localities
make sure the user can only select one of the localities by giving them a list of number to select the locality by
Use the selected locality to get a subset of the offerings data frame of offerings that match that locality and then use those offerings to get a subset of the reviews dataframe to get the reviews that match that locality
instead of having localitie in a separate series, integrate it as a new column in the offerings_df
integrate the amadeus api by performing a hotel list in the chosen locality.
add another column to the offerings_df with the region and use the region and locality (which are states and cities respectively) to derive an accurate IATA city code
can you remove the static fallback mapping
add another column to offerings_df with the postal code and uee the postal code to find the iata code
remove postal code logic
load all hotel data from amadeus into a data frame
only load hotels from the selected iata code
add new colymns to offerings with an address and postal code
add code to drop all rows in offerings without a street address and postal code
use fuzzy search and address matching to match all offerings to a hotel
now create a new data frame for all matched hotels with all the columns from the hotels and offerings data frame
update the code so instead of finding reviews for all the offerings in offerings, it finds the reviews for all the hotels in matched_hotels
save the amadeus hotel data into a csv file in data/raw
create a new dataframe where each hotel in matched_hotels has a column with the title, plain text reviews, and ratings from the reviews_df
make sure that the columns you are analyzing exist in the reviews.csv
make a reviews column with an array of review objects
add the appropriate code to make sure the output json format is returned by the llm
modify this file to implement proper batching of hotels into the user prompt to keep the prompts under the token limit
add logic to sort the top hotels by the score and get the top 10. then, use the amadeus api to request current prices for these 10
make the check in date a week from today and update the check out date so it is one day after that
modify the code to handle all the fact that multiple hotels will be returned and find the lowest offer for each
get the hotel name and display that instead of the id when outputing offers
export the data returned from deepseek to a file under data/enriched
```

## Bugs found in AI code

AI's bugs mostly consisted of errors where it would not use the correct fields returned by the Amadeus API or use the send wrong fields to the API. Additionally, it would sometimes make mistakes when using fields from existing data frames. To fix these, example inputs and outputs of API calls were fed into the LLM. Additonally, files of raw data were attached to queries to give it the ocntext of the data format. This solved many of the issues with it hallucinating fields.  