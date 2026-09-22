from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTMLS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def once(s,old,new,label):
    c=s.count(old)
    assert c==1,(label,c)
    return s.replace(old,new,1)

def patch_html(path):
    s=path.read_text(encoding='utf-8')

    old_preload="""function gv043PreloadGuide(p){
  try{
    return aiNarration(p,'guide','','');
  }catch(_){
    return Promise.resolve('');
  }
}"""
    new_preload="""const gv049GuideCache=new Map();
function gv049GuideKey(p){
  return [clean(p?.placeId||''),clean(p?.name||''),clean(p?.parent||''),clean(p?.kind||'')].join('|').toLowerCase();
}
function gv043PreloadGuide(p,force=false){
  try{
    const key=gv049GuideKey(p);
    if(!force && key && gv049GuideCache.has(key)) return gv049GuideCache.get(key);
    if(force && key) gv049GuideCache.delete(key);
    const request=aiNarration(p,'guide','','').then(text=>{
      if(!text && key) gv049GuideCache.delete(key);
      return text||'';
    }).catch(()=>{ if(key) gv049GuideCache.delete(key); return ''; });
    if(key){
      gv049GuideCache.set(key,request);
      while(gv049GuideCache.size>12) gv049GuideCache.delete(gv049GuideCache.keys().next().value);
    }
    return request;
  }catch(_){
    return Promise.resolve('');
  }
}"""
    s=once(s,old_preload,new_preload,'preload cache')

    old_fail="""if(!continuation){ transcript.innerHTML='<div class=\"narration narration-stage\">Audioguida non disponibile.<br><small>'+esc(gvLastAiError||'Nessun testo restituito dall’intelligenza artificiale')+'</small></div>'; return; }"""
    new_fail="""if(!continuation){
    transcript.innerHTML='<div class=\"loading\">Preparo l’audioguida…</div>';
    await new Promise(resolve=>setTimeout(resolve,320));
    if(run !== narrationRun || current !== p) return;
    continuation=await gv043PreloadGuide(p,true);
    if(run !== narrationRun || current !== p) return;
    if(!continuation){ transcript.innerHTML='<div class=\"narration narration-stage\">Audioguida temporaneamente non disponibile.</div>'; return; }
}"""
    s=once(s,old_fail,new_fail,'silent 503 retry')

    old_open="""async function openPlace(p) {
  macroPrimary = '';
  current = p;
  closeNativeAudio();
  setFields(p);
  setSelectionMarker(p);
  const guidePromise = gv043PreloadGuide(p);
  const cardPromise = renderOfficialGoogleCard(p);
  void enrichNarration(p, guidePromise);
  await cardPromise;
}"""
    new_open="""async function openPlace(p) {
  macroPrimary = '';
  current = p;
  const guidePromise = gv043PreloadGuide(p);
  closeNativeAudio();
  setFields(p);
  setSelectionMarker(p);
  const cardPromise = renderOfficialGoogleCard(p);
  void enrichNarration(p, guidePromise);
  await cardPromise;
}"""
    s=once(s,old_open,new_open,'early guide start')

    checks=[
      'const gv049GuideCache=new Map();' in s,
      'continuation=await gv043PreloadGuide(p,true);' in s,
      'Gemini HTTP 503' not in s,
      "const guidePromise = gv043PreloadGuide(p);\n  closeNativeAudio();" in s,
      'function platformQuery047()' in s,
      'Importa da KeyBox' in s,
      'const lead = gv043GuideLead(p);' not in s,
    ]
    assert all(checks),[i for i,x in enumerate(checks,1) if not x]
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    s=once(s,'c.setConnectTimeout(10000);','c.setConnectTimeout(6500);','connect timeout')
    s=once(s,'c.setReadTimeout(18000);','c.setReadTimeout(15000);','read timeout')
    s=once(s,'.put("maxOutputTokens", 1400);','.put("maxOutputTokens", 900);','initial response size')

    old="""    private String callGemini(String key, String prompt) throws Exception {
        Exception last = null;
        for (String model : new String[]{\"gemini-2.5-flash\",\"gemini-2.0-flash\"}) {
            try {
                String text = callGeminiModel(model,key,prompt);
                if (text.length() > 80) return text;
            } catch (Exception e) { last = e; }
        }
        if (last != null) throw last;
        return \"\";
    }
"""
    new="""    private String callGemini(String key, String prompt) throws Exception {
        Exception last = null;
        String[] models = new String[]{\"gemini-3.5-flash-lite\",\"gemini-2.5-flash-lite\",\"gemini-2.5-flash\"};
        for (String model : models) {
            try {
                String text = callGeminiModel(model,key,prompt);
                if (text.length() > 80) return text;
            } catch (Exception e) { last = e; }
        }
        String msg = last == null ? \"\" : String.valueOf(last.getMessage());
        if (msg.contains(\"HTTP 503\") || msg.contains(\"HTTP 429\")) {
            try {
                Thread.sleep(250);
                String text = callGeminiModel(\"gemini-3.5-flash-lite\",key,prompt);
                if (text.length() > 80) return text;
            } catch (Exception e) { last = e; }
        }
        if (last != null) throw last;
        return \"\";
    }
"""
    s=once(s,old,new,'modern Gemini fallback chain')

    checks=[
      'gemini-3.5-flash-lite' in s,
      'gemini-2.5-flash-lite' in s,
      'gemini-2.0-flash' not in s,
      'c.setConnectTimeout(6500);' in s,
      'c.setReadTimeout(15000);' in s,
      '.put("maxOutputTokens", 900);' in s,
      'Thread.sleep(250);' in s,
    ]
    assert all(checks),[i for i,x in enumerate(checks,1) if not x]
    JAVA.write_text(s,encoding='utf-8')

for p in HTMLS:
    if p.exists(): patch_html(p)
patch_java()
print('LAB049: fast AI audioguide, modern Flash-Lite fallback, cached prefetch, silent automatic retry')
