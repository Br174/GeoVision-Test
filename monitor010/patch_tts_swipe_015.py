from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'android-youtube-test/app/src/main/assets/geovision.html'
OUT = ROOT / 'out/LAB_012_FAILOVER.html'
MANIFEST = ROOT / 'android-youtube-test/app/src/main/AndroidManifest.xml'


def patch_html(path: Path):
    s = path.read_text(encoding='utf-8')

    # 1) Use the already-present native Android TTS bridge first; keep browser speech as fallback.
    a = s.index('function stopSpeech()')
    b = s.index('async function aiNarration', a)
    native_tts = r'''function gvNativeTtsAvailable(){try{return !!(window.GeoVisionTTS&&typeof window.GeoVisionTTS.speak==='function');}catch(_){return false;}}
let gvNativeTtsIgnoreDoneUntil=0;
window.gvNativeTtsState=function(state){
    if(state==='start'){
        speaking=true;
        $('#voice').classList.add('active');
        $('#nativeVoice').classList.add('active');
        return;
    }
    if((state==='done'||state==='error')&&Date.now()<gvNativeTtsIgnoreDoneUntil)return;
    if(state==='done'||state==='error'){
        speaking=false;
        $('#voice').classList.remove('active');
        $('#nativeVoice').classList.remove('active');
    }
};
function stopSpeech(){
    speechToken++;
    speechQueue.length=0;
    speechUtteranceSeq++;
    window.clearTimeout(speechWatchdog);
    speechPumpRunning=false;
    speaking=false;
    try{if(gvNativeTtsAvailable())window.GeoVisionTTS.stop();}catch(_){}
    try{if('speechSynthesis' in window)window.speechSynthesis.cancel();}catch(_){}
    $('#voice').classList.remove('active');
    $('#nativeVoice').classList.remove('active');
}
function speak(text,append=false){
    const parts=speechParts(text);
    if(!parts.length)return;
    if(gvNativeTtsAvailable()){
        if(!append){
            speechToken++;
            speechQueue.length=0;
            speechUtteranceSeq++;
            window.clearTimeout(speechWatchdog);
            speechPumpRunning=false;
            try{window.GeoVisionTTS.stop();}catch(_){}
            try{if('speechSynthesis' in window)window.speechSynthesis.cancel();}catch(_){}
        }
        speaking=true;
        $('#voice').classList.add('active');
        $('#nativeVoice').classList.add('active');
        gvNativeTtsIgnoreDoneUntil=Date.now()+350;
        setTimeout(()=>{
            parts.forEach((part,i)=>{
                try{window.GeoVisionTTS.speak(part,append||i>0);}catch(_){}
            });
        },45);
        return;
    }
    if(!('speechSynthesis' in window))return;
    if(!append){
        stopSpeech();
        try{window.speechSynthesis.resume();}catch(_){}
    }
    const token=speechToken;
    for(const part of parts)speechQueue.push({text:part,token,retries:0});
    pumpSpeech();
}
'''
    s = s[:a] + native_tts + s[b:]

    # 2) Keep the existing header drag, but also close the Google sheet with a real downward finger swipe.
    anchor = "sheetHead.addEventListener('pointercancel', finishSheetDrag);"
    assert anchor in s
    swipe = r'''
// Android touch fallback: a downward swipe closes the sheet even when the Google card owns the content area.
let gvSwipeStartY=0,gvSwipeStartX=0,gvSwipeTracking=false,gvSwipeClosed=false;
sheet.addEventListener('touchstart',(e)=>{
    if(!sheet.classList.contains('show')||e.touches.length!==1)return;
    const t=e.target;
    if(t&&t.closest&&t.closest('button,input,select,a'))return;
    const body=$('#sheetBody');
    const atTop=!body||body.scrollTop<=6||!!(t&&t.closest&&t.closest('.sheet-head'));
    if(!atTop)return;
    gvSwipeStartY=e.touches[0].clientY;
    gvSwipeStartX=e.touches[0].clientX;
    gvSwipeTracking=true;
    gvSwipeClosed=false;
},{passive:true});
sheet.addEventListener('touchmove',(e)=>{
    if(!gvSwipeTracking||gvSwipeClosed||e.touches.length!==1)return;
    const dy=e.touches[0].clientY-gvSwipeStartY;
    const dx=Math.abs(e.touches[0].clientX-gvSwipeStartX);
    const body=$('#sheetBody');
    if(dy>95&&dx<140&&(!body||body.scrollTop<=6)){
        gvSwipeClosed=true;
        gvSwipeTracking=false;
        closeSheet();
    }
},{passive:true});
sheet.addEventListener('touchend',(e)=>{
    if(!gvSwipeTracking||gvSwipeClosed)return;
    const p=e.changedTouches&&e.changedTouches[0];
    gvSwipeTracking=false;
    if(!p)return;
    const dy=p.clientY-gvSwipeStartY;
    const dx=Math.abs(p.clientX-gvSwipeStartX);
    const body=$('#sheetBody');
    if(dy>80&&dx<140&&(!body||body.scrollTop<=6))closeSheet();
},{passive:true});
sheet.addEventListener('touchcancel',()=>{gvSwipeTracking=false;gvSwipeClosed=false;},{passive:true});
'''
    s = s.replace(anchor, anchor + swipe, 1)
    path.write_text(s, encoding='utf-8')


patch_html(HTML)
if OUT.exists():
    patch_html(OUT)

# Android 11+ needs the TTS service query for reliable TextToSpeech engine discovery.
m = MANIFEST.read_text(encoding='utf-8')
if '<queries>' in m and 'android.intent.action.TTS_SERVICE' not in m:
    m = m.replace('<queries>', '<queries><intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>', 1)
elif '<queries>' not in m and 'android.intent.action.TTS_SERVICE' not in m:
    m = m.replace('<application', '<queries><intent><action android:name="android.intent.action.TTS_SERVICE"/></intent></queries>\n    <application', 1)
MANIFEST.write_text(m, encoding='utf-8')
print('LAB015 targeted patch applied: native TTS + Android TTS visibility + downward swipe close')
