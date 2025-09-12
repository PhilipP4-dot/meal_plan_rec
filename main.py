import pandas as pd

df = pd.read_csv('manual_overrides.csv')

df = df.drop_duplicates("Dish")
print(len(df))
df.to_csv('manual_overrides.csv', index=False)