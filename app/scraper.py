from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import re
from pathlib import Path

def fetch_data(url):
    """
    Fetch data from a given URL.
    
    Args:
        url (str): The URL to fetch data from.
        
    Returns:
        str: The content fetched from the URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    
def save_data_to_file(data, filename):
    """
    Save data to a file.
    
    Args:
        data (str): The data to save.
        filename (str): The name of the file to save the data to.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(data)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving data to {filename}: {e}")
    
def load_data_from_file(filename):
    """
    Load data from a file.
    
    Args:
        filename (str): The name of the file to load data from.
        
    Returns:
        str: The content of the file.
    """
    try:
        with open(filename, 'r') as file:
            return file.read()
    except IOError as e:
        print(f"Error loading data from {filename}: {e}")
        return None

def clean_text(text):
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def fact_column_name(label, unit):
    """
    Converts nutrition labels into clean DataFrame column names.

    Example:
        "Total Fat", "g" -> "total_fat_g"
        "Calories", "" -> "calories"
    """
    label = label.lower().replace(" ", "_")
    label = re.sub(r"[^a-z0-9_]", "", label)

    if unit:
        unit = unit.lower().replace(" ", "_")
        unit = re.sub(r"[^a-z0-9_]", "", unit)
        return f"{label}_{unit}"

    return label


def parse_html(load_data):
    soup = BeautifulSoup(load_data, "html.parser")

    meal_tabs = [
        clean_text(tab.get_text())
        for tab in soup.find_all("div", class_="c-tabs-nav__link-inner")
    ]

    rows = []

    for tab_index, tab in enumerate(soup.find_all("div", class_="c-tab__content")):
        meal_period = meal_tabs[tab_index] if tab_index < len(meal_tabs) else None

        for station in tab.find_all("div", class_="menu-station"):
            station_header = station.find("h4", class_="toggle-menu-station-data")
            station_name = clean_text(station_header.get_text()).lower() if station_header else None

            for menu_item in station.find_all("li", class_="menu-item-li"):
                item_link = menu_item.find("a", class_="show-nutrition")

                if not item_link:
                    continue

                recipe_id = item_link.get("data-recipe")
                item_name = clean_text(item_link.get_text())

                nutrition_div = menu_item.find(
                    "div",
                    id=f"recipe-nutrition-{recipe_id}"
                )

                if not nutrition_div:
                    continue

                try:
                    nutrition_data = json.loads(clean_text(nutrition_div.get_text()))
                except json.JSONDecodeError:
                    print(f"Could not parse nutrition JSON for: {item_name}")
                    continue

                row = {
                    "category": ' '.join(meal_period.strip().split(' ')[0:-1]).strip().capitalize(),
                    "time": meal_period.strip().split(' ')[-1],
                    "station": station_name,
                    "item_name": nutrition_data.get("name", item_name),
                    "description": nutrition_data.get("description"),
                    "serving_size": nutrition_data.get("serving_size"),
                    "allergens": nutrition_data.get("allergens_list"),
                    "dietary_preferences": nutrition_data.get("preferences_list"),
                }

                for fact in nutrition_data.get("facts", []):
                    label = fact.get("label")
                    unit = fact.get("unit")
                    value = fact.get("value")
                    percent_drv = fact.get("percent_drv")

                    if not label:
                        continue

                    column = fact_column_name(label, unit)
                    row[column] = value

                    if percent_drv is not None:
                        row[f"{column}_percent_daily_value"] = percent_drv

                rows.append(row)

    return pd.DataFrame(rows)

def main(filename, url):
    data = fetch_data(url)

    if data:
        save_data_to_file(data, filename)

    load_data = load_data_from_file(filename)

    if load_data:
        df = parse_html(load_data)
        return df

    return pd.DataFrame()

def scrape_and_save():
    data = main(str(Path("data") / "huffman.html"), "https://denison.nmcfood.com/locations/the-table-at-huffman/?date=2026-05-06")
    #add hall column to data
    data["hall"] = "Huffman"
    data_1 = main(str(Path("data") / "curtis.html"), "https://denison.nmcfood.com/locations/the-table-at-curtis/?date=2026-05-06")
    #add hall column to data_1
    data_1["hall"] = "Curtis"

    df = pd.concat([data, data_1], ignore_index=True)
    df.to_csv(str(Path("data") / "menu_data.csv"), index=False)
    print("Data processing complete. Data saved to 'menu_data.csv'.")
    return
