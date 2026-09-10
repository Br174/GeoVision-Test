from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v149: il Place selezionato dalla lista territoriale non prova piu a estrarre
# direttamente l'array photos (che sul dispositivo v148 torna vuoto). Usa invece
# lo stesso percorso Places UI Kit gia funzionante per i POI specifici:
# gmp-place-details + gmp-place-media/lightbox tramite renderGoogleUiMediaFallback.
# Nessun autoplay, nessun Radar, nessuna modifica alla scheda Google principale.

start=s.find('async function gvV147OpenTerritorySelectedPlace(place){')
end=s.find('window.gvV148LastTerritoryPlace=', start)
if start < 0 or end < 0:
    raise SystemExit('v149 patch aborted: v147/v148 anchors not found')

new_func=r'''async function gvV147OpenTerritorySelectedPlace(place){
    if(!place) return;
    const id=String(place.id||'');
    if(!id) return;

    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return;

    let name='Luogo';
    try{
        if(typeof place.fetchFields==='function'){
            await Promise.race([
                place.fetchFields({fields:['displayName']}),
                new Promise((_,rej)=>setTimeout(()=>rej(new Error('displayName timeout')),2500))
            ]);
            name=clean(place.displayName||name);
        }
    }catch(e){
        console.log('GeoVision v149 selected place name unavailable',id,e?.message||e);
    }

    title.textContent=name||'Foto Google';
    count.textContent='Carico le foto Google…';
    body.innerHTML='<div class="photo-gallery-loading">Carico la scheda fotografica del luogo…</div>';
    g.classList.add('show','gv-v144-fullscreen');

    try{
        const selected={
            name:name||'Luogo',
            placeId:id,
            kind:'poi',
            category:'poi',
            type:'poi'
        };
        body.innerHTML='';
        await renderGoogleUiMediaFallback(selected,body);
        if(!body.childNodes.length) throw new Error('official media empty');
        count.textContent='Tocca una foto per ingrandirla';
        console.log('GeoVision v149 selected territory -> official Place media',id);
    }catch(e){
        console.log('GeoVision v149 official selected-place media failed',id,e?.message||e);
        count.textContent='Foto non disponibili';
        body.innerHTML='<div class="photo-gallery-empty">Non sono riuscito a caricare le foto di questo luogo.</div>';
    }
}

'''

s=s[:start]+new_func+s[end:]
p.write_text(s,encoding='utf-8')
print('Applied v149 selected territory -> official Google media:',p,len(s))
