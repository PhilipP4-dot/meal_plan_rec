# # For the creation of the database
import sqlite3


# Codes for meal periods
mpc = {
    "continental breakfast":0,
    "breakfast":1,
    "lunch":2,
    "snack break":3,
    "dinner":4,
    "brunch":5,
    "summer breakfast":6,
    "summer lunch":7
}

# Codes for dining halls
dhc = {
    'huffman hall':0,
    'curtis hall':1,
    'slayter market':2,
    'silverstein hall':3,
    'the nest':4,
    'common grounds':5,
    'slayter alcove convenience':6,
    'mitchell recreation & athletic center':7,
    'slayter hall student union':8
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
def insert_codes_schema(my_database):
    with sqlite3.connect(my_database) as con:
        curs = con.cursor()
        for item in dhc:
            curs.execute(
                '''
                INSERT INTO dining_hall (id, name)
                VALUES (?, ?);
                '''
                , (dhc[item], item)
            )
        
        # Import meal codes here
        for item in mpc:
            curs.execute(
                '''
                INSERT INTO meal_period (id, name) VALUES (?,?);
                '''
                , (mpc[item], item,)
            )

def main(database):
    create_sql_database(database)
    insert_codes_schema(database)
    