const $ = s => document.querySelector(s);
let page = 1, searching = false, results = [], currentPantry = [], requestId = 0;
let activeFilters = {types:[], ingredients:[]};
const filterQuery = () => {const params=new URLSearchParams();activeFilters.types.forEach(x=>params.append('type',x));activeFilters.ingredients.forEach(x=>params.append('ingredient',x));return params.toString();};
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Original vector illustrations. No remote image requests or photo API needed.
function cartoonKind(recipe) {
 const t=recipe.title.toLowerCase();
 const rules=[[/apricot salad|ambrosia|fruit salad/,'fruit'],[/lemon.*bar/,'cake'],[/bark|candy/,'brownies'],[/cookie|snickerdoodle/,'cookies'],[/brownie|fudge|chocolate.*bar/,'brownies'],[/cake|torte/,'cake'],[/pie|tart|quiche/,'pie'],[/bread|roll|toast|biscuit/,'bread'],[/muffin|cupcake/,'muffin'],[/pancake|waffle/,'pancakes'],[/tea|coffee|cocoa/,'tea'],[/lemonade|punch|juice|drink|smoothie|shake|slush|beverage/,'drink'],[/ice cream|sherbet/,'icecream'],[/green bean/,'beans'],[/salad|slaw/,'salad'],[/pizza/,'pizza'],[/spaghetti|pasta|noodle|macaroni|lasagna/,'pasta'],[/soup|stew|chili|chowder/,'soup'],[/burger|sandwich/,'burger'],[/chicken|turkey|wings/,'chicken'],[/fish|salmon|tuna|shrimp/,'fish'],[/beef|steak|meat|roast/,'beef'],[/rice/,'rice'],[/potato|potatoes/,'potatoes'],[/broccoli|vegetable|carrot|zucchini/,'salad'],[/pudding|gelatin|jello/,'pudding']];
 const named = rules.find(([pattern])=>new RegExp('\\b(?:'+pattern.source+')(?:s)?\\b').test(t))?.[1];
 if(named)return named;
 const ingredients=(recipe.ingredient_names||[]).join(' ').toLowerCase();
 if(/chocolate|sugar|marshmallow|gelatin/.test(ingredients)&&!/chicken|beef|pork|fish/.test(ingredients))return 'cake';
 return 'casserole';
}
function dishDrawing(kind, title='A tasty dish') {
 const face=(x,y)=>`<g fill="#553c38" stroke="none"><circle cx="${x-12}" cy="${y}" r="3"/><circle cx="${x+12}" cy="${y}" r="3"/></g><path d="M${x-5} ${y+7}q5 7 10 0" fill="none"/><g fill="#f29f9b" stroke="none"><ellipse cx="${x-22}" cy="${y+7}" rx="7" ry="4"/><ellipse cx="${x+22}" cy="${y+7}" rx="7" ry="4"/></g>`;
 const ellipse=(x,y,rx,ry,c)=>`<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${c}"/>`;
 const plate=ellipse(180,176,112,25,'#fffdf4')+ellipse(180,174,90,15,'#f2ddda');
 const bowl=(filling)=>`<path d="M77 132q7 77 103 77t103-77" fill="#9ed9ca"/>${ellipse(180,132,103,33,'#fffdf4')}${ellipse(180,132,88,24,filling)}`;
 let food='';
 if(kind==='cookies') {food=plate;for(const [x,y] of [[134,131],[216,131],[175,163]])food+=ellipse(x,y,40,29,'#e9b574')+`<g fill="#8e5d45" stroke="none"><circle cx="${x-17}" cy="${y-8}" r="4"/><circle cx="${x+14}" cy="${y-13}" r="4"/><circle cx="${x+22}" cy="${y+9}" r="4"/></g>`;food+=face(175,164);}
 else if(kind==='bread'){food=plate+`<path d="M99 169v-43q-18-54 35-57q26-20 48-1q26-13 47 5q41 4 32 51v45Z" fill="#dfa16b"/><path d="M119 160v-38q-14-32 20-32q20-18 40 0q30-20 50 3q23 4 13 29v38Z" fill="#ffe6a9"/>`+face(180,125);}
 else if(kind==='drink'){food=`<path d="M135 68h93l-14 130h-65Z" fill="#fffdf4"/><path d="M143 107h76l-10 82h-56Z" fill="#ffc875"/><path d="M192 139l18-98h29" fill="none" stroke="#d9849b" stroke-width="8"/><circle cx="130" cy="79" r="29" fill="#ffe879"/><path d="M110 79h40m-20-20v40" stroke="#fff9da"/><g fill="#fff9e0" stroke="none"><rect x="156" y="113" width="18" height="17" rx="4"/><rect x="187" y="135" width="15" height="13" rx="3"/></g>`+face(181,156);}
 else if(kind==='tea'){food=plate+`<path d="M241 112q59-12 27 45l-31 6" fill="#f8c1ca"/><path d="M110 100h133v46q0 48-66 48t-67-48Z" fill="#f8c1ca"/>`+ellipse(176,100,66,17,'#fff9e9')+ellipse(176,100,53,10,'#a77c5c')+face(177,142)+`<path d="M155 72q-16-15 0-28m35 28q-16-15 0-28" fill="none" stroke="#b8a092"/>`;}
 else if(kind==='cake'||kind==='brownies'){food=plate+`<path d="M112 100l109-25l39 88l-148 22Z" fill="${kind==='brownies'?'#99624f':'#f1c397'}"/><path d="M112 139l132-24m-132 45l141-23" stroke="${kind==='brownies'?'#6e443b':'#fff5d5'}" stroke-width="10"/><path d="M112 100l109-25l27 48l-136 25Z" fill="${kind==='brownies'?'#81503f':'#f5a9ba'}"/>`+face(171,153)+`<circle cx="193" cy="85" r="14" fill="#e9757c"/><path d="M193 72q0-17 15-20" fill="none" stroke="#759b65"/>`;}
 else if(kind==='pie'||kind==='pudding'){food=plate+`<path d="M95 130h170l-15 58H111Z" fill="#efba81"/>`+ellipse(180,130,85,28,'#f4cd90')+`<path d="M120 116l110 27m-87-37l103 26m-124 11l104-33m-78 44l103-32" stroke="#fff0bc" stroke-width="8"/>`+face(180,169);}
 else if(kind==='pancakes'){food=plate;for(const y of [164,149,134])food+=ellipse(180,y,85,24,'#e9b374');food+=`<path d="M130 123q50-25 97 0l-10 27q-10 12-16-6q-16 28-25 0q-18 9-22-10Z" fill="#b77b53"/><rect x="164" y="111" width="30" height="17" rx="5" fill="#ffe895"/>`+face(180,166);}
 else if(kind==='muffin'){food=plate+`<path d="M127 125h106l-15 65h-76Z" fill="#b7dace"/><path d="M124 127q-25-36 10-48q2-31 35-24q28-25 46 8q41-2 34 37q20 26-16 35Z" fill="#efbd8d"/>`+face(180,158);}
 else if(kind==='icecream'){food=`<path d="M137 125h87l-43 97Z" fill="#efc285"/><path d="M150 149l47 32m-35-40l40 27m-4-26l-36 28" stroke="#c79760"/><path d="M131 128q-25-39 9-52q-5-38 38-39q41-4 43 36q37 15 10 55Z" fill="#f5bacb"/>`+face(179,93);}
 else if(kind==='pizza'){food=plate+`<path d="M101 91q79-35 158 0l-78 117Z" fill="#ffe09a"/><path d="M101 91q79-35 158 0" stroke="#d89b68" stroke-width="16"/><g fill="#e78777"><circle cx="151" cy="110" r="13"/><circle cx="212" cy="113" r="13"/><circle cx="182" cy="156" r="12"/></g>`+face(179,128);}
 else if(kind==='burger'){food=plate+`<path d="M96 124q4-72 84-72t84 72Z" fill="#edbd7e"/><path d="M97 145h166v26q-83 35-166 0Z" fill="#edbd7e"/><path d="M97 138h166" stroke="#865747" stroke-width="23"/><path d="M96 122l22 10 23-7 25 9 29-9 26 8 22-10 21 5" fill="none" stroke="#9abc77" stroke-width="10"/>`+face(180,92);}
 else if(['beef','fish','chicken','potatoes'].includes(kind)){food=plate;if(kind==='fish')food+=`<path d="M109 130q66-69 128-2l33-27v58l-34-22q-64 59-127-7Z" fill="#f3af91"/><path d="M149 111l16 39m15-47l15 49" stroke="#e68c79"/>`;else if(kind==='chicken')food+=`<path d="M202 146l37 28q25-4 23 12q-1 17-18 12q-19 12-22-8l-40-29" fill="#fff8df"/><path d="M190 167q-67 22-79-25q-13-51 39-63q46-12 61 29q11 33-21 59Z" fill="#dca16c"/>`;else if(kind==='beef')food+=`<path d="M110 123q14-48 69-31q78-16 73 37q6 58-67 47q-87 22-75-53Z" fill="#bd796a"/><path d="M131 115l89 35m-68-48l83 32" stroke="#87564e" stroke-width="7"/>`;else for(const [x,y] of [[140,137],[211,132],[180,164]])food+=ellipse(x,y,39,25,'#eac58b');food+=face(kind==='chicken'?157:179,137);}
 else {const color={fruit:'#f7c1bd',salad:'#b7d98b',beans:'#b9d99b',rice:'#fff1c9',pasta:'#f8cf83',soup:'#efb477',casserole:'#edc580'}[kind]||'#edc580';food=bowl(color);if(kind==='beans'){for(let i=0;i<7;i++)food+=`<path d="M${119+i*16} 119q-13 20 9 30" fill="none" stroke="#6eac70" stroke-width="8"/>`;}else if(kind==='pasta'){for(let i=0;i<5;i++)food+=`<path d="M${118+i*25} 120q-23 23 11 25t10-25" fill="none" stroke="#d69e57" stroke-width="5"/>`;}else{for(const [x,y,c] of [[133,125,'#e98878'],[210,125,'#e98878'],[176,140,'#88b979'],[159,118,'#88b979'],[229,139,'#f7df98']])food+=ellipse(x,y,12,8,c);}food+=face(180,177);}
 return `<svg viewBox="0 0 360 250" role="img" aria-label="${escapeHTML('Cartoon illustration of '+title)}" xmlns="http://www.w3.org/2000/svg"><g stroke="#654d45" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">${ellipse(180,215,108,9,'#e8cdbf')}<g stroke="none" fill="#fff9e9"><circle cx="76" cy="72" r="6"/><circle cx="287" cy="171" r="5"/></g><path d="M278 58v18m-9-9h18M69 157v12m-6-6h12" stroke="#d8a45e"/>${food}</g></svg>`;
}
function photoMarkup(recipe, detail=false) {
 return dishDrawing(cartoonKind(recipe), recipe.title)+'<span class="photo-caption">A little dish doodle ✦</span>';
}

async function api(url, data) {
 const response = await fetch(url, data ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)} : {});
 const body = await response.json();
 if (!response.ok) throw Error(body.error || 'Something went wrong. Please try again.');
 return body;
}
function count(n){ document.querySelectorAll('[data-recipe-count]').forEach(el=>el.textContent=n.toLocaleString()); }
function render(){
 $('#carousel-toolbar').hidden=!results.length;
 $('#recipes').innerHTML = results.map((item,i)=>{const r=item.recipe;return `<button class="recipe-card" data-index="${i}"><div class="card-art"><span class="recipe-number">${searching ? "Match" : "No."} ${String(searching?i+1:(page-1)*12+i+1).padStart(2,'0')}</span><span class="recipe-badge">${r.source==='user'?'FROM YOUR KITCHEN':'THE COLLECTION'}</span>${photoMarkup(r)}</div><div class="card-body"><h3>${escapeHTML(r.title)}</h3><p class="card-description">${escapeHTML(r.description || r.ingredient_names.slice(0,5).join(' · '))}</p><div class="card-meta"><span>${r.ingredients.length} ingredients</span><span>·</span><span>${r.directions.length} steps</span></div><div class="card-footer"><span class="match-badge">${searching && currentPantry.length ? `${item.have.length} on hand · ${item.missing.length} missing${item.unverified?.length ? ` · ${item.unverified.length} to check` : ""}` : item.loose?'A little outside your request':'Make something lovely'}</span><span>Read recipe ↗</span></div></div></button>`}).join('');
 selectedRecipe=0;
 $('#recipes').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{const index=Number(b.dataset.index);if(index===selectedRecipe)openRecipe(results[index]);else selectRecipe(index);}));
 requestAnimationFrame(updateCarousel);
}
async function browse(scroll=false){
 const id=++requestId; searching=false; $('#reset').hidden=true;
 $('#collection-kicker').textContent='02 / THE RECIPE COLLECTION';
 $('#collection-heading').textContent='A cookbook worth exploring.';
 $('#collection-description').textContent='Old favorites, new discoveries, and your next signature dish.';
 $('#status').textContent='Opening the cookbook…'; $('#recipes').innerHTML='';$('#carousel-toolbar').hidden=true; $('#pagination').hidden=true;
 try {const data=await api(`/api/recipes?page=${page}&${filterQuery()}`);if(id!==requestId)return;count(data.count);$('#collection-description').textContent=`${data.total} recipes match your current filters.`;results=data.recipes.map(recipe=>({recipe}));render();$('#status').textContent=results.length?'':'No recipes match these filters. Clear a keyword or try another dish type.';$('#pagination').hidden=!results.length;$('#page-label').textContent=`Page ${page} of ${Math.max(1,Math.ceil(data.total/12))}`;$('#previous').disabled=page===1;$('#next').disabled=page*12>=data.total;} catch(e){if(id===requestId)$('#status').textContent=e.message+' Make sure the Python server is running.';}
 if(scroll)$('#collection').scrollIntoView({behavior:'smooth'});
}
$('#search-form').addEventListener('submit',async event=>{
 event.preventDefault(); const need=$('#need').value.trim(); if(!need)return;
 const id=++requestId;currentPantry=$('#pantry').value.split(',').map(x=>x.trim()).filter(Boolean);
 $('#search-button').disabled=true;$('#search-button').textContent='Finding your next dish…';
 $('#status').textContent='Looking through your cookbook for something just right…';$('#recipes').innerHTML='';$('#carousel-toolbar').hidden=true;$('#pagination').hidden=true;
 $('#collection-heading').textContent='A few delicious possibilities.';$('#collection-kicker').textContent='02 / SELECTED FOR YOUR TABLE';$('#collection-description').textContent=need + (currentPantry.length ? ' — Ranked by main ingredients: uses yours first, then fewest missing or unverified. Common seasonings are assumed.' : ' — Ranked from closest to loosest match.');$('#reset').hidden=false;
 $('#collection').scrollIntoView({behavior:'smooth'});
 try{const data=await api('/api/search',{need,pantry:currentPantry,filters:activeFilters});if(id!==requestId)return;currentPantry=data.main_pantry;searching=true;results=data.results;render();$('#status').textContent=results.length?'':'No close matches this time. Try clearing a filter or changing your description.';}catch(e){if(id===requestId)$('#status').textContent=e.message;}finally{$('#search-button').disabled=false;$('#search-button').innerHTML='Find my next dish <span>→</span>';}
});
function openRecipe(item){
 const r=item.recipe;let summary='';
 if(item.have && currentPantry.length){summary=`<div class="pantry-summary"><strong>Your pantry, this recipe</strong><p>Main ingredients on hand: ${escapeHTML(item.have.join(', ')||'No ingredient names matched')}</p><p>Main ingredients to pick up: ${escapeHTML(item.missing.join(', ')||'None from the extracted names')}</p>${item.assumed?.length?`<p>Assumed available: ${escapeHTML(item.assumed.join(', '))}</p>`:''}${item.unverified?.length?`<p>Also check: ${escapeHTML(item.unverified.join('; '))}</p>`:''}</div>`;}
 let source='';if(r.link){try{const url=new URL(r.link.includes('://')?r.link:'https://'+r.link);if(['http:','https:'].includes(url.protocol))source=`<a class="source-link" href="${escapeHTML(url.href)}" target="_blank" rel="noopener noreferrer">Original recipe source ↗</a>`;}catch{}}
 $('#detail-content').innerHTML=`<span class="chapter">${r.source==='user'?'FROM YOUR KITCHEN':'A PAGE FROM THE COLLECTION'}</span><h2>${escapeHTML(r.title)}</h2><figure class="detail-photo-wrap">${photoMarkup(r,true)}</figure><p class="photo-credit">An original cartoon impression — your finished dish may look different.</p><p class="muted">${escapeHTML(r.description||`${r.ingredients.length} ingredients · ${r.directions.length} steps`)}</p>${item.loose?'<p class="muted">A loose match — see whether this suits your craving.</p>':''}${summary}<div class="recipe-detail-columns"><section><h3>What you’ll need</h3><ul class="ingredient-list">${r.ingredients.map(x=>`<li><label class="checklist-label"><input type="checkbox"><span>${escapeHTML(x)}</span></label></li>`).join('')}</ul></section><section><h3>Let’s make it</h3><ol class="method">${r.directions.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ol></section></div><p class="detail-note">Common oils, salt, pepper, sugar, spices and flavorings are assumed available and excluded from pantry counts. Check all quantities below; dietary restrictions and substitutions aren’t verified.</p>${source}`;
 $('#detail').showModal();
}
function openAdd(){$('#add-status').textContent='';$('#add-dialog').showModal();}
$('#add-nav').onclick=openAdd;$('#add-bottom').onclick=openAdd;
for(const button of document.querySelectorAll('[data-close]'))button.onclick=()=>$('#'+button.dataset.close).close();
for(const dialog of document.querySelectorAll('dialog'))dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
$('#add-form').addEventListener('submit',async e=>{
 e.preventDefault();$('#save-button').disabled=true;$('#save-button').textContent='Saving your recipe…';$('#add-status').textContent='';
 const lines=id=>$(id).value.split('\n').map(x=>x.trim()).filter(Boolean);
 try{const data=await api('/api/recipes',{title:$('#title').value,description:$('#description').value,ingredients:lines('#ingredients'),directions:lines('#directions')});count(data.count);$('#add-dialog').close();$('#add-form').reset();page=1;if(isHome)await loadHome();else await browse();openRecipe({recipe:data.recipe});}catch(error){$('#add-status').textContent=error.message;}finally{$('#save-button').disabled=false;$('#save-button').textContent='Save to my cookbook →';}
});
$('#previous').onclick=()=>{if(page>1){page--;browse(true)}};$('#next').onclick=()=>{page++;browse(true)};
$('#reset').onclick=()=>{page=1;browse(true)};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>{$('#need').value=b.dataset.prompt;$('#need').focus()});
const isHome=location.pathname!=='/search';
$('#home-page').hidden=!isHome;$('#search-page').hidden=isHome;
$(isHome?'#home-nav':'#browse-nav').setAttribute('aria-current','page');
document.title=isHome?'Pantry Pal — Home':'Pantry Pal — Search';
if(!isHome){
 const type=new URLSearchParams(location.search).get('type');
 const chip=[...document.querySelectorAll('.filter-panel input[name="types"]')].find(input=>input.value===type);
 if(chip){chip.checked=true;activeFilters.types=[type];$('#filter-summary').textContent='Active: '+chip.nextElementSibling.textContent;}
 browse();
}
const heroArt=document.querySelector('.illustration svg');
if(heroArt)heroArt.outerHTML=dishDrawing('pasta','a happy bowl of pasta');

function applyFilters(clear=false){
 if(clear)document.querySelectorAll('.filter-panel input').forEach(input=>input.checked=false);
 activeFilters={types:[],ingredients:[]};
 const labels=[];
 document.querySelectorAll('.filter-panel input:checked').forEach(input=>{activeFilters[input.name].push(input.value);labels.push(input.nextElementSibling.textContent);});
 $('#filter-summary').textContent=labels.length?'Active: '+labels.join(' · '):'No filters selected. Explore everything!';
 page=1;
 if(searching && $('#need').value.trim())$('#search-form').requestSubmit();else browse(true);
}
$('#apply-filters').onclick=()=>applyFilters();
$('#clear-filters').onclick=()=>applyFilters(true);

let selectedRecipe=0;
function updateCarousel(){
 const track=$('#recipes'), cards=[...track.querySelectorAll('.recipe-card')], total=cards.length;
 let height=0;
 cards.forEach((card,index)=>{
  let distance=(index-selectedRecipe+total)%total;
  if(distance>total/2)distance-=total;
  const depth=Math.abs(distance), scale=Math.pow(.79,depth);
  const step=Math.min(card.offsetWidth*.78,track.clientWidth*.31);
  card.style.transform=`translate(-50%, -50%) translateX(${distance*step}px) scale(${scale})`;
  card.style.zIndex=String(10-depth);
  card.style.opacity=depth>2?'0':String(1-depth*.16);
  card.style.visibility=depth>2?'hidden':'visible';
  card.style.pointerEvents=depth>2?'none':'auto';
  card.classList.toggle('is-selected',distance===0);
  card.setAttribute('aria-current',distance===0?'true':'false');
  card.setAttribute('aria-label',`${distance===0?'Open':'Select'} recipe ${index+1} of ${total}: ${results[index].recipe.title}`);
  card.tabIndex=distance===0?0:-1;
  height=Math.max(height,card.offsetHeight);
 });
 track.style.height=total?`${height+60}px`:'0px';
 $('#carousel-position').textContent=total?`${selectedRecipe+1} of ${total}`:'';
 $('#slide-left').disabled=total<2;
 $('#slide-right').disabled=total<2;
}
function selectRecipe(index){
 const total=results.length;if(!total)return;
 selectedRecipe=(index+total)%total;
 updateCarousel();
}
function slideRecipes(direction){selectRecipe(selectedRecipe+direction);}
$('#slide-left').onclick=()=>slideRecipes(-1);
$('#slide-right').onclick=()=>slideRecipes(1);
window.addEventListener('resize',updateCarousel);
$('#recipes').addEventListener('keydown',event=>{
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
 event.preventDefault();
 if(!results.length)return;
 selectRecipe(event.key==='Home'?0:event.key==='End'?results.length-1:selectedRecipe+(event.key==='ArrowRight'?1:-1));
 $('#recipes').querySelector('.is-selected').focus({preventScroll:true});
});
// Horizontal touch gestures and trackpad motion rotate the centered selection.
let dragStart=null, suppressCardClick=false, wheelSum=0, wheelTime=0;
$('#recipes').addEventListener('pointerdown',event=>{if(event.button===0)dragStart={x:event.clientX,y:event.clientY};});
$('#recipes').addEventListener('pointerup',event=>{
 if(!dragStart)return;
 const dx=event.clientX-dragStart.x,dy=event.clientY-dragStart.y;dragStart=null;
 if(Math.abs(dx)>35 && Math.abs(dx)>Math.abs(dy)){
  suppressCardClick=true;slideRecipes(dx<0?1:-1);
  setTimeout(()=>suppressCardClick=false,0);
 }
});
$('#recipes').addEventListener('pointercancel',()=>dragStart=null);
$('#recipes').addEventListener('click',event=>{if(suppressCardClick){event.preventDefault();event.stopImmediatePropagation();}},true);
$('#recipes').addEventListener('wheel',event=>{
 const delta=event.shiftKey?event.deltaY:event.deltaX;
 if(Math.abs(delta)<Math.abs(event.shiftKey?event.deltaX:event.deltaY)||!delta)return;
 event.preventDefault();
 const now=performance.now();if(now-wheelTime>250)wheelSum=0;
 wheelSum+=delta;
 if(Math.abs(wheelSum)>45 && now-wheelTime>220){slideRecipes(wheelSum>0?1:-1);wheelSum=0;wheelTime=now;}
},{passive:false});

let homePicks=[],homeRequest=0;
function homeCard(recipe,index,featured=false){
 return `<button class="recipe-card ${featured?'featured-card':''}" data-home-index="${index}"><div class="card-art"><span class="recipe-number">${featured?'A happy little discovery':'Surprise '+String(index+1).padStart(2,'0')}</span>${photoMarkup(recipe)}</div><div class="card-body">${featured?'<span class="chapter">IN THE SPOTLIGHT</span>':''}<h3>${escapeHTML(recipe.title)}</h3><p class="card-description">${escapeHTML(recipe.ingredient_names.slice(0,5).join(' · '))}</p><div class="card-meta">${recipe.ingredients.length} ingredients · ${recipe.directions.length} steps</div><div class="card-footer"><span>Give it a try</span><span>Read recipe ↗</span></div></div></button>`;
}
async function loadHome(){
 const id=++homeRequest;$('#shuffle-recipes').disabled=true;$('#home-status').textContent='Picking a few delicious surprises…';
 const params=new URLSearchParams();homePicks.forEach(r=>params.append('exclude',r.id));
 try{
  const data=await api('/api/discover?'+params.toString());if(id!==homeRequest)return;
  homePicks=data.recipes;count(data.count);$('#discovery-count').textContent=homePicks.length;
  $('#home-featured').innerHTML=homePicks.length?homeCard(homePicks[0],0,true):'';
  $('#home-recipes').innerHTML=homePicks.slice(1).map((r,i)=>homeCard(r,i+1)).join('');
  document.querySelectorAll('[data-home-index]').forEach(button=>button.onclick=()=>openRecipe({recipe:homePicks[Number(button.dataset.homeIndex)]}));
  $('#home-status').textContent=homePicks.length?'Fresh picks are ready. Shuffle again for a new selection.':'Your cookbook is empty. Add a recipe to start exploring.';
 }catch(error){if(id===homeRequest)$('#home-status').textContent=error.message+' Try Shuffle recipes again.';}
 finally{if(id===homeRequest)$('#shuffle-recipes').disabled=false;}
}
$('#shuffle-recipes').onclick=loadHome;
$('#home-mascot').innerHTML=dishDrawing('pancakes','happy pancakes');
if(isHome)loadHome();

api('/api/config').then(config=>{$('#demo-notice').hidden=!config.temporary_demo;}).catch(()=>{});
