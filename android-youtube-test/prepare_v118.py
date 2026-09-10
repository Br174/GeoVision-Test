from pathlib import Path

src=Path("GeoVision_Nova_v114_AI_RAPIDA_APPROFONDIMENTO.html")
dst=Path("android-youtube-test/app/src/main/assets/geovision.html")
dst.parent.mkdir(parents=True,exist_ok=True)
s=src.read_text(encoding="utf-8")

if '<meta name="referrer"' not in s:
    s=s.replace('<meta name="viewport"', '<meta name="referrer" content="strict-origin-when-cross-origin">\n<meta name="viewport"', 1)

start=s.index("function openYouTubeInternalPlayer(videoId,title='YouTube'){")
end=s.index("\nfunction launchPlatform(p)", start)
youtube_block=r"""let gvYoutubeItems=[];
let gvYoutubeQuery='';
function closeYouTubeExperience(){
    const shell=document.getElementById('youtubeResultsModal');
    const frame=document.getElementById('ytModalFrame');
    if(frame) frame.src='';
    shell?.remove();
}
function closeYouTubeInternalPlayer(){
    const frame=document.getElementById('ytModalFrame');
    const player=document.getElementById('ytPlayerArea');
    if(frame) frame.src='';
    if(player) player.style.display='none';
}
function openYouTubeInternalPlayer(videoId,title='YouTube'){
    const shell=document.getElementById('youtubeResultsModal');
    const player=document.getElementById('ytPlayerArea');
    const frame=document.getElementById('ytModalFrame');
    const titleEl=document.getElementById('ytNowTitle');
    if(!shell||!player||!frame)return;
    player.style.display='block';
    if(titleEl) titleEl.textContent=title;
    const origin=(location.protocol==='https:'||location.protocol==='http:')?location.origin:'';
    frame.src=`https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0${origin?`&origin=${encodeURIComponent(origin)}`:''}`;
    shell.scrollTop=0;
    player.scrollIntoView({block:'start',behavior:'smooth'});
}
function closeYouTubeResults(){ closeYouTubeExperience(); }
function renderYouTubeResults(items,q){
    gvYoutubeItems=items; gvYoutubeQuery=q;
    closeYouTubeExperience();
    const modal=document.createElement('div');
    modal.id='youtubeResultsModal';
    modal.style.cssText='position:fixed;inset:0;z-index:24500;background:#f7f8fa;display:flex;flex-direction:column;overflow:hidden';
    const cards=items.map((item,i)=>{
        const sn=item?.snippet||{};
        const thumb=sn?.thumbnails?.high?.url||sn?.thumbnails?.medium?.url||sn?.thumbnails?.default?.url||'';
        return `<button type="button" data-yt-index="${i}" style="border:0;background:#fff;border-radius:18px;padding:0;overflow:hidden;text-align:left;box-shadow:0 1px 0 rgba(16,24,40,.04);border:1px solid #e9edf2">
          <div style="aspect-ratio:16/9;background:#e9eef5;position:relative">${thumb?`<img src="${esc(thumb)}" alt="" style="display:block;width:100%;height:100%;object-fit:cover">`:''}<span style="position:absolute;right:10px;bottom:10px;width:42px;height:42px;border-radius:50%;background:rgba(0,0,0,.72);color:#fff;display:grid;place-items:center;font-size:18px">▶</span></div>
          <div style="padding:12px 13px 14px"><b style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:15px;line-height:1.35;color:#283341">${esc(sn.title||'Video YouTube')}</b><small style="display:block;margin-top:7px;color:#8993a1;font-size:12px">${esc(sn.channelTitle||'YouTube')}</small></div>
        </button>`;
    }).join('');
    modal.innerHTML=`
      <div style="height:62px;flex:0 0 62px;display:flex;align-items:center;gap:10px;padding:9px 12px;background:#fff;border-bottom:1px solid #e6eaf0">
        <div style="flex:1;min-width:0"><b style="display:block;color:#344054;font-size:15px">YouTube</b><small style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#8a94a3">${esc(q)}</small></div>
        <button id="youtubeResultsClose" type="button" aria-label="Chiudi" style="width:40px;height:40px;border:1px solid #e5e7eb;border-radius:50%;background:#fff;color:#64748b;font-size:25px">×</button>
      </div>
      <div id="ytScrollArea" style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding:0 0 18px">
        <section id="ytPlayerArea" style="display:none;background:#000;position:sticky;top:0;z-index:3">
          <div style="aspect-ratio:16/9;background:#000"><iframe id="ytModalFrame" style="width:100%;height:100%;border:0;background:#000" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay;encrypted-media;picture-in-picture;fullscreen" allowfullscreen></iframe></div>
          <div style="display:flex;align-items:center;gap:8px;padding:9px 12px;background:#fff;border-bottom:1px solid #e7eaf0">
            <b id="ytNowTitle" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#46505d;font-size:13px"></b>
            <button id="ytStopPlayer" type="button" style="border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:7px 11px;font-size:11px">Chiudi video</button>
          </div>
        </section>
        <div style="padding:14px 12px 8px"><b style="font-size:13px;color:#667085">Risultati</b></div>
        <div id="ytResultsGrid" style="display:grid;grid-template-columns:1fr;gap:12px;padding:0 12px">${cards}</div>
      </div>`;
    document.body.appendChild(modal);
    document.getElementById('youtubeResultsClose').onclick=closeYouTubeExperience;
    document.getElementById('ytStopPlayer').onclick=closeYouTubeInternalPlayer;
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
s=s.replace("""    /* Solo ora parte la frase iniziale: l'AI principale sta già lavorando. */
    speak(told);

    void (async () => {""","""    /* Android v121: aspetta il contenuto AI della scheda prima di parlare. */
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


# v123 — esperienza YouTube avanzata: ricerca, filtri, anno contenuto, scroll infinito.
v123_patch=r"""
const gvYTState={query:'',order:'relevance',year:'',nextPageToken:'',loading:false,done:false,items:[],seen:new Set()};

function gvYTEffectiveQuery(){
    const base=clean(document.getElementById('ytSearchInput')?.value||gvYTState.query||'');
    const year=String(document.getElementById('ytYearFilter')?.value||gvYTState.year||'').trim();
    return clean(year ? \`\${base} \${year}\` : base);
}
function gvYTCard(item){
    const sn=item?.snippet||{};
    const thumb=sn?.thumbnails?.high?.url||sn?.thumbnails?.medium?.url||sn?.thumbnails?.default?.url||'';
    const idx=gvYTState.items.indexOf(item);
    return \`<button type="button" data-yt-index="\${idx}" style="border:1px solid #e7eaf0;background:#fff;border-radius:20px;padding:0;overflow:hidden;text-align:left;box-shadow:0 2px 12px rgba(16,24,40,.035)">
      <div style="aspect-ratio:16/9;background:#e9eef5;position:relative">\${thumb?\`<img src="\${esc(thumb)}" alt="" style="display:block;width:100%;height:100%;object-fit:cover">\`:''}<span style="position:absolute;right:12px;bottom:12px;width:44px;height:44px;border-radius:50%;background:rgba(0,0,0,.74);color:#fff;display:grid;place-items:center;font-size:18px;padding-left:2px">▶</span></div>
      <div style="padding:13px 14px 15px">
        <b style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:15.5px;line-height:1.35;color:#273444">\${esc(sn.title||'Video YouTube')}</b>
        <small style="display:block;margin-top:7px;color:#8792a1;font-size:12px">\${esc(sn.channelTitle||'YouTube')}</small>
        \${sn.publishedAt?\`<small style="display:block;margin-top:4px;color:#a0a8b5;font-size:11px">\${new Date(sn.publishedAt).toLocaleDateString('it-IT')}</small>\`:''}
      </div>
    </button>\`;
}
function gvYTBindCards(root=document){
    root.querySelectorAll('[data-yt-index]').forEach(btn=>{
        if(btn.dataset.bound==='1')return;
        btn.dataset.bound='1';
        btn.onclick=()=>{
            const item=gvYTState.items[Number(btn.dataset.ytIndex)];
            const id=item?.id?.videoId;
            if(id) openYouTubeInternalPlayer(id,item?.snippet?.title||'YouTube');
        };
    });
}
async function gvYTLoadMore(reset=false){
    if(gvYTState.loading || (!reset && gvYTState.done))return;
    const input=document.getElementById('ytSearchInput');
    const base=clean(input?.value||gvYTState.query||'');
    if(!base)return;
    if(reset){
        gvYTState.query=base;
        gvYTState.year=String(document.getElementById('ytYearFilter')?.value||'');
        gvYTState.nextPageToken='';
        gvYTState.done=false;
        gvYTState.items=[];
        gvYTState.seen=new Set();
        const grid=document.getElementById('ytResultsGrid');
        if(grid)grid.innerHTML='';
    }
    gvYTState.loading=true;
    const more=document.getElementById('ytMoreState');
    if(more)more.textContent='Carico altri video…';
    try{
        const q=gvYTEffectiveQuery();
        const params=new URLSearchParams({
            part:'snippet',type:'video',maxResults:'25',safeSearch:'moderate',
            q, key:youtubeKey, order:gvYTState.order,
            relevanceLanguage:'it',regionCode:'IT'
        });
        if(gvYTState.nextPageToken)params.set('pageToken',gvYTState.nextPageToken);
        const r=await fetch('https://www.googleapis.com/youtube/v3/search?'+params.toString());
        if(!r.ok)throw new Error('YouTube '+r.status);
        const d=await r.json();
        const fresh=(d?.items||[]).filter(x=>{
            const id=x?.id?.videoId;
            if(!id||gvYTState.seen.has(id))return false;
            gvYTState.seen.add(id);return true;
        });
        gvYTState.items.push(...fresh);
        gvYTState.nextPageToken=d?.nextPageToken||'';
        gvYTState.done=!gvYTState.nextPageToken;
        const grid=document.getElementById('ytResultsGrid');
        if(grid&&fresh.length){
            grid.insertAdjacentHTML('beforeend',fresh.map(gvYTCard).join(''));
            gvYTBindCards(grid);
        }
        if(more)more.textContent=gvYTState.done?'Fine dei risultati disponibili':'Scorri per altri video';
    }catch(e){
        if(more)more.textContent='Impossibile caricare altri risultati';
    }finally{
        gvYTState.loading=false;
    }
}
function gvYTSetOrder(order,btn){
    gvYTState.order=order;
    document.querySelectorAll('[data-yt-order]').forEach(x=>{
        const on=x===btn;
        x.style.background=on?'#111827':'#fff';
        x.style.color=on?'#fff':'#667085';
        x.style.borderColor=on?'#111827':'#e5e7eb';
    });
    void gvYTLoadMore(true);
}
renderYouTubeResults=function(items,q){
    stopSpeech();
    gvYTState.query=q;gvYTState.order='relevance';gvYTState.year='';
    gvYTState.nextPageToken='';gvYTState.done=false;gvYTState.items=[];gvYTState.seen=new Set();
    closeYouTubeExperience();
    const modal=document.createElement('div');
    modal.id='youtubeResultsModal';
    modal.style.cssText='position:fixed;inset:0;z-index:24500;background:#f6f7f9;display:flex;flex-direction:column;overflow:hidden';
    const currentYear=new Date().getFullYear();
    let years='<option value="">Tutti gli anni</option>';
    for(let y=currentYear;y>=1900;y--)years+=\`<option value="\${y}">\${y}</option>\`;
    modal.innerHTML=\`
      <header style="flex:0 0 auto;background:#fff;border-bottom:1px solid #e7eaf0;padding:10px 12px 9px">
        <div style="display:flex;align-items:center;gap:9px">
          <div style="flex:1;display:flex;align-items:center;background:#f3f5f7;border:1px solid #e2e6eb;border-radius:999px;padding:0 12px;min-height:44px">
            <span style="font-size:16px;color:#7c8795;margin-right:7px">⌕</span>
            <input id="ytSearchInput" value="\${esc(q)}" placeholder="Cerca su YouTube" style="flex:1;min-width:0;border:0;outline:0;background:transparent;color:#344054;font-size:14px">
            <button id="ytSearchGo" type="button" style="border:0;background:transparent;color:#2563eb;font-weight:700;font-size:12px;padding:8px">Cerca</button>
          </div>
          <button id="youtubeResultsClose" type="button" aria-label="Chiudi" style="width:42px;height:42px;border:1px solid #e5e7eb;border-radius:50%;background:#fff;color:#667085;font-size:26px">×</button>
        </div>
        <div style="display:flex;gap:7px;overflow-x:auto;padding-top:9px;padding-bottom:2px;scrollbar-width:none">
          <button data-yt-order="relevance" style="flex:0 0 auto;border:1px solid #111827;background:#111827;color:#fff;border-radius:999px;padding:8px 12px;font-size:11px;font-weight:650">Pertinenti</button>
          <button data-yt-order="viewCount" style="flex:0 0 auto;border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:8px 12px;font-size:11px;font-weight:650">Più visti</button>
          <button data-yt-order="date" style="flex:0 0 auto;border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:8px 12px;font-size:11px;font-weight:650">Più nuovi</button>
          <button data-yt-order="rating" style="flex:0 0 auto;border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:8px 12px;font-size:11px;font-weight:650">Valutati</button>
          <select id="ytYearFilter" aria-label="Anno del contenuto" style="flex:0 0 auto;border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:8px 12px;font-size:11px;font-weight:650;outline:0">\${years}</select>
        </div>
      </header>
      <div id="ytScrollArea" style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding:0 0 22px">
        <section id="ytPlayerArea" style="display:none;background:#000;position:sticky;top:0;z-index:5">
          <div style="aspect-ratio:16/9;background:#000"><iframe id="ytModalFrame" style="width:100%;height:100%;border:0;background:#000" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay;encrypted-media;picture-in-picture;fullscreen" allowfullscreen></iframe></div>
          <div style="display:flex;align-items:center;gap:8px;padding:9px 12px;background:#fff;border-bottom:1px solid #e7eaf0">
            <b id="ytNowTitle" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#46505d;font-size:13px"></b>
            <button id="ytStopPlayer" type="button" style="border:1px solid #e5e7eb;background:#fff;color:#667085;border-radius:999px;padding:7px 11px;font-size:11px">Chiudi video</button>
          </div>
        </section>
        <div style="padding:14px 12px 9px;display:flex;align-items:center;justify-content:space-between"><b style="font-size:13px;color:#667085">Risultati</b><small id="ytQueryLabel" style="max-width:65%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#98a2b3">\${esc(q)}</small></div>
        <div id="ytResultsGrid" style="display:grid;grid-template-columns:1fr;gap:13px;padding:0 12px"></div>
        <div id="ytMoreState" style="padding:20px 12px 8px;text-align:center;color:#98a2b3;font-size:12px">Carico video…</div>
        <div id="ytInfiniteSentinel" style="height:2px"></div>
      </div>\`;
    document.body.appendChild(modal);
    document.getElementById('youtubeResultsClose').onclick=closeYouTubeExperience;
    document.getElementById('ytStopPlayer').onclick=closeYouTubeInternalPlayer;
    document.getElementById('ytSearchGo').onclick=()=>void gvYTLoadMore(true);
    document.getElementById('ytSearchInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();void gvYTLoadMore(true)}});
    document.getElementById('ytYearFilter').onchange=()=>void gvYTLoadMore(true);
    modal.querySelectorAll('[data-yt-order]').forEach(btn=>btn.onclick=()=>gvYTSetOrder(btn.dataset.ytOrder,btn));
    const observer=new IntersectionObserver(entries=>{
        if(entries.some(e=>e.isIntersecting))void gvYTLoadMore(false);
    },{root:document.getElementById('ytScrollArea'),rootMargin:'500px 0px'});
    observer.observe(document.getElementById('ytInfiniteSentinel'));
    modal._ytObserver=observer;
    void gvYTLoadMore(true);
};
openYouTubeInternalPlayer=function(videoId,title='YouTube'){
    stopSpeech();
    const player=document.getElementById('ytPlayerArea'),frame=document.getElementById('ytModalFrame'),titleEl=document.getElementById('ytNowTitle');
    if(!player||!frame)return;
    player.style.display='block';if(titleEl)titleEl.textContent=title;
    const origin=(location.protocol==='https:'||location.protocol==='http:')?location.origin:'';
    frame.src=\`https://www.youtube.com/embed/\${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0&fs=1\${origin?\`&origin=\${encodeURIComponent(origin)}\`:''}\`;
    player.scrollIntoView({block:'start',behavior:'smooth'});
};
launchYouTubeInternal=async function(q){
    stopSpeech();
    if(!youtubeKey)return false;
    renderYouTubeResults([],q);
    return true;
};
"""
# v125: il raw string della patch v123 conservava i backslash davanti ai template literal JS.
# In WebView questo produceva un errore di sintassi all'avvio e quindi la schermata vuota.
v123_patch=v123_patch.replace(r'\\`','`').replace(r'\\\${','\${')
s=s.replace("initGoogleMaps().catch(() => { });",v123_patch+"\\ninitGoogleMaps().catch(() => { });",1)

assert 'maxResults=12' in s
assert 'ytResultsGrid' in s
assert 'position:sticky;top:0' in s
assert "openSocialSearch('tiktok'" in s
assert "openSocialSearch('instagram'" in s
assert "openSocialSearch('facebook'" in s
assert 'x.com/search' not in s
assert 'speak(quick, false)' in s
assert 'window.GeoVisionTTS' in s
dst.write_text(s,encoding="utf-8")
print("Prepared v121 Android",dst,len(s))
