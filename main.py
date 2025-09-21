import random

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import pandas as pd
import ast
from amadeus import Client, ResponseError
import os
from rapidfuzz import fuzz
import re
from deepseek_enrichment import find_best_hotels
from datetime import datetime, timedelta
import json
import kaggle

kaggle.api.authenticate()

kaggle.api.dataset_download_files(
    "joebeachcapital/hotel-reviews", path="data/raw", unzip=True
)

# Amadeus API credentials (set your own credentials as environment variables or directly here)
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
amadeus = Client(client_id=AMADEUS_CLIENT_ID, client_secret=AMADEUS_CLIENT_SECRET)

# Load offerings.csv into a pandas DataFrame
offerings_df = pd.read_csv("data/raw/offerings.csv")

# Parse the 'address' column and extract 'locality' and 'region' values, add as new columns in offerings_df
offerings_df["locality"] = offerings_df["address"].apply(
    lambda x: ast.literal_eval(x).get("locality") if pd.notnull(x) else None
)
offerings_df["region"] = offerings_df["address"].apply(
    lambda x: ast.literal_eval(x).get("region") if pd.notnull(x) else None
)
offerings_df["street_address"] = offerings_df["address"].apply(
    lambda x: (ast.literal_eval(x).get("street-address") if pd.notnull(x) else None)
)
offerings_df["postal_code"] = offerings_df["address"].apply(
    lambda x: ast.literal_eval(x).get("postal-code") if pd.notnull(x) else None
)

# Drop rows without a street address or postal code
before_drop = len(offerings_df)
offerings_df = offerings_df.dropna(subset=["street_address", "postal_code"])
after_drop = len(offerings_df)

unique_localities = offerings_df["locality"].dropna().unique()

print("Available localities:")
for idx, loc in enumerate(unique_localities, 1):
    print(f"{idx}. {loc}")

while True:
    try:
        selection = int(
            input(
                f"Please enter the number of your chosen locality (1-{len(unique_localities)}): "
            )
        )
        if 1 <= selection <= len(unique_localities):
            selected_locality = unique_localities[selection - 1]
            break
        else:
            print("Invalid selection. Please try again.")
    except ValueError:
        print("Please enter a valid number.")

print(f"You selected: {selected_locality}")

# Subset offerings for the selected locality
offerings_subset = offerings_df[offerings_df["locality"] == selected_locality]

# Get the region for the selected locality
selected_region = (
    offerings_subset["region"].iloc[0] if not offerings_subset.empty else None
)


def get_iata_code(city, region):
    """
    Tries to get the IATA code for a city using the Amadeus API.
    """
    try:
        country_code = "US" if region and len(region) == 2 else None
        params = {"keyword": city}
        if country_code:
            params["countryCode"] = country_code
        try:
            response = amadeus.reference_data.locations.cities.get(**params)
            cities = response.data
            # Try to match region/state if possible
            for c in cities:
                if (
                    "address" in c
                    and c["address"].get("stateCode", "").upper()
                    == (region or "").upper()
                ):
                    print(f"IATA code found by city/region: {c['iataCode']}")
                    return c["iataCode"]
            # If no state match, return the first result's IATA code
            if cities:
                print(f"IATA code found by city: {cities[0]['iataCode']}")
                return cities[0]["iataCode"]
        except ResponseError as error:
            print(f"Amadeus city/region lookup error: {error}")
    except Exception as e:
        print(f"Unexpected error during IATA lookup: {e}")
    # Fallback: use first 3 letters of city name
    print(f"No IATA code found for {city}, {region}. Using fallback.")
    return city[:3].upper()


iata_code = get_iata_code(selected_locality, selected_region)

# Attempt to load hotels from Amadeus API for the selected locality
if not iata_code or len(iata_code) != 3:
    print(
        f"Could not determine a valid IATA code for {selected_locality} ({selected_region}). Skipping Amadeus hotel search."
    )
    hotels_df = pd.DataFrame()  # Empty DataFrame if no valid IATA code
else:
    print(f"\nHotels in {selected_locality} from Amadeus API (IATA: {iata_code}):")
    try:
        response = amadeus.reference_data.locations.hotels.by_city.get(
            cityCode=iata_code, radius=30, radiusUnit="MI"
        )
        hotels = response.data
        if not hotels:
            print(f"No hotels found in Amadeus for IATA code {iata_code}.")
            hotels_df = pd.DataFrame()
        else:
            # Store hotels in a DataFrame
            hotels_df = pd.DataFrame(hotels)
            print(
                f"\nTotal hotels loaded from Amadeus for {selected_locality}: {len(hotels_df)}"
            )
    except ResponseError as error:
        print(f"Amadeus API error: {error}")
        hotels_df = pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error during Amadeus hotel search: {e}")
        hotels_df = pd.DataFrame()

# Save the Amadeus hotel data to a CSV file
hotels_df.to_csv("data/raw/amadeus_hotels.csv", index=False)
print("Saved Amadeus hotel data to data/raw/amadeus_hotels.csv")


def normalize(text):
    """
    Normalizes fields in data to try to fuzzy match
    """
    if pd.isnull(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text


if not hotels_df.empty:
    # Prepare normalized columns for matching
    offerings_subset = offerings_subset.copy()  # Avoid SettingWithCopyWarning
    offerings_subset.loc[:, "norm_name"] = offerings_subset["name"].apply(normalize)
    offerings_subset.loc[:, "norm_address"] = offerings_subset["street_address"].apply(
        normalize
    )
    offerings_subset.loc[:, "norm_postal"] = (
        offerings_subset["postal_code"].astype(str).apply(normalize)
    )

    hotels_df["norm_name"] = hotels_df["name"].apply(
        lambda x: (
            normalize(x["text"])
            if isinstance(x, dict) and "text" in x
            else normalize(x)
        )
    )
    hotels_df["norm_address"] = hotels_df["address"].apply(
        lambda x: (
            normalize(x["lines"][0])
            if isinstance(x, dict) and "lines" in x and x["lines"]
            else normalize(x)
        )
    )
    hotels_df["norm_postal"] = hotels_df["address"].apply(
        lambda x: (
            normalize(x.get("postalCode"))
            if isinstance(x, dict) and "postalCode" in x
            else ""
        )
    )

    # Fuzzy match each offering to the best hotel
    matched_hotel_ids = []
    matched_scores = []
    for _, offering in offerings_subset.iterrows():
        best_score = 0
        best_hotel_id = None
        for _, hotel in hotels_df.iterrows():
            name_score = fuzz.token_set_ratio(offering["norm_name"], hotel["norm_name"])
            addr_score = fuzz.token_set_ratio(
                offering["norm_address"], hotel["norm_address"]
            )
            postal_score = (
                100
                if offering["norm_postal"]
                and offering["norm_postal"] == hotel["norm_postal"]
                else 0
            )
            total_score = 0.5 * name_score + 0.4 * addr_score + 0.1 * postal_score
            if total_score > best_score:
                best_score = total_score
                best_hotel_id = hotel.get("hotelId", None)
        if best_score >= 80:
            matched_hotel_ids.append(best_hotel_id)
            matched_scores.append(best_score)
        else:
            matched_hotel_ids.append(None)
            matched_scores.append(best_score)
    offerings_subset.loc[:, "matched_hotel_id"] = matched_hotel_ids
    offerings_subset.loc[:, "matched_hotel_score"] = matched_scores
    print(
        f"Matched {offerings_subset['matched_hotel_id'].notnull().sum()} out of {len(offerings_subset)} offerings to Amadeus hotels."
    )
else:
    print("No hotels found for matching.")

# --- Create a DataFrame for all matched hotels with all columns from both hotels and offerings ---
if not hotels_df.empty and "matched_hotel_id" in offerings_subset.columns:
    # Use only matched offerings
    matched_offs = offerings_subset[
        offerings_subset["matched_hotel_id"].notnull()
    ].copy()
    # Ensure hotelId is a string for join
    hotels_df = hotels_df.copy()
    hotels_df["hotelId"] = hotels_df["hotelId"].astype(str)
    matched_offs["matched_hotel_id"].astype(str)
    # Merge on hotelId
    matched_hotels_df = pd.merge(
        matched_offs,
        hotels_df,
        left_on="matched_hotel_id",
        right_on="hotelId",
        suffixes=("_offering", "_hotel"),
        how="inner",
    )
    print(f"\nTotal matched hotel-offering pairs: {len(matched_hotels_df)}")
else:
    print("No matched hotels to merge.")
    exit()

# Load reviews.csv into a DataFrame
reviews_df = pd.read_csv("data/raw/reviews.csv")

# --- Create a DataFrame with hotel title, reviews, and ratings for each matched hotel ---
required_review_cols = {"offering_id", "text", "ratings", "title"}
missing_cols = required_review_cols - set(reviews_df.columns)
if missing_cols:
    print(
        f"Warning: The following required columns are missing in reviews.csv: {missing_cols}. Review analysis will be limited."
    )

# Build an array of hotel review records to send to LLM
if not matched_hotels_df.empty and not reviews_df.empty:
    hotel_review_records = []
    for _, row in matched_hotels_df.iterrows():
        hotel_id = row["hotelId"] if "hotelId" in row else row["matched_hotel_id"]
        # Filter reviews for this hotel
        hotel_reviews = reviews_df[reviews_df["offering_id"] == row["id"]]
        # Build array of review objects
        review_objs = []
        for _, r in hotel_reviews.iterrows():
            review_obj = {}
            if "title" in r and pd.notnull(r["title"]):
                review_obj["title"] = r["title"]
            if "text" in r and pd.notnull(r["text"]):
                review_obj["text"] = r["text"]
            if "ratings" in r and pd.notnull(r["ratings"]):
                review_obj["rating"] = r["ratings"]
            if review_obj:
                review_objs.append(review_obj)
        hotel_review_records.append(
            {
                "hotel_id": hotel_id,
                "reviews":  random.sample(review_objs, 10) if len(review_objs) > 10 else review_objs,
            }
        )
    print(f"\nCreated hotel_reviews_df with {len(hotel_review_records)} hotels.")
else:
    print("No matched hotels or reviews to create hotel_reviews_df.")
    exit()

raw_data_path = os.path.join(
    "data",
    "raw",
    f"{selected_locality}_reviews.json",
)
with open(raw_data_path, "w") as f:
    json.dump(hotel_review_records, f, indent=2)
print(f"\nHotel Review Records exported to: {raw_data_path}")


# --- Prompt user for hotel preferences and use DeepSeek AI to find the best hotels ---
user_query = input(
    "\nWhat are you looking for in a hotel? (e.g., quiet, good breakfast, family-friendly, etc.): "
)
print("\nAnalyzing reviews with DeepSeek AI. This may take several moments...")
top_hotels = find_best_hotels(hotel_review_records, user_query)


def get_score(h):
    """
    Sort by score and get top 10 hotels (descending)
    """
    try:
        return float(h.get("score", 0))
    except Exception:
        return 0


if top_hotels:
    enriched_path = os.path.join(
        "data",
        "enriched",
        f'deepseek_hotels_{selected_locality}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
    )
    with open(enriched_path, "w") as f:
        json.dump(top_hotels, f, indent=2)
    print(f"\nDeepSeek AI results exported to: {enriched_path}")

    top_hotels_sorted = sorted(top_hotels, key=get_score, reverse=True)[:10]
    # --- Add DeepSeek scores and key points to matched_hotels_df ---
    # Build a mapping from hotel_id to score and key_points
    deepseek_map = {
        h["hotel_id"]: {
            "deepseek_score": h.get("score"),
            "deepseek_key_points": h.get("key_points"),
        }
        for h in top_hotels_sorted
        if h.get("hotel_id")
    }
    matched_hotels_df["deepseek_score"] = matched_hotels_df["hotelId"].map(
        lambda x: deepseek_map.get(x, {}).get("deepseek_score")
    )
    matched_hotels_df["deepseek_key_points"] = matched_hotels_df["hotelId"].map(
        lambda x: deepseek_map.get(x, {}).get("deepseek_key_points")
    )
    print("\nUpdated matched_hotels_df with DeepSeek scores and key points:")
else:
    print("No hotels matched your criteria.")

# --- Use Amadeus API to request current prices for these 10 hotels ---
if top_hotels:
    # Calculate check-in and check-out dates
    today = datetime.now().date()
    check_in = today + timedelta(days=60)
    check_out = check_in + timedelta(days=1)
    check_in_str = check_in.strftime("%Y-%m-%d")
    check_out_str = check_out.strftime("%Y-%m-%d")
    print(
        f"\nRequesting current prices from Amadeus API for top 10 hotels (Check-in: {check_in_str}, Check-out: {check_out_str})..."
    )
    amadeus_ids = [
        hotel.get("hotel_id") for hotel in top_hotels_sorted if hotel.get("hotel_id")
    ]
    try:
        response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=amadeus_ids,
            checkInDate=check_in_str,
            checkOutDate=check_out_str,
            adults=1,
        )
        offers = response.data
        # Map hotelId to lowest price offer
        hotel_prices = {}
        for offer in offers:
            hotel_id = offer.get("hotel", {}).get("hotelId")
            if not hotel_id:
                continue
            lowest = None
            if "offers" in offer and offer["offers"]:
                for o in offer["offers"]:
                    price = o.get("price", {}).get("total")
                    currency = o.get("price", {}).get("currency")
                    if price is not None:
                        try:
                            price_val = float(price)
                        except Exception:
                            price_val = None
                        if price_val is not None:
                            if (lowest is None) or (price_val < lowest["price_val"]):
                                lowest = {
                                    "price_val": price_val,
                                    "price": price,
                                    "currency": currency,
                                }
            if lowest:
                hotel_prices[hotel_id] = lowest
        # Build a mapping from hotel_id to hotel name for display
        hotel_id_to_name = {
            row["hotelId"]: (
                row["name"]
                if "name" in row and pd.notnull(row["name"])
                else row.get("name_offering", row["hotelId"])
            )
            for _, row in hotels_df.iterrows()
            if "hotelId" in row
        }
        print(
            "\nTop 10 hotels matching your preferences (with current price offers and key review points):"
        )
        for idx, hotel in enumerate(top_hotels_sorted, 1):
            amadeus_id = hotel.get("hotel_id")
            price_info = hotel_prices.get(amadeus_id)
            hotel_name = hotel_id_to_name.get(amadeus_id, amadeus_id)
            key_points = hotel.get("key_points", [])
            print(f"{idx}. {hotel_name} | Score: {hotel.get('score', 'N/A')}")
            if price_info:
                print(
                    f"   Lowest price for 1 night ({check_in_str} to {check_out_str}): {price_info['price']} {price_info['currency']}"
                )
            else:
                print(f"   No price offers found.")
            if key_points:
                print(f"   Key Points: {', '.join(key_points)}")
            else:
                print(f"   No key points found.")
    except ResponseError as error:
        print(f"Amadeus API error: {error}")
    except Exception as e:
        print(f"Error fetching prices for hotels: {e}")
