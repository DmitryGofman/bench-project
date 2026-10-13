/* =========================================================================
   concepts/ — four clean-sheet bench ↔ table concepts
   -------------------------------------------------------------------------
   Same principles as the folding bench, redesigned from scratch:
     · every member is a whole board (default 45 × 95, the Israeli "2×4");
     · side frames are built in LAYERS across the bench end. A moving arm
       gets a layer of its own, with 3 mm air either side, so it can only
       ever meet another part edge-on in that layer;
     · pivots are M12 bolts on Ø18 stainless sleeves in Ø18/22 bushings;
       every working pose is held by a Ø12 ball-lock pin at a long radius;
     · every concept carries a LIVE mechanism sweep: the side profile is
       stepped through the whole motion and every pair of parts that share
       a layer is tested for overlap (separating-axis test), plus the floor.
   Coordinates: X along the bench, Y front(−) → back(+), Z up. Profiles are
   (Y, Z) polygons, convex, extruded along X by ctx.prism.
   ========================================================================= */

var CK = (function(){
  var D2R = Math.PI/180;
  function rect(y0, z0, y1, z1){ return [[y0,z0],[y1,z0],[y1,z1],[y0,z1]]; }
  function rot(c, deg){
    var a = deg*D2R, co = Math.cos(a), si = Math.sin(a);
    return function(q){ var y = q[0]-c[0], z = q[1]-c[1]; return [c[0] + y*co - z*si, c[1] + y*si + z*co]; };
  }
  function move(dy, dz){ return function(q){ return [q[0]+dy, q[1]+dz]; }; }
  function id(q){ return q; }
  function circle(c, r, n){
    var out = [];
    for(var i=0;i<n;i++){ var a = i*2*Math.PI/n; out.push([c[0]+r*Math.cos(a), c[1]+r*Math.sin(a)]); }
    return out;
  }
  /* convex hull, monotone chain */
  function hull(pts){
    pts = pts.slice().sort(function(a,b){ return a[0]-b[0] || a[1]-b[1]; });
    function cr(o,a,b){ return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0]); }
    var lo = [], up = [];
    pts.forEach(function(p){ while(lo.length>=2 && cr(lo[lo.length-2], lo[lo.length-1], p) <= 0) lo.pop(); lo.push(p); });
    for(var i=pts.length-1;i>=0;i--){ var p = pts[i];
      while(up.length>=2 && cr(up[up.length-2], up[up.length-1], p) <= 0) up.pop(); up.push(p); }
    up.pop(); lo.pop(); return lo.concat(up);
  }
  /* an arm: a cleat rectangle (or any polygon) with a rounded boss of radius r round each pivot */
  function arm(poly, pivots, r){
    var pts = poly.slice();
    pivots.forEach(function(p){ pts = pts.concat(circle(p, r, 20)); });
    return hull(pts);
  }
  /* a straight member of width w on a centre line p → q, square ends */
  function bar(p, q, w){
    var dy = q[0]-p[0], dz = q[1]-p[1], l = Math.hypot(dy, dz), ny = -dz/l*w/2, nz = dy/l*w/2;
    return [[p[0]+ny,p[1]+nz],[q[0]+ny,q[1]+nz],[q[0]-ny,q[1]-nz],[p[0]-ny,p[1]-nz]];
  }
  /* the pivot that turns point a into point b by a rotation of deg */
  function pivotFor(a, b, deg){
    var t = deg*D2R, mx = (a[0]+b[0])/2, my = (a[1]+b[1])/2, dx = b[0]-a[0], dy = b[1]-a[1];
    var c = Math.hypot(dx, dy), h = c/2/Math.tan(t/2), nx = -dy/c, ny = dx/c;
    var P = [mx - h*nx, my - h*ny], r = rot(P, deg)(a);
    if(Math.hypot(r[0]-b[0], r[1]-b[1]) > 1e-6) P = [mx + h*nx, my + h*ny];
    return P;
  }
  /* separating-axis overlap depth of two convex polygons (0 = apart or touching) */
  function overlap(A, B){
    var best = Infinity;
    [A, B].forEach(function(P){
      for(var i=0;i<P.length;i++){
        var a = P[i], b = P[(i+1)%P.length], ny = -(b[1]-a[1]), nz = b[0]-a[0], l = Math.hypot(ny, nz);
        if(l < 1e-9) continue; ny /= l; nz /= l;
        var a0=Infinity,a1=-Infinity,b0=Infinity,b1=-Infinity;
        A.forEach(function(q){ var d=q[0]*ny+q[1]*nz; if(d<a0)a0=d; if(d>a1)a1=d; });
        B.forEach(function(q){ var d=q[0]*ny+q[1]*nz; if(d<b0)b0=d; if(d>b1)b1=d; });
        var o = Math.min(a1, b1) - Math.max(a0, b0);
        if(o < best) best = o;
      }
    });
    return Math.max(0, best);
  }
  function inside(poly, q, margin){
    for(var i=0;i<poly.length;i++){
      var a = poly[i], b = poly[(i+1)%poly.length];
      var cr = (b[0]-a[0])*(q[1]-a[1]) - (b[1]-a[1])*(q[0]-a[0]);
      var l = Math.hypot(b[0]-a[0], b[1]-a[1]);
      if(cr/l < (margin||0)) return false;
    }
    return true;
  }
  function ccw(poly){
    var A = 0; for(var i=0;i<poly.length;i++){ var a=poly[i], b=poly[(i+1)%poly.length]; A += a[0]*b[1]-b[0]*a[1]; }
    return A < 0 ? poly.slice().reverse() : poly;
  }
  function area(poly){
    var A = 0; for(var i=0;i<poly.length;i++){ var a=poly[i], b=poly[(i+1)%poly.length]; A += a[0]*b[1]-b[0]*a[1]; }
    return Math.abs(A)/2;
  }
  function centroid(poly){
    var A=0, cy=0, cz=0;
    for(var i=0;i<poly.length;i++){ var a=poly[i], b=poly[(i+1)%poly.length], c=a[0]*b[1]-b[0]*a[1];
      A+=c; cy+=(a[0]+b[0])*c; cz+=(a[1]+b[1])*c; }
    return [cy/(3*A), cz/(3*A)];
  }
  /* pin hole for a two-pose lock: a point Q on the fixed member, and the two holes in
     the moving member (in its own frame) that land on Q in pose 1 and pose 2. Searches
     radii and angles for the largest radius that leaves `margin` of wood round every hole. */
  function lockPin(fixedPoly, armPoly, P, deg, margin){
    var best = null;
    for(var R=220; R>=60; R-=5){
      for(var a=0; a<360; a+=3){
        var Q = [P[0]+R*Math.cos(a*D2R), P[1]+R*Math.sin(a*D2R)];
        if(!inside(ccw(fixedPoly), Q, margin)) continue;
        var H2 = rot(P, -deg)(Q);
        if(!inside(ccw(armPoly), Q, margin) || !inside(ccw(armPoly), H2, margin)) continue;
        best = { Q:Q, H1:Q, H2:H2, R:R }; break;
      }
      if(best) break;
    }
    return best;
  }
  /* two-hole lock: one hole pair per pose. H1 is an arm hole that sits over a fixed hole
     Q1 in pose 1; H2 is a second arm hole that lands on a fixed hole Q2 after the
     rotation deg. Each is pushed as far from the pivot as the wood allows. */
  function lockPin2(fixedPoly, armPoly, P, deg, margin){
    var F = ccw(fixedPoly), A = ccw(armPoly), R2 = rot(P, deg), best1 = null, best2 = null;
    for(var R=260; R>=55; R-=5){
      for(var a=0; a<360; a+=3){
        var H = [P[0]+R*Math.cos(a*D2R), P[1]+R*Math.sin(a*D2R)];
        if(!inside(A, H, margin)) continue;
        if(!best1 && inside(F, H, margin)) best1 = { H:H, Q:H, R:R };
        var Q2 = R2(H);
        if(!best2 && inside(F, Q2, margin)) best2 = { H:H, Q:Q2, R:R };
      }
      if(best1 && best2) break;
    }
    if(!best1 || !best2) return null;
    return { H1:best1.H, Q1:best1.Q, H2:best2.H, Q2:best2.Q, R:Math.min(best1.R, best2.R), R1:best1.R, R2:best2.R, Q:best1.Q };
  }
  return { lockPin2:lockPin2, rect:rect, rot:rot, move:move, id:id, circle:circle, hull:hull, arm:arm, bar:bar,
           pivotFor:pivotFor, overlap:overlap, inside:inside, ccw:ccw, area:area,
           centroid:centroid, lockPin:lockPin };
})();

/* ---- the shared engine ---------------------------------------------------
   A concept supplies, for its stock (t thick, w wide):
     layers   {name: [from, to]} measured inward from the bench end;
     parts    [{id, name, g, asm, poly, layer, mid?}]   side-frame members
     boards   [{id, name, g, asm, poly, inset}]          full-length boards
     pose(s)  {asm: transform}  for s = 0…1 along the motion
   and the engine places everything in 3D, runs the sweep and the checks. */
function conceptBuild(C, P, ctx){
  var L = P.L, hasMid = P.mid === 'on' || (P.mid !== 'off' && L > 1700);
  var s = Math.max(0, Math.min(1, (P.fold||0)/100));
  var T = C.pose(s);
  function tf(asm){ return T[asm] || CK.id; }
  function lift(asm){ var v = tf(asm)([0,1]), o = tf(asm)([0,0]); return [0, v[0]-o[0], v[1]-o[1]]; }
  var lay = C.layers;

  /* mid stack: the layers of the parts that repeat in the middle, centred on X = 0 */
  var mids = C.parts.filter(function(p){ return p.mid; });
  var m0 = Infinity, m1 = -Infinity;
  mids.forEach(function(p){ var r = lay[p.layer]; if(r[0]<m0) m0=r[0]; if(r[1]>m1) m1=r[1]; });
  var mc = (m0 + m1)/2;

  C.parts.forEach(function(p){
    var poly = p.poly.map(tf(p.asm)), r = lay[p.layer], o = { note:p.note, partId:p.id, cut:p.cut, W:p.W };
    if(!o.cut){ var yy = p.poly.map(function(q){ return q[0]; }), zz = p.poly.map(function(q){ return q[1]; });
      o.cut = Math.round(Math.max(Math.max.apply(null,yy)-Math.min.apply(null,yy), Math.max.apply(null,zz)-Math.min.apply(null,zz))); }
    if(!p.midOnly){
      ctx.prism(p.name, p.g, L/2 - r[1], L/2 - r[0], poly, [1.1,0,0], o);
      ctx.prism(p.name, p.g, -(L/2 - r[0]), -(L/2 - r[1]), poly, [-1.1,0,0], o);
    }
    if(hasMid && p.mid) ctx.prism(p.name+' (middle)', p.g, r[0]-mc, r[1]-mc, poly, [0,0,0.6], o);
  });
  (C.inner || []).forEach(function(q){
    var poly = q.poly.map(tf(q.asm)), xs = q.xs(L);
    var yy = q.poly.map(function(v){ return v[0]; }), zz = q.poly.map(function(v){ return v[1]; });
    var d1 = Math.max.apply(null,yy) - Math.min.apply(null,yy), d2 = Math.max.apply(null,zz) - Math.min.apply(null,zz);
    xs.forEach(function(xr){
      ctx.prism(q.name, q.g, xr[0], xr[1], poly, lift(q.asm),
        { note:q.note, T:Math.round(Math.min(d1, d2)), W:Math.round(Math.max(d1, d2)), cut:Math.round(xr[1] - xr[0]) });
    });
  });
  C.boards.forEach(function(b){
    var poly = b.poly.map(tf(b.asm)), x = L/2 - b.inset;
    ctx.prism(b.name, b.g, -x, x, poly, lift(b.asm), { cut: Math.round(2*x), T: C.bt, W: C.bw });
  });
  (C.fasteners || []).forEach(function(f){
    var c = tf(f.asm)(f.at), r = lay[f.layer], g = f.k === 'pivot' ? 'pivot' : f.k === 'pin' ? 'pin' : 'bolt';
    var rad = f.k === 'pivot' ? 18 : f.k === 'pin' ? 6 : 12, h = f.k === 'pin' ? 30 : 3;
    var poly = CK.circle(c, rad, f.k === 'bolt' ? 6 : 16);
    [1,-1].forEach(function(sx){
      var xo = sx*(L/2 - r[0]), x0 = sx > 0 ? xo : xo - h, x1 = sx > 0 ? xo + h : xo;
      ctx.prism(f.name, g, x0, x1, poly, [sx*1.3,0,0], { bom:false });
    });
  });

  /* ---- live mechanism sweep (2D, per layer) ---- */
  var sweep = conceptSweep(C, hasMid);

  /* ---- stability, from the side profile at this pose ---- */
  var st = conceptStability(C, T, L, ctx, hasMid);

  var checks = [
    { s: sweep.hits.length ? 'fail' : 'ok',
      t: sweep.hits.length
        ? '<b>Mechanism sweep: '+sweep.hits.length+' clash(es).</b> '+sweep.hits.slice(0,3).map(function(h){
            return h.a+' ↔ '+h.b+' by '+h.d.toFixed(0)+' mm at '+Math.round(h.s*100)+'%'; }).join('; ')
        : C.noMotion ? '<b>Pose check clean.</b> No moving joints: every pair of parts sharing a layer in this pose tested with a separating-axis overlap test, plus the floor.'
        : '<b>Mechanism sweep clean.</b> '+sweep.steps+' poses from 0 to 100 %, every pair of parts sharing a layer '+
          '(and every middle-frame part against every board) tested with a separating-axis overlap test, plus the floor.',
      v: sweep.hits.length+' clashes' }
  ].concat(C.checks(P, st, hasMid));

  var frames = hasMid ? 3 : 2;
  return {
    parts: ctx.parts,
    spans: C.spans(P, hasMid),
    headline: C.headline(P, hasMid),
    headline2: C.headline2(P, s, frames),
    hardware: C.hardware(frames, P), joints: C.joints || [], interfaces: C.interfaces || [],
    checks: checks, fabrication: C.fabrication
  };
}

function conceptSweep(C, hasMid){
  var hits = [], seen = {}, steps = 0, lay = C.layers;
  var items = C.parts.filter(function(p){ return !p.midOnly; }).map(function(p){ return { id:p.name, asm:p.asm, poly:p.poly, r:lay[p.layer], board:false, mid:false }; })
    .concat(C.boards.map(function(b){ return { id:b.name, asm:b.asm, poly:b.poly, r:[b.inset, Infinity], board:true }; }))
    .concat((C.inner || []).map(function(q){ return { id:q.name, asm:q.asm, poly:q.poly, r:[1e6, 1e6+1], inner:true }; }));
  if(hasMid) C.parts.filter(function(p){ return p.mid; }).forEach(function(p){
    items.push({ id:p.name+' (middle)', asm:p.asm, poly:p.poly, r:lay[p.layer], board:false, mid:true });
  });
  var K = C.noMotion ? 0 : 50;
  for(var k=0; k<=K; k++){
    var s = K ? k/K : 0, T = C.pose(s); steps++;
    var cur = items.map(function(it){ return (T[it.asm] ? it.poly.map(T[it.asm]) : it.poly); });
    for(var i=0;i<items.length;i++){
      var A = items[i];
      if(A.asm !== 'frame'){
        var zmin = Math.min.apply(null, cur[i].map(function(q){ return q[1]; }));
        if(zmin < -0.5) note(A.id, 'floor', -zmin, s);
      }
      for(var j=i+1;j<items.length;j++){
        var B = items[j];
        if(A.asm === B.asm && !A.mid && !B.mid) continue;          /* rigid together: laps by design */
        if(A.mid !== B.mid && !A.board && !B.board) continue;      /* middle frame vs end frame: metres apart */
        if((A.inner && !B.board && !B.inner) || (B.inner && !A.board && !A.inner)) continue;
        var xo = A.inner || B.inner || (A.mid && B.board) || (B.mid && A.board) ||
                 (A.r[0] < B.r[1] - 0.01 && B.r[0] < A.r[1] - 0.01);
        if(!xo) continue;
        var d = CK.overlap(cur[i], cur[j]);
        if(d > 0.5) note(A.id, B.id, d, s);
      }
    }
  }
  function note(a, b, d, s){
    var key = a+'|'+b;
    if(!seen[key]){ seen[key] = { a:a, b:b, d:d, s:s }; hits.push(seen[key]); }
    else if(d > seen[key].d){ seen[key].d = d; seen[key].s = s; }
  }
  return { hits:hits, steps:steps };
}

/* self-weight and centre of gravity of the side profile at this pose,
   and the ground footprint (Y range of everything touching the floor) */
function conceptStability(C, T, L, ctx, hasMid){
  var dens = (ctx.density || 500)*1e-9, W = 0, my = 0, fy0 = Infinity, fy1 = -Infinity;
  var lay = C.layers, n = hasMid ? 3 : 2;
  function add(poly, len){
    var a = CK.area(poly), c = CK.centroid(CK.ccw(poly)), m = a*len*dens*9.81;
    W += m; my += m*c[0];
  }
  C.parts.forEach(function(p){
    var poly = (T[p.asm] ? p.poly.map(T[p.asm]) : p.poly), r = lay[p.layer];
    if(p.unit && p.unit !== 1) return;
    add(poly, (r[1]-r[0])*(p.midOnly ? n-2 : p.mid ? n : 2));
    if(!p.midOnly) poly.forEach(function(q){ if(q[1] < 1){ if(q[0]<fy0) fy0=q[0]; if(q[0]>fy1) fy1=q[0]; } });
  });
  C.boards.forEach(function(b){
    if(b.unit && b.unit !== 1) return;
    add(b.poly.map(T[b.asm] || CK.id), L - 2*b.inset);
  });
  (C.inner || []).forEach(function(q){
    var xs = q.xs(L), len = 0; xs.forEach(function(x){ len += x[1]-x[0]; });
    add(q.poly.map(T[q.asm] || CK.id), len);
  });
  return { W:W, cy: my/W, y0:fy0, y1:fy1 };
}

/* tipping: a vertical load F at y (or a horizontal load H at height z, pushing +y),
   about the foot it would tip over. Returns the safety factor. */
function tipSF(st, F, y, H, z){
  var cy = st.cy, W = st.W;
  if(H){ /* push backwards at height z, plus F sitting at y: tips about rear foot */
    var stab = W*(st.y1 - cy) + (F||0)*(st.y1 - y);
    return stab / (H*z);
  }
  if(y < st.y0){ return W*(cy - st.y0) / (F*(st.y0 - y)); }
  if(y > st.y1){ return W*(st.y1 - cy) / (F*(y - st.y1)); }
  return Infinity;
}
function sfRow(label, sf, how){
  var s = sf >= 1.5 ? 'ok' : sf >= 1.1 ? 'warn' : 'fail';
  return { s:s, t:'<b>'+label+'.</b> '+how+' '+(sf === Infinity ? 'Load is inside the footprint — cannot tip.'
           : 'Restoring / overturning moment = '+sf.toFixed(2)+(s==='ok' ? ' (≥ 1.5).' : s==='warn' ? ' — marginal, add weight or widen the feet.' : ' — it tips.')),
           v: sf === Infinity ? 'inside' : '× '+sf.toFixed(2) };
}

/* shared hardware: pivots and pins */
function conceptPivotHW(nPiv, nPin, extra){
  var hw = [
    { id:'P1', qty:nPiv, spec:'M12 hex bolt, ISO 4017 / DIN 933, A4-70 stainless, length to suit (see note)', note:'One per pivot. Grip = layers + 3 mm gaps + 2 washers; bolt clamps the sleeve.' },
    { id:'P2', qty:nPiv, spec:'M12 nyloc nut DIN 985, A4', note:'Torque fully: it clamps the sleeve, not the timber.' },
    { id:'P3', qty:2*nPiv, spec:'M12 washer ISO 7089 (Ø24), A4', note:'Head and nut side.' },
    { id:'P4', qty:nPiv, spec:'Stainless tube OD18 × 2 (ID14), cut to the timber stack − counterbores + 0.5', note:'The journal the timber turns on.' },
    { id:'P5', qty:2*nPiv, spec:'Plain bushing ID18 / OD22 × 20, sintered bronze or POM', note:'Pressed into both members at each pivot.' },
    { id:'P6', qty:nPiv, spec:'Thrust washer UHMW-PE / PTFE, ID18.5 / OD48 / 3', note:'In the 3 mm gap between the moving faces.' },
    { id:'P7', qty:nPin, spec:'Ball-lock quick-release pin Ø12, stainless, grip ≥ 95 mm, lanyard + screw eye', note:'Locks each working pose. Tether every pin.' }
  ];
  return hw.concat(extra || []);
}
function conceptCommonHW(screws, bolts, frames){
  return [
    { id:'F1', qty:Math.ceil(screws*1.1), spec:'Exterior structural screw 6 × 80, countersunk Torx, A2 stainless', note:screws+' fitted + 10% spare. Boards: 2 per board per bearer. Pilot Ø3.5.' },
    { id:'F2', qty:bolts, spec:'M10 × (stack + 20) hex bolt + 2 washers + nyloc, A4', note:'Every lap that carries load across layers (spacer blocks, leg to bearer).' },
    { id:'F3', qty:1, spec:'Exterior PU / D4 wood glue, 500 g', note:'Fixed laps only. Never on moving faces.' },
    { id:'F4', qty:1, spec:'End-grain sealer / deck oil, 1 l', note:'Every cut end and bore before assembly.' },
    { id:'F5', qty:frames*4, spec:'Nail-in plastic glides Ø40', note:'Keeps end grain off the wet floor.' }
  ];
}

/* ---------------------------------------------------------------------------
   shared ergonomics (mm)
   ------------------------------------------------------------------------- */
var CON = { SEAT:450, TABLE:740, GAP:3, PITCH_GAP:6 };

function conceptSchema(extra){
  return [
    {k:'L',    label:'Length', group:'Dimensions', type:'range', min:1400, max:3000, step:10, def:2000, unit:'mm'},
    {k:'mid',  label:'Middle frame', group:'Dimensions', type:'select', def:'auto',
      options:[{v:'auto',label:'Auto (over 1700)'},{v:'on',label:'Always'},{v:'off',label:'Never'}]},
    {k:'fold', label:'Convert, table → bench', group:'Mechanism', type:'range', min:0, max:100, step:1, def:0, unit:'%'}
  ].concat(extra || []);
}
function conceptAreas(){
  return [
    {g:'rail', label:'Frame members', def:[45,95], hint:'Legs, posts, bearers, arms. Geometry is derived from this section.'},
    {g:'slat', label:'Seat, table & back boards', def:[45,95], hint:'All boards are the same section as the frame — one stock to buy.'}
  ];
}
function stockTW(ctx){
  var st = ctx.stock('rail'), sb = ctx.stock('slat');
  return { t: st.t || 45, w: st.w || 95, bt: sb.t || st.t || 45, bw: sb.w || st.w || 95 };
}

/* =========================================================================
   C1 · TWIN — two identical backed benches. Each backrest is a panel on two
   arms that pivot behind the seat; it swings 75° back to become half of a
   table. Put the benches back-to-back: two halves meet = picnic table 1 m
   deep. Push them seat-to-seat with backs up: a 1 m × 2 m daybed.
   ========================================================================= */
function makeTwin(K, P){
  var t = K.t, w = K.w, bt = K.bt, S = CON.SEAT, TB = CON.TABLE, g = CON.GAP, p = K.bw + CON.PITCH_GAP;
  var n = 5, D = n*p - CON.PITCH_GAP;                 /* seat depth = panel depth */
  var lay = { L0:[0,t], L1:[t+g, 2*t+g], L2:[2*t+2*g, 3*t+2*g] };
  var ANG = 75;
  /* table pose: panel inner edge just behind the seat */
  var a = D + 3, W = D;
  var panelUnder = TB - bt;
  /* bench pose: the panel's lower (inner) edge, face side, lands just over the seat back */
  var Et = [a, TB], Eb = [D - 30, S + 22];
  var Pv = CK.pivotFor(Et, Eb, ANG);
  var cleat = CK.rect(a, panelUnder - w, a + W, panelUnder);
  var armPoly = CK.arm(cleat, [Pv], w/2 + 2);
  var post = CK.rect(Pv[0] - w/2, 0, Pv[0] + w/2, TB - 12);
  var lock = CK.lockPin(post, armPoly, Pv, ANG, 16);
  var yPost0 = Pv[0] - w/2, yPost1 = Pv[0] + w/2;
  var parts = [
    { id:'FL', name:'FL · Front leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(0, 0, w, S - bt) },
    { id:'RP', name:'RP · Rear post (pivot)', g:'rail', asm:'frame', layer:'L0', mid:false, poly:post },
    { id:'RPm',name:'RPm · Rear leg, middle', g:'rail', asm:'frame', layer:'L0', mid:true, midOnly:true, poly:CK.rect(yPost0, 0, yPost1, S - bt) },
    { id:'LR', name:'LR · Low rail', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(0, 100, yPost1, 100 + w) },
    { id:'SF', name:'SF · Spacer, front', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(0, S - bt - w, w, S - bt) },
    { id:'SR', name:'SR · Spacer, rear', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(yPost0, S - bt - w, yPost1, S - bt) },
    { id:'SB', name:'SB · Seat bearer', g:'rail', asm:'frame', layer:'L2', mid:true, poly:CK.rect(0, S - bt - w, yPost1, S - bt) },
    { id:'AR', name:'AR · Back / table arm', g:'rail', asm:'arm', layer:'L1', mid:false, poly:armPoly,
      W: Math.round(panelUnder - (Pv[1] - w/2 - 2)), note:'Cleat + pivot boss, one profile: cut from a wide board or glue a boss block under a 45 × 95 cleat.' }
  ];
  var boards = [];
  for(var i=0;i<n;i++) boards.push({ id:'SS', name:'SS · Seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(i*p, S - bt, i*p + K.bw, S) });
  for(i=0;i<n;i++) boards.push({ id:'PB', name:'PB · Back / table board', g:'slat', asm:'arm', inset:lay.L1[0], poly:CK.rect(a + i*p, panelUnder, a + i*p + K.bw, TB) });
  var fasteners = [
    { k:'pivot', name:'Pivot · M12 on Ø18 sleeve', asm:'frame', layer:'L0', at:Pv },
    { k:'pin', name:'Lock pin Ø12', asm:'frame', layer:'L0', at: lock ? lock.Q : [Pv[0], Pv[1]+90] }
  ];

  /* second bench: mirror image. picnic = back-to-back, panels meet; daybed = seat-to-seat */
  var layout = P.layout || 'picnic';
  var yc = layout === 'daybed' ? -1.5 : a + W + 1.5;
  function mir(q){ return [2*yc - q[0], q[1]]; }
  var P2 = mir(Pv);
  parts.slice().forEach(function(q){
    parts.push({ id:q.id+'2', name:q.name.replace(' · ', '·2 · '), g:q.g, asm:q.asm === 'arm' ? 'arm2' : 'frame2',
                 layer:q.layer, mid:q.mid, midOnly:q.midOnly, unit:2, poly:q.poly.map(mir).reverse() });
  });
  boards.slice().forEach(function(b){
    boards.push({ id:b.id+'2', name:b.name.replace(' · ', '·2 · '), g:b.g, asm:b.asm === 'arm' ? 'arm2' : 'frame2',
                  inset:b.inset, unit:2, poly:b.poly.map(mir).reverse() });
  });
  fasteners.slice().forEach(function(f){
    fasteners.push({ k:f.k, name:f.name, asm:'frame2', layer:f.layer, at:mir(f.at) });
  });
  /* the end post is replaced by a short leg in the middle frame (no middle arm) */
  parts = parts.filter(function(q){ return true; });
  parts.forEach(function(q){ if(q.id === 'RP' || q.id === 'RP2') q.mid = false; });

  var dayFix = layout === 'daybed';
  return {
    layers: lay, parts: parts, boards: boards, fasteners: fasteners, bt: bt, bw: K.bw,
    pose: function(s){
      var k = dayFix ? 0 : s;
      return { arm: CK.rot(Pv, ANG*(1 - k)), arm2: CK.rot(P2, -ANG*(1 - k)) };
    },
    D:D, W:W, a:a, Pv:Pv, lock:lock,
    checks: function(P, st, hasMid){
      var bench = (P.fold||0) < 50 || dayFix;
      var faceY = CK.rot(Pv, ANG)([a, TB])[0];
      var rows = [
        { s:'ok', t:'<b>Table mode:</b> two panels meet over the gap between the benches — table '+(2*W+3)+' mm deep, top at '+TB+
            ', '+(TB - bt - S)+' mm from seat to the underside of the boards. Bolt the two panels together with 2 barrel bolts so they cannot step.', v:(2*W+3)+' × '+P.L },
        { s:'ok', t:'<b>Bench mode:</b> the panel stands 15° back, seat '+S+' high and '+Math.round(faceY)+' mm deep to the back.', v:S+' / '+Math.round(faceY) },
        { s:'ok', t:'<b>Daybed:</b> layout “seat-to-seat”, backs up — '+(2*D)+' × '+(P.L - 2*lay.L2[0])+' mm lying surface with a backrest each side.', v:(2*D)+' deep' },
        lock ? { s:'ok', t:'<b>Lock pin</b> at '+lock.R+' mm from the pivot, one post hole, two arm holes (table, bench), ≥ 16 mm of wood round each.', v:'r '+lock.R }
             : { s:'fail', t:'<b>No lock-pin position found</b> with 16 mm of wood round the holes.', v:'—' },
        sfRow('Sit on the front edge', tipSF(st, 1000, 0), 'One bench, 1 kN on the seat front edge.'),
        bench ? sfRow('Lean back hard', tipSF(st, 800, D/2, 300, TB + 200), '300 N pushing back at the top of the backrest, 800 N on the seat.')
              : { s:'ok', t:'<b>Lean on the table.</b> With the two halves bolted together the pair stands on four leg lines '+
                    'and any load on the top is inside that footprint. <b>Unbolted</b>, one bench with 600 N on the far edge of its half '+
                    'has a restoring / overturning ratio of '+tipSF(st, 600, a + W - 20).toFixed(2)+' — so the barrel bolts are part of the design, not an extra.',
                  v:'bolted' }
      ];
      if(st.W) rows.push({ s: st.W/9.81 > 35 ? 'warn' : 'ok', t:'<b>Each bench</b> weighs about '+(st.W/9.81).toFixed(0)+' kg at 500 kg/m³ — '+(st.W/9.81 > 35 ? 'a two-person carry.' : 'one person can drag it.'), v:(st.W/9.81).toFixed(0)+' kg' });
      return rows;
    },
    spans: function(P, hasMid){
      var span = hasMid ? P.L/2 - lay.L2[1] : P.L - 2*lay.L2[1];
      return [
        { label:'Seat boards', span: span, b:K.bw, h:bt, tributary:p, load:2 },
        { label:'Panel boards (table / back)', span: P.L - 2*lay.L1[1], b:K.bw, h:bt, tributary:p, load:2 }
      ];
    },
    headline: function(P){ return P.L+' long · two benches · table '+(2*W+3)+' deep at '+TB+' · daybed '+(2*D)+' deep'; },
    headline2: function(P, s, frames){ return 'C1 Twin · '+(dayFix ? 'DAYBED' : s <= 0 ? 'BENCH' : s >= 1 ? 'TABLE' : 'CONVERTING '+Math.round(s*100)+'%')+' · '+frames+' frames per bench · 1 pivot + 1 pin per end'; },
    hardware: function(frames){
      var boardsPerUnit = 2*n, screws = 2*(n*frames*2 + n*2*2);
      return conceptPivotHW(4, 4, [
        { id:'P8', qty:4, spec:'Barrel bolt / tower bolt 100 mm, stainless', note:'Two per table joint: ties the two panels together in table mode.' }
      ]).concat(conceptCommonHW(screws, 2*4*frames, 2*frames));
    },
    fabrication: [
      { part:'Arms', detail:'Mark the arm outline full size from the drawing: a cleat under the panel with a Ø'+(w+4)+' boss round the pivot. Cut from one 45 × 95 + a glued-on boss block, or from a 45 × 200 board.' },
      { part:'Pivots', detail:'Bore Ø22 through post and arm together, press Ø18/22 bushings, Ø18 sleeve, M12 × 110 bolt through post + arm + 3 mm UHMW washer.' },
      { part:'Lock pin', detail:'Drill the post hole and the first arm hole together in table pose, swing to bench pose, drill the second arm hole through the post hole.' },
      { part:'Layers', detail:'Each end: legs and post (outer layer), arm + spacer blocks (middle layer), seat bearer (inner layer). Spacer blocks are glued and bolted through all three layers with M10.' },
      { part:'Edges', detail:'Round every exposed board arris R3 and the panel corners R20.' }
    ]
  };
}

DESIGNS.concept1 = {
  id:'concept1', name:'C1 · Twin flip-back',
  blurb:'Two identical benches. Each backrest swings back 75° on one pivot to become half of a 1 m table; seat-to-seat they make a 1 × 2 m daybed.',
  info:{ designer:'concept', version:'0.1', license:'MIT' },
  areas: conceptAreas(),
  schema: conceptSchema([
    {k:'layout', label:'Arrangement', group:'Mechanism', type:'select', def:'picnic',
      options:[{v:'picnic',label:'Back-to-back (picnic)'},{v:'daybed',label:'Seat-to-seat (daybed)'}]}
  ]),
  variants:{ C1:{ name:'C1 · 2 m', tag:'Two benches, one pivot + one pin per end. Simplest motion.',
    note:'<b>Twin flip-back.</b> Drag <i>Convert</i>: each backrest swings back over its post and lands level as half of the table. '+
         'Switch <i>Arrangement</i> to see the daybed.', set:{ L:2000, mid:'auto', fold:100, layout:'picnic' } } },
  build:function(P, ctx){ return conceptBuild(makeTwin(stockTW(ctx), P), P, ctx); }
};

/* =========================================================================
   C2 · SWING — one piece. A picnic frame with two fixed seats; the whole
   tabletop is a panel on two arms that pivot just above the rear seat.
   It swings 105° up and over to stand behind the rear seat as a tall,
   reclined backrest (head height). One pivot and one pin per end.
   ========================================================================= */
function makeSwing(K, P){
  var t = K.t, w = K.w, bt = K.bt, S = CON.SEAT, TB = CON.TABLE, g = CON.GAP, p = K.bw + CON.PITCH_GAP;
  var lay = { L0:[0,t], L1:[t+g, 2*t+g], L2:[2*t+2*g, 3*t+2*g] };
  var nT = 8, Wt = nT*p - CON.PITCH_GAP, yT = Wt/2;           /* table panel, centred */
  var nS = 4, Ds = nS*p - CON.PITCH_GAP, ov = 100;
  var yS0 = yT - ov, yS1 = yS0 + Ds;                           /* rear seat; front is the mirror */
  var ANG = -105;
  var under = TB - bt;
  var Et = [yT, under], Eb = [yS1 + 12, S + 12];
  var Pv = CK.pivotFor(Et, Eb, ANG);
  var cleat = CK.rect(-yT, under - w, yT, under);
  /* the pivot boss is its own block, glued under the rear end of the cleat, so the
     cleat underside stays flat where it lands on the front stop */
  var armPoly = CK.hull(CK.circle(Pv, w/2 + 2, 20).concat([[yT - 2*w, under - w], [yT, under - w]]));
  /* the post carries a round head plate (cut from a 45 × 300 offcut) so both lock holes
     can sit well away from the pivot */
  var post = CK.hull(CK.rect(Pv[0] - w/2, 0, Pv[0] + w/2, Pv[1]).concat(CK.circle(Pv, 140, 24)));
  var lock = CK.lockPin2(post, CK.hull(armPoly.concat(cleat)), Pv, ANG, 16);
  var stop = CK.rect(-yT, under - w - 3 - w, -yT + w, under - w - 3);   /* front stop under the cleat */
  var fpost = CK.rect(-yT, 0, -yT + w, under - w - 3);
  var parts = [
    { id:'LF', name:'LF · Front leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(-yS1, 0, -yS1 + w, S - bt) },
    { id:'LB', name:'LB · Rear leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(yS1 - w, 0, yS1, S - bt) },
    { id:'PP', name:'PP · Pivot post', g:'rail', asm:'frame', layer:'L0', mid:false, poly:post },
    { id:'FP', name:'FP · Front stop post', g:'rail', asm:'frame', layer:'L0', mid:false, poly:fpost },
    { id:'LR', name:'LR · Low rail', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yS1, 100, yS1, 100 + w) },
    { id:'SF', name:'SF · Spacer, front leg', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yS1, S - bt - w, -yS1 + w, S - bt) },
    { id:'SR', name:'SR · Spacer, rear leg', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(yS1 - w, S - bt - w, yS1, S - bt) },
    { id:'SP', name:'SP · Spacer, pivot post', g:'rail', asm:'frame', layer:'L1', mid:false, poly:CK.rect(Pv[0] - w/2, S - bt - w, Pv[0] + w/2, S - bt) },
    { id:'ST', name:'ST · Table stop block', g:'rail', asm:'frame', layer:'L1', mid:false, poly:stop },
    { id:'SB', name:'SB · Seat bearer', g:'rail', asm:'frame', layer:'L2', mid:true, poly:CK.rect(-yS1, S - bt - w, yS1, S - bt) },
    { id:'AC', name:'AC · Table cleat', g:'rail', asm:'arm', layer:'L1', mid:false, poly:cleat },
    { id:'AB', name:'AB · Pivot boss', g:'rail', asm:'arm', layer:'L1', mid:false, poly:armPoly,
      W: Math.round(under - (Pv[1] - w/2 - 2)), note:'Glued and bolted (2 × M10) to the rear end of the cleat; carries the pivot.' }
  ];
  var boards = [];
  for(var i=0;i<nS;i++){
    boards.push({ id:'SR', name:'SS · Rear seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(yS0 + i*p, S - bt, yS0 + i*p + K.bw, S) });
    boards.push({ id:'SF', name:'SS · Front seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(-(yS0 + i*p + K.bw), S - bt, -(yS0 + i*p), S) });
  }
  for(i=0;i<nT;i++) boards.push({ id:'TB', name:'TB · Table / back board', g:'slat', asm:'arm', inset:lay.L1[0], poly:CK.rect(-yT + i*p, under, -yT + i*p + K.bw, TB) });
  var fasteners = [
    { k:'pivot', name:'Pivot · M12 on Ø18 sleeve', asm:'frame', layer:'L0', at:Pv },
    { k:'pin', name:'Lock pin Ø12 · table hole', asm:'frame', layer:'L0', at: lock ? lock.Q1 : [Pv[0], Pv[1]+90] },
    { k:'pin', name:'Lock pin Ø12 · bench hole', asm:'frame', layer:'L0', at: lock ? lock.Q2 : [Pv[0], Pv[1]-90] }
  ];
  var backTop = CK.rot(Pv, ANG)([-yT, TB]);
  return {
    layers: lay, parts: parts, boards: boards, fasteners: fasteners, bt: bt, bw: K.bw,
    pose: function(s){ return { arm: CK.rot(Pv, ANG*(1 - s)) }; },
    checks: function(P, st){
      var bench = (P.fold||0) < 50;
      var face = CK.rot(Pv, ANG)([yT, under]);
      return [
        { s:'ok', t:'<b>Table mode:</b> one '+Wt+' mm deep top at '+TB+', seats '+Ds+' deep each side, '+ov+' mm under the table edge, '+
            (TB - bt - S)+' mm from seat to the boards. The front of the top rests on a stop block, the rear is held by the pivot and pin.', v:Wt+' × '+P.L },
        { s:'ok', t:'<b>Bench mode:</b> the top swings 105° and stands behind the rear seat as a reclined back '+Math.round(backTop[1])+
            ' mm high — a head rest for lounging. The front seat stays as a footrest / second seat.', v:Math.round(backTop[1])+' high' },
        lock ? { s:'ok', t:'<b>Lock pin</b>: one Ø12 pin, two hole pairs in the post head plate — table at '+lock.R1+' mm and bench at '+lock.R2+' mm from the pivot, ≥ 16 mm of wood round each.', v:'r '+lock.R }
             : { s:'fail', t:'<b>No lock-pin position found.</b>', v:'—' },
        sfRow('Sit on the front-seat edge', tipSF(st, 1000, -yS1), '1 kN on the outer edge of the front seat.'),
        bench ? sfRow('Lean back hard', tipSF(st, 800, (yS0 + yS1)/2, 300, backTop[1]), '300 N pushing back at the top of the back, 800 N on the rear seat.')
              : sfRow('Lean on the table edge', tipSF(st, 600, -yT), '600 N on the front edge of the top.'),
        { s: (st.W/9.81) > 70 ? 'warn' : 'ok', t:'<b>Weight</b> about '+(st.W/9.81).toFixed(0)+' kg; the swinging top is about '+
            (nT*K.bw*bt*(P.L - 2*lay.L1[0])*5e-7 + 2*CK.area(armPoly)*t*5e-7).toFixed(0)+' kg — swing it with one person at each end.', v:(st.W/9.81).toFixed(0)+' kg' }
      ];
    },
    spans: function(P, hasMid){
      var span = hasMid ? P.L/2 - lay.L2[1] : P.L - 2*lay.L2[1];
      return [
        { label:'Seat boards', span: span, b:K.bw, h:bt, tributary:p, load:2 },
        { label:'Table / back boards', span: P.L - 2*lay.L1[1], b:K.bw, h:bt, tributary:p, load:2 }
      ];
    },
    headline: function(P){ return P.L+' long · one piece · table '+Wt+' deep at '+TB+' · reclined back '+Math.round(backTop[1])+' high'; },
    headline2: function(P, s, frames){ return 'C2 Swing · '+(s <= 0 ? 'BENCH' : s >= 1 ? 'TABLE' : 'SWINGING '+Math.round(s*100)+'%')+' · '+frames+' frames · 1 pivot + 1 pin per end'; },
    hardware: function(frames){
      var screws = 2*(2*nS*frames + nT*2);
      return conceptPivotHW(2, 2).concat(conceptCommonHW(screws, 3*frames + 4, frames));
    },
    fabrication: [
      { part:'Arms', detail:'Each arm is the panel cleat plus a pivot boss: cut the outline full size, or glue and screw a boss block under the cleat end. The pivot sits '+Math.round(Pv[1] - S)+' mm above the rear seat.' },
      { part:'Pivots', detail:'Bore Ø22 through post and arm together; Ø18/22 bushings, Ø18 sleeve, M12 × 110, 3 mm UHMW washer.' },
      { part:'Front stop', detail:'The stop post and block carry the front of the table; glue + M10 through both layers.' },
      { part:'Edges', detail:'Round every exposed arris R3, panel corners R20.' }
    ]
  };
}

/* =========================================================================
   C3 · LIFT — one piece with a fixed backrest. The table top rides on two
   parallel links per end, so it stays level the whole way: up at table
   height, or down flush between the seats → one 1.5 m deep daybed.
   ========================================================================= */
function makeLift(K, P){
  var t = K.t, w = K.w, bt = K.bt, S = CON.SEAT, TB = CON.TABLE, g = CON.GAP, p = K.bw + CON.PITCH_GAP;
  var lay = { L0:[0,t], L1:[t+g, 2*t+g], L2:[2*t+2*g, 3*t+2*g] };
  var nT = 7, Wt = nT*p - CON.PITCH_GAP, yT = Wt/2;
  var nS = 4, Ds = nS*p - CON.PITCH_GAP;
  /* links are horizontal in the low (daybed) pose, so the top's first movement is
     straight up out of the gap between the seats; rotating them THETA up lifts it
     H and moves it SHIFT towards the backrest side */
  var H = TB - S, THETA = 40, R = H/Math.sin(THETA*Math.PI/180), SHIFT = R*(1 - Math.cos(THETA*Math.PI/180));
  /* rear gap: while the top rises out of the daybed it drifts rise²/2R towards the
     rear seat; the cleat must clear the seat boards (rise w + bt) before it gets there */
  var rise0 = w + bt, gapR = Math.ceil(R - Math.sqrt(R*R - rise0*rise0)) + 4;
  var yS0 = yT + gapR, yS1 = yS0 + Ds, yF0 = yT + 3, yF1 = yF0 + Ds;
  var zc = S - bt - w/2;                                   /* cleat centre line, low pose */
  var dz = w + 8;                                          /* front link runs one link-width lower */
  var B1 = [yT*0.25, zc], B2 = [-yT*0.25, zc - dz];
  var A1 = [B1[0] + R, zc], A2 = [B2[0] + R, zc - dz];
  var link1 = CK.arm(CK.bar(A1, B1, w), [A1, B1], w/2), link2 = CK.arm(CK.bar(A2, B2, w), [A2, B2], w/2);
  var cleat = CK.hull(CK.rect(-yT, S - bt - w, yT, S - bt).concat(CK.circle(B2, w/2, 16)));
  var cpY = (A1[0] + A2[0])/2;
  /* one L0 member: a post with a wide head that carries both link pivots and the lock holes */
  var head = CK.hull(CK.circle(A1, w/2 + 70, 20).concat(CK.circle(A2, w/2 + 10, 20), [[cpY - w/2, 0], [cpY + w/2, 0]]));
  var lock = CK.lockPin2(head, link1, A1, -THETA, 14);
  /* fixed back: a leaning post behind the rear seat with three boards */
  var lean = 12*Math.PI/180, bp0 = [yS1 + 4 + w/2, S - bt - w], bpL = 520;
  var bp1 = [bp0[0] + bpL*Math.sin(lean), bp0[1] + bpL*Math.cos(lean)];
  var bpost = CK.bar(bp0, bp1, w);
  var parts = [
    { id:'LF', name:'LF · Front leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(-yF1, 0, -yF1 + w, S - bt) },
    { id:'LB', name:'LB · Rear leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(yS1 - w, 0, yS1, S - bt - w) },
    { id:'HR', name:'HR · Link post', g:'rail', asm:'frame', layer:'L0', mid:false, poly:head, W:300, note:'A 45 × 95 post with a 45 × 300 head plate glued and bolted on; carries both link pivots and the lock holes.' },
    { id:'LR', name:'LR · Low rail', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yF1, 40, yS1, 40 + w) },
    { id:'SF', name:'SF · Spacer, front', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yF1, S - bt - w, -yF1 + w, S - bt) },
    { id:'SR', name:'SR · Spacer, rear', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(yS1 - w, S - bt - w, yS1, S - bt) },
    { id:'BF', name:'BF · Front seat bearer', g:'rail', asm:'frame', layer:'L2', mid:true, poly:CK.rect(-yF1, S - bt - w, -yF0, S - bt) },
    { id:'BR', name:'BR · Rear seat bearer', g:'rail', asm:'frame', layer:'L2', mid:true, poly:CK.rect(yS0, S - bt - w, bp0[0] + w/2 + 30, S - bt) },
    { id:'BP', name:'BP · Back post', g:'rail', asm:'frame', layer:'L0', mid:true, poly:bpost },
    { id:'BS', name:'BS · Back post foot', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(bp0[0] - w/2, S - bt - w, bp0[0] + w/2 + 30, S - bt) },
    { id:'K1', name:'K1 · Link, rear', g:'rail', asm:'link1', layer:'L1', mid:false, poly:link1 },
    { id:'K2', name:'K2 · Link, front', g:'rail', asm:'link2', layer:'L1', mid:false, poly:link2 },
    { id:'TC', name:'TC · Table cleat', g:'rail', asm:'top', layer:'L2', mid:false, poly:cleat }
  ];
  var boards = [];
  for(var i=0;i<nS;i++){
    boards.push({ id:'SR', name:'SS · Rear seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(yS0 + i*p, S - bt, yS0 + i*p + K.bw, S) });
    boards.push({ id:'SF', name:'SS · Front seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(-(yF0 + i*p + K.bw), S - bt, -(yF0 + i*p), S) });
  }
  for(i=0;i<nT;i++) boards.push({ id:'TT', name:'TT · Table / daybed board', g:'slat', asm:'top', inset:lay.L2[0], poly:CK.rect(-yT + i*p, S - bt, -yT + i*p + K.bw, S) });
  /* back boards on the front face of the leaning post */
  var nB = 3, ux = Math.sin(lean), uz = Math.cos(lean), nx = -Math.cos(lean), nz = Math.sin(lean);
  for(i=0;i<nB;i++){
    var o0 = 170 + i*p, o1 = o0 + K.bw, f = w/2;
    var c0 = [bp0[0] + nx*f + ux*o0, bp0[1] + nz*f + uz*o0], c1 = [bp0[0] + nx*f + ux*o1, bp0[1] + nz*f + uz*o1];
    boards.push({ id:'BB', name:'BB · Back board', g:'slat', asm:'frame', inset:lay.L0[0],
      poly:[c0, c1, [c1[0] + nx*bt, c1[1] + nz*bt], [c0[0] + nx*bt, c0[1] + nz*bt]] });
  }
  var fasteners = [
    { k:'pivot', name:'Link pivot · M12', asm:'frame', layer:'L0', at:A1 },
    { k:'pivot', name:'Link pivot · M12', asm:'frame', layer:'L0', at:A2 },
    { k:'pin', name:'Lock pin Ø12 · daybed hole', asm:'frame', layer:'L0', at: lock ? lock.Q1 : [A1[0], A1[1] + 80] },
    { k:'pin', name:'Lock pin Ø12 · table hole', asm:'frame', layer:'L0', at: lock ? lock.Q2 : [A1[0], A1[1] - 80] }
  ];
  function th(s){ return -THETA*s; }
  return {
    layers: lay, parts: parts, boards: boards, fasteners: fasteners, bt: bt, bw: K.bw,
    pose: function(s){
      var a = th(s), Bn = CK.rot(A1, a)(B1);
      return { link1: CK.rot(A1, a), link2: CK.rot(A2, a), top: CK.move(Bn[0] - B1[0], Bn[1] - B1[1]) };
    },
    checks: function(P, st){
      var up = (P.fold||0) >= 50;
      var backFace = bp0[0] - w/2 + (S + 150 - bp0[1])*Math.tan(lean);
      return [
        { s:'ok', t:'<b>Parallel links:</b> two equal links per end ('+Math.round(R)+' mm centres, swinging '+THETA+'°) keep the top level the whole way — '+
            'cups can stay on it while it moves. It leaves the daybed straight up, rises '+H+' mm and ends '+Math.round(SHIFT)+' mm towards the backrest, '+
            'so the rear (backed) seat sits '+Math.round(SHIFT)+' mm under the table edge and the front seat '+Math.round(SHIFT)+' mm clear of it.', v:'level' },
        { s:'ok', t:'<b>Table mode:</b> top '+Wt+' deep at '+TB+', seats each side, '+(TB - bt - S)+' mm knee room over the seats; the rear seat keeps its backrest.', v:Wt+' × '+P.L },
        { s:'ok', t:'<b>Daybed mode:</b> top down flush between the seats — one flat '+Math.round(yF1 + yS1)+' × '+(P.L - 2*lay.L2[0])+' mm surface with a backrest along one side '+
            '(the board gap next to the rear seat is '+gapR+' mm: room for the top to rise before it drifts back).', v:Math.round(yF1 + yS1)+' deep' },
        lock ? { s:'ok', t:'<b>Lock pin</b> through the rear link and the link head plate — daybed hole at '+lock.R1+' mm, table hole at '+lock.R2+' mm from the pivot, ≥ 14 mm of wood round each.', v:'r '+lock.R }
             : { s:'fail', t:'<b>No lock-pin position found.</b>', v:'—' },
        sfRow('Sit on the front-seat edge', tipSF(st, 1000, -yF1), '1 kN on the outer edge of the front seat.'),
        sfRow('Lean back hard', tipSF(st, 800, (yS0 + yS1)/2, 300, bp1[1]), '300 N pushing back at the top of the back, 800 N on the rear seat.'),
        { s:'ok', t:'<b>Weight</b> about '+(st.W/9.81).toFixed(0)+' kg; the moving top is about '+(nT*K.bw*bt*(P.L - 2*lay.L2[0])*5e-7).toFixed(0)+
            ' kg and is lifted '+H+' mm — two people, or add gas struts (not modelled).', v:(st.W/9.81).toFixed(0)+' kg' }
      ];
    },
    spans: function(P, hasMid){
      var span = hasMid ? P.L/2 - lay.L2[1] : P.L - 2*lay.L2[1];
      return [
        { label:'Seat boards', span: span, b:K.bw, h:bt, tributary:p, load:2 },
        { label:'Table / daybed boards', span: P.L - 2*lay.L2[1], b:K.bw, h:bt, tributary:p, load:2 }
      ];
    },
    headline: function(P){ return P.L+' long · one piece · table '+Wt+' at '+TB+' · daybed '+Math.round(yF1 + yS1)+' deep · fixed back'; },
    headline2: function(P, s, frames){ return 'C3 Lift · '+(s <= 0 ? 'DAYBED / BENCH' : s >= 1 ? 'TABLE' : 'LIFTING '+Math.round(s*100)+'%')+' · '+frames+' frames · 2 links + 1 pin per end'; },
    hardware: function(frames){
      var screws = 2*(2*nS*frames + nT*2 + nB*frames);
      return conceptPivotHW(8, 2).concat(conceptCommonHW(screws, 4*frames + 4, frames));
    },
    fabrication: [
      { part:'Links', detail:'Four identical links, '+Math.round(R)+' mm between hole centres, Ø'+w+' round ends. Drill all four as a stack so the centres match — the top only stays level if they are equal.' },
      { part:'Pivots', detail:'8 pivots (2 links × 2 ends × 2 holes): M12, Ø18 sleeves, Ø18/22 bushings in every link end.' },
      { part:'Lock', detail:'One pin per end through the rear link into the head rail: one hole for table, one for daybed.' },
      { part:'Edges', detail:'Round all arrises R3; the daybed edge boards R10.' }
    ]
  };
}

/* =========================================================================
   C4 · LEAF — no moving joints at all. The table top is two loose leaves
   that sit on bearers. Lift one leaf into the back sockets and drop the other
   between the seats → a backed lounger 0.8 m deep; drop both → a flat 1.6 m
   daybed. Strongest and simplest; conversion is by hand (≈ 20 kg a leaf).
   ========================================================================= */
function makeLeaf(K, P){
  var t = K.t, w = K.w, bt = K.bt, S = CON.SEAT, TB = CON.TABLE, g = CON.GAP, p = K.bw + CON.PITCH_GAP;
  var lay = { L0:[0,t], L1:[t+g, 2*t+g], L2:[2*t+2*g, 3*t+2*g] };
  var nL = 4, WL = nL*p - CON.PITCH_GAP;                       /* one leaf */
  var yT = WL + 1.5, nS = 4, Ds = nS*p - CON.PITCH_GAP, yS0 = yT + 3, yS1 = yS0 + Ds;
  var under = TB - bt, bh = 45;                                /* leaf batten 45 deep */
  var mode = P.mode || 'table';
  /* leaf A (rear half) and B (front half), table pose */
  function leaf(y0){ var b = []; for(var i=0;i<nL;i++) b.push(CK.rect(y0 + i*p, under, y0 + i*p + K.bw, TB)); return b; }
  /* back sockets: the leaf leans 15° on the bearer ledge, top against a block on the rear post */
  var ANG = 75, corner = [1.5, TB], place = [yS1 + 7, S - bt + 12];
  var backT = function(q){ var r = CK.rot(corner, ANG)(q); return [r[0] - corner[0] + place[0], r[1] - corner[1] + place[1]]; };
  var backLine0 = backT([1.5, under]), dir = [Math.cos(ANG*Math.PI/180), Math.sin(ANG*Math.PI/180)];
  function backFaceY(z){ return backLine0[0] + (z - backLine0[1])*dir[0]/dir[1]; }
  var blockZ0 = S + 230, blockZ1 = S + 330;
  var rpY0 = backFaceY(blockZ1 + 20) + 3, rpY1 = rpY0 + w;
  var block = [[backFaceY(blockZ0) + 1, blockZ0], [rpY1, blockZ0], [rpY1, blockZ1], [backFaceY(blockZ1) + 1, blockZ1]];
  var tp0 = yT - w;                                             /* table posts just inside the table edge */
  var parts = [
    { id:'LF', name:'LF · Front leg', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(-yS1, 0, -yS1 + w, S - bt) },
    { id:'RP', name:'RP · Rear post / back socket', g:'rail', asm:'frame', layer:'L0', mid:true, poly:CK.rect(rpY0, 0, rpY1, blockZ1 + 20) },
    { id:'TF', name:'TF · Table post, front', g:'rail', asm:'frame', layer:'L0', mid:false, poly:CK.rect(-yT, 0, -tp0, under) },
    { id:'TR', name:'TR · Table post, rear', g:'rail', asm:'frame', layer:'L0', mid:false, poly:CK.rect(tp0, 0, yT, under) },
    { id:'LR', name:'LR · Low rail', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yS1, 80, rpY1, 80 + w) },
    { id:'SF', name:'SF · Spacer, front', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(-yS1, S - bt - w, -yS1 + w, S - bt) },
    { id:'SR', name:'SR · Spacer, rear', g:'rail', asm:'frame', layer:'L1', mid:true, poly:CK.rect(rpY0, S - bt - w, rpY1, S - bt) },
    { id:'ST', name:'ST · Spacer, table posts', g:'rail', asm:'frame', layer:'L1', mid:false, poly:CK.rect(-yT, under - w, -tp0, under) },
    { id:'ST2',name:'ST · Spacer, table posts', g:'rail', asm:'frame', layer:'L1', mid:false, poly:CK.rect(tp0, under - w, yT, under) },
    { id:'BK', name:'BK · Back rest block', g:'rail', asm:'frame', layer:'L1', mid:true, poly:block },
    { id:'SB', name:'SB · Seat / daybed bearer', g:'rail', asm:'frame', layer:'L2', mid:true, poly:CK.rect(-yS1, S - bt - w, rpY1, S - bt) },
    { id:'TB', name:'TB · Table bearer', g:'rail', asm:'frame', layer:'L2', mid:false, poly:CK.rect(-yT, under - w, yT, under) }
  ];
  var boards = [];
  for(var i=0;i<nS;i++){
    boards.push({ id:'SR', name:'SS · Rear seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(yS0 + i*p, S - bt, yS0 + i*p + K.bw, S) });
    boards.push({ id:'SF', name:'SS · Front seat board', g:'slat', asm:'frame', inset:lay.L2[0], poly:CK.rect(-(yS0 + i*p + K.bw), S - bt, -(yS0 + i*p), S) });
  }
  leaf(1.5).forEach(function(q){ boards.push({ id:'LA', name:'LA · Leaf A board', g:'slat', asm:'leafA', inset:lay.L1[0], poly:q }); });
  leaf(-yT).forEach(function(q){ boards.push({ id:'LB', name:'LB · Leaf B board', g:'slat', asm:'leafB', inset:lay.L1[0], poly:q }); });
  /* each leaf: two cross battens 300 mm in from its ends (clear of every frame layer) */
  var inner = [
    { name:'LA · Leaf A batten', g:'rail', asm:'leafA', poly:CK.rect(1.5 + 20, under - bh, WL + 1.5 - 20, under),
      xs:function(L){ var x = L/2 - 300; return [[x - t, x], [-x, -x + t]]; } },
    { name:'LB · Leaf B batten', g:'rail', asm:'leafB', poly:CK.rect(-yT + 20, under - bh, -yT + WL - 20, under),
      xs:function(L){ var x = L/2 - 300; return [[x - t, x], [-x, -x + t]]; } }
  ];
  var drop = S - TB;
  var POSE = {
    table:  { leafA: CK.id, leafB: CK.id },
    lounge: { leafA: backT, leafB: CK.move(yT + 1.5 - 1.5 - 0, drop) },
    daybed: { leafA: CK.move(0, drop), leafB: CK.move(0, drop) }
  };
  return {
    layers: lay, parts: parts, boards: boards, inner: inner, bt: bt, bw: K.bw, noMotion: true,
    fasteners: [],
    pose: function(){ return POSE[mode] || POSE.table; },
    checks: function(P, st){
      var seatDepth = Math.round(backFaceY(S + 100) - yS0), leafKg = (nL*K.bw*bt*(P.L - 2*lay.L1[0]) + 2*2*t*bh*(WL - 40))*5e-7;
      var rows = [
        { s:'ok', t:'<b>Table:</b> two leaves make a '+(2*yT).toFixed(0)+' mm top at '+TB+'; seats each side, '+(TB - bt - S)+' mm knee room. Leaves sit on 2 Ø12 locating dowels each.', v:(2*yT).toFixed(0)+' × '+P.L },
        { s:'ok', t:'<b>Lounger:</b> leaf A into the back sockets (15° recline), leaf B dropped beside the rear seat — '+
            Math.round(backFaceY(S + 100) - 1.5)+' mm deep to the back, a backed day-sofa. The front seat stays as a bench / footrest.', v:'≈ '+Math.round(backFaceY(S + 100))+' deep' },
        { s:'ok', t:'<b>Daybed:</b> both leaves between the seats on the seat bearers — one flat '+(2*yS1).toFixed(0)+' × '+(P.L - 2*lay.L2[0])+' mm surface.', v:(2*yS1).toFixed(0)+' deep' },
        { s: leafKg > 25 ? 'warn' : 'ok', t:'<b>Each leaf</b> weighs about '+leafKg.toFixed(0)+' kg — '+(leafKg > 25 ? 'two people to lift.' : 'one person can lift it.'), v:leafKg.toFixed(0)+' kg' },
        sfRow('Sit on the front-seat edge', tipSF(st, 1000, -yS1), '1 kN on the outer edge of the front seat.'),
        mode === 'lounge' ? sfRow('Lean back hard', tipSF(st, 800, (yS0 + yS1)/2, 300, blockZ1 + 100), '300 N pushing back at the top of the back, 800 N on the rear seat.')
                          : sfRow('Lean on the table edge', tipSF(st, 600, -yT), '600 N on the front edge of the top.')
      ];
      return rows;
    },
    spans: function(P, hasMid){
      var span = hasMid ? P.L/2 - lay.L2[1] : P.L - 2*lay.L2[1];
      return [
        { label:'Seat / daybed boards', span: span, b:K.bw, h:bt, tributary:p, load:2 },
        { label:'Leaf boards in table mode', span: P.L - 2*lay.L2[1], b:K.bw, h:bt, tributary:p, load:2 }
      ];
    },
    headline: function(P){ return P.L+' long · one frame + two loose leaves · table '+(2*yT).toFixed(0)+' · daybed '+(2*yS1).toFixed(0)+' deep'; },
    headline2: function(P, s, frames){ return 'C4 Leaf · '+mode.toUpperCase()+' · '+frames+' frames · no hinges, no pivots'; },
    hardware: function(frames){
      var screws = 2*(2*nS*frames + 2*nL*2) + 2*2*nL*2;
      return [
        { id:'D1', qty:8, spec:'Ø12 × 60 stainless dowel pin (or M12 rod), chamfered', note:'2 per leaf per end: locate the leaves on the table bearers and in the back sockets.' },
        { id:'D2', qty:4, spec:'Barrel bolt 100 mm, stainless', note:'Holds leaf A in the back sockets.' },
        { id:'D3', qty:4, spec:'Recessed lifting handle, stainless', note:'One per leaf end.' }
      ].concat(conceptCommonHW(screws, 4*frames + 4, frames));
    },
    fabrication: [
      { part:'Leaves', detail:'Each leaf = 4 boards screwed to 2 cross battens 300 mm in from the ends. Mark them A (rear) and B (front); they are interchangeable if built to the same jig.' },
      { part:'Locating', detail:'Drill Ø12.5 holes in the leaf battens and set Ø12 dowels in the table bearers and back blocks — the leaves drop on, nothing to tighten.' },
      { part:'Back sockets', detail:'The rear post carries a bevelled block at '+Math.round(blockZ0)+'–'+Math.round(blockZ1)+' mm; the leaf foot sits on the seat bearer ledge behind the rear seat.' },
      { part:'Edges', detail:'Round all arrises R3, leaf corners R20.' }
    ]
  };
}

DESIGNS.concept2 = {
  id:'concept2', name:'C2 · Swing-top',
  blurb:'One piece. The whole tabletop swings 105° on one pivot per end and becomes a tall reclined backrest behind the rear seat.',
  info:{ designer:'concept', version:'0.1', license:'MIT' },
  areas: conceptAreas(), schema: conceptSchema(),
  variants:{ C2:{ name:'C2 · 2 m', tag:'One piece, one pivot + one pin per end, head-high back.',
    note:'<b>Swing-top.</b> Drag <i>Convert</i>: the table lifts at the front and swings over the rear seat. Nothing to carry, nothing loose.',
    set:{ L:2000, mid:'auto', fold:100 } } },
  build:function(P, ctx){ return conceptBuild(makeSwing(stockTW(ctx), P), P, ctx); }
};
DESIGNS.concept3 = {
  id:'concept3', name:'C3 · Level-lift daybed',
  blurb:'One piece with a fixed back. The top rides on parallel links and stays level: up = table, down = flush with the seats → 1.6 m daybed.',
  info:{ designer:'concept', version:'0.1', license:'MIT' },
  areas: conceptAreas(), schema: conceptSchema(),
  variants:{ C3:{ name:'C3 · 2 m', tag:'Parallel links, top stays level; biggest lying surface.',
    note:'<b>Level-lift.</b> Drag <i>Convert</i>: the top rises on four links without tilting. At 0 % it is flush with the seats — a daybed.',
    set:{ L:2000, mid:'auto', fold:100 } } },
  build:function(P, ctx){ return conceptBuild(makeLift(stockTW(ctx), P), P, ctx); }
};
DESIGNS.concept4 = {
  id:'concept4', name:'C4 · Lift-off leaves',
  blurb:'No hinges at all: two loose leaves sit on bearers as a table, drop into back sockets and between the seats as a lounger or flat daybed.',
  info:{ designer:'concept', version:'0.1', license:'MIT' },
  areas: conceptAreas(),
  schema: [
    {k:'L',    label:'Length', group:'Dimensions', type:'range', min:1400, max:3000, step:10, def:2000, unit:'mm'},
    {k:'mid',  label:'Middle frame', group:'Dimensions', type:'select', def:'auto',
      options:[{v:'auto',label:'Auto (over 1700)'},{v:'on',label:'Always'},{v:'off',label:'Never'}]},
    {k:'mode', label:'Mode', group:'Mechanism', type:'select', def:'table',
      options:[{v:'table',label:'Table'},{v:'lounge',label:'Backed lounger'},{v:'daybed',label:'Flat daybed'}]}
  ],
  variants:{ C4:{ name:'C4 · 2 m', tag:'Zero moving parts, three modes, strongest.',
    note:'<b>Lift-off leaves.</b> Switch <i>Mode</i>. Each leaf is about 20 kg; dowels locate it, nothing to unscrew.',
    set:{ L:2000, mid:'auto', mode:'table' } } },
  build:function(P, ctx){ return conceptBuild(makeLeaf(stockTW(ctx), P), P, ctx); }
};

/* =========================================================================
   SWING-TOP + SLIDING SECOND BENCH — four ways to bring the front bench
   back to the main bench, all sharing the swing-top frame:
     · the tabletop swings 105° back on one pivot per end to become the back;
     · ARM PLANKS fixed to each swing arm: horizontal armrests / carry handles
       in bench mode, and in table mode they swing down into slanted struts
       that land on a stop block — a second hard stop and a brace for the top;
     · the second bench is shorter than the main one (it lives between the end
       frames), so it can move back and join the rear seat into one deep
       sofa / daybed with a back and two armrests.
   fold 0 % = table · 0–50 % the top swings back · 50–100 % the bench moves.
   ========================================================================= */
function makeSwingSlide(K, P, how){
  var t = K.t, w = K.w, bt = K.bt, S = CON.SEAT, TB = CON.TABLE, g = CON.GAP, p = K.bw + CON.PITCH_GAP;
  var lay = { L0:[0,t], L1:[t+g, 2*t+g], L2:[2*t+2*g, 3*t+2*g], L3:[3*t+3*g, 4*t+3*g], L4:[4*t+4*g, 5*t+4*g] };
  var nT = 8, Wt = nT*p - CON.PITCH_GAP, yT = Wt/2;
  var nS = 4, Ds = nS*p - CON.PITCH_GAP, ov = 100;
  var yS0 = yT - ov, yS1 = yS0 + Ds;                             /* rear (main) seat */
  var ANG = -105, under = TB - bt;
  var Pv = CK.pivotFor([yT, under], [yS1 + 12, S + 12], ANG);
  var cleat = CK.rect(-yT, under - w, yT, under);
  var boss = CK.hull(CK.circle(Pv, w/2 + 2, 20).concat([[yT - 2*w, under - w], [yT, under - w]]));
  var post = CK.hull(CK.rect(Pv[0] - w/2, 0, Pv[0] + w/2, Pv[1]).concat(CK.circle(Pv, 140, 24)));
  var lock = CK.lockPin2(post, CK.hull(boss.concat(cleat)), Pv, ANG, 16);
  var stop = CK.rect(-yT, under - w - 3 - w, -yT + w, under - w - 3);
  var fpost = CK.rect(-yT, 0, -yT + w, under - w - 3);
  var toTable = CK.rot(Pv, -ANG);                                 /* bench frame → arm frame */
  var KICK = 300;                                                 /* rear foot extension under the back */

  /* ARM PLANK: drawn in bench pose — an armrest 200 mm above the seat, from the back
     forward over the rear seat; stored in the arm's (table) frame */
  var hz0 = S + 160, hy0 = yS0 + 20, hy1 = Pv[0] + 250;
  var handleB = CK.rect(hy0, hz0, hy1, hz0 + w);
  var handle = handleB.map(toTable);
  /* its lower end in table pose lands on a block on the low rail */
  var lo = handle.slice().sort(function(a,b){ return a[1]-b[1]; });
  var e0 = lo[0], e1 = lo[1];                                     /* the bearing end edge */
  var ya = Math.min(e0[0], e1[0]), yb = Math.max(e0[0], e1[0]);
  var hstop = CK.hull([[ya, 100], [yb, 100], [e1[0], e1[1] - 1], [e0[0], e0[1] - 1]]);
  var parts = [
    { id:'LF', name:'LF · Front leg', g:'rail', asm:'frame', layer:'L0', poly:CK.rect(-yS1, 0, -yS1 + w, S - bt) },
    { id:'LB', name:'LB · Rear leg', g:'rail', asm:'frame', layer:'L0', poly:CK.rect(yS1 - w, 0, yS1, S - bt) },
    { id:'PP', name:'PP · Pivot post + head plate', g:'rail', asm:'frame', layer:'L0', poly:post, W:280 },
    { id:'FP', name:'FP · Front stop post', g:'rail', asm:'frame', layer:'L0', poly:fpost },
    { id:'LR', name:'LR · Low rail', g:'rail', asm:'frame', layer:'L1', poly:CK.rect(-yS1, 100 - w, yS1 + KICK, 100) },
    { id:'RK', name:'RK · Rear kick foot', g:'rail', asm:'frame', layer:'L0', poly:CK.rect(yS1, 0, yS1 + KICK, 70),
      note:'Carries the footprint back under the reclined back so leaning back hard cannot tip the sofa. Bolted through the low rail.' },
    { id:'SF', name:'SF · Spacer, front leg', g:'rail', asm:'frame', layer:'L1', poly:CK.rect(-yS1, S - bt - w, -yS1 + w, S - bt) },
    { id:'SR', name:'SR · Spacer, rear leg', g:'rail', asm:'frame', layer:'L1', poly:CK.rect(yS1 - w, S - bt - w, yS1, S - bt) },
    { id:'SP', name:'SP · Spacer, pivot post', g:'rail', asm:'frame', layer:'L1', poly:CK.rect(Pv[0] - w/2, S - bt - w, Pv[0] + w/2, S - bt) },
    { id:'ST', name:'ST · Table stop block', g:'rail', asm:'frame', layer:'L1', poly:stop },
    { id:'SF2',name:'SF · Spacer, front leg (2)', g:'rail', asm:'frame', layer:'L2', poly:CK.rect(-yS1, S - bt - w, -yS1 + w, S - bt) },
    { id:'SR2',name:'SR · Spacer, rear leg (2)', g:'rail', asm:'frame', layer:'L2', poly:CK.rect(yS1 - w, 0, yS1, 100) },
    { id:'HS', name:'HS · Arm-plank stop block', g:'rail', asm:'frame', layer:'L2', poly:hstop, note:'Bolted to the low rail; the arm plank lands on it in table mode.' },
    { id:'SB', name:'SB · Seat bearer', g:'rail', asm:'frame', layer:'L3', poly:CK.rect(-yS1, S - bt - w, yS1, S - bt) },
    { id:'AC', name:'AC · Table cleat', g:'rail', asm:'arm', layer:'L1', poly:cleat },
    { id:'AB', name:'AB · Pivot boss', g:'rail', asm:'arm', layer:'L1', poly:boss, W: Math.round(under - (Pv[1] - w/2 - 2)) },
    { id:'HP', name:'HP · Arm plank (handle / table strut)', g:'rail', asm:'arm', layer:'L2', poly:handle,
      note:'Bench: armrest and carry handle. Table: a slanted strut that lands on HS. Lapped and bolted (2 × M10) to the table cleat.' }
  ];
  var boards = [];
  for(var i=0;i<nS;i++) boards.push({ id:'SR', name:'SS · Main seat board', g:'slat', asm:'frame', inset:lay.L3[0], poly:CK.rect(yS0 + i*p, S - bt, yS0 + i*p + K.bw, S) });
  for(i=0;i<nT;i++) boards.push({ id:'TB', name:'TB · Table / back board', g:'slat', asm:'arm', inset:lay.L1[0], poly:CK.rect(-yT + i*p, under, -yT + i*p + K.bw, TB) });
  var fasteners = [
    { k:'pivot', name:'Pivot · M12 on Ø18 sleeve', asm:'frame', layer:'L0', at:Pv },
    { k:'pin', name:'Lock pin Ø12 · table hole', asm:'frame', layer:'L0', at: lock ? lock.Q1 : [Pv[0], Pv[1]+90] },
    { k:'pin', name:'Lock pin Ø12 · bench hole', asm:'frame', layer:'L0', at: lock ? lock.Q2 : [Pv[0], Pv[1]-90] }
  ];

  /* ---- the second bench: front seat in table pose, joined to the main seat in bench pose ---- */
  var nF = how === 'free' ? 3 : 4, DF = nF*p - CON.PITCH_GAP;
  var yF1 = -yS0, yF0 = yF1 - DF;                                  /* table pose, front edge yF0 */
  var join = (yS0 - 3) - yF1;                                      /* how far it travels back */
  var sledEnd = lay.L3[1] + 6;                                     /* inner face of the end frames */
  var inner = [], sledMove, sledNote, extraHW = [], extraChecks = [], sledKg = 0;
  function sledX(L, inset){ var x = L/2 - sledEnd - (inset||0); return [[-x, x]]; }
  function sledBoards(z, inset, asm){
    for(var k=0;k<nF;k++) inner.push({ name:'BS · Second-bench board', g:'slat', asm:asm||'sled',
      poly:CK.rect(yF0 + k*p, z - bt, yF0 + k*p + K.bw, z), xs:function(L){ return sledX(L, inset); } });
  }
  function sledCleats(z, inset, asm, label){
    inner.push({ name:label || 'BC · Second-bench end cleat', g:'rail', asm:asm||'sled',
      poly:CK.rect(yF0, z - bt - w, yF1, z - bt),
      xs:function(L){ var x = L/2 - sledEnd - (inset||0); return [[x - t, x], [-x, -x + t]]; } });
  }
  if(how === 'runner'){
    /* D1 · runners: the second bench has no legs. Its end cleats sit on hardwood ledgers
       screwed to the inside of the seat bearers and slide straight back. */
    var ledger = CK.rect(-yS1, S - bt - w - 30, yS1, S - bt - w);
    parts.push({ id:'RL', name:'RL · Runner ledger (UHMW-faced)', g:'rail', asm:'frame', layer:'L4', poly:ledger,
      note:'45 × 30 hardwood or 45 × 95 ripped, 2 mm UHMW tape on top; glued + screwed to the bearer.' });
    parts.push({ id:'BC', name:'BC · Second-bench runner cleat', g:'rail', asm:'sled', layer:'L4', poly:CK.rect(yF0, S - bt - w, yF1, S - bt) });
    sledBoards(S, -lay.L4[1] + lay.L3[1] - 0, 'sled');
    inner.forEach(function(q){ q.xs = function(L){ var x = L/2 - lay.L4[0]; return [[-x, x]]; }; });
    sledMove = function(v){ return CK.move(v*join, 0); };
    sledNote = 'slides straight back on two UHMW-faced ledgers — no legs, nothing to lift';
    extraHW = [{ id:'S1', qty:2, spec:'UHMW-PE tape 2 × 50 mm, 1.5 m (or 2 mm UHMW strip)', note:'On top of each runner ledger.' },
               { id:'S2', qty:2, spec:'Ø12 ball-lock pin (same as the pivot lock)', note:'Through ledger + cleat: holds the second bench in table or bench position.' }];
    sledKg = (nF*K.bw*bt*(P.L - 2*lay.L4[0]) + 2*t*w*DF)*5e-7;
  } else if(how === 'free'){
    /* D2 · free: a light, shorter stool-bench with its own legs. Lift it, drop it against
       the main seat — two dowels locate it, two hooks hold it. */
    var inset = 30, lz = S - bt - w;
    sledBoards(S, inset);
    sledCleats(S, inset);
    inner.push({ name:'BL · Second-bench leg', g:'rail', asm:'sled', poly:CK.rect(yF0, 0, yF0 + w, lz),
      xs:function(L){ var x = L/2 - sledEnd - inset; return [[x - t, x], [-x, -x + t]]; } });
    inner.push({ name:'BL · Second-bench leg', g:'rail', asm:'sled', poly:CK.rect(yF1 - w, 0, yF1, lz),
      xs:function(L){ var x = L/2 - sledEnd - inset; return [[x - t, x], [-x, -x + t]]; } });
    sledMove = function(v){ var up = Math.sin(Math.PI*v)*60; return CK.move(v*join, up); };
    sledNote = 'is lifted and dropped against the main seat';
    extraHW = [{ id:'S1', qty:4, spec:'Ø12 × 60 stainless dowel', note:'Two per end on the main seat edge; holes in the second-bench cleats locate it.' },
               { id:'S2', qty:2, spec:'Stainless hook-and-eye or toggle latch', note:'Holds the two benches together as a sofa.' }];
    sledKg = (nF*K.bw*bt*(P.L - 2*sledEnd - 2*inset) + 4*t*w*lz + 2*t*w*DF)*5e-7;
  } else if(how === 'link'){
    /* D3 · glide links: two parallel links per end hang the second bench from the frame.
       It swings back and up over its own footprint and lands level against the main seat
       — a four-bar, so it never tilts. */
    var R = join/(2*Math.sin(60*Math.PI/180)), zc = S - bt - w/2;
    var B1 = [yF1 - w/2 - 10, zc], B2 = [yF0 + w/2 + 10, zc];
    var dA = [R*Math.sin(60*Math.PI/180), -R*Math.cos(60*Math.PI/180)];
    var A1 = [B1[0] + dA[0], B1[1] + dA[1]], A2 = [B2[0] + dA[0], B2[1] + dA[1]];
    var k1 = CK.arm(CK.bar(A1, B1, w*0.8), [A1, B1], w/2), k2 = CK.arm(CK.bar(A2, B2, w*0.8), [A2, B2], w/2);
    parts.push({ id:'GR', name:'GR · Link rail', g:'rail', asm:'frame', layer:'L4',
      poly:CK.hull(CK.circle(A1, w/2 + 6, 16).concat(CK.circle(A2, w/2 + 6, 16), [[A2[0], S - bt - w + 50], [A1[0], S - bt - w + 50]])),
      note:'Lapped and bolted to the seat bearer.' });
    parts.push({ id:'K1', name:'K1 · Glide link, rear', g:'rail', asm:'link1', layer:'L5', poly:k1 });
    parts.push({ id:'K2', name:'K2 · Glide link, front', g:'rail', asm:'link2', layer:'L5', poly:k2 });
    parts.push({ id:'BC', name:'BC · Second-bench end cleat', g:'rail', asm:'sled', layer:'L6', poly:CK.hull(CK.rect(yF0, S - bt - w, yF1, S - bt).concat(CK.circle(B1, w/2, 12), CK.circle(B2, w/2, 12))) });
    lay.L5 = [5*t+5*g, 6*t+5*g]; lay.L6 = [6*t+6*g, 7*t+6*g];
    sledBoards(S, 0, 'sled');
    inner.forEach(function(q){ q.xs = function(L){ var x = L/2 - lay.L6[0]; return [[-x, x]]; }; });
    var th0 = Math.atan2(B1[1] - A1[1], B1[0] - A1[0]);
    sledMove = function(v){
      var a = -2*60*v*Math.PI/180, Bn = [A1[0] + R*Math.cos(th0 + a), A1[1] + R*Math.sin(th0 + a)];
      return CK.move(Bn[0] - B1[0], Bn[1] - B1[1]);
    };
    var linkRot = function(v){ return -2*60*v; };
    sledNote = 'swings back on two parallel links per end and lands level against the main seat';
    fasteners.push({ k:'pivot', name:'Glide pivot · M12', asm:'frame', layer:'L4', at:A1 });
    fasteners.push({ k:'pivot', name:'Glide pivot · M12', asm:'frame', layer:'L4', at:A2 });
    extraHW = conceptPivotHW(8, 2).slice(0, 6).map(function(h){ var c = Object.assign({}, h); c.id = 'G' + h.id.slice(1); c.note = 'Glide links: ' + h.note; return c; });
    sledKg = (nF*K.bw*bt*(P.L - 2*lay.L6[0]) + 2*t*w*DF)*5e-7;
    makeSwingSlide._link = { A1:A1, A2:A2, rot:linkRot };
  } else {
    /* D4 · tumble stool: a smaller box-bench, 450 high one way up and 300 the other.
       Table: upright as the second seat. Bench: tip it on its side and push it under the
       main seat — or leave it in front as a footrest. */
    var Hs = S, Ds2 = 300 - bt, inset4 = 30;
    var y0 = yF1 - Ds2 - bt;
    inner.length = 0;
    var box = [
      CK.rect(y0, S - bt, yF1, S),                        /* top */
      CK.rect(y0, 0, y0 + bt, S - bt),                    /* front side */
      CK.rect(yF1 - bt, 0, yF1, S - bt),                  /* back side */
      CK.rect(y0 + bt, 0, yF1 - bt, bt)                   /* bottom rail */
    ];
    var names = ['BT · Stool top board', 'BF · Stool side', 'BB · Stool side', 'BR · Stool bottom rail'];
    box.forEach(function(q, k){ inner.push({ name:names[k], g:k ? 'rail' : 'slat', asm:'sled', poly:q,
      xs:function(L){ var x = L/2 - sledEnd - inset4; return [[-x, x]]; } }); });
    var ctr = [yF1, 0];                                  /* tips about its back-bottom edge */
    var under0 = yS0 + 20;
    sledMove = function(v){
      var a = Math.min(1, v/0.5), m = Math.max(0, (v - 0.5)/0.5);
      var r = CK.rot(ctr, -90*a);
      var dy = m*(under0 - yF1);
      return function(q){ var u = r(q); return [u[0] + dy, u[1]]; };
    };
    sledNote = 'tips onto its side (300 high) and slides under the main seat, or stays in front as a footrest';
    extraHW = [{ id:'S1', qty:4, spec:'Felt / UHMW glides Ø30', note:'On the stool side that becomes the bottom.' }];
    sledKg = ((Ds2 + bt)*bt*2 + S*bt*2)*(P.L - 2*sledEnd - 2*inset4)*5e-7;
  }

  var layNames = Object.keys(lay);
  return {
    layers: lay, parts: parts, boards: boards, inner: inner, fasteners: fasteners, bt: bt, bw: K.bw,
    pose: function(s){
      var u = Math.min(1, s/0.5), v = Math.max(0, (s - 0.5)/0.5);
      var T = { arm: CK.rot(Pv, ANG*u), sled: sledMove(v) };
      if(how === 'link'){ var L = makeSwingSlide._link; T.link1 = CK.rot(L.A1, L.rot(v)); T.link2 = CK.rot(L.A2, L.rot(v)); }
      return T;
    },
    checks: function(P, st){
      var s = (P.fold||0)/100, backTop = CK.rot(Pv, ANG)([-yT, TB]);
      var depth = how === 'tumble' ? Ds : Math.round(yS1 - (yF0 + join));
      var armTop = hz0 + w - S;
      var lapA = 0;   /* arm plank ↔ cleat overlap, in the arm frame: proves the plank is fixed to the arm */
      var hb = handle, cb = CK.hull(boss.concat(cleat));
      lapA = CK.overlap(hb, cb);
      var rows = [
        { s:'ok', t:'<b>Table:</b> '+Wt+' mm top at '+TB+'; the second bench ('+DF+' deep, '+(how === 'tumble' ? 'stool' : 'shorter than the main bench')+') sits '+
            'opposite the main seat, both '+ov+' mm under the table edge.', v:Wt+' × '+P.L },
        { s: lapA > 10 ? 'ok' : 'fail', t:'<b>Arm planks.</b> Bench: armrests '+armTop+' mm above the seat, '+Math.round(hy1 - hy0)+' mm long — also the carry handles. '+
            'Table: they swing down into slanted struts landing on the HS blocks on the low rail, so the top is held by the pivot, the front stop, '+
            'the lock pin <i>and</i> the struts — it cannot rack or drop. Lapped onto the arm by '+Math.round(lapA)+' mm.', v:'handles' },
        { s:'ok', t:'<b>Bench → sofa:</b> the back swings over; the second bench '+sledNote+'. '+
            (how === 'tumble' ? 'Main seat stays '+Ds+' deep with back and armrests.' :
             'Joined seat '+depth+' mm deep with a back '+Math.round(backTop[1])+' high and armrests both ends — a sofa you can lie on ('+depth+' × '+(P.L - 2*sledEnd)+').'),
          v: how === 'tumble' ? Ds+' deep' : depth+' deep' },
        { s: sledKg > 25 && how === 'free' ? 'warn' : 'ok', t:'<b>Second bench</b> ≈ '+sledKg.toFixed(0)+' kg'+
            (how === 'free' ? (sledKg > 25 ? ' — two people, or use thinner boards for it.' : ' — one person can lift it.') :
             how === 'runner' ? ' — slides, never lifted.' : how === 'link' ? ' — swings on links, never lifted.' : ' — tipped, never lifted clear.'), v:sledKg.toFixed(0)+' kg' },
        lock ? { s:'ok', t:'<b>Top lock pin</b>: table hole at '+lock.R1+' mm, bench hole at '+lock.R2+' mm from the pivot, ≥ 16 mm of wood round each.', v:'r '+lock.R }
             : { s:'fail', t:'<b>No lock-pin position found.</b>', v:'—' },
        sfRow('Sit on the main-seat front edge', tipSF(st, 1000, s >= 1 && how !== 'tumble' ? yF0 + join : yS0), '1 kN on the front edge of the seat in use.'),
        s >= 0.5 ? sfRow('Lean back hard', tipSF(st, 800, (yS0 + yS1)/2, 300, backTop[1]), '300 N pushing back at the top of the back, 800 N on the seat.')
                 : sfRow('Lean on the table edge', tipSF(st, 600, -yT), '600 N on the front edge of the top (the second bench is a separate body, not counted).')
      ];
      return rows;
    },
    spans: function(P){
      return [
        { label:'Main seat boards', span: P.L - 2*lay.L3[1], b:K.bw, h:bt, tributary:p, load:2 },
        { label:'Table / back boards', span: P.L - 2*lay.L1[1], b:K.bw, h:bt, tributary:p, load:2 }
      ];
    },
    headline: function(P){ return P.L+' long · swing-top + '+({runner:'sliding', free:'loose', link:'gliding', tumble:'tumble-stool'})[how]+' second bench · arm planks'; },
    headline2: function(P, s){
      var st = s <= 0 ? 'TABLE' : s < 0.5 ? 'TOP SWINGING '+Math.round(s*200)+'%' : s < 1 ? 'SECOND BENCH MOVING '+Math.round((s - 0.5)*200)+'%' : 'SOFA';
      return st+' · 1 pivot + 1 pin per end · arm planks = handles / table struts';
    },
    hardware: function(){
      var screws = 2*(nS*2 + nT*2 + nF*2) + 8;
      return conceptPivotHW(2, 2).concat(extraHW,
        [{ id:'H1', qty:4, spec:'M10 × 130 hex bolt + washers + nyloc, A4', note:'Two per arm plank, through plank + table cleat.' }],
        conceptCommonHW(screws, 12, 2));
    },
    fabrication: [
      { part:'Arm planks', detail:'One 45 × 95 × '+Math.round(hy1 - hy0)+' per end, lapped on the inside of the table cleat with 2 × M10. Round the top edges R10 — they are the armrests and the carry handles. Cut the lower end parallel to the HS block face so it lands flat.' },
      { part:'Second bench', detail: how === 'runner' ? 'Two end cleats + '+nF+' boards; cleats ride on UHMW tape on the ledgers. Wax the tape once a season.' :
          how === 'free' ? 'A light stool-bench: 4 legs, 2 cleats, '+nF+' boards. Dowels in the main seat edge locate it, two latches hold it.' :
          how === 'link' ? 'Four identical glide links drilled as a stack, M12 pivots with sleeves. The second bench rises ≈ '+Math.round(R*(1 - Math.cos(60*Math.PI/180)))+' mm mid-swing.' :
          'A closed box: top board, two sides, bottom rail; works either way up. Felt glides on the side that becomes the bottom.' },
      { part:'Pivots', detail:'Same as the swing-top: M12 on Ø18 sleeves, Ø18/22 bushings, Ø36 counterbores, 3 mm UHMW washer.' },
      { part:'Edges', detail:'Round every exposed arris R3; armrests R10; table corners R20.' }
    ]
  };
}

function swingSlideDesign(id, name, how, blurb, tag, note){
  DESIGNS[id] = {
    id:id, name:name, blurb:blurb, info:{ designer:'concept', version:'0.1', license:'MIT' },
    areas: conceptAreas(),
    schema: [
      {k:'L',    label:'Length', group:'Dimensions', type:'range', min:1600, max:2600, step:10, def:2000, unit:'mm'},
      {k:'fold', label:'Convert: table → back → sofa', group:'Mechanism', type:'range', min:0, max:100, step:1, def:0, unit:'%'}
    ],
    variants:{ V:{ name:name.split(' · ')[0]+' · 2 m', tag:tag, note:note, set:{ L:2000, fold:0, mid:'off' } } },
    build:function(P, ctx){ P.mid = 'off'; return conceptBuild(makeSwingSlide(stockTW(ctx), P, how), P, ctx); }
  };
}
swingSlideDesign('slide1', 'S1 · Runner slide', 'runner',
  'Swing-top with a legless second bench riding on UHMW-faced wooden ledgers: it slides straight back and joins the main seat into a deep sofa.',
  'Legless second bench on wooden runners.',
  '<b>Runner slide.</b> Drag <i>Convert</i>: 0–50 % the top swings back and the arm planks rise into armrests; 50–100 % the second bench slides back on its ledgers.');
swingSlideDesign('slide2', 'S2 · Free dock', 'free',
  'Swing-top with a loose, lighter second bench on its own legs. Lift it, drop it against the main seat on two dowels — no rails at all.',
  'Loose 3-board stool-bench, dowel-docked.',
  '<b>Free dock.</b> The second bench is a separate light piece; drag <i>Convert</i> to see it lifted over and docked.');
swingSlideDesign('slide3', 'S3 · Glide links', 'link',
  'Swing-top with the second bench hung on parallel links: it swings back level, like a glider swing, and lands against the main seat.',
  'Second bench on parallel links — never lifted, never tilts.',
  '<b>Glide links.</b> Two links per end keep the second bench level while it swings 600 mm back.');
swingSlideDesign('slide4', 'S4 · Tumble stool', 'tumble',
  'Swing-top with a box stool-bench: upright it is the second seat at 450, tipped on its side it is 300 high and slides under the main seat or serves as a footrest.',
  'Box stool: seat one way up, footrest / storage the other.',
  '<b>Tumble stool.</b> Drag <i>Convert</i>: the stool tips onto its side and slides under the main seat.');
