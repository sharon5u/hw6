## Web APP for HW 6 - Pantry Pal
Pantry Pal is a recipe discovery app that helps users find recipes through meaning-based search, available ingredients, and customizable filters new. User can enter their description of the meal they want and put down the ingredients they have to search for a dish.

## Data Source and Info
Data is originally from RecipeNLG: a novel dataset of cooking recipes.
One item: One complete RecipeNLG recipe, including its title, ingredients, and cooking instructions.
The searchable text combines the title, description if available, ingredient names, and instructions. Long recipes are split into chunks of 240 tokens.
Amount loaded: The original dataset contains 500 recipes, stored as 501 vector chunks (one that I added). Recipes added through the app increase this count.
Metadata: Each chunk stores its recipe ID and the complete recipe as JSON, including its title, ingredients, ingredient names, directions, description, source, and original recipe link. This allows the search to retrieve a matching chunk of data but display the entire recipe.

## How to add/use?
User can add an entry to the dataset by adding their own recipe (name, ingredients, steps). 
User can search for a recipe by entering ingredients, filtering, and describing the occasion/feature of the recipe. 

## Two queries
1. "A refreshing beverage for a summer gathering” --> Easy Party Punch
The recipe does not contain the important query words “refreshing,” “beverage,” “summer,” or “gathering.” Semantic search connects the request to a shareable fruit drink and an exact keyword search would miss the meaningful connections between refreshing and punch, for example.  
3. “A cozy dinner on a cold winter night” --> Swiss Vegetable Medley
The recipe does not contain the important query words “cozy,” “dinner,” “cold,” “winter,” or “night.” Semantic search connects that request to a warm, baked vegetable-and-cheese dish. An exact keyword search would miss the meaningful connections between cozy and baked vegetables, for example. 

## How to obtain data
People can download and load the dataset using the files in the repository. From the folder, run:
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python fetch_recipes.py #saves the recipes locally
python app.py import data/recipes_500.json #generates their embeddings and loads them into a persistent ChromaDB database.
python web_app.py

Then open **http://127.0.0.1:8000** in your browser.

## Vector Database (Wrote with AI's assistance) 
The app uses ChromaDB 1.5.9 with persistent local storage and the all-MiniLM-L6-v2 embedding model, running through ONNX.
The first time recipes are imported or embedded, Chroma downloads the model—approximately 79 MB. After the dependencies, dataset, and model are downloaded, searching and adding recipes work locally without an internet connection or API key.

## How to run app (Wrote with AI's assistance) 
Install Python 3.12, then open a terminal in the project folder and run:
#Create and activate a virtual environment (macOS/Linux)
python3.12 -m venv .venv
source .venv/bin/activate

#Install dependencies
pip install -r requirements.txt

#Download and load the recipe dataset
python fetch_recipes.py
python app.py import data/recipes_500.json

#Start the app
python web_app.py
Open http://127.0.0.1:8000 in your browser. Internet access is required for the initial downloads. Keep the terminal open while using the app; press Ctrl+C to stop it.
