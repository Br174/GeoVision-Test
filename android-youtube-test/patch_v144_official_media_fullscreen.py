from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v144: test isolato della CARTELLA FOTO gia esistente.
# - disattiva l'auto-tap v143 durante questo test
# - riattiva davvero il pulsante Google Foto vicino alla X
# - riusa googleGalleryPhotos() gia presente (fino a 30 foto Google)
# - mostra una foto per volta a tutto schermo con swipe/frecce
# - NON aggiunge autoplay e NON modifica la scheda Google / storytelling

old_hook='async function renderOfficialGoogleCard(p) { void gvV143TapOfficialGooglePhoto(p);'
new_hook='async function renderOfficialGoogleCard(p) {'
if old_hook not in s:
    raise SystemExit('v144 patch aborted: v143 render hook not found')
s=s.replace(old_hook,new_hook,1)

helper=r'''
function gvV144UniquePhotoUrls(urls){
    const out=[];
    for(const raw of (urls||[])){
        const u=clean(raw||'');
        if(!u || u.startsWith('data:') || out.includes(u)) continue;
        out.push(u);
    }
    return out;
}

function gvV144RenderPhotoFolder(p,urls){
    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return false;

    urls=gvV144UniquePhotoUrls(urls);
    if(!urls.length) return false;

    title.textContent=p?.name||'Foto';
    count.textContent=`${urls.length} foto Google`;
    g.classList.add('show','gv-v144-fullscreen');

    body.innerHTML=`
      <div class="gv-v144-stage">
        <img id="gvV144FolderImage" class="gv-v144-image" alt="">
        <button id="gvV144FolderPrev" class="gv-v144-nav gv-v144-prev" type="button" aria-label="Foto precedente">‹</button>
        <button id="gvV144FolderNext" class="gv-v144-nav gv-v144-next" type="button" aria-label="Foto successiva">›</button>
        <div id="gvV144FolderCounter" class="gv-v144-counter"></div>
      </div>`;

    let i=0,sx=0,sy=0;
    const img=document.getElementById('gvV144FolderImage');
    const counter=document.getElementById('gvV144FolderCounter');
    const stage=body.querySelector('.gv-v144-stage');
    const show=(n)=>{
        if(!img || !counter || !urls.length) return;
        i=(n+urls.length)%urls.length;
        img.src=urls[i];
        img.alt=`${p?.name||'Luogo'} · foto ${i+1}`;
        counter.textContent=`${i+1} / ${urls.length}`;
        // Precarica la foto successiva per rendere lo swipe piu fluido.
        try{ const pre=new Image(); pre.src=urls[(i+1)%urls.length]; }catch(e){}
    };

    document.getElementById('gvV144FolderPrev').onclick=()=>show(i-1);
    document.getElementById('gvV144FolderNext').onclick=()=>show(i+1);
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
    console.log('GeoVision v144 photo folder fullscreen active',urls.length);
    return true;
}

async function gvV144OpenExistingPhotoFolder(){
    const p=current;
    if(!p) return toast('Seleziona prima un luogo');

    const g=document.getElementById('photoGallery');
    const body=document.getElementById('photoGalleryBody');
    const title=document.getElementById('photoGalleryTitle');
    const count=document.getElementById('photoGalleryCount');
    if(!g || !body) return;

    title.textContent=p.name||'Foto';
    count.textContent='Carico le foto Google…';
    body.innerHTML='<div class="photo-gallery-loading">Carico le foto del luogo…</div>';
    g.classList.add('show','gv-v144-fullscreen');

    let urls=[];
    try{
        // Riusa ESATTAMENTE il canale della cartella Foto gia esistente.
        urls=await googleGalleryPhotos(p);
    }catch(e){
        console.log('GeoVision v144 googleGalleryPhotos failed',e?.message||e);
    }

    if(current!==p || !g.classList.contains('show')) return;

    // Se il canale API non rende URL, prova le immagini che la scheda Google
    // ha gia materializzato. Questo fallback non tocca la scheda.
    if((!urls || !urls.length) && typeof gvCollectRenderedPlacePhotosV141==='function'){
        try{ urls=gvCollectRenderedPlacePhotosV141(); }catch(e){}
    }

    urls=gvV144UniquePhotoUrls(urls);
    if(urls.length){
        gvV144RenderPhotoFolder(p,urls);
        return;
    }

    // Ultimo fallback: mantieni il comportamento UI Kit gia presente nella cartella.
    count.textContent='Foto Google';
    try{
        await renderGoogleUiMediaFallback(p,body);
    }catch(e){
        body.innerHTML='<div class="photo-gallery-empty">Foto Google non disponibili per questo luogo.</div>';
        count.textContent='Foto non disponibili';
    }
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvV144OpenExistingPhotoFolder()' not in s:
    if anchor not in s:
        raise SystemExit('v144 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

# CSS: il pulsante Foto era stato reso solo grafico con pointer-events:none.
# Riattiviamolo e trasformiamo la cartella esistente in un viewer nero fullscreen.
css=r'''
<style id="gvV144PhotoFolderStyle">
#sheetPhotosVisual{pointer-events:auto!important;cursor:pointer!important;}
.photo-gallery.gv-v144-fullscreen{z-index:2147483647!important;background:#090909!important;color:#fff!important;}
.photo-gallery.gv-v144-fullscreen .photo-gallery-head{
  height:62px!important;flex:0 0 62px!important;background:#0d0d0f!important;
  border-bottom:1px solid #242428!important;color:#fff!important;padding:8px 12px!important;
}
.photo-gallery.gv-v144-fullscreen .photo-gallery-head b{color:#fff!important;}
.photo-gallery.gv-v144-fullscreen .photo-gallery-head small{display:block;color:#b9bbc2!important;margin-top:2px;}
.photo-gallery.gv-v144-fullscreen .photo-gallery-close{
  background:#17171a!important;color:#fff!important;border:1px solid #303036!important;
}
.photo-gallery.gv-v144-fullscreen .photo-gallery-body{
  flex:1!important;min-height:0!important;display:block!important;overflow:hidden!important;
  background:#090909!important;padding:0!important;
}
.gv-v144-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#090909;touch-action:pan-y;}
.gv-v144-image{display:block;width:100%;height:100%;object-fit:contain;background:#090909;user-select:none;-webkit-user-drag:none;}
.gv-v144-nav{position:absolute;top:50%;transform:translateY(-50%);width:48px;height:48px;border:0;border-radius:50%;background:rgba(0,0,0,.58);color:#fff;font-size:34px;line-height:1;display:grid;place-items:center;}
.gv-v144-prev{left:10px}.gv-v144-next{right:10px}
.gv-v144-counter{position:absolute;right:12px;bottom:14px;padding:6px 10px;border-radius:999px;background:rgba(0,0,0,.62);color:#fff;font-size:12px;font-weight:700;}
</style>
'''
if 'id="gvV144PhotoFolderStyle"' not in s:
    if '</head>' not in s:
        raise SystemExit('v144 patch aborted: head close not found')
    s=s.replace('</head>',css+'\n</head>',1)

# Collega davvero il logo Foto vicino alla X alla cartella fullscreen.
event_anchor="$('#photoGalleryClose').onclick = closePhotoGallery;"
if event_anchor not in s:
    raise SystemExit('v144 patch aborted: photo gallery close anchor not found')
binding="""$('#photoGalleryClose').onclick = () => { document.getElementById('photoGallery')?.classList.remove('gv-v144-fullscreen'); closePhotoGallery(); };\nconst gvV144PhotoButton=document.getElementById('sheetPhotosVisual');\nif(gvV144PhotoButton){\n    gvV144PhotoButton.tabIndex=0;\n    gvV144PhotoButton.onclick=()=>void gvV144OpenExistingPhotoFolder();\n}\n"""
s=s.replace(event_anchor,binding,1)

p.write_text(s,encoding='utf-8')
print('Applied v144 existing Google photo folder fullscreen patch:',p,len(s))
