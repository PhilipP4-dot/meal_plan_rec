import sqlite3
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import fileinput


# date_served established
def date_served_and_dining_hall (file_page):
    with open(file_page, 'r', encoding = 'utf-8') as file:
        container = file.read()
        parser = BeautifulSoup(container, 'html.parser')
        d_s = parser.find('button', id= 'location-selected-date')
        if d_s:
            date_served = d_s.text.strip()
        d_h = parser.find('h2', class_= 'location-header-venue')
        if d_h:
            dining_hall = d_h.text.strip()
    return date_served, dining_hall

# stores the meal informations of every thing
def creates_dataframe(file_page, meal_period_codes):
    with open(file_page, 'r', encoding = 'utf-8') as file:
        container = file.read()
        bs4_parser = BeautifulSoup(container, 'html.parser')
        c_tabs = bs4_parser.find_all('div', class_= 'c-tab__content')
        
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
        
        # change meal_periods
        for i, one_c_tab in enumerate(c_tabs):
            li_tags = one_c_tab.find_all('li', class_= 'menu-item-li')
            for one_li in li_tags:
                a_tag = one_li.find('a')
                if a_tag:
                    meal_name.append(a_tag.text.strip())
                    meal_period.append(i)
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

        my_df = pd.DataFrame(all_menu_dict)
    
    return my_df

# creates schema
def connect_and_create_schema(meal_period_codes, my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        # create dining halls
        curs.executescript(
            '''
            CREATE TABLE IF NOT EXISTS dining_hall (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
            ):
            INSERT INTO dining_hall (id, name) 
            VALUES 
                    ('00', 'Huffman Hall'),
                    ('01', 'Curtis Hall'),
                    ('02', 'Slayter Market'),
                    ('03', 'Silverstein Hall'),
                    ('04', 'The Nest'),
                    ('05','Common Grounds'),
                    ('06', 'Slayter Alcove Convenience'),
                    ('07', 'Mitchell Recreation & Athletic Center');
            '''
        )

        # create meal periods for each entry in the meal period codes
        curs.execute(
            '''
            CREATE TABLE IF NOT EXISTS meal_period (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
            );
            '''
        )
        for item in meal_period_codes:
            curs.execute(
                '''
                INSERT INTO meal_period (id, name) VALUES (?,?);
                '''
                , (f"{meal_period_codes[item]:02d}", meal_period_codes,)
            )

        # Creating the menu entry schemas
        curs.executescript(
            '''
            CREATE TABLE IF NOT EXISTS menu_entry (
                    id TEST PRIMARY KEY,
                    dining_hall_id INTEGER,
                    meal_period_id INTEGER,
                    date_served DATE,
                    name, TEXT
                    FOREIGN KEY (dining_hall_id) REFERENCES dining_hall(id), 
                    FOREIGN KEY (meal_period_id) REFERENCES meal_period(id)
            );


            CREATE TABLE nutritional_info ( 
                    id INTEGER PRIMARY KEY, 
                    menu_entry_id INTEGER, 
                    total_fat REAL, 
                    sat_fat REAL, 
                    tran_fat REAL, 
                    cholesterol REAL, 
                    sodium REAL, 
                    total_carbohydrate REAL, 
                    total_sugars REAL, 
                    added_sugars REAL, 
                    diet_fiber REAL, 
                    protein REAL, 
                    potassium REAL, 
                    calcium REAL, 
                    iron REAL, 
                    vitamin_d REAL, 
                    FOREIGN KEY (menu_entry_id) REFERENCES menu_entry(id) 
            );
            '''
        )
        curs.commit()

# inputs menu entry into the database
def menu_entry(date_served, dining_hall_id, df, my_database):
    with sqlite3.connect(my_database) as con:
        cur = con.cursor()
        num = 0
        for item in df:
            num += 1
            menu_entry_id = f"{num:02}"
            meal_period_id = df['meal_period']
            custom_id = f"{meal_period_id:02}-{menu_entry_id:03}-{dining_hall_id:02}"
            cur.execute(
                '''
                INSERT INTO menu_entry (menu_entry_id, meal_period_id, custom_id, dining_hall_id, date_served) VALUES (?,?,?,?,?);
                '''
                , (menu_entry_id, meal_period_id, custom_id, dining_hall_id, date_served, )
            )
            cur.commit()

# meal period codes
mpc = {
    "Continental Breakfast":0,
    "Brekfast":1,
    "Lunch":2,
    "Snack Break":3,
    "Dinner":4
}

# dining hall codes
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

def scraping_function (file_page, database):
    date, dine_hall = date_served_and_dining_hall(file_page)
    created_df = creates_dataframe(file_page, mpc)
    connect_and_create_schema(file_page, database)
    menu_entry(date, dine_hall, created_df, database)

# use standard input to get file
my_database = 'my_database.db'
url = ''
raw_file = ''
scraping_function(raw_file, my_database)
