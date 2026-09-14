from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    old="""async function gvGeminiNarration(p, mode, extract='', previous='', depth=0){
    const key=gvAiKey(); if(!key) return '';
    const prompt=gvNarrationPrompt(p,mode,extract,previous,depth);
    try{
        const nativeText=await gvNativeNarration(key,prompt);
        if(nativeText.length>80)return nativeText;
    }catch(e){try{console.error('GeoVision native AI failed',e);}catch(_){}}
    return '';
}"""
    new="""let gvLastAiError='';
async function gvGeminiNarration(p, mode, extract='', previous='', depth=0){
    const key=gvAiKey();
    if(!key){ gvLastAiError='Chiave AI assente o disattivata'; return ''; }
    const prompt=gvNarrationPrompt(p,mode,extract,previous,depth);
    try{
        const nativeText=await gvNativeNarration(key,prompt);
        gvLastAiError='';
        if(nativeText.length>80)return nativeText;
        gvLastAiError='Risposta AI troppo breve o vuota';
    }catch(e){
        gvLastAiError=String(e?.message||e||'Errore AI sconosciuto');
        try{console.error('GeoVision native AI failed',e);}catch(_){}
    }
    return '';
}"""
    assert old in s, 'gvGeminiNarration anchor not found'
    s=s.replace(old,new,1)
    old_err="transcript.innerHTML='<div class=\"narration narration-stage\">Audioguida temporaneamente non disponibile.</div>'; return;"
    new_err="transcript.innerHTML='<div class=\"narration narration-stage\">Audioguida non disponibile.<br><small>'+esc(gvLastAiError||'Nessun testo restituito dall’intelligenza artificiale')+'</small></div>'; return;"
    assert old_err in s, 'audioguide error anchor not found'
    s=s.replace(old_err,new_err,1)
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    s=s.replace('JSONObject cfg = new JSONObject().put("temperature", 0.55).put("maxOutputTokens", 1400);','JSONObject cfg = new JSONObject().put("maxOutputTokens", 1400);',1)
    old='for (String model : new String[]{"gemini-2.5-flash","gemini-2.0-flash"}) {'
    new='for (String model : new String[]{"gemini-3.6-flash","gemini-2.5-flash","gemini-3.5-flash-lite"}) {'
    assert old in s, 'model fallback anchor not found'
    s=s.replace(old,new,1)
    old2='if (code < 200 || code >= 300) throw new Exception("Gemini HTTP " + code + " " + raw);'
    new2='if (code < 200 || code >= 300) { String msg=raw; try { JSONObject er=new JSONObject(raw).optJSONObject("error"); if(er!=null) msg=er.optString("message",raw); } catch(Exception ignored){} throw new Exception("Gemini HTTP " + code + ": " + msg); }'
    assert old2 in s, 'HTTP error anchor not found'
    s=s.replace(old2,new2,1)
    JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists(): patch_html(OUT)
patch_java()
print('LAB021 Gemini current models + visible AI diagnostics applied')
