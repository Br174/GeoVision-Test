from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
MANIFEST=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'

def patch(path):
    s=path.read_text(encoding='utf-8')
    # SAFE: do not replace existing speech engine functions or application initialization.
    # Only intercept speak() after the page is fully loaded; native Android bridge first.
    hook=r'''\n<script id="gv-tts-swipe-safe-016">\n(function(){\nfunction install(){\n  try{\n    if(window.__gv016Installed)return; window.__gv016Installed=true;\n    const oldSpeak=window.speak;\n    if(typeof oldSpeak==='function') window.speak=function(text,append){\n      try{\n        if(window.GeoVisionTTS&&typeof window.GeoVisionTTS.speak==='function'){\n          if(!append&&typeof window.GeoVisionTTS.stop==='function')window.GeoVisionTTS.stop();\n          const p=(typeof speechParts==='function'?speechParts(text):[String(text||'')]).filter(Boolean);\n          p.forEach((x,i)=>window.GeoVisionTTS.speak(x,!!append||i>0));\n          return;\n        }\n      }catch(_){}\n      return oldSpeak.apply(this,arguments);\n    };\n    const oldStop=window.stopSpeech;\n    if(typeof oldStop==='function') window.stopSpeech=function(){try{if(window.GeoVisionTTS&&GeoVisionTTS.stop)GeoVisionTTS.stop();}catch(_){} return oldStop.apply(this,arguments);};\n    const sh=document.getElementById('sheet');\n    const body=document.getElementById('sheetBody');\n    if(sh){let y=0,x=0,on=false;\n      sh.addEventListener('touchstart',e=>{if(e.touches.length!==1)return;const t=e.target;if(t&&t.closest&&t.closest('button,input,select,a'))return;if(body&&body.scrollTop>6)return;y=e.touches[0].clientY;x=e.touches[0].clientX;on=true;},{passive:true});\n      sh.addEventListener('touchend',e=>{if(!on)return;on=false;const p=e.changedTouches&&e.changedTouches[0];if(!p)return;const dy=p.clientY-y,dx=Math.abs(p.clientX-x);if(dy>90&&dx<140&&(!body||body.scrollTop<=6)&&typeof closeSheet==='function')closeSheet();},{passive:true});\n      sh.addEventListener('touchcancel',()=>on=false,{passive:true});\n    }\n  }catch(e){console.warn('GV016 isolated patch',e);}\n}\nif(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else setTimeout(install,0);\n})();\n</script>\n'''
    assert '</body>' in s
    s=s.replace('</body>',hook+'</body>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists():patch(OUT)
m=MANIFEST.read_text(encoding='utf-8')
if 'android.intent.action.TTS_SERVICE' not in m:
    if '<queries>' in m:m=m.replace('<queries>','<queries><intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>',1)
    else:m=m.replace('<application','<queries><intent><action android:name="android.intent.action.TTS_SERVICE"/></intent></queries>\n    <application',1)
MANIFEST.write_text(m,encoding='utf-8')
print('LAB016 isolated post-load TTS/swipe patch applied')
