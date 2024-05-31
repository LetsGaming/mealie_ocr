import os
import json
import pytesseract
from PIL import Image
import openai
import asyncio
import aiohttp
from dotenv import load_dotenv

from utils.utils import recipe_data
from utils.languages import Languages

# Load environment variables
load_dotenv()

# Mealie service URL and API key
mealie_url = os.getenv('MEALIE_URL')
mealie_api_key = os.getenv('MEALIE_API_KEY')

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

language = Languages.GER

def clean_special_characters(text):
    # Replace special characters
    cleaned_text = text.replace("�", "").replace("°C", "C").replace("ö", "oe").replace("ä", "ae").replace("ü", "ue").replace("ß", "ss").replace("```", "").replace("json", "")
    return cleaned_text

def extract_text_from_image(image_path: str) -> str:
    try:
        image = Image.open(image_path)
        pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def generate_recipe_from_text(text: str) -> dict:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Assistant, specialized on the selfhost service 'Mealie'."},
                {"role": "user", "content": f"This is the JSON-Format for Mealie Recipes: {recipe_data}"},
                {"role": "user", "content": f"Create a detailed Mealie recipe in {language}, as JSON format using the following text. The response should contain only the JSON. The JSON should be directly importable using the Mealie API. For the ingredients and instructions, use ONLY this text:\n\n{text}"}
            ],
            max_tokens=2500
        )
        response_content = response['choices'][0]['message']['content'].strip()
        cleaned_content = clean_special_characters(response_content)
        recipe_json = json.loads(cleaned_content)
        return recipe_json
    except Exception as e:
        print(f"Error generating recipe from text: {e}")
        raise

def create_mealie_recipe(recipe_data: dict) -> dict:
    user_id = os.getenv('MEALIE_USER_ID')
    group_id = os.getenv('MEALIE_GROUP_ID')
    
    recipe_data['userId'] = user_id
    recipe_data['groupId'] = group_id
    
    return recipe_data

async def upload_recipe_to_mealie(recipe: dict):
    headers = {
        'Authorization': f'Bearer {mealie_api_key}', 
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(mealie_url, json=recipe, headers=headers) as response:
            if response.status == 201:
                print("Recipe successfully uploaded.")
            else:
                print(f"Failed to upload recipe. Status code: {response.status}")
                print(await response.text())

async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of the script
    imgs_folder = os.path.join(script_dir, "imgs")  # Path to the imgs folder
    
    # Iterate over all files in the imgs folder
    for filename in os.listdir(imgs_folder):
        if filename.endswith((".jpg", ".jpeg", ".png")):  # Check if file is an image
            image_path = os.path.join(imgs_folder, filename)  # Get full path to the image
            extracted_text = extract_text_from_image(image_path)

            try:
                generated_recipe = generate_recipe_from_text(extracted_text)
            except Exception as e:
                generated_recipe = None

            if generated_recipe:
                mealie_recipe = create_mealie_recipe(recipe_data=generated_recipe)
                print(f"Mealie Recipe JSON for {filename}: {mealie_recipe}")

                await upload_recipe_to_mealie(mealie_recipe)

if __name__ == '__main__':
    asyncio.run(main())
