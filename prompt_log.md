## Tools

CodeX: Python implementation, building first version, debugging, tests. 

## CodeX Prompts
# First Version + embedding testing model: 
> I want to go for the cooking direction where that dataset is hundreds of recipes and the user can input what ingredients they currently have and the app will search for these ingredients and return the recipes that includes the ingredients and return a dish.

> You’re building an app that uses a vector database, rather than implementing the database itself. The assignment lists today, October 26, at 8 PM as the deadline and estimates 4.5 hours.
Follow this order:
1. Choose a useful idea and real dataset: a few hundred items or chunks minimum.
2. Write two semantic-search examples: queries that should retrieve relevant items without sharing important keywords.
3. Start a new standalone project. Python + ChromaDB is recommended; a CLI is sufficient.
4. Prove persistence: add a small sample, restart, and confirm it remains.
5. Load your corpus, splitting long documents into smaller chunks.
6. Implement search and runtime additions. Newly added items must be immediately searchable.
7. Make results useful: explain recommendations, answer questions, compare matches, or flag duplicates.
8. Test the complete workflow, including both semantic examples and restarting.

> Explain how vector database search works in my project 
> Your app combines semantic search through ChromaDB with category filtering and ingredient ranking.
1. Recipes become searchable vectors
Each recipe’s text is converted into an embedding: a list of numbers representing its meaning. Your project uses the all-MiniLM-L6-v2 embedding model.
ChromaDB stores these vectors alongside the recipe information. Long recipes are split into overlapping chunks so their content fits the model.
2. The user’s description becomes another vector
For a request such as:
“A cozy dinner on a cold winter night”

The same model converts that sentence into a vector. ChromaDB compares it with the stored recipe vectors using cosine distance. A lower distance means greater semantic similarity.
This can find a comforting casserole even if its recipe never uses the words “cozy” or “winter.” That is the main advantage over exact keyword search.
3. Your app filters incompatible results
Semantic similarity alone can produce mistakes. Your app therefore applies additional rules:
- Discard results above the configured distance threshold of 0.70.
- Combine matching chunks so each recipe appears only once.
- Apply meal/category constraints—for example, exclude breakfast dishes from an ordinary dinner request.
These category rules are your application code, not something ChromaDB automatically understands.
4. Pantry ingredients determine the final ranking
If the user enters pantry ingredients, your app compares them with each eligible recipe’s ingredients. It prioritizes recipes that use something available, then those requiring fewer missing or unverified ingredients.
Common seasonings are assumed available. Without pantry ingredients, results stay ordered by semantic similarity.
5. The frontend displays the recipes
The app returns the ranked recipes, ingredients, instructions, and pantry counts. The cartoon illustrations are selected separately; they do not affect vector search.

# Developing Frontend
> OK, I want a functioning app aside from VS code that has a front end that users can use, build it, using the theme of a cook book.
> Built your cookbook-style frontend, connected to your existing ChromaDB collection.
You can now:
- Browse all 500 recipes.
- Search by pantry ingredients and meal preferences.
- Open recipes with checkable ingredients and instructions.
- Add recipes that persist and become searchable immediately.

>OK, the search results should be layed out with more design. They should be horizontally layed out for the user to slide left and right, like choosing a movie on an air plane's tv.
>where should I edit to make the search results horizontal
>In VS Code, edit web/style.css. Search for:
.recipe-carousel
That controls the horizontal layout. The latest rules near the bottom control the large centered card and smaller side cards.
For scrolling, selection, and arrow-button behavior, edit web/app.js, especially:
updateCarousel()
selectRecipe()
slideRecipes()
Your current app already has this horizontal carousel. If you still see an older layout, refresh Chrome with Cmd+Shift+R.
>It should be symmetrical, with the one selected to be the biggest and in the middle, while ones on the side getting smaller and smaller, when the user scrolls, the one selected changes

# Debugging
> OK, I tested the app, but often times I only have 1 item in hand, which doesn't really work because I would still need a lot to make the dish. When you present the search results, rank from top match to bottom.
> Where should I put this in VS code, which file does this portion belong?
> How does implementing filters relate to vector spaces, are key words matched by meaning or just word search?
> i only have one or zero item on hand for all the recipes suggested, what is going on? Am I have too less of data in dataset
> The main reason is that you entered only rice. “1 on hand” means the recipe uses one ingredient from your list—not that it’s a poor match. With only one ingredient listed, a recipe can match at most one pantry item.
Enter everything you actually have, for example:
rice, eggs, onion, garlic, butter, salt, pepper
500 recipes is enough for the assignment, but a larger, more varied collection could improve your choices. It won’t solve the ingredient-count issue by itself. Another limitation is that matching is strict: rice and white rice may currently be treated as different ingredients.
> OK, this is too narrow of research, seasoning such as oil, salt, pepper, sugar can ba ignored in research and assume we have them. The search is focused more on raw ingrdiantes such as beef, brocoli, etc, does not include seasoning and flavoring
> what is the problem with the narrow search mentioned earlier
> The earlier search was too narrow because it focused heavily on exact ingredient matches. If you entered only “rice,” most recipes matched just that one ingredient and still required several others. Counting salt, oil, and seasonings as missing made this worse.
We improved it by assuming common seasonings are available, ranking recipes by pantry fit and fewer missing ingredients, and using semantic search for your meal description.
> the search is not correct, don't put dishes in here when the word Beverage appears, fix this bug and similar bugs where the category of the food doesn't even match
> Food category now filters results before pantry ranking, so matching garlic can’t make a chicken dish appear in a beverage search.
Your exact example now returns only:
- Lemonade
- Aggie Maroon Punch
- Easy Party Punch
- Hot Cranberry Punch
- Heavenly Punch
- Russian Tea
Added checks for soups, salads, desserts, bread, pasta, and breakfast.
> searching cozy dinner produces a breakfast burrito, this is an error, make sure to avoid any coonflicting recipes that don't fit the description by user
> OK, the search results should be layed out with more design. They should be horizontally layed out for the user to slide left and right, like choosing a movie on an air plane's tv
> OK, seperate the search page and a home page. Search page is what we have so far, home page is a dashboard that allows users to browse different recipes at random
