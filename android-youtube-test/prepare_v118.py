from pathlib import Path

src=Path("GeoVision_Nova_v114_AI_RAPIDA_APPROFONDIMENTO.html")
dst=Path("android-youtube-test/app/src/main/assets/geovision.html")
dst.parent.mkdir(parents=True,exist_ok=True)
s=src.read_text(encoding="utf-8")

# Mantieni la base HTML funzionante e applica solo patch conservative.
if '<meta name="referrer"' not in s:
    s=s.replace('<meta name="viewport"', '<meta name="referrer" content="strict-origin-when-cross-origin">\n<meta name="viewport"', 1)

# YouTube: manteniamo il blocco funzionante della v118 come base stabile.
start=s.index("function openYouTubeInternalPlayer(videoId,title='YouTube'){")
end=s.index("\nfunction launchPlatform(p)", start)

youtube_block=r'''function closeYouTubeInternalPlayer(){
    const modal=document.getElementById('youtubeInternalModal');
    const frame=document.getElementById('ytModalFrame');
    if(frame) frame.src='';
    modal?.remove();
}
function openYouTubeInternalPlayer(videoId,title='YouTube'){
    try{ stopSpeech(); }catch(e){}
    closeYouTubeInternalPlayer();
    const modal=document.createElement('div');
    modal.id='youtubeInternalModal';
    modal.style.cssText='position:fixed;inset:0;z-index:25000;background:#000;display:flex;flex-direction:column';
    modal.innerHTML=`
      <div style="height:54px;flex:0 0 54px;display:flex;align-items:center;gap:10px;padding:7px 10px;background:#fff;border-bottom:1px solid #e7eaf0">
        <b id="ytModalTitle" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#475569"></b>
        <button id="ytModalClose" type="button" aria-label="Chiudi" style="width:38px;height:38px;border:1px solid #e5e7eb;border-radius:50%;background:#fff;color:#64748b;font-size:24px">×</button>
      </div>
      <div style="flex:1;min-height:0;background:#000;display:flex;align-items:center;justify-content:center">
        <iframe id="ytModalFrame" style="width:100%;height:100%;border:0;background:#000" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay;encrypted-media;picture-in-picture;fullscreen" allowfullscreen></iframe>
      </div>`;
    document.body.appendChild(modal);
    document.getElementById('ytModalTitle').textContent=title;
    document.getElementById('ytModalClose').onclick=closeYouTubeInternalPlayer;
    const origin=(location.protocol==='https:'||location.protocol==='http:')?location.origin:'';
    document.getElementById('ytModalFrame').src=`https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0&fs=1${origin?`&origin=${encodeURIComponent(origin)}`:''}`;
}
function closeYouTubeResults(){
    document.getElementById('youtubeResultsModal')?.remove();
}
function renderYouTubeResults(items,q){
    try{ stopSpeech(); }catch(e){}
    closeYouTubeResults();
    const modal=document.createElement('div');
    modal.id='youtubeResultsModal';
    modal.style.cssText='position:fixed;inset:0;z-index:24500;background:#fff;display:flex;flex-direction:column';
    const rows=items.map((item,i)=>{
        const sn=item?.snippet||{};
        const thumb=sn?.thumbnails?.high?.url||sn?.thumbnails?.medium?.url||sn?.thumbnails?.default?.url||'';
        return `<button type="button" data-yt-index="${i}" style="border:0;border-bottom:1px solid #eef1f4;background:#fff;padding:10px 12px;display:grid;grid-template-columns:142px 1fr;gap:11px;text-align:left;align-items:start">
          <div style="aspect-ratio:16/9;border-radius:12px;overflow:hidden;background:#eef2f7">${thumb?`<img src="${esc(thumb)}" alt="" style="display:block;width:100%;height:100%;object-fit:cover">`:''}</div>
          <div style="min-width:0"><b style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:13px;line-height:1.35;color:#344054">${esc(sn.title||'Video YouTube')}</b><small style="display:block;margin-top:6px;color:#8a94a3;font-size:11px">${esc(sn.channelTitle||'YouTube')}</small></div>
        </button>`;
    }).join('');
    modal.innerHTML=`<div style="height:58px;flex:0 0 58px;display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #e7eaf0;background:#fff"><div style="flex:1;min-width:0"><b style="display:block;color:#344054;font-size:14px">Video trovati</b><small style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#8a94a3">${esc(q)}</small></div><button id="youtubeResultsClose" type="button" aria-label="Chiudi" style="width:38px;height:38px;border:1px solid #e5e7eb;border-radius:50%;background:#fff;color:#64748b;font-size:24px">×</button></div><div style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch">${rows}</div>`;
    document.body.appendChild(modal);
    document.getElementById('youtubeResultsClose').onclick=closeYouTubeResults;
    modal.querySelectorAll('[data-yt-index]').forEach(btn=>btn.onclick=()=>{
        const item=items[Number(btn.dataset.ytIndex)], id=item?.id?.videoId;
        if(id) openYouTubeInternalPlayer(id,item?.snippet?.title||'YouTube');
    });
}
async function launchYouTubeInternal(q){
    try{ stopSpeech(); }catch(e){}
    if(!youtubeKey)return false;
    try{
        const u=`https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=12&safeSearch=moderate&q=${encodeURIComponent(q)}&key=${encodeURIComponent(youtubeKey)}`;
        const r=await fetch(u);
        if(!r.ok)return false;
        const d=await r.json();
        const items=(d?.items||[]).filter(x=>x?.id?.videoId);
        if(!items.length)return false;
        renderYouTubeResults(items,q);
        return true;
    }catch{return false}
}
'''
s=s[:start]+youtube_block+s[end:]

# TTS nativo Android con fallback browser.
needle="\nasync function aiNarration(p, mode,"
idx=s.index(needle)
tts_bridge=r'''
const gvBrowserSpeak=speak;
const gvBrowserStopSpeech=stopSpeech;
window.gvNativeTtsState=function(state){
    const active=state==='start'; speaking=active;
    $('#voice')?.classList.toggle('active',active); $('#nativeVoice')?.classList.toggle('active',active);
};
speak=function(text,append=false){
    const t=speechText(text); if(!t)return;
    try{
        if(window.GeoVisionTTS&&typeof window.GeoVisionTTS.speak==='function'){
            speaking=true; $('#voice')?.classList.add('active'); $('#nativeVoice')?.classList.add('active');
            window.GeoVisionTTS.speak(t,!!append); return;
        }
    }catch{}
    return gvBrowserSpeak(t,append);
};
stopSpeech=function(){
    try{if(window.GeoVisionTTS&&typeof window.GeoVisionTTS.stop==='function')window.GeoVisionTTS.stop();}catch{}
    return gvBrowserStopSpeech();
};
'''
s=s[:idx]+"\n"+tts_bridge+s[idx:]

# Diagnostica visibile: se un errore JS globale si verifica, non lasciare schermo vuoto.
diagnostic=r'''
<script>
window.addEventListener('error',function(ev){
  try{
    var box=document.getElementById('gv-startup-error');
    if(!box){
      box=document.createElement('div'); box.id='gv-startup-error';
      box.style.cssText='position:fixed;z-index:999999;left:12px;right:12px;bottom:12px;background:#fff;border:1px solid #ef4444;border-radius:14px;padding:12px;color:#7f1d1d;font:12px/1.45 system-ui;box-shadow:0 8px 30px rgba(0,0,0,.15)';
      document.body.appendChild(box);
    }
    box.textContent='Errore avvio GeoVision: '+(ev.message||'errore JavaScript')+' · riga '+(ev.lineno||'?');
  }catch(e){}
});
window.addEventListener('unhandledrejection',function(ev){
  try{ console.error('GeoVision unhandled rejection',ev.reason); }catch(e){}
});
</script>
'''
s=s.replace('</body>',diagnostic+'\n</body>',1)

dst.write_text(s,encoding='utf-8')
print('Prepared v128 Android',dst,len(s))
