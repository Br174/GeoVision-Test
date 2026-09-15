from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    # LAB027 stopped narration when merely opening the media selector. Undo that.
    s=s.replace('function launchPlatform(p) {\n  gv027StopGuideForMedia();','function launchPlatform(p) {',1)
    s=s.replace("$('#sheetVideo').onclick = e => { e.preventDefault(); e.stopPropagation(); gv027StopGuideForMedia(); $('#videoPicker').classList.toggle('show'); };",
                "$('#sheetVideo').onclick = e => { e.preventDefault(); e.stopPropagation(); $('#videoPicker').classList.toggle('show'); };",1)

    # Stop only on actual media navigation/play click, not while browsing/searching.
    hook="""document.addEventListener('click',e=>{
  const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;
  if(!a)return;
  const u=String(a.href||'').toLowerCase();
  if(/youtube\\.com\\/watch|youtu\\.be\\/|facebook\\.com\\/(watch|reel)|instagram\\.com\\/(reel|p)\\/|tiktok\\.com\\/.+video/.test(u)) gv027StopGuideForMedia();
},true);
"""
    if hook not in s:
        s=s.replace('</body>',hook+'</body>',1)

    # Stabilize the official Google card: one retry if the host remains empty/blank.
    anchor='async function renderOfficialGoogleCard'
    assert anchor in s, 'Google card renderer missing'
    retry="""function gv028EnsureGoogleCard(p){
  let tries=0;
  const check=()=>{
    const host=document.getElementById('googleCardHost');
    const visible=document.getElementById('sheet')?.classList.contains('show');
    if(!visible||!p||!host)return;
    const empty=!host.textContent.trim()&&!host.querySelector('img,iframe,[role="img"],a');
    if(empty&&tries++<2){ try{ renderOfficialGoogleCard(p); }catch(_){} setTimeout(check,1200); }
  };
  setTimeout(check,900);
}
"""
    if 'function gv028EnsureGoogleCard(p)' not in s:
        s=s.replace(anchor,retry+'\n'+anchor,1)
    # Attach retry after every normal official-card request without changing its renderer/UI.
    needle='renderOfficialGoogleCard(p);'
    if 'gv028EnsureGoogleCard(p);' not in s:
        pos=s.find(needle)
        assert pos>=0
        end=pos+len(needle)
        s=s[:end]+' gv028EnsureGoogleCard(p);'+s[end:]
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    # LAB027 external Facebook bridge stopped immediately on search launch; remove that early stop.
    s=s.replace('            main.post(() -> {\n                stopNative();\n                try {\n                    android.content.Intent intent = new android.content.Intent(',
                '            main.post(() -> {\n                try {\n                    android.content.Intent intent = new android.content.Intent(',1)
    JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists(): patch_html(OUT)
patch_java()
print('LAB028 deferred media TTS stop + Google card blank retry')
