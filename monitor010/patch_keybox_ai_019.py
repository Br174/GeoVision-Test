from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')

    # Native TTS: when idle, the first real narration chunk must FLUSH/start;
    # following chunks append to the same Android TTS queue.
    anchor="if (window.GeoVisionTTS && typeof window.GeoVisionTTS.speak === 'function') {"
    pos=s.find(anchor)
    assert pos>=0, 'native TTS bridge anchor not found'
    insert_pos=pos+len(anchor)
    s=s[:insert_pos]+"\n        const gvWasSpeaking = speaking;"+s[insert_pos:]
    old="parts.forEach((part, i) => window.GeoVisionTTS.speak(part, !!append || i > 0));"
    assert old in s, 'native TTS queue anchor not found'
    s=s.replace(old,"parts.forEach((part, i) => window.GeoVisionTTS.speak(part, (append && gvWasSpeaking) || i > 0));",1)

    addon=r'''
<style id="gv019-keybox-visible-style">
#gvLocalApi .gv-keybox-import{display:block!important;width:100%!important;margin:0 0 10px!important;border:1px solid #bfdbfe!important;border-radius:13px!important;background:#eff6ff!important;color:#1d4ed8!important;padding:12px 14px!important;font-weight:900!important}
</style>
<script id="gv019-keybox-audioguide">
(function(){
  function toastSafe(t){try{if(typeof toast==='function')toast(t);}catch(_){}}
  function saveImported(keys){
    try{
      const g1=String(keys?.google1||'').trim(),g2=String(keys?.google2||'').trim(),g3=String(keys?.google3||'').trim();
      const ai=String(keys?.ai||'').trim(),yt=String(keys?.youtube||'').trim(),maps=[g1,g2,g3];
      localStorage.setItem('geovision_google_maps_api_key_1',g1);
      localStorage.setItem('geovision_google_maps_api_key_2',g2);
      localStorage.setItem('geovision_google_maps_api_key_3',g3);
      localStorage.setItem('geovision_google_maps_api_keys',JSON.stringify(maps));
      const first=maps.find(Boolean)||'';
      if(first)localStorage.setItem('geovision_google_maps_api_key',first);else localStorage.removeItem('geovision_google_maps_api_key');
      if(ai)localStorage.setItem('geovision_ai_api_key',ai);else localStorage.removeItem('geovision_ai_api_key');
      if(yt)localStorage.setItem('geovision_youtube_api_key',yt);else localStorage.removeItem('geovision_youtube_api_key');
      try{const st=window.GVKeyState?.create?.(localStorage);st?.apply?.({google1:g1,google2:g2,google3:g3,ai:ai,youtube:yt,googleEnabled:[true,true,true],revision:0});}catch(_){}
      try{googleKey=first||googleKey;}catch(_){}
      const root=document.getElementById('gvLocalApi');
      if(root){
        const vals={google1:g1,google2:g2,google3:g3,ai:ai,youtube:yt};
        Object.keys(vals).forEach(n=>{const row=root.querySelector('[data-name="'+n+'"]');const inp=row?.querySelector('input[type=password]');if(inp)inp.value=vals[n];const st=row?.querySelector('.state');if(st)st.textContent=vals[n]?'Configurata':'Chiave assente';});
      }
      toastSafe('Chiavi importate da KeyBox');
    }catch(_){toastSafe('Importazione KeyBox non riuscita');}
  }
  window.gvReceiveKeyBox=saveImported;
  window.gvKeyBoxError=function(msg){toastSafe(msg||'GeoVision KeyBox non disponibile');};

  function addImportButton(root){
    if(!root||root.querySelector('.gv-keybox-import'))return;
    const b=document.createElement('button');b.type='button';b.className='gv-keybox-import';b.textContent='Importa da KeyBox';
    b.onclick=function(){try{const k=window.GeoVisionKeyBox;if(k&&typeof k.importKeys==='function')k.importKeys();else window.gvKeyBoxError('GeoVision KeyBox non installato');}catch(_){window.gvKeyBoxError('GeoVision KeyBox non disponibile');}};
    const rows=root.querySelector('.rows'),save=root.querySelector('.save');
    if(rows?.parentElement)rows.parentElement.insertBefore(b,rows);else if(save?.parentElement)save.parentElement.insertBefore(b,save);else root.querySelector('.box')?.appendChild(b);
  }
  const watch=new MutationObserver(()=>addImportButton(document.getElementById('gvLocalApi')));
  watch.observe(document.documentElement,{childList:true,subtree:true});
  addImportButton(document.getElementById('gvLocalApi'));

  // Audioguida: ogni nuova scheda Google avvia automaticamente la narrazione AI.
  // Non modifica la scheda: osserva soltanto l'apertura dell'area audioGuide.
  let guideSeq=0,lastGuide=null;
  async function startGuide(node){
    if(!node||node===lastGuide)return; lastGuide=node; const seq=++guideSeq;
    try{
      if(typeof stopSpeech==='function')stopSpeech();
      const p=window.current;
      if(!p||typeof window.aiNarration!=='function')return;
      const text=String(await window.aiNarration(p,'initial','', '',0)||'').trim();
      if(seq!==guideSeq||!node.isConnected||!text)return;
      node.innerHTML='<div class="narration-text"></div>';
      const out=node.querySelector('.narration-text'); if(out)out.textContent=text;
      if(typeof window.speak==='function')window.speak(text,false);
    }catch(_){ }
  }
  const guideWatch=new MutationObserver(()=>{const n=document.getElementById('audioGuide');if(n&&n!==lastGuide)setTimeout(()=>startGuide(n),0);});
  guideWatch.observe(document.documentElement,{childList:true,subtree:true});
  const n=document.getElementById('audioGuide');if(n)startGuide(n);
})();
</script>
'''
    assert '</body>' in s
    s=s.replace('</body>',addon+'\n</body>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB019 visible KeyBox import + automatic AI audioguide applied')
