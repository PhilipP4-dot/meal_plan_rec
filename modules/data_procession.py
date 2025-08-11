import sqlite3
import pandas as pd
import data_collection

# Converts dictionary into dataframe
def create_dataframe(data_dict):
    my_df = pd.DataFrame(data_dict)
    return my_df


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
            cur.execute(
                '''
                INSERT INTO nutritional_info (
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
                    vitamin_d) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
                '''
                , (custom_menu_entry_id, 
                   row["Total Fat"], 
                   row["Saturated Fat"], 
                   row["Trans Fat"], 
                   row["Cholesterol"], 
                   row["Sodium"], 
                   row["Total Carbohydrate"], 
                   row["Total Sugars"], 
                   row["Added Sugars"], 
                   row["Dietary Fiber"], 
                   row["Protein"], 
                   row["Potassium"], 
                   row["Calcium"], 
                   row["Iron"], 
                   row["Vitamin D"])
            )
            num += 1

def main (data_dict, date, dine_hall, database):
    created_df = create_dataframe(data_dict)
    create_menu_entry(date, dine_hall, created_df, database)