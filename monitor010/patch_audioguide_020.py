from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def once(s,old,new):
    c=s.count(old)
    assert c==1,(old[:100],c)
    return s.replace(old,new,1)

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    old="""async function gvGeminiNarration(p, mode, extract='', previous='', depth=0){
    const key=gvAiKey(); if(!key) return '';
    const prompt=gvNarrationPrompt(p,mode,extract,previous,depth);
    const models=['gemini-2.5-flash','gemini-2.0-flash'];
    for(const model of models){
        try{
            const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,{
                method:'POST',headers:{'Content-Type':'application/json'},
                body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:0.55,maxOutputTokens:mode==='deepen'?900:1400}})
            });
            if(!r.ok) continue;
            const j=await r.json();
            const text=clean((j.candidates?.[0]?.content?.parts||[]).map(x=>x.text||'').join(' '));
            if(text.length>80) return text;
        }catch{}
    }
    return '';
}"""
    new="""let gvAiSeq=0;
const gvAiPending=new Map();
window.gvNativeAiResult=function(id,text,error){
    const p=gvAiPending.get(String(id)); if(!p)return;
    gvAiPending.delete(String(id));
    if(error)p.reject(new Error(String(error))); else p.resolve(clean(text||''));
};
function gvNativeNarration(key,prompt){
    return new Promise((resolve,reject)=>{
        try{
            if(!window.GeoVisionAI || typeof window.GeoVisionAI.generate!=='function') return reject(new Error('Native AI bridge unavailable'));
            const id='gvai_'+Date.now()+'_'+(++gvAiSeq);
            const timer=setTimeout(()=>{gvAiPending.delete(id);reject(new Error('Native AI timeout'));},20000);
            gvAiPending.set(id,{resolve:t=>{clearTimeout(timer);resolve(t);},reject:e=>{clearTimeout(timer);reject(e);}});
            window.GeoVisionAI.generate(String(key||''),String(prompt||''),id);
        }catch(e){reject(e);}
    });
}
async function gvGeminiNarration(p, mode, extract='', previous='', depth=0){
    const key=gvAiKey(); if(!key) return '';
    const prompt=gvNarrationPrompt(p,mode,extract,previous,depth);
    try{
        const nativeText=await gvNativeNarration(key,prompt);
        if(nativeText.length>80)return nativeText;
    }catch(e){try{console.error('GeoVision native AI failed',e);}catch(_){}}
    return '';
}"""
    s=once(s,old,new)

    old2="""async function enrichNarration(p) { const run = ++narrationRun; try {
    window.speechSynthesis?.resume();
}
catch { } const guide = $('#audioGuide'); if (!guide)
    return; guide.innerHTML = '<div class=\"audio-title\">Audioguida AI</div><div id=\"guideScroll\" class=\"guide-scroll\"><div id=\"guideTranscript\"></div><div id=\"guideSource\" class=\"source\"></div></div><button id=\"deepenGuide\" class=\"deepen-guide\" type=\"button\" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = instantNarrationIntro(p), depth = 0; transcript.innerHTML = `<div class=\"narration narration-stage\">${esc(told)}</div>`; speak(told); const wikiPromise = wikiInfo(p), metaPromise = enrichPlaceNarrationMeta(p); const w = await wikiPromise; await metaPromise; if (run !== narrationRun || current !== p)
    return; let continuation = await aiNarration(p, 'guide', w.extract, told);"""
    new2="""async function enrichNarration(p) { const run = ++narrationRun; const guide = $('#audioGuide'); if (!guide)
    return; guide.innerHTML = '<div class=\"audio-title\">Audioguida AI</div><div id=\"guideScroll\" class=\"guide-scroll\"><div id=\"guideTranscript\"><div class=\"loading\">Preparo l’audioguida…</div></div><div id=\"guideSource\" class=\"source\"></div></div><button id=\"deepenGuide\" class=\"deepen-guide\" type=\"button\" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = '', depth = 0; let continuation = await aiNarration(p, 'guide', '', ''); if (run !== narrationRun || current !== p)
    return; if(!continuation){ transcript.innerHTML='<div class=\"narration narration-stage\">Audioguida temporaneamente non disponibile.</div>'; return; } transcript.innerHTML='';"""
    s=once(s,old2,new2)
    # remove redundant fallback call because native bridge already handles model fallback
    s=s.replace("if (!continuation)\n    continuation = await aiNarration(p, 'guide', '', told); if (run !== narrationRun || current !== p)\n    return; ","",1)
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    s=once(s,'import java.util.UUID;','import java.util.UUID;\nimport java.net.HttpURLConnection;\nimport java.net.URL;\nimport java.net.URLEncoder;\nimport java.io.BufferedReader;\nimport java.io.InputStream;\nimport java.io.InputStreamReader;\nimport java.io.OutputStream;\nimport org.json.JSONArray;\nimport org.json.JSONObject;')
    s=once(s,'        webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");','        webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");\n        webView.addJavascriptInterface(new NativeAiBridge(), "GeoVisionAI");')
    anchor='    private class NativeTtsBridge {'
    ai=r'''    private String readAll(InputStream in) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(in, "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        return sb.toString();
    }

    private String callGeminiModel(String model, String key, String prompt) throws Exception {
        URL url = new URL("https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + URLEncoder.encode(key, "UTF-8"));
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setRequestMethod("POST");
        c.setConnectTimeout(10000);
        c.setReadTimeout(18000);
        c.setDoOutput(true);
        c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
        JSONObject req = new JSONObject();
        JSONArray contents = new JSONArray();
        JSONObject item = new JSONObject();
        JSONArray parts = new JSONArray();
        parts.put(new JSONObject().put("text", prompt));
        item.put("role", "user").put("parts", parts);
        contents.put(item);
        req.put("contents", contents);
        JSONObject cfg = new JSONObject().put("temperature", 0.55).put("maxOutputTokens", 1400);
        req.put("generationConfig", cfg);
        byte[] body = req.toString().getBytes("UTF-8");
        c.setFixedLengthStreamingMode(body.length);
        try (OutputStream os = c.getOutputStream()) { os.write(body); }
        int code = c.getResponseCode();
        InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
        String raw = in == null ? "" : readAll(in);
        if (code < 200 || code >= 300) throw new Exception("Gemini HTTP " + code + " " + raw);
        JSONObject root = new JSONObject(raw);
        JSONArray cand = root.optJSONArray("candidates");
        if (cand == null || cand.length() == 0) return "";
        JSONObject content = cand.optJSONObject(0).optJSONObject("content");
        JSONArray outParts = content == null ? null : content.optJSONArray("parts");
        if (outParts == null) return "";
        StringBuilder text = new StringBuilder();
        for (int i=0;i<outParts.length();i++) {
            String t = outParts.optJSONObject(i).optString("text", "");
            if (!t.isEmpty()) { if (text.length()>0) text.append(' '); text.append(t); }
        }
        return text.toString().trim();
    }

    private String callGemini(String key, String prompt) throws Exception {
        Exception last = null;
        for (String model : new String[]{"gemini-2.5-flash","gemini-2.0-flash"}) {
            try {
                String text = callGeminiModel(model,key,prompt);
                if (text.length() > 80) return text;
            } catch (Exception e) { last = e; }
        }
        if (last != null) throw last;
        return "";
    }

    private class NativeAiBridge {
        @JavascriptInterface public void generate(String key, String prompt, String requestId) {
            final String k = key == null ? "" : key.trim();
            final String p = prompt == null ? "" : prompt;
            final String id = requestId == null ? "" : requestId;
            new Thread(() -> {
                String text = "";
                String error = "";
                try {
                    if (k.isEmpty()) throw new Exception("Chiave AI assente");
                    text = callGemini(k,p);
                    if (text.isEmpty()) throw new Exception("Risposta AI vuota");
                } catch (Exception e) { error = e.getMessage() == null ? e.toString() : e.getMessage(); }
                final String js = "window.gvNativeAiResult&&window.gvNativeAiResult(" + JSONObject.quote(id) + "," + JSONObject.quote(text) + "," + JSONObject.quote(error) + ")";
                main.post(() -> { if (webView != null) webView.evaluateJavascript(js, null); });
            }, "GeoVisionAI").start();
        }
    }

'''
    s=once(s,anchor,ai+anchor)
    JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists(): patch_html(OUT)
patch_java()
print('LAB020 native AI audioguide bridge applied')
