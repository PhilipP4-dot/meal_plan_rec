from bs4 import BeautifulSoup
import requests
import json
import re

# Codes for meal periods
mpc = {
    "Continental Breakfast":0,
    "Breakfast":1,
    "Lunch":2,
    "Snack Break":3,
    "Dinner":4,
    "Brunch":5
}

# Codes for dining halls
dhc = {
    'Huffman Hall':0,
    'Curtis Hall':1,
    'Slayter Market':2,
    'Silverstein Hall':3,
    'The Nest':4,
    'Common Grounds':5,
    'Slayter Alcove Convenience':6,
    'Mitchell Recreation & Athletic Center':7
}


def save_data_to_file(data, filename):
    try:
        with open(filename, 'w', encoding= 'utf-8') as file:
            file.write(data)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving data to {filename}: {e}")
    
def load_data_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8' ) as file:
            return file.read()
    except IOError as e:
        print(f"Error loading data from {filename}: {e}")
        return None
    
# Gets the date the menu was served and retrieves the dining hall id based on which
# dining hall it is served in
# Parameters:   load_data - the opened webpage file that contains the menu
# Returns:      date_served - the date the menu was served
#               dining_hall_id - the code for the particular dining hall based on the dhc
#               dictionary
def date_served_and_dining_hall_id (load_data):
    parser = BeautifulSoup(load_data, 'html.parser')
    d_s = parser.find('button', id= 'location-selected-date')
    if d_s:
        date_served = d_s.text.strip()
    d_h = parser.find('h2', class_= 'location-header-venue')
    if d_h:
        dining_hall_id = dhc.get(d_h.text.strip())
    return date_served, dining_hall_id

# Parses the webpage for the meal name, meal period and then the nutritional information
# Parameters:   load_data - the opened webpage file that contains the menu
# Returns:      all_menu_dict - a dictionary which contains all of the relevant information
def parse_html(load_data):
    bs4_parser = BeautifulSoup(load_data, 'html.parser')
    c_tabs = bs4_parser.find_all('div', class_= 'c-tab__content')
    c_tabs_nav_inner = bs4_parser.find_all('div', class_= 'c-tabs-nav__link-inner')
    c_tabs_nav_inner = [item.text.strip() for item in c_tabs_nav_inner]
    c_tabs_nav_inner = [re.match(r'^[^(]+', item).group().strip() for item in c_tabs_nav_inner]

    all_menu_dict = {}

    meal_name = []
    meal_period = []
    meal_total_fat = []
    meal_sat_fat = []
    meal_tran_fat = []
    meal_cholesterol = []
    meal_sodium = []
    meal_total_carbohydrate = []
    meal_total_sugars = []
    meal_added_sugars = []
    meal_diet_fiber = []
    meal_protein = []
    meal_potassium = []
    meal_calcium = []
    meal_iron = []
    meal_vitamin_d = []

    for one_c_tab in c_tabs:
        li_tags = one_c_tab.find_all('li', class_= 'menu-item-li')
        for one_li in li_tags:
            a_tag = one_li.find('a')
            if a_tag:
                meal_name.append(a_tag.text.strip())
                meal_period_words = c_tabs_nav_inner[c_tabs.index(one_c_tab)]
                meal_period.append(mpc[meal_period_words])
            div_tag = one_li.find('div')
            if div_tag:
                div_text = div_tag.text
                json_ready = json.loads(div_text)
                meal_total_fat.append(json_ready["facts"][1]["value"])
                meal_sat_fat.append(json_ready["facts"][2]["value"])
                meal_tran_fat.append(json_ready["facts"][3]["value"])
                meal_cholesterol.append(json_ready["facts"][4]["value"])
                meal_sodium.append(json_ready["facts"][5]["value"])
                meal_total_carbohydrate.append(json_ready["facts"][6]["value"])
                meal_total_sugars.append(json_ready["facts"][7]["value"])
                meal_added_sugars.append(json_ready["facts"][8]["value"])
                meal_diet_fiber.append(json_ready["facts"][9]["value"])
                meal_protein.append(json_ready["facts"][10]["value"])
                meal_potassium.append(json_ready["facts"][11]["value"])
                meal_calcium.append(json_ready["facts"][12]["value"])
                meal_iron.append(json_ready["facts"][13]["value"])
                meal_vitamin_d.append(json_ready["facts"][14]["value"])

    all_menu_dict['Name'] = meal_name
    all_menu_dict['Meal Period'] = meal_period
    all_menu_dict["Total Fat"] =  meal_total_fat
    all_menu_dict["Saturated Fat"] = meal_sat_fat
    all_menu_dict["Trans Fat"] = meal_tran_fat
    all_menu_dict["Cholesterol"] = meal_cholesterol
    all_menu_dict["Sodium"] = meal_sodium
    all_menu_dict["Total Carbohydrate"] = meal_total_carbohydrate
    all_menu_dict["Total Sugars"] = meal_total_sugars
    all_menu_dict["Added Sugars"] = meal_added_sugars
    all_menu_dict["Dietary Fiber"] = meal_diet_fiber
    all_menu_dict["Protein"] = meal_protein
    all_menu_dict["Potassium"] = meal_potassium
    all_menu_dict["Calcium"] = meal_calcium
    all_menu_dict["Iron"] = meal_iron
    all_menu_dict["Vitamin D"] = meal_vitamin_d 

    return all_menu_dict

def main():    
    filename = "page_source.html"
    load_data = load_data_from_file(filename) 
    date, dine_hall_id = date_served_and_dining_hall_id(load_data)
    if load_data:
        data_dict = parse_html(load_data)
    return data_dict, date, dine_hall_id

main()