from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

# LAB025 is deliberately narrow: preserve LAB024 UI, restore the official Google-card
# rendering path and make the photo button open Google results already filtered to photos.

def patch(path):
    s=path.read_text(encoding='utf-8')
    # Do not alter the card renderer itself. Remove only any LAB024 accidental takeover of card clicks.
    assert 'async function renderOfficialGoogleCard' in s
    assert 'id="googleCardHost"' in s
    assert 'const gv024PhotoButton' in s

    # Replace only LAB024 photo-button action. The selected place is `current`, the same object used by the card.
    old="gv024PhotoButton.onclick=e=>{e.preventDefault();e.stopPropagation();openPhotoGallery();};"
    new="""gv024PhotoButton.onclick=e=>{
    e.preventDefault();e.stopPropagation();
    const p=(typeof current!=='undefined'&&current)?current:null;
    const q=String((p&&(p.name||p.title||p.address))||'').trim();
    if(!q){ if(typeof openPhotoGallery==='function') openPhotoGallery(); return; }
    const url='https://www.google.com/search?tbm=isch&q='+encodeURIComponent(q+' foto');
    try{
      if(window.GeoVisionSocial&&typeof window.GeoVisionSocial.open==='function') window.GeoVisionSocial.open(url);
      else window.open(url,'_blank');
    }catch(_){ window.location.href=url; }
  };"""
    assert old in s, 'LAB024 photo handler anchor missing'
    s=s.replace(old,new,1)

    # Guard against the regression observed on phone: the official card must still be rendered by openPlace.
    assert 'const cardPromise=renderOfficialGoogleCard(p);' in s, 'official Google card call missing'
    assert 'await cardPromise;' in s, 'official Google card await missing'
    assert "$('#sheet').classList.add('show')" in s, 'sheet show missing'
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB025: Google card preserved + photo button opens Google image results for current place')
