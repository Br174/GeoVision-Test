from pathlib import Path

p = Path('android-youtube-test/app/src/main/assets/geovision.html')
s = p.read_text(encoding='utf-8')

marker = 'GV_PHOTO_URI_LAB_V1'
if marker in s:
    print('Photo URI LAB already present')
    raise SystemExit(0)

lab = r'''
<!-- GV_PHOTO_URI_LAB_V1: test isolato Place.fetchFields({photos}) -> Photo.getURI() -->
<style>
#gvPhotoUriLabBtn{position:fixed;left:12px;bottom:22px;z-index:50000;border:0;border-radius:999px;padding:11px 14px;background:#111827;color:#fff;font:700 12px/1 system-ui;box-shadow:0 5px 20px rgba(0,0,0,.22)}
#gvPhotoUriLabOverlay{position:fixed;inset:0;z-index:51000;background:rgba(15,23,42,.72);display:none;align-items:center;justify-content:center;padding:16px}
#gvPhotoUriLabOverlay.show{display:flex}
#gvPhotoUriLabCard{width:min(620px,96vw);max-height:92vh;overflow:auto;background:#fff;border-radius:18px;padding:14px;font:13px/1.45 system-ui;color:#1f2937}
#gvPhotoUriLabHead{display:flex;align-items:center;gap:10px;margin-bottom:10px}
#gvPhotoUriLabTitle{font-weight:800;flex:1}
#gvPhotoUriLabClose{width:36px;height:36px;border:1px solid #e5e7eb;border-radius:50%;background:#fff;font-size:22px}
#gvPhotoUriLabStatus{white-space:pre-wrap;background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:10px;margin:8px 0}
#gvPhotoUriLabImage{display:none;width:100%;max-height:58vh;object-fit:contain;background:#eef2f7;border-radius:12px}
#gvPhotoUriLabAttrib{font-size:11px;color:#6b7280;margin-top:8px}
</style>
<button id="gvPhotoUriLabBtn" type="button">TEST FOTO GOOGLE</button>
<div id="gvPhotoUriLabOverlay" role="dialog" aria-modal="true">
  <div id="gvPhotoUriLabCard">
    <div id="gvPhotoUriLabHead"><div id="gvPhotoUriLabTitle">Laboratorio foto Google</div><button id="gvPhotoUriLabClose" type="button">×</button></div>
    <div id="gvPhotoUriLabStatus">Pronto.</div>
    <img id="gvPhotoUriLabImage" alt="Foto Google di prova">
    <div id="gvPhotoUriLabAttrib"></div>
  </div>
</div>
<script>
(function(){
  const btn=document.getElementById('gvPhotoUriLabBtn');
  const ov=document.getElementById('gvPhotoUriLabOverlay');
  const st=document.getElementById('gvPhotoUriLabStatus');
  const im=document.getElementById('gvPhotoUriLabImage');
  const at=document.getElementById('gvPhotoUriLabAttrib');
  const close=document.getElementById('gvPhotoUriLabClose');
  const show=()=>ov.classList.add('show');
  close.onclick=()=>ov.classList.remove('show');
  ov.addEventListener('click',e=>{if(e.target===ov)ov.classList.remove('show')});
  function text(v){return String(v==null?'':v)}
  btn.onclick=async()=>{
    show();
    im.style.display='none'; im.removeAttribute('src'); at.textContent='';
    const p=(typeof current!=='undefined')?current:null;
    if(!p){st.textContent='NESSUN LUOGO ATTIVO\nApri prima la scheda di una attività commerciale Google e poi premi di nuovo TEST FOTO GOOGLE.';return;}
    if(!p.placeId){st.textContent='PLACE ID ASSENTE\nLuogo: '+text(p.name)+'\nQuesta prova richiede una scheda con Place ID Google.';return;}
    st.textContent='TEST IN CORSO\nLuogo: '+text(p.name)+'\nPlace ID: '+text(p.placeId)+'\nMetodo: Place.fetchFields({fields:[photos]})';
    try{
      if(!(window.google&&google.maps&&google.maps.importLibrary))throw new Error('Google Maps JavaScript non pronta');
      const lib=await google.maps.importLibrary('places');
      const Place=lib&&lib.Place;
      if(!Place)throw new Error('Classe Place non disponibile');
      const place=new Place({id:String(p.placeId)});
      await place.fetchFields({fields:['photos']});
      const photos=Array.isArray(place.photos)?place.photos:[];
      if(!photos.length){
        st.textContent='RISULTATO: ZERO FOTO\nLuogo: '+text(p.name)+'\nPlace ID: '+text(p.placeId)+'\nLa chiamata fetchFields è terminata senza errore, ma photos[] è vuoto.';
        return;
      }
      const ph=photos[0];
      if(!ph||typeof ph.getURI!=='function')throw new Error('Photo.getURI non disponibile sulla prima foto');
      const uri=ph.getURI({maxWidth:1600,maxHeight:1200});
      if(!uri)throw new Error('Photo.getURI ha restituito URI vuoto');
      st.textContent='SUCCESSO: FOTO ESTRATTE DA GOOGLE\nLuogo: '+text(p.name)+'\nPlace ID: '+text(p.placeId)+'\nFoto restituite: '+photos.length+'\nPrima foto: URI ottenuto. Verifico il caricamento immagine…';
      const attrs=Array.isArray(ph.authorAttributions)?ph.authorAttributions:[];
      at.textContent=attrs.length?'Attribuzione: '+attrs.map(a=>a.displayName||a.uri||'Google').join(' · '):'Attribuzione foto: nessun testo restituito dal campo disponibile.';
      im.onload=()=>{im.style.display='block';st.textContent='SUCCESSO COMPLETO\nLuogo: '+text(p.name)+'\nPlace ID: '+text(p.placeId)+'\nFoto restituite: '+photos.length+'\nPhoto.getURI(): OK\nCaricamento IMG nel contenitore GeoVision: OK';};
      im.onerror=()=>{im.style.display='none';st.textContent='SUCCESSO PARZIALE\nFoto restituite: '+photos.length+'\nPhoto.getURI(): OK\nCaricamento IMG: FALLITO';};
      im.src=uri;
    }catch(err){
      st.textContent='ERRORE TEST FOTO\nLuogo: '+text(p.name)+'\nPlace ID: '+text(p.placeId)+'\n'+text(err&&err.name)+': '+text(err&&err.message||err);
    }
  };
})();
</script>
'''

if '</body>' not in s:
    raise SystemExit('Missing </body> in generated HTML')
s = s.replace('</body>', lab + '\n</body>', 1)
p.write_text(s, encoding='utf-8')
print('Applied', marker, 'bytes', len(s.encode('utf-8')))
