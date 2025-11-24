from bs4 import BeautifulSoup
import requests
import json
import pandas as pd

def fetch_data(url):
    """
    Fetch data from a given URL.
    
    Args:
        url (str): The URL to fetch data from.
        
    Returns:
        str: The content fetched from the URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    
def save_data_to_file(data, filename):
    """
    Save data to a file.
    
    Args:
        data (str): The data to save.
        filename (str): The name of the file to save the data to.
    """
    try:
        with open(filename, 'w') as file:
            file.write(data)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving data to {filename}: {e}")
    
def load_data_from_file(filename):
    """
    Load data from a file.
    
    Args:
        filename (str): The name of the file to load data from.
        
    Returns:
        str: The content of the file.
    """
    try:
        with open(filename, 'r') as file:
            return file.read()
    except IOError as e:
        print(f"Error loading data from {filename}: {e}")
        return None

def parse_html(load_data):
    """
    Parse HTML content and extract relevant data.
    
    Args:
        load_data (str): The HTML content to parse.
        
    Returns:
        list: A list of extracted data.
    """
    soup = BeautifulSoup(load_data, 'html.parser')
    
    menu_tabs = [tab.text.strip() for tab in soup.find_all('div', class_="c-tabs-nav__link-inner")]
    time_tabs = []
    calorie_tabs = []
    for tab in soup.find_all('div', class_="c-tab__content"):
        links = [a.text.replace('\n', '').replace('   ', '').strip() for a in tab.find_all('a', tabindex="0")]
        time_tabs.append(links)
    

    calorie_tabs = []
    serving_size_tabs = []    
            
    for tab in soup.find_all('div', class_="c-tab__content"):
        calories = []
        serving_size = []
        for tab_1 in tab.find_all('li', class_="menu-item-li"):
            for a in tab_1.find('div', id="recipe-nutrition-"+ str(tab_1.find('a', href=lambda x: x and x.strip() == "#").get('data-recipe'))):
                item = json.loads(a.text.replace('\n', '').replace('   ', '').strip())
                calories.append(next((fact['value'] for fact in item['facts'] if fact['label'] == 'Calories'), None))
                serving_size.append(item.get('serving_size', None))
        calorie_tabs.append(calories)
        serving_size_tabs.append(serving_size)
    
    final_menu = {}
    calorie_menu = {}
    serving_size_menu = {}
    for tab in range(len(menu_tabs)):
        final_menu[menu_tabs[tab]] = time_tabs[tab]
        calorie_menu[menu_tabs[tab]] = calorie_tabs[tab]
        serving_size_menu[menu_tabs[tab]] = serving_size_tabs[tab]  
    

    return final_menu, calorie_menu, serving_size_menu

def main(filename, url):
    
    # Fetch data from the URL
    data = fetch_data(url)
    if data:
        #Save the fetched data to a file
        save_data_to_file(data, filename)
        
        # Load the data back from the file
    load_data = load_data_from_file(filename) 
    # Parse the HTML content and extract relevant data
    if load_data:
        data = parse_html(load_data)
    # For demonstration, we will directly use the filename
    # Parse the HTML content and extract relevant data
    # Assuming the file already exists and contains valid HTML content

    return data


data = main("data\huff.html", "https://denison.nmcfood.com/locations/the-table-at-huffman/")
df = pd.DataFrame(columns=['Hall', 'Category', 'Time', 'Dish', 'Calories', 'Serving Size'])
for dishes, calories, serving in zip(data[0], data[1], data[2]):
    for dish, calorie, serving_size in zip(data[0][dishes], data[1][calories], data[2][serving]):
        df = df._append({'Hall': 'Huffman', 'Category': ' '.join(dishes.strip().split(' ')[0:-1]).strip().capitalize(), 'Time': dishes.strip().split(' ')[-1], 'Dish': dish, 'Calories': calorie, 'Serving Size': serving_size}, ignore_index=True)

data_1 = main("data\curtis.html", "https://denison.nmcfood.com/locations/the-table-at-curtis/")
df1 = pd.DataFrame(columns=['Hall', 'Category', 'Time','Dish', 'Calories', 'Serving Size'])
for dishes, calories, serving in zip(data_1[0], data_1[1], data_1[2]):
    for dish, calorie, serving_size in zip(data_1[0][dishes], data_1[1][calories], data_1[2][serving]):
        df1 = df1._append({'Hall': 'Curtis', 'Category': ' '.join(dishes.strip().split(' ')[0:-1]).strip().capitalize(), 'Time': dishes.strip().split(' ')[-1], 'Dish': dish, 'Calories': calorie, 'Serving Size': serving_size}, ignore_index=True)

df = pd.concat([df, df1], ignore_index=True)
df.to_csv('data\menu_data.csv', index=False)
print("Data processing complete. Data saved to 'menu_data.csv'.")