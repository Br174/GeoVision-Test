from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v141: corregge il caso reale Android in cui il viewer v140 parte prima
# che Google abbia reso/reso disponibili le foto. Storytelling invariato.
helper=r'''
function gvCollectRenderedPlacePhotosV141(){
    const urls=[];
    const seenNodes=new Set();
    const add=(u)=>{
        u=clean(u||'');
        if(!u || u.startsWith('data:') || urls.includes(u)) return;
        if(!/^https?:/i.test(u)) return;
        urls.push(u);
    };
    const walk=(root)=>{
        if(!root || seenNodes.has(root)) return;
        seenNodes.add(root);
        try{
            root.querySelectorAll?.('img').forEach(img=>{
                try{
                    const r=img.getBoundingClientRect();
                    const large=(r.width>=110 && r.height>=80) || (img.naturalWidth>=240 && img.naturalHeight>=160);
                    if(large) add(img.currentSrc||img.src||'');
                }catch(e){}
            });
            root.querySelectorAll?.('*').forEach(el=>{
                try{ if(el.shadowRoot) walk(el.shadowRoot); }catch(e){}
            });
        }catch(e){}
    };
    walk(document.getElementById('googleCityPhotos'));
    walk(document.getElementById('googleCardHost'));
    return urls.slice(0,30);
}

async function gvAutoOpenPhotoViewerV141(p){
    const token=(window.gvAutoViewerV141Token=(window.gvAutoViewerV141Token||0)+1);
    let apiTried=false;
    let localityTried=false;
    const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));

    for(let attempt=0; attempt<28; attempt++){
        if(token!==window.gvAutoViewerV141Token || current!==p) return;

        let urls=gvCollectRenderedPlacePhotosV141();
        if(urls.length){
            gvRenderAutoPhotoViewer(p,urls,0);
            console.log('GeoVision v141: opened rendered Google photo',urls.length,'attempt',attempt);
            return;
        }

        if(!apiTried && googleReady && p?.placeId){
            apiTried=true;
            try{
                urls=await googleGalleryPhotos(p);
                if(token!==window.gvAutoViewerV141Token || current!==p) return;
                if(urls?.length){
                    gvRenderAutoPhotoViewer(p,urls,0);
                    console.log('GeoVision v141: opened Place ID photo',urls.length);
                    return;
                }
            }catch(e){ console.log('GeoVision v141: placeId photo lookup failed',e?.message||e); }
        }

        if(!localityTried && googleReady && isOfficialCityLocality(p)){
            localityTried=true;
            try{
                urls=await googleLocalityPhotos(p);
                if(token!==window.gvAutoViewerV141Token || current!==p) return;
                if(urls?.length){
                    gvRenderAutoPhotoViewer(p,urls,0);
                    console.log('GeoVision v141: opened locality photo',urls.length);
                    return;
                }
            }catch(e){ console.log('GeoVision v141: locality photo lookup failed',e?.message||e); }
        }

        await sleep(300);
    }
    console.log('GeoVision v141: no usable photo after wait/retry');
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvAutoOpenPhotoViewerV141(p)' not in s:
    if anchor not in s:
        raise SystemExit('v141 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old='void enrichNarration(p); void gvAutoOpenPhotoViewer(p); await cardPromise;'
new='void enrichNarration(p); await cardPromise; void gvAutoOpenPhotoViewerV141(p);'
if old not in s:
    raise SystemExit('v141 patch aborted: v140 openPlace hook not found')
s=s.replace(old,new,1)

# Il viewer v140 resta lo stesso, ma deve stare sicuramente sopra qualsiasi UI Google.
s=s.replace("#gvAutoPhotoViewer{position:fixed;inset:0;z-index:4500;", "#gvAutoPhotoViewer{position:fixed;inset:0;z-index:2147483647;", 1)

p.write_text(s,encoding='utf-8')
print('Applied v141 photo wait/retry patch:',p,len(s))
