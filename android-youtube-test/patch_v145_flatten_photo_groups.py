from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v145: galleria fullscreen con due comportamenti distinti.
# - POI/monumento/attivita: SOLO foto del placeId corrente.
# - Citta/paese/localita: foto dei gruppi/luoghi trovati nella localita.
# Nessun autoplay, nessun Radar, nessuna modifica alla scheda Google o storytelling.
# Entrambi gli accessi Foto usano lo stesso viewer fullscreen v144.

helper=r'''
function gvV145AddPhotoUrl(out,raw,maxCount=60){
    if(out.length>=maxCount) return;
    let u='';
    try{
        if(typeof raw==='string') u=raw;
        else if(typeof raw?.getURI==='function') u=raw.getURI({maxWidth:1800,maxHeight:1800})||'';
        else if(typeof raw?.getUrl==='function') u=raw.getUrl({maxWidth:1800,maxHeight:1800})||'';
    }catch(e){}
    u=clean(u||'');
    if(!u || u.startsWith('data:') || out.includes(u)) return;
    out.push(u);
}

async function gvV145CollectSinglePlacePhotos(p){
    const out=[];
    if(!googleReady || !p?.placeId) return out;
    const placeId=String(p.placeId);

    // Percorso principale: foto esclusivamente del Place corrente.
    try{
        const lib=await google.maps.importLibrary('places');
        const P=lib.Place;
        const detail=new P({id:placeId});
        await detail.fetchFields({fields:['displayName','photos']});
        for(const ph of (Array.isArray(detail.photos)?detail.photos:[])){
            gvV145AddPhotoUrl(out,ph,30);
            if(out.length>=30) break;
        }
    }catch(e){
        console.log('GeoVision v145 single place fetch failed',placeId,e?.message||e);
    }

    // Fallback legacy sempre sullo STESSO placeId: mai ricerca di luoghi vicini.
    if(!out.length && typeof legacyGooglePhotos==='function'){
        try{
            const photos=await legacyGooglePhotos(placeId);
            for(const ph of (photos||[])){
                gvV145AddPhotoUrl(out,ph,30);
                if(out.length>=30) break;
            }
        }catch(e){ console.log('GeoVision v145 legacy single place photos failed',e?.message||e); }
    }

    return out;
}

async function gvV145CollectGroupPhotos(p){
    const out=[];
    if(!googleReady || !p) return out;
    const seenIds=new Set();
    const base=[p.name,p.parent].filter(Boolean).join(' ');
    const queries=[`${base} attrazioni turistiche`,`${base} monumenti`,`${base} luoghi da visitare`];

    try{
        const lib=await google.maps.importLibrary('places');
        const P=lib.Place;
        for(const textQuery of queries){
            if(out.length>=60) break;
            let places=[];
            try{
                const res=await P.searchByText({
                    textQuery,
                    fields:['id','displayName','location'],
                    locationBias:{lat:p.lat,lng:p.lon},
                    language:'it',
                    region:'IT',
                    maxResultCount:10
                });
                places=Array.isArray(res?.places)?res.places:[];
            }catch(e){
                console.log('GeoVision v145 searchByText failed',textQuery,e?.message||e);
            }

            for(const pl of places){
                if(out.length>=60) break;
                const id=String(pl?.id||'');
                if(!id || seenIds.has(id)) continue;
                try{
                    const loc=pl.location;
                    const lat=loc ? (typeof loc.lat==='function'?loc.lat():Number(loc.lat)) : p.lat;
                    const lng=loc ? (typeof loc.lng==='function'?loc.lng():Number(loc.lng)) : p.lon;
                    if(Number.isFinite(lat)&&Number.isFinite(lng)&&metersBetween({lat:p.lat,lng:p.lon},{lat,lng})>5500) continue;
                }catch(e){}
                seenIds.add(id);

                try{
                    const detail=new P({id});
                    await detail.fetchFields({fields:['displayName','photos']});
                    for(const ph of (Array.isArray(detail.photos)?detail.photos:[])){
                        gvV145AddPhotoUrl(out,ph,60);
                        if(out.length>=60) break;
                    }
                }catch(e){
                    console.log('GeoVision v145 group fetchFields photos failed',id,e?.message||e);
                }
            }
        }
    }catch(e){
        console.log('GeoVision v145 Places import failed',e?.message||e);
    }

    // Fallback legacy limitato alla sola modalita citta/paese.
    if(out.length<8 && typeof legacyGoogleTextPhotos==='function'){
        for(const textQuery of queries){
            if(out.length>=60) break;
            let results=[];
            try{ results=await legacyGoogleTextPhotos(textQuery,p); }catch(e){}
            for(const r of (results||[])){
                if(out.length>=60) break;
                try{
                    const loc=r?.geometry?.location;
                    if(loc && metersBetween({lat:p.lat,lng:p.lon},{lat:loc.lat(),lng:loc.lng()})>5500) continue;
                }catch(e){}
                for(const ph of (Array.isArray(r?.photos)?r.photos:[])){
                    gvV145AddPhotoUrl(out,ph,60);
                    if(out.length>=60) break;
                }
            }
        }
    }

    return out;
}

async function gvV145OpenFlattenedGroupGallery(){
    const p=current;
    if(!p) return toast('Seleziona prima un luogo');
    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return;

    const locality=(typeof isOfficialCityLocality==='function') && isOfficialCityLocality(p);
    title.textContent=p.name||'Foto';
    count.textContent=locality?'Raccolgo le foto della localita…':'Carico le foto del luogo…';
    body.innerHTML=`<div class="photo-gallery-loading">${locality?'Raccolgo le foto dei luoghi…':'Carico solo le foto di questo luogo…'}</div>`;
    g.classList.add('show','gv-v144-fullscreen');

    let urls=[];
    try{
        urls=locality ? await gvV145CollectGroupPhotos(p) : await gvV145CollectSinglePlacePhotos(p);
    }catch(e){ console.log('GeoVision v145 collect failed',e?.message||e); }
    if(current!==p || !g.classList.contains('show')) return;

    if(urls.length){
        gvV144RenderPhotoFolder(p,urls);
        console.log(locality?'GeoVision v145 locality group gallery active':'GeoVision v145 single place gallery active',urls.length);
        return;
    }

    // Fallback v144. Per un POI googleGalleryPhotos resta legato al suo placeId;
    // per una localita mantiene il comportamento galleria gia esistente.
    console.log('GeoVision v145 no direct URLs, fallback to existing photo folder');
    await gvV144OpenExistingPhotoFolder();
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvV145OpenFlattenedGroupGallery()' not in s:
    if anchor not in s:
        raise SystemExit('v145 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old="gvV144PhotoButton.onclick=()=>void gvV144OpenExistingPhotoFolder();"
new="gvV144PhotoButton.onclick=()=>void gvV145OpenFlattenedGroupGallery();"
if old not in s:
    raise SystemExit('v145 patch aborted: v144 photo button binding not found')
s=s.replace(old,new,1)

button_anchor="if(gvV144PhotoButton){\n    gvV144PhotoButton.tabIndex=0;\n    gvV144PhotoButton.onclick=()=>void gvV145OpenFlattenedGroupGallery();\n}\n"
if button_anchor not in s:
    raise SystemExit('v145 patch aborted: v145 photo button block not found')
extra="""if(gvV144PhotoButton){\n    gvV144PhotoButton.tabIndex=0;\n    gvV144PhotoButton.onclick=()=>void gvV145OpenFlattenedGroupGallery();\n}\nconst gvV145ImagesMenuButton=document.querySelector('[data-vp=\"images\"]');\nif(gvV145ImagesMenuButton){\n    gvV145ImagesMenuButton.onclick=()=>{ document.getElementById('videoPicker')?.classList.remove('show'); void gvV145OpenFlattenedGroupGallery(); };\n}\n"""
s=s.replace(button_anchor,extra,1)

p.write_text(s,encoding='utf-8')
print('Applied v145 single-place/locality photo routing:',p,len(s))
