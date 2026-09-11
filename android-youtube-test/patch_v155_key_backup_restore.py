from pathlib import Path

html_path=Path('android-youtube-test/app/src/main/assets/geovision.html')
java_path=Path('android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java')
s=html_path.read_text(encoding='utf-8')
j=java_path.read_text(encoding='utf-8')

# v155 — ripristino backup/importazione chiavi API su Android.
# Mantiene intatta la logica foto v154 e la scheda Google. Aggiunge soltanto
# i pulsanti Importa chiavi / Esporta chiavi nel pannello API e un bridge Android
# basato su Storage Access Framework: nessun permesso storage aggiuntivo.

footer_old='''<div class="keys-footer">\n  <button id="keysDiagnosticsOpen" class="secondary keys-diagnostic-btn" type="button">Diagnostica servizi</button>\n</div>'''
footer_new='''<div class="keys-footer gv-v155-keys-footer">\n  <button id="keysImportOpen" class="secondary gv-v155-key-btn" type="button">Importa chiavi</button>\n  <button id="keysExportOpen" class="secondary gv-v155-key-btn" type="button">Esporta chiavi</button>\n  <button id="keysDiagnosticsOpen" class="secondary keys-diagnostic-btn" type="button">Diagnostica servizi</button>\n</div>'''
if footer_old not in s:
    raise SystemExit('v155 aborted: keys footer anchor not found')
s=s.replace(footer_old,footer_new,1)

css=r'''
<style id="gvV155KeyBackupStyle">
.gv-v155-keys-footer{display:flex!important;gap:8px!important;flex-wrap:wrap!important;justify-content:flex-end!important;align-items:center!important}
.gv-v155-key-btn{min-height:40px!important;border:1px solid #dbe4ee!important;border-radius:12px!important;background:#f8fbff!important;color:#4f79a8!important;padding:9px 12px!important;font-size:12px!important;font-weight:600!important}
.gv-v155-key-btn:active{transform:scale(.98)}
</style>
'''
if 'id="gvV155KeyBackupStyle"' not in s:
    if '</head>' not in s:
        raise SystemExit('v155 aborted: </head> not found')
    s=s.replace('</head>',css+'\n</head>',1)

js=r'''
function gvV155KeyConfig(){
    return {
        format:'geovision-api-keys-v1',
        exportedAt:new Date().toISOString(),
        googleMaps:[googleMapKeys?.[0]||'',googleMapKeys?.[1]||'',googleMapKeys?.[2]||''],
        googleMapsActiveIndex:Number(googleMapKeyIndex)||0,
        gemini:geminiKey||'',
        youtube:youtubeKey||'',
        youtubeInternal:!!youtubeInternal
    };
}

function gvV155LooseKeyObject(raw){
    raw=String(raw||'').trim();
    if(!raw) throw new Error('File vuoto');
    try{
        const obj=JSON.parse(raw);
        if(obj&&typeof obj==='object') return obj;
    }catch(e){}

    const obj={};
    const anonymous=[];
    for(const line0 of raw.split(/\r?\n/)){
        const line=String(line0||'').trim();
        if(!line||line.startsWith('#')) continue;
        const m=line.match(/^([^:=]+)\s*[:=]\s*(.+)$/);
        if(!m){ anonymous.push(line); continue; }
        const k=m[1].trim().toLowerCase().replace(/[^a-z0-9]+/g,'');
        const v=m[2].trim();
        if(/(google|maps).*(1|uno)$/.test(k)||/^(maps1|google1|googlemaps1)$/.test(k)) obj.maps1=v;
        else if(/(google|maps).*(2|due)$/.test(k)||/^(maps2|google2|googlemaps2)$/.test(k)) obj.maps2=v;
        else if(/(google|maps).*(3|tre)$/.test(k)||/^(maps3|google3|googlemaps3)$/.test(k)) obj.maps3=v;
        else if(k.includes('gemini')) obj.gemini=v;
        else if(k.includes('youtube')) obj.youtube=v;
    }
    if(!Object.keys(obj).length && anonymous.length>=3){
        obj.googleMaps=anonymous.slice(0,3);
        if(anonymous[3]) obj.gemini=anonymous[3];
        if(anonymous[4]) obj.youtube=anonymous[4];
    }
    return obj;
}

function gvV155ExtractKeys(raw){
    const root=gvV155LooseKeyObject(raw);
    const src=(root.keys&&typeof root.keys==='object')?root.keys:root;
    let maps=[];
    if(Array.isArray(src.googleMaps)) maps=src.googleMaps.slice(0,3);
    else if(Array.isArray(src.maps)) maps=src.maps.slice(0,3);
    else maps=[
        src.maps1??src.googleMaps1??src.google_map_1??src.geovision_google_maps_api_key_1??src.geovision_google_maps_api_key??'',
        src.maps2??src.googleMaps2??src.google_map_2??src.geovision_google_maps_api_key_2??'',
        src.maps3??src.googleMaps3??src.google_map_3??src.geovision_google_maps_api_key_3??''
    ];
    while(maps.length<3) maps.push('');
    maps=maps.slice(0,3).map(v=>String(v||'').trim());
    const gemini=String(src.gemini??src.geminiKey??src.geovision_gemini_api_key??'').trim();
    const youtube=String(src.youtube??src.youtubeKey??src.geovision_youtube_api_key??'').trim();
    let active=Number(src.googleMapsActiveIndex??src.activeIndex??src.geovision_google_maps_active_index??0);
    if(!Number.isFinite(active)) active=0;
    active=Math.max(0,Math.min(2,Math.trunc(active)));
    const yi=src.youtubeInternal??src.geovision_youtube_internal;
    const internal=(yi===true||yi===1||yi==='1'||String(yi||'').toLowerCase()==='true');
    if(!maps.some(Boolean)&&!gemini&&!youtube) throw new Error('Nessuna chiave riconosciuta nel file');
    return {maps,gemini,youtube,active,internal};
}

function gvV155SaveImportedKeys(cfg){
    googleMapKeys=cfg.maps.slice(0,3);
    googleMapKeyIndex=cfg.active;
    if(!googleMapKeys[googleMapKeyIndex]){
        const first=googleMapKeys.findIndex(Boolean);
        googleMapKeyIndex=first>=0?first:0;
    }
    googleKey=googleMapKeys[googleMapKeyIndex]||'';
    geminiKey=cfg.gemini||'';
    youtubeKey=cfg.youtube||'';
    youtubeInternal=!!cfg.internal;

    try{
        googleMapKeys.forEach((v,i)=>{
            const k=`geovision_google_maps_api_key_${i+1}`;
            if(v)localStorage.setItem(k,v); else localStorage.removeItem(k);
        });
        if(googleMapKeys[0]) localStorage.setItem('geovision_google_maps_api_key',googleMapKeys[0]);
        else localStorage.removeItem('geovision_google_maps_api_key');
        localStorage.setItem('geovision_google_maps_active_index',String(googleMapKeyIndex));
        if(geminiKey)localStorage.setItem('geovision_gemini_api_key',geminiKey); else localStorage.removeItem('geovision_gemini_api_key');
        if(youtubeKey)localStorage.setItem('geovision_youtube_api_key',youtubeKey); else localStorage.removeItem('geovision_youtube_api_key');
        localStorage.setItem('geovision_youtube_internal',youtubeInternal?'1':'0');
    }catch(e){ throw new Error('Impossibile salvare le chiavi: '+String(e?.message||e)); }

    try{ fillKeysPanel(); }catch(e){}
    try{ syncApiKeysTriggerState(); }catch(e){}
}

window.gvV155ReceiveImportedKeys=function(raw){
    try{
        const cfg=gvV155ExtractKeys(raw);
        gvV155SaveImportedKeys(cfg);
        try{ toast('Chiavi importate. Riavvio GeoVision…'); }catch(e){}
        setTimeout(()=>location.reload(),700);
        return true;
    }catch(e){
        console.log('GeoVision v155 key import failed',e?.message||e);
        try{ toast('Importazione fallita: '+String(e?.message||e)); }catch(x){}
        return false;
    }
};

function gvV155BrowserImportFallback(){
    const input=document.createElement('input');
    input.type='file';
    input.accept='.json,.txt,application/json,text/plain';
    input.style.display='none';
    input.onchange=()=>{
        const f=input.files?.[0];
        if(!f){ input.remove(); return; }
        const r=new FileReader();
        r.onload=()=>{ window.gvV155ReceiveImportedKeys(String(r.result||'')); input.remove(); };
        r.onerror=()=>{ try{toast('Non riesco a leggere il file chiavi.')}catch(e){} input.remove(); };
        r.readAsText(f);
    };
    document.body.appendChild(input);
    input.click();
}

function gvV155ImportKeys(){
    try{
        if(window.GeoVisionKeyBackup&&typeof window.GeoVisionKeyBackup.importKeys==='function'){
            window.GeoVisionKeyBackup.importKeys();
            return;
        }
    }catch(e){}
    gvV155BrowserImportFallback();
}

function gvV155ExportKeys(){
    const payload=JSON.stringify(gvV155KeyConfig(),null,2);
    try{
        if(window.GeoVisionKeyBackup&&typeof window.GeoVisionKeyBackup.exportKeys==='function'){
            window.GeoVisionKeyBackup.exportKeys(payload);
            return;
        }
    }catch(e){}
    try{
        const blob=new Blob([payload],{type:'application/json'});
        const a=document.createElement('a');
        a.href=URL.createObjectURL(blob);
        a.download='GeoVision_chiavi_api.json';
        document.body.appendChild(a); a.click();
        setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},1000);
    }catch(e){ try{toast('Esportazione non disponibile.')}catch(x){} }
}

const gvV155ImportBtn=document.getElementById('keysImportOpen');
if(gvV155ImportBtn) gvV155ImportBtn.onclick=gvV155ImportKeys;
const gvV155ExportBtn=document.getElementById('keysExportOpen');
if(gvV155ExportBtn) gvV155ExportBtn.onclick=gvV155ExportKeys;
'''

js_anchor="$('#keysDiagnosticsOpen').onclick=openKeysDiagnostics;"
if js_anchor not in s:
    raise SystemExit('v155 aborted: diagnostics binding anchor not found')
if 'function gvV155KeyConfig()' in s:
    raise SystemExit('v155 aborted: JS already present')
s=s.replace(js_anchor,js+'\n'+js_anchor,1)

# Android imports.
import_anchor='import android.app.Activity;\n'
java_imports='''import android.app.Activity;\nimport android.content.Intent;\nimport android.net.Uri;\n'''
if import_anchor not in j:
    raise SystemExit('v155 aborted: Java Activity import anchor not found')
j=j.replace(import_anchor,java_imports,1)

io_anchor='import java.util.ArrayList;\n'
io_imports='''import java.io.BufferedReader;\nimport java.io.InputStream;\nimport java.io.InputStreamReader;\nimport java.io.OutputStream;\nimport java.nio.charset.StandardCharsets;\nimport org.json.JSONObject;\n\nimport java.util.ArrayList;\n'''
if io_anchor not in j:
    raise SystemExit('v155 aborted: Java util import anchor not found')
j=j.replace(io_anchor,io_imports,1)

field_anchor='''    private boolean ttsReady = false;\n    private final Handler main = new Handler(Looper.getMainLooper());\n'''
field_new='''    private boolean ttsReady = false;\n    private final Handler main = new Handler(Looper.getMainLooper());\n    private static final int GV_IMPORT_KEYS_REQUEST = 7011;\n    private static final int GV_EXPORT_KEYS_REQUEST = 7012;\n    private String gvPendingKeyExport = null;\n'''
if field_anchor not in j:
    raise SystemExit('v155 aborted: Java field anchor not found')
j=j.replace(field_anchor,field_new,1)

bridge_reg='''        webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");\n        webView.addJavascriptInterface(new NativeUiBridge(), "GeoVisionNativeUI");\n'''
bridge_reg_new='''        webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");\n        webView.addJavascriptInterface(new NativeUiBridge(), "GeoVisionNativeUI");\n        webView.addJavascriptInterface(new NativeKeyBackupBridge(), "GeoVisionKeyBackup");\n'''
if bridge_reg not in j:
    raise SystemExit('v155 aborted: JS interface registration anchor not found')
j=j.replace(bridge_reg,bridge_reg_new,1)

class_anchor='''    private class NativeTtsBridge {\n'''
key_bridge=r'''    private class NativeKeyBackupBridge {
        @JavascriptInterface
        public void importKeys() {
            main.post(() -> {
                try {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("*/*");
                    i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/json", "text/plain", "application/octet-stream"});
                    startActivityForResult(i, GV_IMPORT_KEYS_REQUEST);
                } catch (Exception e) {
                    sendKeyImportError("Impossibile aprire il selettore file");
                }
            });
        }

        @JavascriptInterface
        public void exportKeys(String json) {
            if (json == null) json = "";
            final String payload = json;
            main.post(() -> {
                gvPendingKeyExport = payload;
                try {
                    Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("application/json");
                    i.putExtra(Intent.EXTRA_TITLE, "GeoVision_chiavi_api.json");
                    startActivityForResult(i, GV_EXPORT_KEYS_REQUEST);
                } catch (Exception e) {
                    gvPendingKeyExport = null;
                }
            });
        }
    }

    private void sendKeyImportError(String message) {
        main.post(() -> {
            if (webView == null) return;
            String q = JSONObject.quote(message == null ? "Errore importazione" : message);
            webView.evaluateJavascript("(function(){try{toast(" + q + ")}catch(e){}})()", null);
        });
    }

    private String readUtf8(Uri uri) throws Exception {
        StringBuilder out = new StringBuilder();
        try (InputStream in = getContentResolver().openInputStream(uri);
             BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            char[] buf = new char[4096];
            int n;
            while ((n = br.read(buf)) > 0) {
                out.append(buf, 0, n);
                if (out.length() > 65536) throw new Exception("File chiavi troppo grande");
            }
        }
        return out.toString();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();

        if (requestCode == GV_IMPORT_KEYS_REQUEST) {
            try {
                final String raw = readUtf8(uri);
                final String quoted = JSONObject.quote(raw);
                main.post(() -> {
                    if (webView != null) webView.evaluateJavascript(
                            "window.gvV155ReceiveImportedKeys&&window.gvV155ReceiveImportedKeys(" + quoted + ")", null);
                });
            } catch (Exception e) {
                sendKeyImportError("Errore lettura file chiavi: " + e.getMessage());
            }
            return;
        }

        if (requestCode == GV_EXPORT_KEYS_REQUEST && gvPendingKeyExport != null) {
            try (OutputStream out = getContentResolver().openOutputStream(uri, "w")) {
                if (out == null) throw new Exception("Output non disponibile");
                out.write(gvPendingKeyExport.getBytes(StandardCharsets.UTF_8));
                out.flush();
            } catch (Exception e) {
                android.util.Log.e("GeoVisionKeys", "Export failed", e);
            } finally {
                gvPendingKeyExport = null;
            }
        }
    }

'''
if class_anchor not in j:
    raise SystemExit('v155 aborted: NativeTtsBridge anchor not found')
if 'class NativeKeyBackupBridge' in j:
    raise SystemExit('v155 aborted: Java bridge already present')
j=j.replace(class_anchor,key_bridge+class_anchor,1)

# Static regression checks.
html_checks=[
    'id="keysImportOpen"',
    '>Importa chiavi<',
    'id="keysExportOpen"',
    'function gvV155KeyConfig()',
    'window.gvV155ReceiveImportedKeys',
    'geovision_google_maps_api_key_1',
    'geovision_gemini_api_key',
    'geovision_youtube_api_key',
    'async function gvV154LocalityPhotos(p)',
    'GeoVision v149 selected territory -> official Place media'
]
java_checks=[
    'new NativeKeyBackupBridge()',
    'GV_IMPORT_KEYS_REQUEST = 7011',
    'Intent.ACTION_OPEN_DOCUMENT',
    'Intent.ACTION_CREATE_DOCUMENT',
    'window.gvV155ReceiveImportedKeys',
    'JSONObject.quote(raw)'
]
missing=[x for x in html_checks if x not in s]+[x for x in java_checks if x not in j]
if missing:
    raise SystemExit('v155 static checks failed: '+repr(missing))
if s.count('id="keysImportOpen"')!=1 or s.count('function gvV155KeyConfig()')!=1:
    raise SystemExit('v155 duplicate HTML/JS regression')
if j.count('class NativeKeyBackupBridge')!=1 or j.count('GV_IMPORT_KEYS_REQUEST = 7011')!=1:
    raise SystemExit('v155 duplicate Java bridge regression')

html_path.write_text(s,encoding='utf-8')
java_path.write_text(j,encoding='utf-8')
print('Applied v155 API key backup/restore:',html_path,java_path)
print('v155 key backup static checks: 16/16 OK')
