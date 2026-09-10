from pathlib import Path
import re

src=Path("GeoVision_Nova_v114_AI_RAPIDA_APPROFONDIMENTO.html")
dst=Path("android-youtube-test/app/src/main/assets/geovision.html")
dst.parent.mkdir(parents=True,exist_ok=True)
s=src.read_text(encoding="utf-8")

if '<meta name="referrer"' not in s:
    s=s.replace('<meta name="viewport"', '<meta name="referrer" content="strict-origin-when-cross-origin">\n<meta name="viewport"', 1)

start=s.index("function openYouTubeInternalPlayer(videoId,title='YouTube'){")
end=s.index("\nfunction launchPlatform(p)", start)
youtube_block=r"""function closeYouTubeInternalPlayer(){
    const modal=document.getElementById('youtubeInternalModal');
    const frame=document.getElementById('ytModalFrame');
    if(frame) frame.src='';
    modal?.remove();
}
function openYouTubeInternalPlayer(videoId,title='YouTube'){
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
    document.getElementById('ytModalFrame').src=`https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0${origin?`&origin=${encodeURIComponent(origin)}`:''}`;
}
function closeYouTubeResults(){ document.getElementById('youtubeResultsModal')?.remove(); }
function renderYouTubeResults(items,q){
    closeYouTubeResults();
    const modal=document.createElement('div');
    modal.id='youtubeResultsModal';
    modal.style.cssText='position:fixed;inset:0;z-index:24500;background:#fff;display:flex;flex-direction:column';
    const rows=items.map((item,i)=>{
        const sn=item?.snippet||{};
        const thumb=sn?.thumbnails?.medium?.url||sn?.thumbnails?.high?.url||sn?.thumbnails?.default?.url||'';
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
    if(!youtubeKey)return false;
    try{
        const u=`https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=12&safeSearch=moderate&q=${encodeURIComponent(q)}&key=${encodeURIComponent(youtubeKey)}`;
        const r=await fetch(u); if(!r.ok)return false;
        const d=await r.json(),items=(d?.items||[]).filter(x=>x?.id?.videoId);
        if(!items.length)return false; renderYouTubeResults(items,q); return true;
    }catch{return false}
}
"""
s=s[:start]+youtube_block+s[end:]

# Social: TikTok, Instagram, Facebook -> specific search page, Android app/browser fallback.
launch=s.index("function launchPlatform(p)")
helper=r"""
function openSocialSearch(platform,q){
    const encoded=encodeURIComponent(q);
    const web=platform==='instagram'
      ? `https://www.instagram.com/explore/search/keyword/?q=${encoded}`
      : platform==='facebook'
      ? `https://www.facebook.com/watch/search/?q=${encoded}`
      : platform==='tiktok'
      ? `https://www.tiktok.com/search?q=${encoded}`
      : '';
    if(!web)return false;
    try{
      if(window.GeoVisionExternal&&typeof window.GeoVisionExternal.openUrl==='function'){
        window.GeoVisionExternal.openUrl(web); return true;
      }
    }catch{}
    openUrl(web); return true;
}
"""
s=s[:launch]+helper+"\n"+s[launch:]
s=s.replace("""if (p === 'instagram') {
    copyInstagramQuery(social);
    return openIntent(`instagram://search?query=${enc}`);
}""","""if (p === 'instagram') {
    copyInstagramQuery(social);
    return openSocialSearch('instagram',social);
}""",1)
s=s.replace("""if (p === 'tiktok') {
    const web = `https://www.tiktok.com/search?q=${enc}`, intent = `intent://search/?keyword=${enc}#Intent;scheme=snssdk1233;package=com.zhiliaoapp.musically;S.browser_fallback_url=${encodeURIComponent(web)};end`;
    return openIntent(intent);
}""","""if (p === 'tiktok') return openSocialSearch('tiktok',social);
if (p === 'facebook') return openSocialSearch('facebook',social);""",1)

# Native TTS bridge.
needle="\nasync function aiNarration(p, mode,"
idx=s.index(needle)
tts_bridge=r"""
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
"""
s=s[:idx]+"\n"+tts_bridge+s[idx:]

# AI-first: read AI card text, not the generic intro.
s=s.replace("""    /* Solo ora parte la frase iniziale: l'AI principale sta già lavorando. */
    speak(told);

    void (async () => {""","""    /* Android v120: aspetta il contenuto AI della scheda prima di parlare. */
    void (async () => {""",1)
s=s.replace("""        if (quick) {
            paintAiState(false);
            firstContinuation = quick;
            appendAndSpeak(quick);
            /* appena parte la parte AI principale, preparo già il primo approfondimento */""","""        if (quick) {
            paintAiState(false);
            firstContinuation = quick;
            told += ' ' + quick;
            transcript.insertAdjacentHTML('beforeend', `<div class="narration narration-stage">${esc(quick)}</div>`);
            speak(quick, false);
            /* appena parte la parte AI principale, preparo già il primo approfondimento */""",1)
s=s.replace("""        const bridge = smartLocalContinuation(p, w.extract || '');
        if (bridge) {
            firstContinuation = bridge;
            appendAndSpeak(bridge);
        }""","""        const bridge = smartLocalContinuation(p, w.extract || '');
        if (bridge) {
            firstContinuation = bridge;
            told += ' ' + bridge;
            transcript.insertAdjacentHTML('beforeend', `<div class="narration narration-stage">${esc(bridge)}</div>`);
            speak(bridge, false);
        }""",1)

# Sanity checks before build.
assert 'maxResults=12' in s
assert 'youtubeResultsModal' in s
assert "openSocialSearch('tiktok'" in s
assert "openSocialSearch('instagram'" in s
assert "openSocialSearch('facebook'" in s
assert 'x.com/search' not in s
assert 'speak(quick, false)' in s
assert 'window.GeoVisionTTS' in s
dst.write_text(s,encoding="utf-8")
print("Prepared v120 Android",dst,len(s))
