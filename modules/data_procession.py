import sqlite3
import pandas as pd
import data_collection

# Initializes a dictionary and then inputs the collected data in it
def collect_data():
    data_dict, date, dine_hall = data_collection.main()
    return data_dict, date, dine_hall

# Converts dictionary into dataframe
def creates_dataframe(data_dict):
    my_df = pd.DataFrame(data_dict)
    return my_df

# Create SQLite Schema
def connect_and_create_schema(meal_period_codes, my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        # create dining halls
        curs.executescript(
            '''
            DROP TABLE IF EXISTS dining_hall;
            CREATE TABLE IF NOT EXISTS dining_hall (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
            );
            INSERT INTO dining_hall (id, name) 
            VALUES 
                    (0, 'Huffman Hall'),
                    (1, 'Curtis Hall'),
                    (2, 'Slayter Market'),
                    (3, 'Silverstein Hall'),
                    (4, 'The Nest'),
                    (5,'Common Grounds'),
                    (6, 'Slayter Alcove Convenience'),
                    (7, 'Mitchell Recreation & Athletic Center');
            '''
        )

        # create meal periods for each entry in the meal period codes
        curs.executescript(
            '''
            DROP TABLE IF EXISTS meal_period;
            CREATE TABLE IF NOT EXISTS meal_period (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
            );
            '''
        )
        
        # Import meal codes here
        for item in meal_period_codes:
            curs.execute(
                '''
                INSERT INTO meal_period (id, name) VALUES (?,?);
                '''
                , (meal_period_codes[item], item,)
            )

        # Creating the menu entry schemas
        curs.executescript(
            '''
            DROP TABLE IF EXISTS menu_entry;
            CREATE TABLE IF NOT EXISTS menu_entry (
                    id TEXT PRIMARY KEY,
                    dining_hall_id INTEGER,
                    meal_period_id INTEGER,
                    date_served DATE,
                    name TEXT,
                    FOREIGN KEY (dining_hall_id) REFERENCES dining_hall(id), 
                    FOREIGN KEY (meal_period_id) REFERENCES meal_period(id)
            );

            DROP TABLE IF EXISTS nutritional_info;
            CREATE TABLE nutritional_info ( 
                    id INTEGER PRIMARY KEY, 
                    menu_entry_id TEXT, 
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

# inputs menu entry into the database
def create_menu_entry(date_served, dining_hall_id, df, my_database):
    with sqlite3.connect(my_database) as con:
        cur = con.cursor()
        num = 0
        for index, row in df.iterrows():
            menu_entry_number = num
            meal_period_id = row['Meal Period']
            meal_name = row['Name']
            custom_menu_entry_id = f"{meal_period_id:02}-{menu_entry_number:03}-{dining_hall_id:02}"
            cur.execute(
                '''
                INSERT INTO menu_entry (id, dining_hall_id, meal_period_id, date_served, name) VALUES (?,?,?,?,?);
                '''
                , (custom_menu_entry_id, dining_hall_id, meal_period_id, date_served, meal_name)
            )
            nutritional_info_number = num
            cur.execute(
                '''
                INSERT INTO nutritional_info (id, 
                    menu_entry_id, 
                    total_fat, 
                    sat_fat, 
                    tran_fat, 
                    cholesterol, 
                    sodium, 
                    total_carbohydrate, 
                    total_sugars, 
                    added_sugars, 
                    diet_fiber, 
                    protein, 
                    potassium, 
                    calcium, 
                    iron, 
                    vitamin_d) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                '''
                , (nutritional_info_number, custom_menu_entry_id, row["Total Fat"], row["Saturated Fat"], row["Trans Fat"], row["Cholesterol"], row["Sodium"], row["Total Carbohydrate"], row["Total Sugars"], row["Added Sugars"], row["Dietary Fiber"], row["Protein"], row["Potassium"], row["Calcium"], row["Iron"], row["Vitamin D"])
            )
            num += 1


def main ():
    database = 'my_database.db'
    data_dict, date, dine_hall = collect_data()
    created_df = creates_dataframe(data_dict)
    connect_and_create_schema(data_collection.mpc, database)
    create_menu_entry(date, dine_hall, created_df, database)

main()