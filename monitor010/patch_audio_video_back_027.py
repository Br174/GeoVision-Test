from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    anchor='function launchPlatform(p)'
    assert anchor in s
    helper="""function gv027StopGuideForMedia(){
  try{ if(window.GeoVisionTTS&&typeof window.GeoVisionTTS.stop==='function') window.GeoVisionTTS.stop(); }catch(_){}
  try{ if(window.speechSynthesis) window.speechSynthesis.cancel(); }catch(_){}
}
"""
    if 'function gv027StopGuideForMedia()' not in s:
        s=s.replace(anchor,helper+'\n'+anchor,1)
    s=s.replace('function launchPlatform(p) {','function launchPlatform(p) {\n  gv027StopGuideForMedia();',1)
    # Internal YouTube/video picker also stops narration as soon as it is opened.
    old="$('#sheetVideo').onclick = e => { e.preventDefault(); e.stopPropagation(); $('#videoPicker').classList.toggle('show'); };"
    if old in s:
        new="$('#sheetVideo').onclick = e => { e.preventDefault(); e.stopPropagation(); gv027StopGuideForMedia(); $('#videoPicker').classList.toggle('show'); };"
        s=s.replace(old,new,1)
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    # External Facebook launch: stop TTS before leaving GeoVision. Activity/card stays alive underneath.
    old='''            main.post(() -> {\n                try {\n                    android.content.Intent intent = new android.content.Intent('''
    new='''            main.post(() -> {\n                stopNative();\n                try {\n                    android.content.Intent intent = new android.content.Intent('''
    assert old in s, 'external bridge anchor missing'
    s=s.replace(old,new,1)
    # Android back: close only video overlays first; otherwise use WebView history. It never closes the sheet itself.
    assert 'public void onBackPressed()' in s
    JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists(): patch_html(OUT)
patch_java()
print('LAB027 stop audioguide on media launch; preserve underlying Google card/back state')
