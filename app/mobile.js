var ptrs={}, pinch=null;
function ptrDist(){ var k=Object.keys(ptrs); if(k.length<2) return 0;
  var a=ptrs[k[0]], b=ptrs[k[1]]; return Math.hypot(a.x-b.x, a.y-b.y); }
host.addEventListener('pointerdown', function(e){
  if(VIEWTAB!=='3d') return;
  ptrs[e.pointerId]={x:e.clientX,y:e.clientY};
  host.setPointerCapture(e.pointerId);
  if(Object.keys(ptrs).length===2){ pinch={d:ptrDist(), dist:dist}; drag=null; return; }
  drag={x:e.clientX,y:e.clientY,pan:(MODE==='pan'||e.button===2||e.button===1||e.shiftKey),
        ox:e.clientX, oy:e.clientY, moved:0};
});
host.addEventListener('pointerup', function(e){
  /* a click/tap, not the end of an orbit */
  if(VIEWTAB==='3d' && drag && drag.moved < 5 && e.button===0 && !pinch){
    var i = pickAt(e.clientX, e.clientY);
    selectPart(i===null ? null : MODEL.parts[i]);
  }
});
host.addEventListener('pointermove', function(e){
  if(ptrs[e.pointerId]){ ptrs[e.pointerId].x=e.clientX; ptrs[e.pointerId].y=e.clientY; }
  if(pinch){
    var d=ptrDist();
    if(d>0 && pinch.d>0) setDist(pinch.dist*pinch.d/d);
    return;
  }
  if(!drag) return;
  var dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  if(drag.pan){
    var eye=camPos(), f=nrm(vsub(target,eye)), r=nrm(vcross(f,[0,0,1])), u=vcross(r,f);
    var k=dist*0.0013;
    target[0]+=(-dx*r[0]+dy*u[0])*k;
    target[1]+=(-dx*r[1]+dy*u[1])*k;
    target[2]+=(-dx*r[2]+dy*u[2])*k;
  } else {
    az-=dx*0.006;
    el=Math.max(-0.35, Math.min(1.45, el+dy*0.005));
  }
  drag.moved = Math.max(drag.moved||0,
    Math.abs(e.clientX-drag.ox) + Math.abs(e.clientY-drag.oy));
  drag.x=e.clientX; drag.y=e.clientY; draw();
});
function endPtr(e){
  delete ptrs[e.pointerId];
  if(Object.keys(ptrs).length<2) pinch=null;
  if(!Object.keys(ptrs).length) drag=null;
}
window.addEventListener('pointerup', endPtr);
window.addEventListener('pointercancel', endPtr);
