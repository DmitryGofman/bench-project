/* =========================================================================
   extras/ — Buy & BOM tab, assembly plan, drawing BOM sheet, one-click files
   -------------------------------------------------------------------------
   · CATALOG   every purchasable item, matched to a design's hardware line by
               its specification text, with the exact name, standard / SKU,
               supplier, link and listed price (Tel Aviv / Gush Dan, Oct 2026 —
               prices are as listed by the shops, call before going).
   · buyList() timber (from the nesting) + hardware + finish + tools, grouped
               by category, with quantities from the live model.
   · assemblyPlan() sub-assemblies in build order, with their parts and the
               fasteners each one uses (folding bench: from its joint schedule).
   ========================================================================= */

var SUPPLIERS = {
  galboreg: { name:'Galboreg (גלבורג), Rishon LeZion', tel:'03-9665902', url:'https://galboreg-shop.co.il/' },
  technobar:{ name:'Technobar (טכנובר), Rishon LeZion', tel:'03-9632333', url:'https://www.technobar.co.il/cnrt/cinvrvt-lmkwvr-tubes' },
  shinitzky:{ name:'Shinitzky Artzi (שניצקי ארצי), Rishon LeZion', tel:'03-6881575', url:'https://www.bearing.co.il/%D7%A7%D7%98%D7%9C%D7%95%D7%92%D7%99%D7%9D/' },
  babigum:  { name:'Babigum 7 (באביגום 7), Rosh HaAyin', tel:'03-9740740', url:'https://babigum7.com/product/%D7%9C%D7%95%D7%97-%D7%A4%D7%95%D7%9C%D7%99%D7%90%D7%AA%D7%99%D7%9C%D7%9F-%D7%99%D7%A8%D7%95%D7%A7-%D7%9C%D7%91%D7%9F-pe/' },
  camping:  { name:'Camping Life (קמפינג לייף), ships nationwide', tel:'', url:'https://www.campinglife.co.il/p/%D7%A4%D7%99%D7%9F-%D7%90%D7%91%D7%98%D7%97%D7%94-12-%D7%9E%D7%9E-%D7%A0%D7%99%D7%A8%D7%95%D7%A1%D7%98%D7%94-%D7%90%D7%95%D7%A8%D7%9A-9-%D7%A1%D7%9E-%D7%A2%D7%9D-2-%D7%9B%D7%93%D7%95%D7%A8%D7%99%D7%95%D7%AA-%D7%A7%D7%A4%D7%99%D7%A6%D7%99%D7%95%D7%AA-%D7%9B%D7%95%D7%9C%D7%9C-%D7%A0%D7%99%D7%A6%D7%A8%D7%94-%D7%91%D7%A7%D7%A6%D7%94-%D7%95%D7%9B%D7%91%D7%9C-%D7%90%D7%91%D7%98%D7%97%D7%94-%D7%A2%D7%9D-%D7%A0%D7%A7%D7%95%D7%93%D7%95%D7%AA-%D7%A2%D7%99%D7%92%D7%95%D7%9F' },
  noyman:   { name:'Noyman (נוימן), Caesarea, delivers', tel:'04-6339422', url:'https://www.noyman-wood.co.il/%D7%91%D7%95%D7%A8%D7%92-%D7%98%D7%95%D7%A8%D7%A7%D7%A1-570-%D7%A0%D7%99%D7%A8%D7%95%D7%A1%D7%98%D7%94-416615---i5733' },
  noyman6:  { name:'Noyman (נוימן), Caesarea, delivers', tel:'04-6339422', url:'https://www.noyman-wood.co.il/%D7%91%D7%95%D7%A8%D7%92-%D7%98%D7%95%D7%A8%D7%A7%D7%A1-670-%D7%A0%D7%99%D7%A8%D7%95%D7%A1%D7%98%D7%94----i2418' },
  villager: { name:'Villager (online)', tel:'', url:'https://www.villager.co.il/items/6302703-500-%D7%9E-%D7%9C-%D7%93%D7%91%D7%A7-%D7%A4%D7%95%D7%9C%D7%99%D7%90%D7%95%D7%A8%D7%99%D7%AA%D7%9F-PUR-%D7%91%D7%A8%D7%9E%D7%94-D4-%D7%9C%D7%94%D7%93%D7%91%D7%A7%D7%AA-%D7%A2%D7%A5-%D7%95%D7%93%D7%A9%D7%90-%D7%A1%D7%99%D7%A0%D7%98%D7%98%D7%99' },
  homecenter:{ name:'Home Center (Dizengoff 50 / Sderot Yerushalayim 31 / HaHashmonaim 117)', tel:'', url:'https://www.homecenter.co.il/products/4041106213' },
  ace:      { name:'ACE (Yigal Alon 59 TA / HaMerkava 38 Holon)', tel:'03-6870405', url:'https://www.ace.co.il/stores' },
  gueta:    { name:'Gueta Avigdor (גואטה אביגדור), Rishon LeZion', tel:'050-9512625', url:'https://shop.guetaavigdor.co.il/product/%D7%A2%D7%A5-%D7%90%D7%95%D7%A8%D7%9F-%D7%9E%D7%95%D7%A7%D7%A6%D7%A2-%D7%95%D7%9E%D7%97%D7%95%D7%98%D7%90-%D7%91%D7%A4%D7%A8%D7%95%D7%A4%D7%99%D7%9C-45x92-%D7%9E%D7%9E/' },
  shults:   { name:'Shults (שולץ), Ra\'anana', tel:'09-7461920', url:'https://shults.co.il/shop/%D7%A2%D7%A5/%D7%A2%D7%A5-%D7%9C%D7%93%D7%A7/%D7%A2%D7%A5-%D7%90%D7%95%D7%A8%D7%9F-45-95-%D7%9E%D7%9E-%D7%9E%D7%95%D7%A7%D7%A6%D7%A2-%D7%95%D7%9E%D7%97%D7%95%D7%98%D7%90/' },
  mhdr:     { name:'MHDR-Elec (online)', tel:'', url:'https://www.mhdr-elec.com/items/3118711-%D7%9E%D7%A7%D7%93%D7%97%D7%99-%D7%A4%D7%95%D7%A8%D7%A1%D7%98%D7%A0%D7%A8-%D7%A7%D7%95%D7%98%D7%A8-35-%D7%9E-%D7%9E-TOTAL' }
};

/* rx matches the design's hardware spec text; cat = shopping-list category */
var CATALOG = [
  { k:'bolt12', rx:/M12[^,;]*hex bolt|hex bolt[^,;]*M12/i, cat:'Bolts, nuts & washers',
    name:'Hex bolt M12 × 80, full thread, stainless A4 (316)', no:'DIN 933 / ISO 4017 M12×80 A4-70', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?path=333', price:12.98, unit:'pc' },
  { k:'nyloc12', rx:/M12 nyloc/i, cat:'Bolts, nuts & washers',
    name:'Nyloc nut M12, stainless 316', no:'DIN 985 M12 A4 · SKU CH1405790414', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?path=30_181_184', price:18.53, unit:'pc' },
  { k:'washer12', rx:/M12[^,;]*washer|washer[^,;]*M12/i, cat:'Bolts, nuts & washers',
    name:'Flat washer M12 (Ø24), stainless 316', no:'DIN 125 / ISO 7089 M12 A4 · SKU CN1405788862', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?path=177', price:4.96, unit:'pc' },
  { k:'m8set', rx:/M8×65|M8 × 65/i, cat:'Bolts, nuts & washers',
    name:'M8 × 65 hex bolt + 2 washers + nyloc, stainless 316', no:'DIN 933 M8×65 A4 + DIN 125 M8 + DIN 985 M8 (SKU CF1405788838)', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?path=327', price:null, unit:'set', note:'Nyloc ₪7.16, washers ₪1.77 each; bolt price on request.' },
  { k:'m10set', rx:/M10/i, cat:'Bolts, nuts & washers',
    name:'M10 hex bolt (length = stack + 20) + 2 washers + nyloc, stainless 316', no:'DIN 933 M10 A4 + DIN 125 M10 + DIN 985 M10', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?path=327', price:null, unit:'set' },
  { k:'tube18', rx:/tube OD18|OD18 ×/i, cat:'Pivot bearings (tube, bushings, washers)',
    name:'Stainless tube 316L, seamless, OD 18 × 2.0 wall (ID 14) — cut into 54.5 mm sleeves', no:'316L instrumentation tube 18×2', sup:'technobar',
    url:'https://www.technobar.co.il/cnrt/cinvrvt-lmkwvr-tubes', price:null, unit:'sleeve', note:'Buy 0.5 m; quote only.' },
  { k:'bush', rx:/bushing/i, cat:'Pivot bearings (tube, bushings, washers)',
    name:'Plain bush, oil-impregnated sintered bronze, ID 18 / OD 22 × 25 (and × 20)', no:'DIN 1850 / ISO 2795 — 18×22×25 and 18×22×20', sup:'shinitzky',
    url:SUPPLIERS.shinitzky.url, price:null, unit:'pc', note:'Call to order; fallback: have POM bushes turned from Ø25 rod.' },
  { k:'thrust', rx:/thrust washer/i, cat:'Pivot bearings (tube, bushings, washers)',
    name:'UHMW-PE (PE1000) sheet 3 mm — cut Ø48 discs, Ø18.5 hole', no:'PE1000 3 mm offcut ≈ 200 × 300', sup:'babigum',
    url:SUPPLIERS.babigum.url, price:null, unit:'disc', note:'One offcut makes all discs (hole saw + 18 mm drill).' },
  { k:'pin', rx:/ball-lock/i, cat:'Lock pins',
    name:'Ball-lock quick-release pin Ø12 × 90 to balls, stainless, push button, with lanyard', no:'Ø12 × 90 stainless ball-lock pin', sup:'camping',
    url:SUPPLIERS.camping.url, price:65, unit:'pc', note:'+ ₪41 shipping per order.' },
  { k:'screw5', rx:/5\s*×\s*70|5×70/i, cat:'Wood screws',
    name:'Torx wood screw 5 × 70, stainless, countersunk', no:'Noyman model 416615 (5×70 A2)', sup:'noyman',
    url:SUPPLIERS.noyman.url, price:0.77, unit:'pc' },
  { k:'screw6', rx:/6\s*×\s*80|6 × 110|6×110/i, cat:'Wood screws',
    name:'Torx wood screw 6 × 70–80, stainless, countersunk', no:'Noyman 6/70 A2 (or SPAX 6×80 A2 at Etz HaMahlef)', sup:'noyman6',
    url:SUPPLIERS.noyman6.url, price:1.30, unit:'pc' },
  { k:'glue', rx:/glue|adhesive/i, cat:'Glue & finish',
    name:'Polyurethane wood glue PUR D4, 500 ml', no:'SOMA FIX S605 PUR D4', sup:'villager',
    url:SUPPLIERS.villager.url, price:29, unit:'bottle' },
  { k:'oil', rx:/sealer|oil|preservative/i, cat:'Glue & finish',
    name:'Clear deck oil, 1 L (three flood coats on every end grain)', no:'Tambour clear deck oil · Home Center 4041106213', sup:'homecenter',
    url:SUPPLIERS.homecenter.url, price:114.90, unit:'1 L' },
  { k:'glide', rx:/glide/i, cat:'Glue & finish',
    name:'Nail-in plastic furniture glide Ø40', no:'generic', sup:'ace', url:SUPPLIERS.ace.url, price:null, unit:'pc' },
  { k:'dowel', rx:/dowel/i, cat:'Lock pins',
    name:'Stainless pin Ø12 × 60 (clevis pin DIN 1444 or cut 316 rod), chamfered', no:'DIN 1444 Ø12 A4 / 316 rod Ø12', sup:'galboreg',
    url:'https://galboreg-shop.co.il/category/?page=9&path=231', price:null, unit:'pc' },
  { k:'barrel', rx:/barrel bolt|tower bolt/i, cat:'Lock pins',
    name:'Barrel bolt 100 mm, stainless', no:'generic', sup:'ace', url:SUPPLIERS.ace.url, price:null, unit:'pc' },
  { k:'uhmw', rx:/UHMW-PE tape|UHMW strip/i, cat:'Pivot bearings (tube, bushings, washers)',
    name:'UHMW-PE strip / tape 2 × 50 mm', no:'PE1000 2 mm strip', sup:'babigum', url:SUPPLIERS.babigum.url, price:null, unit:'pc' },
  { k:'misc', rx:/latch|hook|handle/i, cat:'Lock pins',
    name:'Stainless latch / handle', no:'generic', sup:'ace', url:SUPPLIERS.ace.url, price:null, unit:'pc' }
];
var CAT_ORDER = ['Timber', 'Bolts, nuts & washers', 'Pivot bearings (tube, bushings, washers)', 'Lock pins',
                 'Wood screws', 'Glue & finish', 'Tools (one-off)', 'Other'];

function catalogFor(spec){
  for(var i=0;i<CATALOG.length;i++) if(CATALOG[i].rx.test(spec)) return CATALOG[i];
  return null;
}

/* the shopping list for the current model */
function buyList(model, S, nest){
  var rows = [];
  /* timber: whole bars from the nesting, per section */
  (nest || []).forEach(function(g){
    var n = g.bins.length, m = n*S.cut.len/1000;
    rows.push({ cat:'Timber', name:'Planed pressure-treated pine '+g.sec+' mm, '+S.cut.len+' mm lengths',
      no: g.sec === '38×89' ? 'Buy 42×92 / 45×95 and have the yard plane to 38×89' : g.sec+' planed & treated',
      qty:n, unit:'bars', sup:'gueta', url:SUPPLIERS.gueta.url, price:Math.round(14*S.cut.len/100)/10,
      note: m.toFixed(1)+' m. ₪14/m listed (sale). Alternative: '+SUPPLIERS.shults.name+'.' });
  });
  /* hardware lines, matched to the catalogue (spec text decides) */
  (model.hardware || []).forEach(function(h){
    var qty = typeof h.qty === 'number' ? h.qty : parseInt(h.qty, 10) || 1;
    var c = catalogFor(h.spec);
    var tubeLen = c && c.k === 'tube18';
    if(c && c.k === 'bush'){
      var len = (h.spec.match(/OD\s?22\s?×\s?(\d+)/) || [])[1] || '25';
      c = Object.assign({}, c, { name:'Plain bush, oil-impregnated sintered bronze, ID 18 / OD 22 × '+len, no:'DIN 1850 / ISO 2795 — 18 × 22 × '+len });
    }
    rows.push(c ? { cat:c.cat, ref:h.id, name:c.name, no:c.no, qty:qty, unit:c.unit, sup:c.sup, url:c.url, price:c.price,
                    note:(tubeLen ? qty+' sleeves × 54.5 mm = '+Math.round(qty*55)+' mm of tube. ' : '')+(c.note || '') }
                : { cat:'Other', ref:h.id, name:h.spec, no:'', qty:qty, unit:'', sup:null, url:null, price:null, note:h.note || '' });
  });
  /* tools, only if the model has pivots */
  if((model.hardware || []).some(function(h){ return /bushing/i.test(h.spec); })){
    rows.push({ cat:'Tools (one-off)', name:'Forstner bit Ø35 (counterbores for the M12 washer + socket)', no:'TOTAL TCT Forstner 35 mm', qty:1, unit:'pc', sup:'mhdr', url:SUPPLIERS.mhdr.url, price:37 });
    rows.push({ cat:'Tools (one-off)', name:'Forstner bit or bi-metal hole saw Ø22 (bushing bores)', no:'Ø22 — call a plumbing / HVAC supplier', qty:1, unit:'pc', sup:'ace', url:SUPPLIERS.ace.url, price:null });
    rows.push({ cat:'Tools (one-off)', name:'Brad-point drill Ø12.5 (lock-pin holes) and Ø3 / Ø3.5 pilots', no:'generic', qty:1, unit:'set', sup:'ace', url:SUPPLIERS.ace.url, price:null });
  }
  rows.forEach(function(r){ r.line = (r.price != null) ? r.price*r.qty : null; });
  rows.sort(function(a,b){ return CAT_ORDER.indexOf(a.cat) - CAT_ORDER.indexOf(b.cat); });
  return rows;
}

/* ---- assembly plan ------------------------------------------------------ */
function partsById(model){
  var by = {};
  model.parts.forEach(function(p){
    if(p.bom === false) return;
    var id = p.partId || p.name, k = id+'|'+p.name;
    if(!by[k]) by[k] = { id:id, name:p.name, qty:0, cut:p.cut, sec:p.sec };
    by[k].qty++;
  });
  return by;
}
function assemblyPlan(model, S){
  var by = partsById(model), list = Object.keys(by).map(function(k){ return by[k]; });
  function pick(ids){ return list.filter(function(p){ return ids.indexOf(p.id) >= 0; }); }
  var J = {}; (model.joints || []).forEach(function(j){ J[j.id] = j; });
  function fast(ids, sides){
    return ids.filter(function(i){ return J[i]; }).map(function(i){
      var j = J[i]; return { id:i, what:j.a+' → '+j.b, how:j.fastener, n:(j.qty||1)*(sides||2), drive:j.drive };
    });
  }
  if(S.designId === 'folding'){
    var ext = list.filter(function(p){ return /extension/.test(p.name); });
    return [
      { t:'Prepare all timber', x:1, parts:[], fast:[], steps:[
        'Cut every part to the Schedule tab (cut lengths include the chosen length and seat depth).',
        'Mark the profiles of F3, T4, T5 and the pivot ends from the Drawing tab at 1:1; cut and round all arrises R3.',
        'Seal every cut end and every bore with three coats of deck oil; let the treated pine dry a week before drilling pivots.'] },
      { t:'SA-1 · Rear side frame', x:2, parts:pick(['R1','R2','R3','R4','R5','S1']), fast:fast(['J01','J02','J03','J04','J05','J08'], 2),
        steps:['Lay R1 and R2 on the bench, glue and screw R3 and R4 across them (J01–J04), then R5 (J05) and the stop S1 (J08).',
               'Make a left and a right (mirror images). Check the diagonals before the glue sets.',
               'Bore pivot B in R3: Ø22 through, press the 18/22 × 20 bushing flush with the moving face; Ø35 × 15 counterbore on the inner face.'] },
      { t:'SA-2 · Top (table / back) side frame', x:2, parts:pick(['T1','T2','T4','T5']), fast:fast(['J14','J20','J21'], 2),
        steps:['Bolt T2 to T1 with two M8 (J14), counterbored Ø24 × 12 both faces.',
               'Glue + M8 + screws for T4 (J20) and glue + screws for T5 (J21). T4 and T5 are the hard stops — glue is mandatory.',
               'Bore pivot B in T2 (bushing 18/22 × 25, Ø35 × 10 head counterbore) and pivot A in T1 (bushing 18/22 × 20, Ø35 × 15).'] },
      { t:'SA-3 · Front side frame', x:2, parts:pick(['F1','F2','F3']), fast:fast(['J09','J10','J11'], 2),
        steps:['Glue + screw F2 to F1 (J09) and F3 to F1 (J10); toe-screw F3 into F2 (J11).',
               'Bore pivot A in F1: bushing 18/22 × 25, Ø35 × 10 head counterbore.'] },
      { t:'SA-4 · Pivot B (top frame on rear frame)', x:2, parts:[], fast:[], hw:['H01','H02','H03','H04','H05','H06','H07'],
        steps:['Sleeve through both bushings, UHMW washer between the frames, washer + M12 bolt + washer + nyloc. Tighten fully: the bolt clamps the sleeve.'] },
      { t:'SA-5 · Join the two sides: rear seat boards', x:1, parts:pick(['S3']), fast:fast(['J06','J07'], 2),
        steps:['Stand both rear frames at the length apart, square them, screw the rear seat boards S3 down (2 per board end).'] },
      { t:'SA-6 · Table / back boards', x:1, parts:pick(['S4']), fast:fast(['J15','J16','J17','J18','J19','J22','J23','J24'], 2),
        steps:['With both top frames in table position, screw the five S4 boards to T1, T4 and T5.'] },
      { t:'SA-7 · Pivot A (hang the front frames)', x:2, parts:[], fast:[], hw:['H01','H02','H03','H04','H05','H06','H07'],
        steps:['Same stack as pivot B, through F1 and T1.'] },
      { t:'SA-8 · Front seat boards', x:1, parts:pick(['S2']).concat(ext), fast:fast(['J12','J13'], 2),
        steps:['Screw the front seat boards to F2 (2 per board end)'+(ext.length ? ', including the '+ext[0].qty+' extension boards at the front.' : '.')] },
      { t:'SA-9 · Lock pins', x:2, parts:[], fast:[], hw:['H08'],
        steps:['Table pose: match-drill Ø12.5 through F1 into T1. Fold to bench pose, drill the second T1 hole through the F1 hole.',
               'Fit the ball-lock pin with its lanyard and screw eye.'] },
      { t:'SA-10 · Finish and test', x:1, parts:[], fast:[], hw:['H12','H13'],
        steps:['Oil everything, glides under every leg end.', 'Fold slowly with two people the first time; check every stop lands flat.'] }
    ];
  }
  /* generic plan: by name groups */
  return [{ t:'All parts', x:1, parts:list, fast:[], steps:['See the Hardware and Checks tabs for joints and fabrication notes.'] }];
}

/* ---- render the Buy / BOM tab ----------------------------------------- */
function xesc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function renderBuy(){
  var host = document.getElementById('buyBody'); if(!host || !MODEL) return;
  var rows = buyList(MODEL, S, NEST), total = 0, unknown = 0, h = [], cat = null;
  h.push('<div class="buyhead"><b>Shopping list</b> — every item to buy, grouped by category. Quantities follow the design you are looking at. '+
         'Prices are as listed by the shops (Oct 2026) — call before going. '+
         '<button class="ghost" id="btnBuyCsv">Download CSV</button> <a class="ghost" href="suppliers.html" target="_blank">All suppliers ↗</a></div>');
  h.push('<table class="buy"><thead><tr><th>#</th><th>Item — exact name</th><th>Catalog / standard no.</th><th>Qty</th><th>Supplier</th><th>Unit ₪</th><th>Line ₪</th></tr></thead><tbody>');
  rows.forEach(function(r, i){
    if(r.cat !== cat){ cat = r.cat; h.push('<tr class="cat"><td colspan="7">'+xesc(cat)+'</td></tr>'); }
    var sup = r.sup ? SUPPLIERS[r.sup] : null;
    if(r.line != null) total += r.line; else unknown++;
    h.push('<tr><td class="dim">'+(i+1)+(r.ref ? '<br><span class="ref">'+xesc(r.ref)+'</span>' : '')+'</td>'+
      '<td>'+xesc(r.name)+(r.note ? '<div class="dim small">'+xesc(r.note)+'</div>' : '')+'</td>'+
      '<td class="dim small">'+xesc(r.no)+'</td><td class="num">'+r.qty+' '+xesc(r.unit)+'</td>'+
      '<td>'+(sup ? '<a href="'+xesc(r.url || sup.url)+'" target="_blank" rel="noopener">'+xesc(sup.name)+' ↗</a>'+(sup.tel ? '<div class="dim small">'+sup.tel+'</div>' : '') : '—')+'</td>'+
      '<td class="num">'+(r.price != null ? r.price.toFixed(2) : 'ask')+'</td><td class="num">'+(r.line != null ? r.line.toFixed(0) : '—')+'</td></tr>');
  });
  h.push('<tr class="tot"><td></td><td colspan="5">Total of listed prices'+(unknown ? ' — plus '+unknown+' item(s) priced on request' : '')+'</td><td class="num">₪ '+total.toFixed(0)+'</td></tr></tbody></table>');

  /* assembly plan */
  var plan = assemblyPlan(MODEL, S), hw = {};
  (MODEL.hardware || []).forEach(function(x){ hw[x.id] = x; });
  h.push('<div class="buyhead" style="margin-top:22px"><b>Assembly, by sub-assembly in build order</b> — what each step needs. '+
         '<button class="ghost" id="btnPlanMd">Download as Markdown</button></div>');
  plan.forEach(function(a){
    h.push('<div class="sa"><div class="sat">'+xesc(a.t)+(a.x > 1 ? ' <span class="dim">× '+a.x+' (left + right)</span>' : '')+'</div>');
    if(a.parts.length){
      h.push('<table class="buy"><thead><tr><th>Part</th><th>Section</th><th>Cut</th><th>Qty (total)</th></tr></thead><tbody>');
      a.parts.forEach(function(p){ h.push('<tr><td>'+xesc(p.name)+'</td><td class="dim">'+xesc(p.sec)+'</td><td class="num">'+p.cut+'</td><td class="num">'+p.qty+'</td></tr>'); });
      h.push('</tbody></table>');
    }
    if(a.fast.length){
      h.push('<table class="buy"><thead><tr><th>Joint</th><th>Members</th><th>Fastening</th><th>Qty (both sides)</th></tr></thead><tbody>');
      a.fast.forEach(function(f){ h.push('<tr><td class="dim">'+f.id+'</td><td>'+xesc(f.what)+'</td><td>'+xesc(f.how)+'<div class="dim small">'+xesc(f.drive)+'</div></td><td class="num">'+f.n+'</td></tr>'); });
      h.push('</tbody></table>');
    }
    if(a.hw && a.hw.length){
      h.push('<div class="dim small" style="margin:4px 0">Hardware: '+a.hw.filter(function(i){ return hw[i]; }).map(function(i){ return '<b>'+i+'</b> '+xesc(hw[i].spec); }).join(' · ')+'</div>');
    }
    h.push('<ol>'+a.steps.map(function(s){ return '<li>'+xesc(s)+'</li>'; }).join('')+'</ol></div>');
  });
  host.innerHTML = h.join('');
  document.getElementById('btnBuyCsv').onclick = function(){ saveText(buyCSV(), 'shopping-list.csv'); };
  document.getElementById('btnPlanMd').onclick = function(){ saveText(planMD(), 'assembly-plan.md'); };
}
function buyCSV(){
  var q = function(v){ return '"'+String(v==null?'':v).replace(/"/g,'""')+'"'; };
  var L = ['"Category","Ref","Item","Catalog / standard","Qty","Unit","Supplier","Phone","Link","Unit ILS","Line ILS","Note"'];
  buyList(MODEL, S, NEST).forEach(function(r){
    var s = r.sup ? SUPPLIERS[r.sup] : {};
    L.push([r.cat, r.ref, r.name, r.no, r.qty, r.unit, s.name, s.tel, r.url || s.url, r.price, r.line != null ? r.line.toFixed(2) : '', r.note].map(q).join(','));
  });
  return L.join('\n');
}
function planMD(){
  var L = ['# '+DESIGNS[S.designId].name+' — '+DESIGNS[S.designId].variants[S.variantId].name+' · assembly plan', ''];
  assemblyPlan(MODEL, S).forEach(function(a){
    L.push('## '+a.t+(a.x > 1 ? ' (× '+a.x+')' : ''), '');
    a.parts.forEach(function(p){ L.push('- '+p.qty+' × '+p.name+' — '+p.sec+', cut '+p.cut); });
    a.fast.forEach(function(f){ L.push('- '+f.id+' '+f.what+': '+f.how+' × '+f.n); });
    if(a.parts.length || a.fast.length) L.push('');
    a.steps.forEach(function(s, i){ L.push((i+1)+'. '+s); });
    L.push('');
  });
  return L.join('\n');
}
function saveText(text, file){
  var type = /\.svg$/.test(file) ? 'image/svg+xml' : 'text/plain';
  var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], {type:type}));
  a.download = file; document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

/* ---- BOM sheet for the Drawing tab (and bom.svg) ------------------------ */
function svgBom(model){
  var parts = Object.keys(partsById(model)).map(function(k){ return partsById(model)[k]; })
               .sort(function(a,b){ return String(a.id).localeCompare(String(b.id)); });
  var rows = buyList(model, S, NEST).filter(function(r){ return r.cat !== 'Timber' && r.cat !== 'Tools (one-off)'; });
  var W = 1400, lh = 19, y = 60, out = [];
  function t(x, yy, s, o){ return '<text x="'+x+'" y="'+yy+'" '+(o||'')+'>'+xesc(s)+'</text>'; }
  out.push(t(30, 34, 'BILL OF MATERIALS — '+DESIGNS[S.designId].name+' · '+DESIGNS[S.designId].variants[S.variantId].name, 'font-size="16" font-weight="700"'));
  out.push(t(30, y, 'TIMBER PARTS', 'font-size="11" fill="#555" letter-spacing="2"')); y += 8;
  var cols = [30, 90, 520, 640, 740];
  out.push('<line x1="30" x2="'+(W-30)+'" y1="'+y+'" y2="'+y+'" stroke="#999"/>'); y += lh;
  out.push(t(cols[0], y, 'ITEM', 'font-size="10" fill="#666"')+t(cols[1], y, 'PART', 'font-size="10" fill="#666"')+t(cols[2], y, 'SECTION', 'font-size="10" fill="#666"')+t(cols[3], y, 'CUT mm', 'font-size="10" fill="#666"')+t(cols[4], y, 'QTY', 'font-size="10" fill="#666"'));
  parts.forEach(function(p, i){ y += lh; out.push(t(cols[0], y, String(i+1))+t(cols[1], y, p.name)+t(cols[2], y, p.sec)+t(cols[3], y, String(p.cut))+t(cols[4], y, String(p.qty))); });
  y += 2*lh;
  out.push(t(30, y, 'HARDWARE — buy', 'font-size="11" fill="#555" letter-spacing="2"')); y += 8;
  out.push('<line x1="30" x2="'+(W-30)+'" y1="'+y+'" y2="'+y+'" stroke="#999"/>'); y += lh;
  var hc = [30, 90, 150, 640, 1010];
  out.push(t(hc[0], y, 'ITEM', 'font-size="10" fill="#666"')+t(hc[1], y, 'REF', 'font-size="10" fill="#666"')+t(hc[2], y, 'DESCRIPTION', 'font-size="10" fill="#666"')+t(hc[3], y, 'CATALOG / STANDARD', 'font-size="10" fill="#666"')+t(hc[4], y, 'QTY · SUPPLIER', 'font-size="10" fill="#666"'));
  rows.forEach(function(r, i){
    y += lh; var s = r.sup ? SUPPLIERS[r.sup].name.split(' (')[0] : '';
    var link = r.url || (r.sup ? SUPPLIERS[r.sup].url : '');
    out.push(t(hc[0], y, String(parts.length + i + 1))+t(hc[1], y, r.ref || '')+t(hc[2], y, r.name.length > 80 ? r.name.slice(0,78)+'…' : r.name)+
             t(hc[3], y, r.no.length > 58 ? r.no.slice(0,56)+'…' : r.no)+
             (link ? '<a href="'+xesc(link)+'" target="_blank">'+t(hc[4], y, r.qty+' '+r.unit+' · '+s, 'fill="#1a5fb4" text-decoration="underline"')+'</a>' : t(hc[4], y, r.qty+' '+r.unit)));
  });
  y += 30;
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+y+'" width="'+W+'" style="display:block;margin:24px auto;background:#fff;font-family:Helvetica,Arial,sans-serif;font-size:12px">'+
         '<rect x="10" y="10" width="'+(W-20)+'" height="'+(y-20)+'" fill="none" stroke="#333"/>'+out.join('')+'</svg>';
}

/* ---- Files: one click per generated file, plus the whole set as a zip --- */
var REPO_FILES = [
  ['suppliers-tel-aviv.md', 'Supplier list (Markdown)'],
  ['../simple-G1/assembly.svg', 'G1 assembly drawing (SVG)'], ['../simple-G1/exploded.svg', 'G1 exploded drawing (SVG)'],
  ['../simple-G1/parts-and-drilling.svg', 'G1 parts & drilling (SVG)'], ['../simple-G1/full-bom.csv', 'G1 full BOM (CSV)'],
  ['../simple-G1/hardware.csv', 'G1 hardware (CSV)'], ['../simple-G1/cutting-plan.txt', 'G1 cutting plan'],
  ['../simple-G1/profiles-mm.dxf', 'G1 profiles (DXF)'], ['../simple-G1/timber-with-drilling.FCMacro', 'G1 FreeCAD macro'],
  ['../simple-G1/fabrication-register.md', 'G1 fabrication register'], ['../simple-G1/parts.json', 'G1 parts (JSON)'],
  ['../simple-G1/project.json', 'G1 project (JSON)']
];
function allExports(){
  return EXPORTS.concat([
    { k:'buy.csv', label:'Shopping list — CSV', file:'shopping-list.csv', make:buyCSV },
    { k:'plan.md', label:'Assembly plan — Markdown', file:'assembly-plan.md', make:planMD },
    { k:'bom.svg', label:'BOM sheet — SVG', file:'bom-sheet.svg', make:function(){ return svgBom(MODEL); } }
  ]);
}
function renderFiles(){
  var host = document.getElementById('filesBox'); if(!host) return;
  var base = (S.designId+'-'+S.variantId).toLowerCase().replace(/[^a-z0-9]+/g, '-');
  var h = ['<p class="eyebrow" style="margin:0 0 8px">Files for this design — click to download, ↗ to open</p><div class="files">'];
  allExports().forEach(function(e, i){
    h.push('<span class="f"><a href="#" data-i="'+i+'" data-act="dl">'+xesc(base+'-'+e.file)+'</a> <a href="#" data-i="'+i+'" data-act="open" title="open in a new tab">↗</a></span>');
  });
  h.push('</div><button class="ghost" id="btnZip" style="margin-top:8px">Download all as .zip</button> <span class="msg" id="zipMsg"></span>');
  h.push('<p class="eyebrow" style="margin:14px 0 8px">Files in the project folder</p><div class="files">');
  REPO_FILES.forEach(function(f){ h.push('<span class="f"><a href="'+f[0]+'" target="_blank" rel="noopener">'+xesc(f[1])+'</a></span>'); });
  h.push('</div>');
  host.innerHTML = h.join('');
  var ex = allExports();
  host.querySelectorAll('a[data-act]').forEach(function(a){
    a.onclick = function(ev){
      ev.preventDefault();
      var e = ex[+a.dataset.i], text = e.make();
      if(a.dataset.act === 'dl') return saveText(text, base+'-'+e.file);
      var type = /\.svg$/.test(e.file) ? 'image/svg+xml' : 'text/plain;charset=utf-8';
      window.open(URL.createObjectURL(new Blob([text], {type:type})), '_blank');
    };
  });
  document.getElementById('btnZip').onclick = function(){
    var msg = document.getElementById('zipMsg');
    function go(){
      var z = new JSZip(), dir = z.folder(base);
      ex.forEach(function(e){ try{ dir.file(e.file, e.make()); }catch(err){ dir.file(e.file+'.error.txt', String(err)); } });
      z.generateAsync({type:'blob'}).then(function(b){
        var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = base+'.zip'; a.click();
        msg.textContent = 'zip ready'; });
    }
    if(window.JSZip) return go();
    msg.textContent = 'loading…';
    var s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
    s.onload = go; s.onerror = function(){ msg.textContent = 'could not load the zip library — use the single-file links'; };
    document.head.appendChild(s);
  };
}
