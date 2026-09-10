from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v140: sostituisce il click sintetico sulla lightbox Google (non affidabile)
# con un viewer fullscreen GeoVision alimentato dalle stesse foto del luogo.
# Lo storytelling resta indipendente e continua a parlare in parallelo.
helper=r'''
function gvCloseAutoPhotoViewer(){
    const v=document.getElementById('gvAutoPhotoViewer');
    if(v) v.remove();
}
function gvRenderAutoPhotoViewer(p, urls, index){
    gvCloseAutoPhotoViewer();
    if(!Array.isArray(urls) || !urls.length) return;
    let i=Math.max(0,Math.min(index||0,urls.length-1));
    const v=document.createElement('div');
    v.id='gvAutoPhotoViewer';
    v.innerHTML=`
      <style>
      #gvAutoPhotoViewer{position:fixed;inset:0;z-index:4500;background:#111;display:flex;flex-direction:column;color:#fff;touch-action:pan-y}
      #gvAutoPhotoViewer .gvp-head{height:74px;display:flex;align-items:center;justify-content:space-between;padding:12px 18px;background:rgba(10,12,16,.96);font:600 17px/1.2 system-ui,sans-serif}
      #gvAutoPhotoViewer .gvp-title{min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:14px}
      #gvAutoPhotoViewer .gvp-close{width:46px;height:46px;border:0;border-radius:50%;background:#0c0d10;color:#fff;font-size:30px;line-height:1;flex:0 0 auto}
      #gvAutoPhotoViewer .gvp-stage{position:relative;flex:1;min-height:0;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#111}
      #gvAutoPhotoViewer .gvp-stage img{width:100%;height:100%;object-fit:contain;display:block;user-select:none;-webkit-user-drag:none}
      #gvAutoPhotoViewer .gvp-footer{height:92px;display:flex;align-items:center;justify-content:center;gap:28px;background:rgba(10,12,16,.96)}
      #gvAutoPhotoViewer .gvp-nav{width:52px;height:52px;border:0;border-radius:50%;background:#050506;color:#fff;font-size:34px;line-height:1}
      #gvAutoPhotoViewer .gvp-count{position:absolute;right:16px;bottom:12px;padding:6px 10px;border-radius:999px;background:rgba(0,0,0,.55);font:600 13px system-ui,sans-serif}
      #gvAutoPhotoViewer .gvp-brand{position:absolute;left:50%;bottom:18px;transform:translateX(-50%);font:700 15px system-ui,sans-serif;color:#fff;pointer-events:none}
      </style>
      <div class="gvp-head"><div class="gvp-title"></div><button class="gvp-close" type="button" aria-label="Chiudi">×</button></div>
      <div class="gvp-stage"><img alt=""><div class="gvp-count"></div></div>
      <div class="gvp-footer"><button class="gvp-nav gvp-prev" type="button" aria-label="Foto precedente">‹</button><button class="gvp-nav gvp-next" type="button" aria-label="Foto successiva">›</button><div class="gvp-brand">Google Maps</div></div>`;
    document.body.appendChild(v);
    const img=v.querySelector('.gvp-stage img');
    const title=v.querySelector('.gvp-title');
    const count=v.querySelector('.gvp-count');
    title.textContent=p?.name||'Foto del luogo';
    const show=(n)=>{
        i=(n+urls.length)%urls.length;
        img.src=urls[i];
        img.alt=`${p?.name||'Luogo'} · foto ${i+1}`;
        count.textContent=`${i+1} / ${urls.length}`;
    };
    v.querySelector('.gvp-close').onclick=()=>gvCloseAutoPhotoViewer();
    v.querySelector('.gvp-prev').onclick=()=>show(i-1);
    v.querySelector('.gvp-next').onclick=()=>show(i+1);
    let sx=0, sy=0;
    v.addEventListener('touchstart',e=>{const t=e.changedTouches?.[0]; if(t){sx=t.clientX; sy=t.clientY;}},{passive:true});
    v.addEventListener('touchend',e=>{const t=e.changedTouches?.[0]; if(!t)return; const dx=t.clientX-sx, dy=t.clientY-sy; if(Math.abs(dx)>55 && Math.abs(dx)>Math.abs(dy)){ if(dx<0) show(i+1); else show(i-1); }},{passive:true});
    show(i);
}
async function gvAutoOpenPhotoViewer(p){
    const token=(window.gvAutoViewerToken=(window.gvAutoViewerToken||0)+1);
    try{
        const urls=await googleGalleryPhotos(p);
        if(token!==window.gvAutoViewerToken || current!==p || !urls?.length) return;
        gvRenderAutoPhotoViewer(p,urls,0);
        console.log('GeoVision v140: fullscreen first photo opened');
    }catch(e){
        console.log('GeoVision v140: fullscreen photo unavailable',e?.message||e);
    }
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvAutoOpenPhotoViewer(p)' not in s:
    if anchor not in s:
        raise SystemExit('v140 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old='void enrichNarration(p); gvAutoOpenFirstGooglePhoto(p); await cardPromise;'
new='void enrichNarration(p); void gvAutoOpenPhotoViewer(p); await cardPromise;'
if old not in s:
    raise SystemExit('v140 patch aborted: v139 openPlace hook not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Applied v140 fullscreen photo viewer patch:',p,len(s))
