from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')

    old="speak(text, true);"
    start=s.find('function appendAndSpeak')
    pos=s.find(old,start)
    assert start>=0 and pos>=0, 'appendAndSpeak TTS anchor not found'
    s=s[:pos]+"speak(text, speaking);"+s[pos+len(old):]

    addon=r'''
<script id="gv019-simple-keybox">
(function(){
  function saveImported(keys){
    try{
      const g1=String(keys?.google1||'').trim(),g2=String(keys?.google2||'').trim(),g3=String(keys?.google3||'').trim();
      const ai=String(keys?.ai||'').trim(),yt=String(keys?.youtube||'').trim();
      const maps=[g1,g2,g3];
      localStorage.setItem('geovision_google_maps_api_key_1',g1);
      localStorage.setItem('geovision_google_maps_api_key_2',g2);
      localStorage.setItem('geovision_google_maps_api_key_3',g3);
      localStorage.setItem('geovision_google_maps_api_keys',JSON.stringify(maps));
      const first=maps.find(Boolean)||'';
      if(first)localStorage.setItem('geovision_google_maps_api_key',first);else localStorage.removeItem('geovision_google_maps_api_key');
      if(ai)localStorage.setItem('geovision_ai_api_key',ai);else localStorage.removeItem('geovision_ai_api_key');
      if(yt)localStorage.setItem('geovision_youtube_api_key',yt);else localStorage.removeItem('geovision_youtube_api_key');
      try{const st=window.GVKeyState?.create?.(localStorage);st?.apply?.({google1:g1,google2:g2,google3:g3,ai:ai,youtube:yt,googleEnabled:[true,true,true],revision:0});}catch(_){}
      const root=document.getElementById('gvLocalApi');
      if(root){
        const vals={google1:g1,google2:g2,google3:g3,ai:ai,youtube:yt};
        Object.keys(vals).forEach(n=>{const row=root.querySelector('[data-name="'+n+'"]');const inp=row?.querySelector('input[type=password]');if(inp)inp.value=vals[n];});
      }
      try{googleKey=first||googleKey;}catch(_){}
      toast('Chiavi importate da KeyBox');
    }catch(_){toast('Importazione KeyBox non riuscita');}
  }
  window.gvReceiveKeyBox=saveImported;
  window.gvKeyBoxError=function(msg){toast(msg||'GeoVision KeyBox non disponibile');};
  const original=window.gvOpenLocalApiPanel;
  if(typeof original==='function'){
    window.gvOpenLocalApiPanel=function(){
      original();
      const root=document.getElementById('gvLocalApi'); if(!root)return;
      if(!root.querySelector('.gv-keybox-import')){
        const b=document.createElement('button');b.type='button';b.className='save gv-keybox-import';b.textContent='Importa da KeyBox';b.style.marginTop='0';b.style.marginBottom='8px';
        const save=root.querySelector('.save');save?.parentElement?.insertBefore(b,save);
        b.onclick=function(){try{if(window.GeoVisionKeyBox&&typeof window.GeoVisionKeyBox.importKeys==='function')window.GeoVisionKeyBox.importKeys();else window.gvKeyBoxError('GeoVision KeyBox non installato');}catch(_){window.gvKeyBoxError('GeoVision KeyBox non disponibile');}};
      }
    };
  }
})();
</script>
'''
    assert '</body>' in s
    s=s.replace('</body>',addon+'\n</body>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB019 simple KeyBox import + AI native TTS start applied')
