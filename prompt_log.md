# Prompt log — working record

This file was assembled by Codex from the visible conversation. It is not a complete
student-authored process log or a claim of time spent. Review it, add future prompts
verbatim, record your own work, and identify the exact model shown in your app if required.

## Tools used and purpose

- Codex: dataset research, Python implementation, debugging, tests, and setup notes.
- Web search/browser retrieval: assignment, RecipeNLG data cards, current Chroma docs.
- Python and terminal tools: fetch a small subset, build the index, test CLI behavior.
- Chroma's all-MiniLM-L6-v2 ONNX model: local embeddings used by the app, not a chat model.
- No language-model API is used inside the app.

## Important user prompts (verbatim)

> I am completing a homework to build a vector database: [https://www.cs.cmu.edu/\~113/hw6.html](https://www.cs.cmu.edu/~113/hw6.html) read the instructions and tell me what I should do

> OK, brainstorm some ideas for me

> I want to go for the cooking direction where that dataset is hundreds of recipes and the user can input what ingredients they currently have and the app will search for these ingredients and return the recipes that includes the ingredients and return a dish, does this meet the requirements

> 好的,就这么做，我现在第一步需要干什么

> 帮我把我需要做的都列出来，从第一步到提交

> ok, help me do the second step, find a dataset for my project

> use english now, please help me built the first version of my app

> No, the dataset it too large, help me extract 500 recipes from there and continue from there

## Development record — AI-generated factual notes

1. Discussed why ingredient-only matching does not demonstrate semantic search.
   Selected meal-intent retrieval plus explicit pantry matching.
2. Researched RecipeNLG and its fields. Initially suggested the full download.
   User requested a small extract instead because the full dataset is too large.
3. Located a readable Hugging Face mirror and used its rows API. Downloaded 600
   complete unique recipes from six windows; selected 500 using seed 42 (about 463 KB).
4. Installed ChromaDB 1.5.9 in a Python 3.12 environment after network access was granted.
5. Built data parsing, local model caching, token-aware chunking, persistent storage,
   retrieval, pantry reranking, runtime additions, and a CLI.
6. Downloaded the real embedding model and indexed the 500 recipes into 501 chunks.
7. Initial testing showed weak matches for vague warmth-related requests and poor
   handling of negation. An initial integration assertion expecting stew from
   "Something warming for a chilly evening" failed. Replaced that speculative
   test with a concrete vegetable-dinner test and recorded the limitation rather
   than claiming the failed example worked. Tightened the distance cutoff from
   0.85 to 0.70 after observing irrelevant bicycle-query results around 0.74.
8. Tested actual semantic examples against the 500-recipe corpus, including a
   beverage query and a winter-dinner query. Details are in TEST_REPORT.md.
9. Found that Easy Party Punch's extracted ingredient names omit Kool-Aid. Added
   explicit flags for raw ingredient lines not covered by extracted names, with a regression test.
10. All 8 automated tests passed. Repeated the complete import and verified that
    500 recipes / 501 chunks remained unchanged. Added a launch script and initialized
    a local Git repository; nothing was published or submitted.

## Continue here

### Frontend follow-up prompt (verbatim)

> OK, I want a functioning app that has a front end that users can use, build it, using the theme of a cook book.

Codex added a local Python HTTP server and a responsive HTML/CSS/JavaScript cookbook
interface connected to the existing Chroma collection. Added four HTTP tests for
saving/searching/persistence, static serving, validation, and cross-origin rejection.
The full 12-test suite passed. Browser checks used the actual collection for search
and a separate disposable collection for testing recipe creation.

Add your actual prompts, your debugging observations, changes you made, and actual
time spent. Do not invent development steps or rewrite prompts as if you had asked them.

### Pantry ranking follow-up (verbatim)

> OK, I tested the app, but often times I only have 1 item in hand, which doesn't really work because I would still need a lot to make the dish. When you present the search results, rank from top match to bottom.

Codex replaced the weighted semantic-first ranking with pantry-first ranking among
semantically eligible recipes. Missing and unverified ingredient counts determine
shopping effort; coverage and semantic distance break ties. Removed the candidate
cap for this small corpus and added result-card counts and four ranking tests.

### Main-ingredient matching follow-up (verbatim)

> OK, this is too narrow of research, seasoning such as oil, salt, pepper, sugar can ba ignored in research and assume we have them. The search is focused more on raw ingrdiantes such as beef, brocoli, etc, does not include seasoning and flavoring

Codex added an explicit seasoning/flavoring list, excluded those items from pantry
coverage and shopping penalties (including quantity-bearing unverified lines),
and updated the browser and CLI explanation. Main ingredients remain checked.
Seasoning-only pantry input falls back to semantic ordering.

### Category correction prompt (verbatim)

> the search is not correct, don't put dishes in here when the word Beverage appears, fix this bug and similar bugs where the category of the food doesn't even match

Codex traced this to pantry ranking promoting semantically loose, wrong-category
recipes. Added explicit category constraints before ranking using title-based
classification, plus five tests including the screenshot's exact query and pantry.
Also verified the existing 15 core tests. The conservative rules may exclude
unusually named recipes; unknown categories are not silently used as fallback.

### Recipe photo prompt (verbatim)

> Have a photo ready for each dish the app recommends

Codex added 60 locally stored Wikimedia photos, dish-type matching for cards and
recipe details, and visible illustrative labels with author/license/source credit.
RecipeNLG has no exact-recipe image field, so similar recipes share representative
photos. New recipes receive a matching photo or fallback automatically. All 501
recipes currently stored resolve to a local image. The 28-test suite passed;
photo tests were repeated after final asset refinements. Browser preview verified
loaded photographs and attribution. PHOTO_CREDITS.md documents all sources.

### Cartoon redesign prompt (verbatim)

> These images don't look right, the photo should be a cartoon image of the dish might look like. Also, change the entire web app's style to cartoon and cute fonts.

Replaced photographs in the interface with original inline SVG food illustrations;
added a pastel cartoon theme, rounded cards, playful buttons, and local Nunito font.
Illustrations also work with older API responses lacking photo metadata. Recipe
search, pantry counts, adding recipes, and recipe detail interactions are retained.

### Meal-intent correction prompt (verbatim)

> searching cozy dinner produces a breakfast burrito, this is an error, make sure to avoid any coonflicting recipes that don't fit the description by user

Made lunch/dinner/supper/main-course requests require a recognized meal category
and exclude breakfast, snacks, bread, desserts, beverages and condiments unless
explicitly requested. Explicit breakfast/brunch labels now take precedence over
casserole/pasta classification. Tested breakfast-for-dinner exceptions, negative
category requests, and real cozy-dinner searches with and without pantry inputs.
Rules support meal/category constraints; arbitrary natural-language preferences
still rely on semantic retrieval and are not guaranteed hard constraints.

### Keyword filters prompt (verbatim)

> OK, now the app seems a bit too simple, implement a filter feature where the user can choose key words to filter dishes

Added accessible checkbox chips for dish types and ingredient keywords with Apply
and Clear controls. Shared backend filtering supports browsing and semantic search,
validates the filter vocabulary, and runs before ranking limits and pagination.
Added unit and HTTP integration coverage and verified applying/clearing in browser.

### Horizontal carousel prompt (verbatim)

> OK, the search results should be layed out with more design. They should be horizontally layed out for the user to slide left and right, like choosing a movie on an air plane's tv

Changed recipe results and collection pages into a horizontal snap-scrolling shelf
with larger cartoon cards, previous/next arrows, visible-result position, and
keyboard Arrow/Home/End navigation. Native touch/trackpad scrolling is supported.
Verified arrow navigation, end boundary, and opening a recipe with Enter in browser.

### Centered carousel prompt (verbatim)

> It should be symmetrical, with the one selected to be the biggest and in the middle, while ones on the side getting smaller and smaller, when the user scrolls, the one selected changes

Implemented a circular centered carousel with progressive side-card scaling,
horizontal trackpad/wheel and swipe selection, arrow/keyboard controls, and side
card selection before opening. The first result remains the initial selection;
wrapping keeps neighboring results on both sides.

### Home dashboard prompt (verbatim)

> OK, seperate the search page and a home page. Search page is what we have so far, home page is a dashboard that allows users to browse different recipes at random

Added separate Home and Search routes with shared navigation and dialogs. Home
samples nine recipes, highlights one, and supports shuffling without immediate
batch repeats when enough records exist. Search retains its existing behavior.
Added discovery endpoint tests for unique sampling, exclusions and both routes.
