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
from utils.ai_models import Models

# Load environment variables
load_dotenv()

# Mealie service URL and API key
mealie_base_url = os.getenv('MEALIE_BASE_URL')
mealie_api_key = os.getenv('MEALIE_API_KEY')

# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

language = Languages.GER.value
ai_model = Models.GPT4.value

def clean_special_characters(text):
    # First replace longer substrings
    cleaned_text = text.replace("```", "").replace("json", "").replace("°C", "C")
    
    # Translation table for single character replacements
    translation_table = str.maketrans({
        "�": "",
        "ß": "ss",
        "'": '"'
    })
    
    # Then translate single characters
    cleaned_text = cleaned_text.translate(translation_table)
    
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

async def generate_recipe_from_text(text: str) -> dict:
    try:
        response = await openai.ChatCompletion.acreate(
            model=ai_model,
            messages=[
                {"role": "system", "content": "You're a helpful Assistant, specialized in the Mealie self-hosting service."},
                {"role": "user", "content": f"Here's the JSON format for Mealie Recipes: {recipe_data}."},
                {"role": "user", "content": f"Generate a detailed Mealie recipe in {language}, following the format strictly, especially for ingredients and instructions. Use double quotes for properties, except for values like numbers (except for nutrion label), booleans or null. Ensure units are in the correct format with the UUIDs from the given recipe-format. Quantity only accepts integers or floats. IDs must be valid UUIDs of length 32 with version 4. Each Instruction need to have a UUID. Include only relevant data from the given format."},
                {"role": "user", "content": "Incorporate the userId and groupId from the provided format into the recipe. Add suitable tags for the recipe, but no categories. Calculate nutrition label data, based on ingredients. 'showNutrition' needs to be true and 'disableAmount' needs to be false. Cook Time is set under 'performTime'"},
                {"role": "user", "content": "Name of the ingredient goes into 'note'. Numbering for instructions is not needed in text. The nutrions are in the following units: Calories: calories, Sodium: milligrams. Everything else: grams"},
                {"role": "user", "content": f"For ingredients and instructions, use ONLY this text: {text}."}
            ],
            max_tokens=3000
        )
        response_content = response['choices'][0]['message']['content'].strip()
        cleaned_response = clean_special_characters(response_content)
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error generating recipe from text: {e}")
        raise

async def updated_recipe(slug: str, recipe: dict):
    headers = {
        'Authorization': f'Bearer {mealie_api_key}', 
        'Content-Type': 'application/json'
    }
    
    recipe_data = json.dumps(recipe)
    print(f"Recipe Data: {recipe_data}")
    async with aiohttp.ClientSession() as session:
        async with session.put(mealie_base_url + f"api/recipes/{slug}", json=recipe_data, headers=headers) as response:
            if response.status == 200 or 201:
                print("Recipe successfully updated.")
            else:
                print(f"Failed to update recipe. Status code: {response.status}")
                print(await response.text())

async def upload_recipe_to_mealie(recipe: dict):
    headers = {
        'Authorization': f'Bearer {mealie_api_key}', 
        'Content-Type': 'application/json'
    }
        
    async with aiohttp.ClientSession() as session:
        async with session.post(mealie_base_url + "api/recipes", json=recipe, headers=headers) as response:
            if response.status == 200 or 201:
                print("Recipe successfully uploaded.")
                slug = await response.text()
                await updated_recipe(slug, recipe)
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
                generated_recipe = await generate_recipe_from_text(extracted_text)
            except Exception as e:
                generated_recipe = None

            if generated_recipe:
                await upload_recipe_to_mealie(generated_recipe)

if __name__ == '__main__':
    asyncio.run(main())
