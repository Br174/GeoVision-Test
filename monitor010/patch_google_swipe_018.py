from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')
    old="const sheetInteractive = el => !!(el?.closest?.('button,input,select,a,gmp-place-details'));"
    new="const sheetInteractive = el => !!(el?.closest?.('button,input,select,a'));"
    assert old in s
    s=s.replace(old,new,1)
    anchor="sheet.addEventListener('pointercancel', finishSheetDrag);"
    extra=r'''sheet.addEventListener('pointercancel', finishSheetDrag);
let gvTouchStartY=0, gvTouchStartX=0, gvTouchDragging=false;
sheet.addEventListener('touchstart', e => {
    if (e.touches.length !== 1 || sheetInteractive(e.target)) return;
    const inHead = !!e.target?.closest?.('.sheet-head');
    if (!inHead && sheetBody && sheetBody.scrollTop > 2) return;
    const t=e.touches[0]; gvTouchStartY=t.clientY; gvTouchStartX=t.clientX; gvTouchDragging=true;
    sheet.style.transition='none';
}, {capture:true, passive:true});
sheet.addEventListener('touchmove', e => {
    if (!gvTouchDragging || e.touches.length !== 1) return;
    const t=e.touches[0], dy=t.clientY-gvTouchStartY, dx=Math.abs(t.clientX-gvTouchStartX);
    if (dy <= 0 || dx > 120) return;
    if (e.cancelable) e.preventDefault();
    sheet.style.transform=`translate(-50%,${Math.min(dy,280)}px)`;
}, {capture:true, passive:false});
sheet.addEventListener('touchend', e => {
    if (!gvTouchDragging) return;
    gvTouchDragging=false; sheet.style.transition='';
    const t=e.changedTouches && e.changedTouches[0];
    const dy=t ? Math.max(0,t.clientY-gvTouchStartY) : 0;
    const dx=t ? Math.abs(t.clientX-gvTouchStartX) : 999;
    if (dy > 64 && dx < 140) { sheet.style.transform=''; closeSheet(); }
    else sheet.style.transform='';
}, {capture:true, passive:true});
sheet.addEventListener('touchcancel', () => { gvTouchDragging=false; sheet.style.transition=''; sheet.style.transform=''; }, {capture:true, passive:true});'''
    assert anchor in s
    s=s.replace(anchor,extra,1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB018 Google card swipe fixed')
