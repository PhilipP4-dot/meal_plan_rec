import data_collection
import pandas as pd


data = data_collection.main()
df = pd.DataFrame(columns=['Category','Dish', 'Calories', 'Serving Size'])
for dishes, calories, serving in zip(data[0], data[1], data[2]):
    for dish, calorie, serving_size in zip(data[0][dishes], data[1][calories], data[2][serving]):
        df = df._append({'Category': dishes, 'Dish': dish, 'Calories': calorie, 'Serving Size': serving_size}, ignore_index=True)

df.to_csv('menu_data.csv', index=False)
print("Data processing complete. Data saved to 'menu_data.csv'.")


