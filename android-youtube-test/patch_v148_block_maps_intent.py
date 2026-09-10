from pathlib import Path

html_path=Path('android-youtube-test/app/src/main/assets/geovision.html')
java_path=Path('android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java')
html=html_path.read_text(encoding='utf-8')
java=java_path.read_text(encoding='utf-8')

# v148: il componente Google della lista territoriale prova ad aprire intent://maps
# anche quando il risultato viene selezionato. In WebView questo produce
# ERR_UNKNOWN_URL_SCHEME e copre il viewer GeoVision. Salviamo il Place selezionato
# e blocchiamo SOLO gli intent Google Maps a livello Android, riprendendo poi
# l'apertura foto interna. Nessun autoplay/Radar, nessuna modifica alla scheda Google.

old_listener="""search.addEventListener('gmp-select', (event) => {\n            try{ event.preventDefault?.(); }catch(e){}\n            void gvV147OpenTerritorySelectedPlace(event?.place);\n        });"""
new_listener="""search.addEventListener('gmp-select', (event) => {\n            const selected=event?.place||null;\n            window.gvV148LastTerritoryPlace=selected;\n            try{ event.preventDefault?.(); }catch(e){}\n            try{ event.stopPropagation?.(); }catch(e){}\n            if(selected) void gvV147OpenTerritorySelectedPlace(selected);\n        });"""
if old_listener not in html:
    raise SystemExit('v148 patch aborted: v147 gmp-select listener not found')
html=html.replace(old_listener,new_listener,1)

resume_helper=r'''
window.gvV148LastTerritoryPlace=window.gvV148LastTerritoryPlace||null;
window.gvV148ResumeSelectedTerritoryPlace=function(){
    const selected=window.gvV148LastTerritoryPlace;
    if(!selected) return false;
    try{ void gvV147OpenTerritorySelectedPlace(selected); return true; }
    catch(e){ console.log('GeoVision v148 resume selected place failed',e?.message||e); return false; }
};
'''
anchor='function googlePlaceUrl(p) {'
if 'window.gvV148ResumeSelectedTerritoryPlace=function()' not in html:
    if anchor not in html:
        raise SystemExit('v148 patch aborted: googlePlaceUrl anchor not found')
    html=html.replace(anchor,resume_helper+'\n'+anchor,1)

client_anchor='''        webView.setWebViewClient(new WebViewClientCompat() {\n            @Override\n            public android.webkit.WebResourceResponse shouldInterceptRequest('''
client_new='''        webView.setWebViewClient(new WebViewClientCompat() {\n            private boolean gvV148HandleSpecialUrl(WebView view, String url) {\n                if (url == null) return false;\n                String lower = url.toLowerCase(java.util.Locale.ROOT);\n                if (lower.startsWith("intent://") && lower.contains("google.com/maps")) {\n                    android.util.Log.i("GeoVisionUI", "Blocked Google Maps intent: " + url);\n                    main.postDelayed(() -> {\n                        if (view != null) {\n                            view.evaluateJavascript(\n                                    "window.gvV148ResumeSelectedTerritoryPlace&&window.gvV148ResumeSelectedTerritoryPlace()",\n                                    null);\n                        }\n                    }, 60);\n                    return true;\n                }\n                return false;\n            }\n\n            @Override\n            public boolean shouldOverrideUrlLoading(\n                    WebView view, android.webkit.WebResourceRequest request) {\n                String url = request != null && request.getUrl() != null\n                        ? request.getUrl().toString() : "";\n                return gvV148HandleSpecialUrl(view, url);\n            }\n\n            @Override\n            @SuppressWarnings("deprecation")\n            public boolean shouldOverrideUrlLoading(WebView view, String url) {\n                return gvV148HandleSpecialUrl(view, url);\n            }\n\n            @Override\n            public android.webkit.WebResourceResponse shouldInterceptRequest('''
if 'private boolean gvV148HandleSpecialUrl(WebView view, String url)' not in java:
    if client_anchor not in java:
        raise SystemExit('v148 patch aborted: WebViewClient anchor not found')
    java=java.replace(client_anchor,client_new,1)

html_path.write_text(html,encoding='utf-8')
java_path.write_text(java,encoding='utf-8')
print('Applied v148 Google Maps intent guard + selected-place resume')