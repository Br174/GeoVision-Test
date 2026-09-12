from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
html_paths = [
    ROOT / 'android-youtube-test/app/src/main/assets/geovision.html',
    ROOT / 'out/LAB_012_FAILOVER.html',
]

NATIVE_TTS_PATCH = r'''
<script id="gv-lab015-tts-swipe">
(function(){
'use strict';

function gvSetSpeechActive(active){
  try{
    speaking=!!active;
    const a=document.getElementById('voice');
    const b=document.getElementById('nativeVoice');
    if(a)a.classList.toggle('active',!!active);
    if(b)b.classList.toggle('active',!!active);
  }catch(_){ }
}

window.gvNativeTtsState=function(state){
  if(state==='start') gvSetSpeechActive(true);
  if(state==='done'||state==='error') gvSetSpeechActive(false);
};

const gvBrowserStop = (typeof stopSpeech==='function') ? stopSpeech : null;
const gvBrowserSpeak = (typeof speak==='function') ? speak : null;

window.stopSpeech = function(){
  try{ speechToken++; }catch(_){ }
  try{ speechQueue.length=0; }catch(_){ }
  try{ speechUtteranceSeq++; }catch(_){ }
  try{ clearTimeout(speechWatchdog); }catch(_){ }
  try{ speechPumpRunning=false; }catch(_){ }
  gvSetSpeechActive(false);
  try{
    if(window.GeoVisionTTS && typeof window.GeoVisionTTS.stop==='function'){
      window.GeoVisionTTS.stop();
    }
  }catch(_){ }
  try{ window.speechSynthesis && window.speechSynthesis.cancel(); }catch(_){ }
};

window.speak = function(text, append=false){
  let cleanText='';
  try{ cleanText=typeof speechText==='function' ? speechText(text) : String(text||'').trim(); }
  catch(_){ cleanText=String(text||'').trim(); }
  if(!cleanText)return;

  try{
    if(window.GeoVisionTTS && typeof window.GeoVisionTTS.speak==='function'){
      if(!append) window.stopSpeech();
      const parts=(typeof speechParts==='function' ? speechParts(cleanText) : [cleanText]).filter(Boolean);
      if(!parts.length)return;
      gvSetSpeechActive(true);
      parts.forEach((part,i)=>window.GeoVisionTTS.speak(part, !!append || i>0));
      return;
    }
  }catch(_){ }

  if(gvBrowserSpeak){
    try{return gvBrowserSpeak(cleanText,append);}catch(_){ }
  }
};

function installSwipeDown(){
  const sheet=document.getElementById('sheet');
  const head=document.querySelector('#sheet .sheet-head');
  const body=document.getElementById('sheetBody');
  if(!sheet||!head)return;

  head.style.touchAction='none';
  let startY=0, lastY=0, active=false, dragging=false, startedInHeader=false;

  const interactive=(el)=>!!(el&&el.closest&&el.closest('button,select,input,a,gmp-place-details'));

  sheet.addEventListener('touchstart',function(e){
    if(!sheet.classList.contains('show')||!e.touches||e.touches.length!==1)return;
    const t=e.target;
    startedInHeader=!!(t&&t.closest&&t.closest('.sheet-head'));
    if(interactive(t) && !startedInHeader)return;
    const canBodyPull=!startedInHeader && body && body.scrollTop<=0;
    if(!startedInHeader && !canBodyPull)return;
    startY=lastY=e.touches[0].clientY;
    active=true;
    dragging=false;
  },{passive:true,capture:true});

  sheet.addEventListener('touchmove',function(e){
    if(!active||!e.touches||e.touches.length!==1)return;
    lastY=e.touches[0].clientY;
    const dy=lastY-startY;
    if(dy<=0)return;
    if(!startedInHeader && body && body.scrollTop>0){active=false;dragging=false;sheet.style.transform='';return;}
    if(dy>10)dragging=true;
    if(!dragging)return;
    e.preventDefault();
    sheetDragging=true;
    sheet.style.transition='none';
    sheet.style.transform='translate(-50%,'+Math.min(dy,220)+'px)';
  },{passive:false,capture:true});

  const finish=function(){
    if(!active)return;
    const dy=lastY-startY;
    active=false;
    sheetDragging=false;
    sheet.style.transition='';
    if(dragging && dy>=64){
      try{ closeSheet(); }catch(_){ sheet.classList.remove('show'); sheet.style.transform=''; }
    }else{
      sheet.style.transform='';
    }
    dragging=false;
  };

  sheet.addEventListener('touchend',finish,{passive:true,capture:true});
  sheet.addEventListener('touchcancel',finish,{passive:true,capture:true});
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installSwipeDown,{once:true});
else installSwipeDown();

})();
</script>
'''

for path in html_paths:
    s = path.read_text(encoding='utf-8')
    assert 'function renderOfficialGoogleCard(p)' in s, f'Google card guard missing in {path}'
    assert 'function closeSheet()' in s, f'closeSheet guard missing in {path}'
    assert 'function speak(text, append = false)' in s, f'TTS guard missing in {path}'
    assert 'gv-lab015-tts-swipe' not in s, f'patch already applied in {path}'
    s = s.replace("if (speaking) {\n    speechSynthesis.cancel();\n    return;", "if (speaking) {\n    stopSpeech();\n    return;", 1)
    s = s.replace('</body>', NATIVE_TTS_PATCH + '\n</body>', 1)
    path.write_text(s, encoding='utf-8')

print('LAB015 patch applied: native Android TTS + swipe-down close only')
