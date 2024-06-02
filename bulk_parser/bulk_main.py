import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Mealie API key
mealie_api_key = os.getenv('MEALIE_API_KEY')

def parse_recipe_into_mealie(recipe_url):
    # Define the API endpoint
    api_endpoint = "http://mealie.lan.net/api/recipes/create-url"
    
    headers = {
        'Authorization': f'Bearer {mealie_api_key}', 
        'Content-Type': 'application/json'
    }
    
    # Create the payload
    payload = {
        "includeTags": True,
        "url": recipe_url
    }
    
    # Send the POST request to the Mealie API
    response = requests.post(api_endpoint, json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200 or response.status_code == 201:
        print(f"Recipe successfully parsed and added to Mealie: {recipe_url}")
        return True
    else:
        print(f"Failed to parse recipe. Status code: {response.status_code}")
        print("Response:", response.text)
        return False

def parse_multiple_recipes(recipe_urls, file_path):
    for url in recipe_urls:
        if parse_recipe_into_mealie(url):
            # Remove the URL from the file if the import was successful
            remove_url_from_file(file_path, url)

def remove_url_from_file(file_path, url):
    lines = None
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    if not lines:
        print("Could not find any lines")
        return
        
    with open(file_path, 'w') as file:
        for line in lines:
            if line.strip() != url:
                file.write(line)

def find_text_file_in_folder():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    files_in_directory = os.listdir(current_directory)
    for file in files_in_directory:
        if file.endswith('.txt'):
            return os.path.join(current_directory, file)
    return None

def read_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        recipe_urls = [line.strip() for line in file.readlines()]
    return recipe_urls

# Example usage
file_path = find_text_file_in_folder()
if file_path:
    recipe_urls = read_urls_from_file(file_path)
    parse_multiple_recipes(recipe_urls, file_path)
else:
    print("No text file found in the directory.")
