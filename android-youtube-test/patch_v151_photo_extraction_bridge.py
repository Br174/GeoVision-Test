from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v151: un solo obiettivo funzionale: portare le foto del Place selezionato
# dalla UI Google al viewer proprietario GeoVision. Prova, in ordine:
# 1) Place (new) photos/getURI
# 2) PlacesService legacy photos/getUrl
# 3) PlaceDetails UI Kit dopo gmp-load + scansione DOM/shadow DOM accessibile
# Se nessuna strada espone URI utilizzabili, conserva il fallback ufficiale v149.
# Nessun autoplay, musica, Radar o modifica alla scheda Google principale.

start=s.find('async function gvV147OpenTerritorySelectedPlace(place){')
end=s.find('window.gvV148LastTerritoryPlace=', start)
if start < 0 or end < 0:
    raise SystemExit('v151 patch aborted: selected-place anchors not found')

new_code=r'''function gvV151UniquePush(items,url,attrs=[],source=''){
    try{ url=clean(url||''); }catch(e){ url=String(url||'').trim(); }
    if(!url || !/^https?:/i.test(url) || items.some(x=>x.url===url)) return false;
    items.push({url,attrs:Array.isArray(attrs)?attrs:[],source});
    return true;
}

function gvV151AttrsFromNewPhoto(ph){
    const out=[];
    try{
        for(const a of (Array.isArray(ph?.authorAttributions)?ph.authorAttributions:[])){
            const displayName=clean(a?.displayName||'');
            const uri=clean(a?.uri||'');
            if(displayName) out.push({displayName,uri});
        }
    }catch(e){}
    return out;
}

function gvV151AttrsFromLegacyPhoto(ph){
    const out=[];
    try{
        const raw=Array.isArray(ph?.html_attributions)?ph.html_attributions:[];
        for(const html of raw){
            const box=document.createElement('div');
            box.innerHTML=String(html||'');
            const a=box.querySelector('a');
            const displayName=clean((a?.textContent||box.textContent||'').trim());
            const uri=clean(a?.href||'');
            if(displayName) out.push({displayName,uri});
        }
    }catch(e){}
    return out;
}

function gvV151RenderOwned(name,items){
    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g||!body||!title||!count||!items?.length) return false;

    title.textContent=name||'Foto';
    count.textContent=`${items.length} foto Google · GeoVision`;
    g.classList.add('show','gv-v144-fullscreen');
    body.innerHTML=`
      <div class="gv-v150-stage">
        <img id="gvV150Image" class="gv-v150-image" alt="">
        <button id="gvV150Prev" class="gv-v150-nav gv-v150-prev" type="button" aria-label="Foto precedente">‹</button>
        <button id="gvV150Next" class="gv-v150-nav gv-v150-next" type="button" aria-label="Foto successiva">›</button>
        <div id="gvV150Counter" class="gv-v150-counter"></div>
        <div id="gvV150Attribution" class="gv-v150-attribution"></div>
      </div>`;

    let i=0,sx=0,sy=0;
    const img=document.getElementById('gvV150Image');
    const counter=document.getElementById('gvV150Counter');
    const attribution=document.getElementById('gvV150Attribution');
    const stage=body.querySelector('.gv-v150-stage');
    const show=(n)=>{
        i=(n+items.length)%items.length;
        const item=items[i];
        img.src=item.url;
        img.alt=`${name||'Luogo'} · foto ${i+1}`;
        counter.textContent=`${i+1} / ${items.length}`;
        attribution.innerHTML='';
        if(item.attrs?.length){
            const prefix=document.createElement('span'); prefix.textContent='Foto: '; attribution.appendChild(prefix);
            item.attrs.forEach((a,idx)=>{
                if(idx) attribution.appendChild(document.createTextNode(' · '));
                if(a.uri){
                    const link=document.createElement('a'); link.textContent=a.displayName; link.href=a.uri;
                    link.target='_blank'; link.rel='noopener noreferrer'; attribution.appendChild(link);
                }else attribution.appendChild(document.createTextNode(a.displayName));
            });
        }else attribution.textContent='Foto Google Maps';
        try{ const pre=new Image(); pre.src=items[(i+1)%items.length].url; }catch(e){}
    };
    document.getElementById('gvV150Prev').onclick=()=>show(i-1);
    document.getElementById('gvV150Next').onclick=()=>show(i+1);
    stage.addEventListener('touchstart',e=>{ const t=e.changedTouches?.[0]; if(t){sx=t.clientX;sy=t.clientY;} },{passive:true});
    stage.addEventListener('touchend',e=>{
        const t=e.changedTouches?.[0]; if(!t) return;
        const dx=t.clientX-sx,dy=t.clientY-sy;
        if(Math.abs(dx)>42 && Math.abs(dx)>Math.abs(dy)) show(i+(dx<0?1:-1));
    },{passive:true});
    show(0);
    return true;
}

async function gvV151NewPlaceItems(id,place){
    const items=[]; let name=clean(place?.displayName||'')||'Luogo';
    try{
        const lib=await google.maps.importLibrary('places');
        const P=lib.Place;
        const fresh=new P({id});
        await Promise.race([
            fresh.fetchFields({fields:['displayName','photos']}),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('new photos timeout')),12000))
        ]);
        name=clean(fresh.displayName||name)||name;
        for(const ph of (Array.isArray(fresh.photos)?fresh.photos:[])){
            if(items.length>=10) break;
            let url='';
            try{ url=ph?.getURI?.({maxWidth:2048,maxHeight:2048})||''; }catch(e){}
            gvV151UniquePush(items,url,gvV151AttrsFromNewPhoto(ph),'new');
        }
        return {items,name,error:''};
    }catch(e){ return {items,name,error:String(e?.message||e||'new error')}; }
}

async function gvV151LegacyItems(id){
    const items=[];
    return await new Promise(resolve=>{
        try{
            const S=google.maps.places?.PlacesService;
            if(!S) return resolve({items,error:'PlacesService unavailable'});
            const svc=new S(googleMap||document.createElement('div'));
            svc.getDetails({placeId:id,fields:['name','photos']},(r,status)=>{
                const ok=status===google.maps.places.PlacesServiceStatus.OK;
                if(ok){
                    for(const ph of (Array.isArray(r?.photos)?r.photos:[])){
                        if(items.length>=10) break;
                        let url='';
                        try{ url=ph?.getUrl?.({maxWidth:2048,maxHeight:2048})||''; }catch(e){}
                        gvV151UniquePush(items,url,gvV151AttrsFromLegacyPhoto(ph),'legacy');
                    }
                }
                resolve({items,name:clean(r?.name||''),error:ok?'':String(status||'legacy error')});
            });
        }catch(e){ resolve({items,error:String(e?.message||e||'legacy error')}); }
    });
}

function gvV151CollectRendered(root){
    const items=[]; const seen=new Set();
    const addCss=(el)=>{
        try{
            const bg=getComputedStyle(el).backgroundImage||'';
            const re=/url\(["']?([^"')]+)["']?\)/g; let m;
            while((m=re.exec(bg)) && items.length<10) gvV151UniquePush(items,m[1],[],'rendered-css');
        }catch(e){}
    };
    const walk=(node)=>{
        if(!node||seen.has(node)||items.length>=10) return; seen.add(node);
        try{
            node.querySelectorAll?.('img').forEach(img=>{
                if(items.length>=10) return;
                let u=''; try{ u=img.currentSrc||img.src||''; }catch(e){}
                gvV151UniquePush(items,u,[],'rendered-img');
            });
            node.querySelectorAll?.('*').forEach(el=>{
                if(items.length>=10) return;
                addCss(el);
                try{ if(el.shadowRoot) walk(el.shadowRoot); }catch(e){}
            });
        }catch(e){}
    };
    walk(root); return items;
}

async function gvV151OfficialRenderedItems(id){
    const items=[];
    try{
        await google.maps.importLibrary('places');
        await Promise.race([customElements.whenDefined('gmp-place-details'),new Promise((_,rej)=>setTimeout(()=>rej(new Error('details define timeout')),8000))]);
        const wrap=document.createElement('div');
        wrap.style.cssText='position:fixed;left:0;top:0;width:680px;height:520px;opacity:.001;pointer-events:none;z-index:-1;overflow:hidden;';
        document.body.appendChild(wrap);
        const details=document.createElement('gmp-place-details');
        const request=document.createElement('gmp-place-details-place-request');
        const config=document.createElement('gmp-place-content-config');
        const media=document.createElement('gmp-place-media');
        const attr=document.createElement('gmp-place-attribution');
        request.setAttribute('place',id); media.setAttribute('lightbox-preferred',''); media.setAttribute('preferred-size','large');
        config.appendChild(media); config.appendChild(attr); details.appendChild(request); details.appendChild(config); wrap.appendChild(details);
        await Promise.race([
            new Promise((resolve,reject)=>{ details.addEventListener('gmp-load',()=>resolve(),{once:true}); details.addEventListener('gmp-error',()=>reject(new Error('gmp-error')),{once:true}); }),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('gmp-load timeout')),10000))
        ]);
        await new Promise(r=>setTimeout(r,900));
        items.push(...gvV151CollectRendered(wrap));
        try{ wrap.remove(); }catch(e){}
        return {items,error:''};
    }catch(e){ return {items,error:String(e?.message||e||'render error')}; }
}

async function gvV147OpenTerritorySelectedPlace(place){
    if(!place) return;
    const id=String(place.id||''); if(!id) return;
    const g=document.getElementById('photoGallery'),body=document.getElementById('photoGalleryBody'),title=document.getElementById('photoGalleryTitle'),count=document.getElementById('photoGalleryCount');
    if(!g||!body||!title||!count) return;
    g.classList.add('show','gv-v144-fullscreen'); title.textContent='Luogo'; count.textContent='Carico le foto Google…';
    body.innerHTML='<div class="photo-gallery-loading">Preparo la galleria GeoVision…</div>';

    let name=clean(place?.displayName||'')||'Luogo';
    const diagnostics=[];

    const modern=await gvV151NewPlaceItems(id,place);
    if(modern.name) name=modern.name;
    diagnostics.push(`new:${modern.items.length}${modern.error?':'+modern.error:''}`);
    if(modern.items.length && gvV151RenderOwned(name,modern.items)){
        console.log('GeoVision v151 proprietary viewer source=new',id,diagnostics.join(' | ')); return;
    }

    const legacy=await gvV151LegacyItems(id);
    if(legacy.name) name=legacy.name;
    diagnostics.push(`legacy:${legacy.items.length}${legacy.error?':'+legacy.error:''}`);
    if(legacy.items.length && gvV151RenderOwned(name,legacy.items)){
        console.log('GeoVision v151 proprietary viewer source=legacy',id,diagnostics.join(' | ')); return;
    }

    const rendered=await gvV151OfficialRenderedItems(id);
    diagnostics.push(`rendered:${rendered.items.length}${rendered.error?':'+rendered.error:''}`);
    if(rendered.items.length && gvV151RenderOwned(name,rendered.items)){
        console.log('GeoVision v151 proprietary viewer source=rendered',id,diagnostics.join(' | ')); return;
    }

    // Fallback ufficiale stabile v149. Mostriamo una piccola diagnostica soltanto
    // nel sottotitolo, così un solo test sul telefono ci dice dove si è fermato.
    try{
        title.textContent=name||'Luogo';
        count.textContent='Google fallback · '+diagnostics.map(x=>x.split(':').slice(0,2).join(':')).join(' · ');
        body.innerHTML='';
        const selected={name:name||'Luogo',placeId:id,kind:'poi',category:'poi',type:'poi'};
        await renderGoogleUiMediaFallback(selected,body);
        if(!body.childNodes.length) throw new Error('official media empty');
        console.log('GeoVision v151 fallback official media',id,diagnostics.join(' | '));
    }catch(e){
        count.textContent='Foto non disponibili';
        body.innerHTML='<div class="photo-gallery-empty">Non sono riuscito a caricare le foto di questo luogo.</div>';
    }
}

'''

# Rimpiazza la funzione v150 e conserva il resto delle patch.
s=s[:start]+new_code+s[end:]
p.write_text(s,encoding='utf-8')
print('Applied v151 multi-source photo extraction bridge:',p,len(s))
