from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v144: non tenta più di aprire la lightbox Google con eventi sintetici.
# Apre invece un fullscreen separato: prima prova le Photo ufficiali del Place,
# usando tutte quelle restituite da Google, con swipe/frecce e attribuzione; se il canale
# foto non è disponibile, usa direttamente gmp-place-media ufficiale di Places UI Kit.
# La scheda originale resta intatta.

old='async function renderOfficialGoogleCard(p) { void gvV143TapOfficialGooglePhoto(p);'
new='async function renderOfficialGoogleCard(p) { void gvV144AutoOpenOfficialMedia(p);'
if old not in s:
    raise SystemExit('v144 patch aborted: v143 render hook not found')
s=s.replace(old,new,1)

helper=r'''
function gvV144CloseOfficialMedia(){
    document.getElementById('gvV144PhotoViewer')?.remove();
}

function gvV144PhotoAttribution(photo){
    try{
        const a=Array.isArray(photo?.authorAttributions)?photo.authorAttributions[0]:null;
        return {
            name:clean(a?.displayName||'Google Maps'),
            uri:clean(a?.uri||'')
        };
    }catch(e){ return {name:'Google Maps',uri:''}; }
}

async function gvV144FetchPlacePhotos(p){
    if(!googleReady || !p?.placeId) return [];
    const lib=await google.maps.importLibrary('places');
    const P=lib.Place;
    const place=new P({id:p.placeId});
    await place.fetchFields({fields:['displayName','photos']});
    const out=[];
    for(const ph of Array.isArray(place.photos)?place.photos:[]){
        try{
            const url=clean(ph.getURI({maxWidth:1600,maxHeight:1600})||'');
            if(!url) continue;
            const a=gvV144PhotoAttribution(ph);
            out.push({url,authorName:a.name,authorUri:a.uri});
        }catch(e){}
    }
    return out;
}

function gvV144BaseOverlay(p){
    gvV144CloseOfficialMedia();
    const v=document.createElement('div');
    v.id='gvV144PhotoViewer';
    v.style.cssText='position:fixed;inset:0;z-index:2147483647;background:#111;display:flex;flex-direction:column;color:#fff;font-family:system-ui,sans-serif';
    v.innerHTML=`
      <div style="height:66px;flex:0 0 66px;display:flex;align-items:center;padding:8px 14px;background:#101113;gap:10px">
        <div id="gvV144Title" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:17px;font-weight:650"></div>
        <button id="gvV144Close" type="button" aria-label="Chiudi" style="width:46px;height:46px;border:0;border-radius:50%;background:#050506;color:#fff;font-size:30px;line-height:1">×</button>
      </div>
      <div id="gvV144Stage" style="position:relative;flex:1;min-height:0;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#111"></div>`;
    document.body.appendChild(v);
    v.querySelector('#gvV144Title').textContent=p?.name||'Foto del luogo';
    v.querySelector('#gvV144Close').onclick=gvV144CloseOfficialMedia;
    return v;
}

async function gvV144RenderUiKitPhoto(p,token){
    if(!p?.placeId || token!==window.gvV144MediaToken || current!==p) return false;
    try{
        await google.maps.importLibrary('places');
        await Promise.race([
            Promise.all([
                customElements.whenDefined('gmp-place-details'),
                customElements.whenDefined('gmp-place-media')
            ]),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout')),5000))
        ]);
        if(token!==window.gvV144MediaToken || current!==p) return false;
        const v=gvV144BaseOverlay(p);
        const stage=v.querySelector('#gvV144Stage');
        const wrap=document.createElement('div');
        wrap.style.cssText='width:min(100%,900px);max-height:100%;overflow:auto;background:#fff;border-radius:0';
        const details=document.createElement('gmp-place-details');
        details.style.cssText='display:block;width:100%;background:#fff';
        const request=document.createElement('gmp-place-details-place-request');
        request.setAttribute('place',p.placeId);
        const config=document.createElement('gmp-place-content-config');
        const media=document.createElement('gmp-place-media');
        media.setAttribute('preferred-size','large');
        media.setAttribute('lightbox-preferred','');
        media.style.cssText='display:block;width:100%;min-height:55vh';
        const attr=document.createElement('gmp-place-attribution');
        config.appendChild(media);
        config.appendChild(attr);
        details.appendChild(request);
        details.appendChild(config);
        wrap.appendChild(details);
        stage.appendChild(wrap);
        return true;
    }catch(e){
        console.log('GeoVision v144 UI Kit photo fallback failed',e?.message||e);
        return false;
    }
}

function gvV144RenderSwipePhotos(p,photos,token){
    if(token!==window.gvV144MediaToken || current!==p || !Array.isArray(photos) || !photos.length) return;
    const v=gvV144BaseOverlay(p);
    const stage=v.querySelector('#gvV144Stage');
    stage.innerHTML=`
      <img id="gvV144Image" alt="" style="width:100%;height:100%;object-fit:contain;display:block;user-select:none;-webkit-user-drag:none">
      <div id="gvV144Attr" style="position:absolute;left:12px;bottom:14px;max-width:68%;padding:6px 9px;border-radius:9px;background:rgba(0,0,0,.58);font-size:12px;line-height:1.25"></div>
      <div id="gvV144Count" style="position:absolute;right:12px;bottom:14px;padding:6px 9px;border-radius:999px;background:rgba(0,0,0,.58);font-size:12px;font-weight:700"></div>
      <button id="gvV144Prev" type="button" aria-label="Foto precedente" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);width:50px;height:50px;border:0;border-radius:50%;background:rgba(0,0,0,.66);color:#fff;font-size:34px">‹</button>
      <button id="gvV144Next" type="button" aria-label="Foto successiva" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);width:50px;height:50px;border:0;border-radius:50%;background:rgba(0,0,0,.66);color:#fff;font-size:34px">›</button>`;
    let i=0,sx=0,sy=0;
    const img=stage.querySelector('#gvV144Image');
    const count=stage.querySelector('#gvV144Count');
    const attr=stage.querySelector('#gvV144Attr');
    const show=(n)=>{
        i=(n+photos.length)%photos.length;
        const ph=photos[i];
        img.src=ph.url;
        img.alt=`${p?.name||'Luogo'} · foto ${i+1}`;
        count.textContent=`${i+1} / ${photos.length}`;
        attr.textContent=ph.authorName?`Foto: ${ph.authorName}`:'Google Maps';
        if(ph.authorUri){
            attr.style.cursor='pointer';
            attr.onclick=()=>openUrl(ph.authorUri);
        }else{
            attr.style.cursor='default';
            attr.onclick=null;
        }
    };
    stage.querySelector('#gvV144Prev').onclick=()=>show(i-1);
    stage.querySelector('#gvV144Next').onclick=()=>show(i+1);
    stage.addEventListener('touchstart',e=>{const t=e.changedTouches?.[0];if(t){sx=t.clientX;sy=t.clientY;}},{passive:true});
    stage.addEventListener('touchend',e=>{const t=e.changedTouches?.[0];if(!t)return;const dx=t.clientX-sx,dy=t.clientY-sy;if(Math.abs(dx)>48&&Math.abs(dx)>Math.abs(dy)){show(i+(dx<0?1:-1));}},{passive:true});
    show(0);
}

async function gvV144AutoOpenOfficialMedia(p){
    const token=(window.gvV144MediaToken=(window.gvV144MediaToken||0)+1);
    if(!p?.placeId) return;
    const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
    await sleep(180);
    if(token!==window.gvV144MediaToken || current!==p) return;

    // Primo obiettivo: una foto grande deve comparire comunque usando il componente ufficiale UI Kit.
    const fallbackPromise=gvV144RenderUiKitPhoto(p,token);

    // In parallelo proviamo il canale Photo ufficiale. Se disponibile, passiamo a un viewer
    // scorrevole usando tutte le immagini che Google restituisce per il Place.
    try{
        const photos=await Promise.race([
            gvV144FetchPlacePhotos(p),
            new Promise(resolve=>setTimeout(()=>resolve([]),4500))
        ]);
        if(token!==window.gvV144MediaToken || current!==p) return;
        if(photos?.length){
            gvV144RenderSwipePhotos(p,photos,token);
            console.log('GeoVision v144: swipe viewer active',photos.length);
            return;
        }
    }catch(e){ console.log('GeoVision v144 photo API unavailable',e?.message||e); }

    await fallbackPromise;
    console.log('GeoVision v144: official UI Kit fullscreen fallback active');
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvV144AutoOpenOfficialMedia(p)' not in s:
    if anchor not in s:
        raise SystemExit('v144 patch aborted: anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

p.write_text(s,encoding='utf-8')
print('Applied v144 official media fullscreen patch:',p,len(s))
