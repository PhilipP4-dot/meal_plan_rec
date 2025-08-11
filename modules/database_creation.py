# # For the creation of the database
import sqlite3


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

def create_sql_database(my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        curs.executescript(
            '''
            DROP TABLE IF EXISTS dining_hall;
            CREATE TABLE IF NOT EXISTS dining_hall (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
            );

            DROP TABLE IF EXISTS meal_period;
            CREATE TABLE IF NOT EXISTS meal_period (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
            );

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
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
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

# Create SQLite Schema
def insert_codes_schema(meal_period_codes, my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        curs.executescript(
            '''
            INSERT INTO dining_hall (id, name) 
            VALUES 
                    (0, 'Huffman Hall'),
                    (1, 'Curtis Hall'),
                    (2, 'Slayter Market'),
                    (3, 'Silverstein Hall'),
                    (4, 'The Nest'),
                    (5, 'Common Grounds'),
                    (6, 'Slayter Alcove Convenience'),
                    (7, 'Mitchell Recreation & Athletic Center');
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

def main(database):
    create_sql_database(database)
    insert_codes_schema(mpc, database)
    