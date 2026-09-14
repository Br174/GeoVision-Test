from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

CSS=r'''
<style id="gv024-photo-button-style">
/* LAB024: only the existing photo control is activated/repositioned. */
#sheet .sheet-head{gap:8px!important}
#sheetPhotosVisual.sheet-photos-visual{
  width:42px!important;height:42px!important;flex:0 0 42px!important;
  display:grid!important;place-items:center!important;
  border:1px solid #e4e8ee!important;border-radius:50%!important;
  background:#fff!important;padding:0!important;box-shadow:none!important;
  cursor:pointer!important;pointer-events:auto!important;
  margin-left:0!important;margin-right:0!important;
}
#sheetClose.close-sheet{margin-left:4px!important}
#sheetPhotosVisual:active{background:#f8fafc!important;transform:scale(.97)}
.gv-gphotos-logo{position:relative;display:block;width:24px;height:24px}
.gv-gphotos-logo .gp{position:absolute;display:block;width:10px;height:10px}
.gv-gphotos-logo .gp-red{left:7px;top:0;background:#ea4335;border-radius:7px 7px 2px 7px}
.gv-gphotos-logo .gp-blue{right:0;top:7px;background:#4285f4;border-radius:7px 7px 7px 2px}
.gv-gphotos-logo .gp-green{left:7px;bottom:0;background:#34a853;border-radius:2px 7px 7px 7px}
.gv-gphotos-logo .gp-yellow{left:0;top:7px;background:#fbbc04;border-radius:7px 2px 7px 7px}
</style>
'''

HOOK="""$('#sheetVideo').onclick = e => { e.preventDefault(); e.stopPropagation(); $('#videoPicker').classList.toggle('show'); };"""
ADD=HOOK+"""
const gv024PhotoButton=$('#sheetPhotosVisual');
if(gv024PhotoButton){
  gv024PhotoButton.tabIndex=0;
  gv024PhotoButton.setAttribute('aria-label','Foto Google del luogo');
  gv024PhotoButton.setAttribute('title','Foto Google');
  gv024PhotoButton.onclick=e=>{e.preventDefault();e.stopPropagation();openPhotoGallery();};
}
"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert 'id="sheetPhotosVisual"' in s, 'photo button missing'
    assert 'async function openPhotoGallery()' in s, 'photo gallery function missing'
    assert HOOK in s, 'sheet video hook anchor missing'
    s=s.replace(HOOK,ADD,1)
    assert '</head>' in s
    s=s.replace('</head>',CSS+'</head>',1)
    assert 'pointer-events:auto!important' in s
    assert "gv024PhotoButton.onclick" in s
    assert "openPhotoGallery();" in s
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB024 Google Photos button activated + aligned')
