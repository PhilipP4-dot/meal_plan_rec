import data_collection
import pandas as pd


data = data_collection.main("modules\huff.html")
df = pd.DataFrame(columns=['Hall', 'Category', 'Time', 'Dish', 'Calories', 'Serving Size'])
for dishes, calories, serving in zip(data[0], data[1], data[2]):
    for dish, calorie, serving_size in zip(data[0][dishes], data[1][calories], data[2][serving]):
        df = df._append({'Hall': 'Huffman', 'Category': dishes.split(' ')[0], 'Time': dishes.split(' ')[1], 'Dish': dish, 'Calories': calorie, 'Serving Size': serving_size}, ignore_index=True)


data_1 = data_collection.main("modules\curtis.html")
df1 = pd.DataFrame(columns=['Hall', 'Category', 'Time','Dish', 'Calories', 'Serving Size'])
for dishes, calories, serving in zip(data_1[0], data_1[1], data_1[2]):
    for dish, calorie, serving_size in zip(data_1[0][dishes], data_1[1][calories], data_1[2][serving]):
        df1 = df1._append({'Hall': 'Curtis', 'Category': dishes.split(' ')[0], 'Time': dishes.split(' ')[1], 'Dish': dish, 'Calories': calorie, 'Serving Size': serving_size}, ignore_index=True)

df = pd.concat([df, df1], ignore_index=True)
df.to_csv('menu_data.csv', index=False)
print("Data processing complete. Data saved to 'menu_data.csv'.")
print(df.head())


