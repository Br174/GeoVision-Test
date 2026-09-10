from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v146: nella lista "Foto Google del territorio", il tap su un risultato
# apre le foto DEL SOLO LUOGO SELEZIONATO dentro il viewer GeoVision.
# Nessun autoplay, nessun Radar, nessuna modifica alla scheda Google principale.

helper=r'''
async function gvV146OpenTerritorySelectedPlace(place){
    if(!place) return;
    const id=String(place.id||'');
    if(!id) return;

    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return;

    let name=clean(place.displayName||'Luogo');
    title.textContent=name;
    count.textContent='Carico le foto Google…';
    body.innerHTML='<div class="photo-gallery-loading">Carico le foto del luogo…</div>';
    g.classList.add('show','gv-v144-fullscreen');

    const urls=[];
    try{
        if(typeof place.fetchFields==='function'){
            await place.fetchFields({fields:['displayName','photos']});
            name=clean(place.displayName||name||'Luogo');
            title.textContent=name;
            for(const ph of (Array.isArray(place.photos)?place.photos:[])){
                gvV145AddPhotoUrl(urls,ph,30);
                if(urls.length>=30) break;
            }
        }
    }catch(e){
        console.log('GeoVision v146 selected place fetchFields failed',id,e?.message||e);
    }

    if(!urls.length && typeof legacyGooglePhotos==='function'){
        try{
            const photos=await legacyGooglePhotos(id);
            for(const ph of (photos||[])){
                gvV145AddPhotoUrl(urls,ph,30);
                if(urls.length>=30) break;
            }
        }catch(e){ console.log('GeoVision v146 selected place legacy photos failed',id,e?.message||e); }
    }

    if(urls.length){
        gvV144RenderPhotoFolder({name,placeId:id},urls);
        console.log('GeoVision v146 selected territory place photos active',id,urls.length);
        return;
    }

    count.textContent='Foto non disponibili';
    body.innerHTML='<div class="photo-gallery-empty">Non sono riuscito a caricare le foto di questo luogo.</div>';
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvV146OpenTerritorySelectedPlace(place)' not in s:
    if anchor not in s:
        raise SystemExit('v146 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

# Il fallback localita usa gmp-place-search. E gia selectable: agganciamo
# l'evento ufficiale gmp-select e usiamo il Place restituito da Google.
old="search.setAttribute('selectable', '');\n        request.setAttribute('text-query', [p.name, p.parent, 'attrazioni'].filter(Boolean).join(' '));"
new="search.setAttribute('selectable', '');\n        search.addEventListener('gmp-select', (event) => {\n            try{ event.preventDefault?.(); }catch(e){}\n            void gvV146OpenTerritorySelectedPlace(event?.place);\n        });\n        request.setAttribute('text-query', [p.name, p.parent, 'attrazioni'].filter(Boolean).join(' '));"
if old not in s:
    raise SystemExit('v146 patch aborted: selectable territory search anchor not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Applied v146 territory result -> selected place photos:',p,len(s))
