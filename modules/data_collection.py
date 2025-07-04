from bs4 import BeautifulSoup
import requests
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
    for tab in soup.find_all('div', class_="c-tab__content"):
        links = [a.text.replace('\n', '').replace('   ', '').strip() for a in tab.find_all('a', tabindex="0")]
        time_tabs.append(links)

        #[tab.find_all('a', tabindex="0") for tab in soup.find_all('div', class_="c-tabs__content", )]    
    final_menu = {}
    for tab in range(len(menu_tabs)):
        final_menu[menu_tabs[tab]] = time_tabs[tab]
    return final_menu

def main():
    url = "https://example.com/data"
    filename = "modules\huff.html"
    
    # Fetch data from the URL
    #data = fetch_data(url)
    #if data:
        # Save the fetched data to a file
        #save_data_to_file(data, filename)
        
        # Load the data back from the file
    load_data = load_data_from_file(filename) 
    # Parse the HTML content and extract relevant data
    if load_data:
        data = parse_html(load_data)
    # For demonstration, we will directly use the filename
    # Parse the HTML content and extract relevant data
    # Assuming the file already exists and contains valid HTML content

    return data
