from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v146: usa direttamente i Place gia trovati dal componente gmp-place-search che
# sul dispositivo ha dimostrato di funzionare. Dopo gmp-load legge search.places,
# carica le photos di ogni Place e le passa al viewer fullscreen v144.
# POI singoli restano sul ramo v145 legato esclusivamente al loro placeId.
# Nessun autoplay, nessun Radar, nessuna modifica alla scheda Google/storytelling.

helper=r'''
async function gvV146CollectUiKitLoadedPlacePhotos(p){
    const out=[];
    if(!googleReady || !p) return out;
    let host=null;
    try{
        await google.maps.importLibrary('places');
        await Promise.race([
            customElements.whenDefined('gmp-place-search'),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('gmp-place-search timeout')),7000))
        ]);

        host=document.createElement('div');
        host.id='gvV146HiddenPlaceSearchHost';
        host.style.cssText='position:fixed;left:-1400px;top:0;width:360px;height:700px;opacity:.001;pointer-events:none;overflow:hidden;z-index:-1';

        const search=document.createElement('gmp-place-search');
        const request=document.createElement('gmp-place-text-search-request');
        const all=document.createElement('gmp-place-all-content');
        search.setAttribute('orientation','vertical');
        search.setAttribute('selectable','');
        request.setAttribute('text-query',[p.name,p.parent,'attrazioni'].filter(Boolean).join(' '));
        request.setAttribute('max-result-count','10');
        search.appendChild(all);
        search.appendChild(request);
        host.appendChild(search);
        document.body.appendChild(host);

        const places=await new Promise(resolve=>{
            let done=false;
            const finish=(items)=>{
                if(done) return;
                done=true;
                resolve(Array.isArray(items)?items:[]);
            };
            search.addEventListener('gmp-load',()=>{
                const items=Array.from(search.places||[]);
                console.log('GeoVision v146 gmp-load places',items.length);
                finish(items);
            },{once:true});
            search.addEventListener('gmp-requesterror',e=>{
                console.log('GeoVision v146 gmp-requesterror',e?.detail?.error||e);
                finish([]);
            },{once:true});
            setTimeout(()=>finish(Array.from(search.places||[])),9000);
        });

        const count=document.getElementById('photoGalleryCount');
        const body=document.getElementById('photoGalleryBody');
        if(count) count.textContent=`${places.length} luoghi trovati · carico le foto…`;
        if(body) body.innerHTML=`<div class="photo-gallery-loading">Trovati ${places.length} luoghi. Carico le foto…</div>`;
        if(!places.length) return out;

        const lib=await google.maps.importLibrary('places');
        const P=lib.Place;
        const groups=await Promise.all(places.slice(0,10).map(async pl=>{
            const urls=[];
            try{
                let target=pl;
                if(typeof target?.fetchFields==='function'){
                    await target.fetchFields({fields:['displayName','photos']});
                }else if(pl?.id){
                    target=new P({id:String(pl.id)});
                    await target.fetchFields({fields:['displayName','photos']});
                }
                for(const ph of (Array.isArray(target?.photos)?target.photos:[])){
                    gvV145AddPhotoUrl(urls,ph,12);
                    if(urls.length>=12) break;
                }
                // Se il Place restituito dal widget non espone le photos dopo fetchFields,
                // riprova creando un Place esplicito con lo stesso id.
                if(!urls.length && pl?.id){
                    const retry=new P({id:String(pl.id)});
                    await retry.fetchFields({fields:['photos']});
                    for(const ph of (Array.isArray(retry.photos)?retry.photos:[])){
                        gvV145AddPhotoUrl(urls,ph,12);
                        if(urls.length>=12) break;
                    }
                }
            }catch(e){
                console.log('GeoVision v146 place photos failed',pl?.id||'',e?.message||e);
            }
            return urls;
        }));

        for(const urls of groups){
            for(const u of urls){
                gvV145AddPhotoUrl(out,u,60);
                if(out.length>=60) break;
            }
            if(out.length>=60) break;
        }
        console.log('GeoVision v146 UI Kit places -> photos',places.length,out.length);
        return out;
    }catch(e){
        console.log('GeoVision v146 UI Kit collector failed',e?.message||e);
        return out;
    }finally{
        try{host?.remove();}catch(e){}
    }
}

async function gvV146OpenPhotoGallery(){
    const p=current;
    if(!p) return toast('Seleziona prima un luogo');
    const locality=(typeof isOfficialCityLocality==='function') && isOfficialCityLocality(p);

    // Un POI/monumento resta rigorosamente sul suo placeId: nessun gruppo cittadino.
    if(!locality) return void gvV145OpenFlattenedGroupGallery();

    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return;

    title.textContent=p.name||'Foto';
    count.textContent='Cerco i luoghi Google…';
    body.innerHTML='<div class="photo-gallery-loading">Cerco i luoghi della localita…</div>';
    g.classList.add('show','gv-v144-fullscreen');

    let urls=[];
    try{ urls=await gvV146CollectUiKitLoadedPlacePhotos(p); }
    catch(e){ console.log('GeoVision v146 collection failed',e?.message||e); }
    if(current!==p || !g.classList.contains('show')) return;

    if(urls.length){
        gvV144RenderPhotoFolder(p,urls);
        console.log('GeoVision v146 fullscreen from UI Kit places active',urls.length);
        return;
    }

    // Se anche il canale che sul dispositivo rende la lista non espone foto,
    // conserva la lista Google visibile come fallback invece di lasciare uno schermo nero.
    count.textContent='Foto Google del territorio';
    body.innerHTML='<div class="photo-gallery-loading">Apro i luoghi Google disponibili…</div>';
    try{ await renderGoogleUiMediaFallback(p,body); }
    catch(e){
        body.innerHTML='<div class="photo-gallery-empty">Foto Google non disponibili per questo luogo.</div>';
        count.textContent='Foto non disponibili';
    }
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvV146OpenPhotoGallery()' not in s:
    if anchor not in s:
        raise SystemExit('v146 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

# Entrambi gli ingressi Foto passano ora da v146.
old="gvV144PhotoButton.onclick=()=>void gvV145OpenFlattenedGroupGallery();"
new="gvV144PhotoButton.onclick=()=>void gvV146OpenPhotoGallery();"
if old not in s:
    raise SystemExit('v146 patch aborted: v145 round photo binding not found')
s=s.replace(old,new,1)

old2="gvV145ImagesMenuButton.onclick=()=>{ document.getElementById('videoPicker')?.classList.remove('show'); void gvV145OpenFlattenedGroupGallery(); };"
new2="gvV145ImagesMenuButton.onclick=()=>{ document.getElementById('videoPicker')?.classList.remove('show'); void gvV146OpenPhotoGallery(); };"
if old2 not in s:
    raise SystemExit('v146 patch aborted: v145 images menu binding not found')
s=s.replace(old2,new2,1)

p.write_text(s,encoding='utf-8')
print('Applied v146 UI Kit loaded places -> fullscreen photos:',p,len(s))
