import sqlite3
import pandas as pd
import data_collection

# Initializes a dictionary and then inputs the collected data in it
def collect_data():
    data_dict, date, dine_hall = data_collection.main()
    return data_dict, date, dine_hall


def creates_dataframe(data_dict):
    my_df = pd.DataFrame(data_dict)
    return my_df

# creates schema
def connect_and_create_schema(meal_period_codes, my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        # create dining halls
        curs.executescript(
            '''
            DROP TABLE IF EXISTS dining_hall;
            CREATE TABLE IF NOT EXISTS dining_hall (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
            );
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
        curs.executescript(
            '''
            DROP TABLE IF EXISTS meal_period;
            CREATE TABLE IF NOT EXISTS meal_period (
                    id TEXT PRIMARY KEY,
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
                , (f"{meal_period_codes[item]:02d}", item,)
            )

        # Creating the menu entry schemas
        curs.executescript(
            '''
            DROP TABLE IF EXISTS menu_entry;
            CREATE TABLE IF NOT EXISTS menu_entry (
                    menu_entry_id TEXT PRIMARY KEY,
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
        con.commit()

# inputs menu entry into the database
def create_menu_entry(date_served, dining_hall_id, df, my_database):
    with sqlite3.connect(my_database) as con:
        cur = con.cursor()
        num = 0
        for index, row in df.iterrows():
            num += 1
            menu_entry_id = f"{num:02}"
            meal_period_id = row['Meal Period']
            meal_name = row['Name']
            custom_id = f"{meal_period_id:02}-{menu_entry_id:03}-{dining_hall_id:02}"
            cur.execute(
                '''
                INSERT INTO menu_entry (menu_entry_id, dining_hall_id, meal_period_id, date_served, name) VALUES (?,?,?,?,?);
                '''
                , (custom_id, dining_hall_id, meal_period_id, date_served, meal_name)
            )

# def inserting_nutritional_info():



def main ():
    database = 'my_database.db'
    data_dict, date, dine_hall = collect_data()
    created_df = creates_dataframe(data_dict)
    # print(created_df)
    connect_and_create_schema(data_collection.mpc, database)
    create_menu_entry(date, dine_hall, created_df, database)

main()