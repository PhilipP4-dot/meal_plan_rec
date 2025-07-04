import data_collection
import pandas as pd


data = data_collection.main()
df = pd.DataFrame(columns=['Dish', 'Category'])
for i in data:
    for j in data[i]:
        df = df._append({'Dish': j, 'Category': i}, ignore_index=True)

df.to_csv('menu_data.csv', index=False)
print("Data processing complete. Data saved to 'menu_data.csv'.")


