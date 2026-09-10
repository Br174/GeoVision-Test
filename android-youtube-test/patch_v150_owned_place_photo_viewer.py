from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v150: prova isolata. Per un luogo scelto dalla lista territoriale usa il placeId
# ormai verificato dalla v149, crea un NUOVO Place, richiede photos e mostra gli URI
# in un viewer GeoVision proprietario. Nessun autoplay, musica, Radar o modifica
# alla scheda Google principale. Se il recupero raw fallisce resta il fallback
# ufficiale Google della v149.

start=s.find('async function gvV147OpenTerritorySelectedPlace(place){')
end=s.find('window.gvV148LastTerritoryPlace=', start)
if start < 0 or end < 0:
    raise SystemExit('v150 patch aborted: v149 selected-place function anchors not found')

new_func=r'''async function gvV147OpenTerritorySelectedPlace(place){
    if(!place) return;
    const id=String(place.id||'');
    if(!id) return;

    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body || !title || !count) return;

    g.classList.add('show','gv-v144-fullscreen');
    title.textContent='Luogo';
    count.textContent='Carico le foto Google…';
    body.innerHTML='<div class="photo-gallery-loading">Preparo la presentazione fotografica…</div>';

    let fresh=null;
    let name='Luogo';
    const items=[];

    try{
        const lib=await google.maps.importLibrary('places');
        const P=lib.Place;
        fresh=new P({id});
        await Promise.race([
            fresh.fetchFields({fields:['displayName','photos']}),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('photos timeout')),8000))
        ]);
        name=clean(fresh.displayName||place.displayName||name);

        for(const ph of (Array.isArray(fresh.photos)?fresh.photos:[])){
            if(items.length>=10) break;
            let url='';
            try{ url=clean(ph?.getURI?.({maxWidth:2048,maxHeight:2048})||''); }catch(e){}
            if(!url || !/^https?:/i.test(url) || items.some(x=>x.url===url)) continue;

            const attrs=[];
            for(const a of (Array.isArray(ph?.authorAttributions)?ph.authorAttributions:[])){
                const displayName=clean(a?.displayName||'');
                const uri=clean(a?.uri||'');
                if(displayName) attrs.push({displayName,uri});
            }
            items.push({url,attrs});
        }
    }catch(e){
        console.log('GeoVision v150 fresh Place photos failed',id,e?.message||e);
    }

    if(items.length){
        title.textContent=name||'Foto';
        count.textContent=`${items.length} foto Google · GeoVision`;
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
            if(item.attrs.length){
                const prefix=document.createElement('span');
                prefix.textContent='Foto: ';
                attribution.appendChild(prefix);
                item.attrs.forEach((a,idx)=>{
                    if(idx){ attribution.appendChild(document.createTextNode(' · ')); }
                    if(a.uri){
                        const link=document.createElement('a');
                        link.textContent=a.displayName;
                        link.href=a.uri;
                        link.target='_blank';
                        link.rel='noopener noreferrer';
                        attribution.appendChild(link);
                    }else{
                        attribution.appendChild(document.createTextNode(a.displayName));
                    }
                });
            }else{
                attribution.textContent='Foto Google Maps';
            }
            try{ const pre=new Image(); pre.src=items[(i+1)%items.length].url; }catch(e){}
        };

        document.getElementById('gvV150Prev').onclick=()=>show(i-1);
        document.getElementById('gvV150Next').onclick=()=>show(i+1);
        stage.addEventListener('touchstart',e=>{
            const t=e.changedTouches?.[0];
            if(t){sx=t.clientX;sy=t.clientY;}
        },{passive:true});
        stage.addEventListener('touchend',e=>{
            const t=e.changedTouches?.[0];
            if(!t) return;
            const dx=t.clientX-sx,dy=t.clientY-sy;
            if(Math.abs(dx)>42 && Math.abs(dx)>Math.abs(dy)) show(i+(dx<0?1:-1));
        },{passive:true});

        show(0);
        console.log('GeoVision v150 proprietary selected-place viewer active',id,items.length);
        return;
    }

    // Fallback stabile v149: se l'API Photo non rende URI, manteniamo il media
    // ufficiale Google che sul dispositivo e gia stato verificato funzionante.
    try{
        title.textContent=name||'Luogo';
        count.textContent='Tocca una foto per ingrandirla';
        body.innerHTML='';
        const selected={name:name||'Luogo',placeId:id,kind:'poi',category:'poi',type:'poi'};
        await renderGoogleUiMediaFallback(selected,body);
        if(!body.childNodes.length) throw new Error('official media empty');
        console.log('GeoVision v150 fallback official media active',id);
    }catch(e){
        count.textContent='Foto non disponibili';
        body.innerHTML='<div class="photo-gallery-empty">Non sono riuscito a caricare le foto di questo luogo.</div>';
    }
}

'''
s=s[:start]+new_func+s[end:]

css=r'''
<style id="gvV150OwnedPhotoStyle">
.gv-v150-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#090909;touch-action:pan-y;}
.gv-v150-image{display:block;width:100%;height:100%;object-fit:contain;background:#090909;user-select:none;-webkit-user-drag:none;}
.gv-v150-nav{position:absolute;top:50%;transform:translateY(-50%);width:50px;height:50px;border:0;border-radius:50%;background:rgba(0,0,0,.58);color:#fff;font-size:36px;line-height:1;display:grid;place-items:center;z-index:3;}
.gv-v150-prev{left:12px}.gv-v150-next{right:12px}
.gv-v150-counter{position:absolute;right:14px;bottom:16px;padding:6px 10px;border-radius:999px;background:rgba(0,0,0,.64);color:#fff;font-size:12px;font-weight:700;z-index:3;}
.gv-v150-attribution{position:absolute;left:14px;bottom:16px;max-width:70%;padding:7px 10px;border-radius:12px;background:rgba(0,0,0,.64);color:#fff;font-size:11px;line-height:1.25;z-index:3;}
.gv-v150-attribution a{color:#fff;text-decoration:underline;text-underline-offset:2px;}
</style>
'''
if 'id="gvV150OwnedPhotoStyle"' not in s:
    if '</head>' not in s:
        raise SystemExit('v150 patch aborted: head close not found')
    s=s.replace('</head>',css+'\n</head>',1)

p.write_text(s,encoding='utf-8')
print('Applied v150 proprietary Place Photos viewer:',p,len(s))
