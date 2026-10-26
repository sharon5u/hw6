# First-version verification — AI-generated

## Food-category regression fix

The reported beverage query was retested with `egg, beef, garlic` in the pantry.
All returned recipes were beverages; pantry ranking no longer admits dips or
chicken dishes. Five new tests cover the actual corpus, category mismatches,
compound food names, negative requests, and ingredient/category confusion.
The existing 15 core tests also passed. Categories use conservative title rules;
unusual names and complex requests may need more classification rules.

## Cookbook frontend follow-up

- Full suite: 12 tests passed (8 original tests plus 4 HTTP integration tests).
- Browser search returned Easy Party Punch with the expected pantry matches,
  missing sherbet, and the flagged Kool-Aid ingredient.
- Recipe details displayed ingredients, checkboxes, directions, and a source link.
- Browser recipe creation was tested in an isolated temporary collection. Saving
  Lemon Chickpea Toast opened its complete detail view successfully.
- The narrow-screen layout was visually inspected in the in-app browser.
- Preview: cookbook-preview.png. Start the local server with `python web_app.py`.

Tested locally on October 26, 2026 with Python 3.12.14, ChromaDB 1.5.9, and real all-MiniLM-L6-v2 embeddings.

## Checks performed

- 8 automated tests passed: JSON/Python-list parsing, conservative ingredient matching, incomplete-record rejection and deduplication, flagging omitted ingredient names, semantic retrieval, token-aware long-text chunking, repeat indexing, and interactive add/search followed by search in a new process.
- Actual subset: 500 unique, complete RecipeNLG recipes; 501 vector chunks.
- Reimported all 500 recipes: count stayed at 500 recipes / 501 chunks.
- Independent CLI invocations opened the same persistent database.
- An unrelated bicycle-repair request returned no close matches at the final 0.70 cutoff.

## Semantic examples on the actual corpus

Run with an empty pantry to reproduce the semantic ranking independently of ingredient reranking. These are observed examples, not a claim of broad accuracy.

| Query | First result | Cosine distance |
|---|---|---|
| A refreshing beverage for a summer gathering | Easy Party Punch | 0.6425 |
| A cozy dinner on a cold winter night | Swiss Vegetable Medley | 0.6484 |

For each example, the query's non-stopword tokens are absent from the indexed recipe text (title, description, extracted ingredients, and instructions). This checks exact word overlap, not every possible keyword-search implementation.

- The punch is a shareable drink made with fruit juice, ginger ale, and sherbet. Its title and method support the gathering interpretation even without the query words.
- The vegetable medley is a baked casserole with broccoli, soup, cheese, and sour cream, which is a reasonable cozy-dinner result. Whether it fits an individual user's preferences remains subjective.

## Observed limitations and debugging

- An initial synthetic test expected stew for “Something warming for a chilly evening”; it failed. The final test uses “A hearty vegetable dinner.” Vague requests are not consistently reliable.
- “A meatless supper with Italian flavors” returned a beef casserole in exploratory testing. Negation is not a hard filter.
- The threshold was tightened from 0.85 to 0.70 after unrelated-query inspection. It needs more evaluation; it is not a calibrated confidence score.
- Easy Party Punch's extracted names omit Kool-Aid. The final app flags the original Kool-Aid ingredient line for manual checking.

## Data provenance

Subset size: 474,587 bytes. SHA-256: `cec1b0ac713a9a54a468336a31d559f319cebd348e5596870e19be004d2db2b8`.

The local `data/recipes_500.manifest.json` records exact requests and recipe IDs. See README.md for the original source, mirror, and reproduction commands.

## Recipe photos — October 26

- Full suite: 28 tests passed, including photo mapping, image signatures, local
  asset coverage, attribution, and HTTP image serving.
- Repeated four photo tests after final asset refinements: all passed.
- Original 500 dataset recipes and all 501 current database recipes resolve to
  existing local photos.
- Browser verification: beverage results display beverage photographs; the
  Easy Party Punch detail displays its photo, illustrative label, and credit.
- Library contains 60 reusable photographs. These illustrate dish types, not
  the exact RecipeNLG preparations; some recipes share photographs.
- Saved browser evidence: photo-preview.png.

## Cartoon redesign — October 26

- Four HTTP integration tests passed after adding local font serving.
- Browser verified: rounded font loads, cartoon cookie and bread cards render,
  recipe detail opens with its illustration and checklist, and beverage search
  returns drink cards in the new theme.
- Images are inline SVG and require neither photo metadata nor image downloads.
- Preview evidence: cartoon-preview.png. Dish art is illustrative and reused by
  dish type rather than an exact depiction of every recipe.

## Meal-intent regression — October 26

27 non-HTTP tests passed, including eight category tests. The four HTTP tests
initially could not bind a local port under sandbox restrictions; all four passed
when rerun with local network permission (31 tests total).

Actual query “A cozy dinner on a cold winter night” returned Swiss Vegetable
Medley, Broccoli Casserole, Casserole Italiano, Chicken Casserole, Consomme Chicken,
Brown Rice, and Special Mashed Potatoes (two distinct Chicken Casserole recipes).
No breakfast recipes appeared either without pantry items or with egg/beef/garlic.
Explicit breakfast-for-dinner, bread-for-dinner, dessert-after-dinner, soup-for-dinner,
and negative salad requests have separate regression coverage.

## Keyword filters — October 26

- 27 core/category/filter tests and five HTTP tests passed (32 relevant tests).
- Checked category OR logic, ingredient AND logic, plural/word-boundary matching,
  invalid filter rejection, filtered pagination, search filtering, and description
  conflicts returning no results.
- Browser: Soup + Chicken shows eight matches; Clear restores 501 recipes.
- Saved visual evidence: filter-preview.png.

## Horizontal carousel — October 26

Browser verified cozy-dinner results render in a horizontal carousel. Right arrow
moves from 1 of 8 to 2 of 8; left arrow returns to the first card. End focuses the
last card, updates to 8 of 8, and disables the right arrow. Enter opens the selected
recipe detail. Saved screenshot: carousel-preview.png. Backend unchanged.

## Centered carousel refinement — October 26

Browser verified symmetric side cards and larger selected center card. Next arrow
changed selection from 1 to 2; horizontal scrolling changed 2 to 3; previous arrow
returned to 2. Clicking the centered bread card opened its correct recipe details.
Visual evidence: centered-carousel-preview.png. Navigation is now circular rather
than stopping at the ends. Backend unchanged.

## Home dashboard and Search routes — October 26

Six HTTP integration tests passed, including nine unique random picks, exclusion
of the previous batch, route availability, existing search, filters and additions.
Browser verified Home displays 501 recipes and nine picks; Shuffle replaces picks;
Search navigation opens /search with existing filters and carousel. Beverage
semantic search still returns matching drinks. Evidence: home-preview.png.
