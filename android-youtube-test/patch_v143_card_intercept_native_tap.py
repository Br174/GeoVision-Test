from pathlib import Path

html_path=Path('android-youtube-test/app/src/main/assets/geovision.html')
java_path=Path('android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java')
s=html_path.read_text(encoding='utf-8')
j=java_path.read_text(encoding='utf-8')

# v143: intercetta direttamente renderOfficialGoogleCard, indipendentemente dal caller.
# Disattiva il vecchio hook v142 su openPlace. Il tap usa la viewport reale WebView,
# non devicePixelRatio. I messaggi di diagnosi sono Toast Android nativi.
old_hook='void enrichNarration(p); await cardPromise; void gvAutoOpenNativeGooglePhotoV142(p);'
new_hook='void enrichNarration(p); await cardPromise;'
if old_hook not in s:
    raise SystemExit('v143 patch aborted: v142 openPlace hook not found')
s=s.replace(old_hook,new_hook,1)

helper=r'''
async function gvV143TapOfficialGooglePhoto(p){
    const token=(window.gvV143TapToken=(window.gvV143TapToken||0)+1);
    const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
    try{
        window.GeoVisionNativeUI?.showStatus?.('V143: scheda Google intercettata');
    }catch(e){}

    for(let attempt=0; attempt<28; attempt++){
        if(token!==window.gvV143TapToken || current!==p) return;
        const host=document.getElementById('googleCardHost');
        const body=document.getElementById('sheetBody');
        if(host && host.isConnected){
            try{
                let r=host.getBoundingClientRect();
                if(r.width>240 && r.height>360){
                    // La foto ufficiale, come da scheda testata, occupa la zona centrale
                    // del riquadro Google. Portiamo quel punto dentro la viewport.
                    let wantedY=r.top + r.height*0.50;
                    if(body && wantedY>window.innerHeight-120){
                        body.scrollTop += wantedY-(window.innerHeight*0.58);
                        await sleep(260);
                        r=host.getBoundingClientRect();
                        wantedY=r.top + r.height*0.50;
                    }
                    const x=r.left + r.width*0.28;
                    const y=wantedY;
                    if(x>20 && x<window.innerWidth-20 && y>80 && y<window.innerHeight-70){
                        if(window.GeoVisionNativeUI && typeof window.GeoVisionNativeUI.tapViewportCss==='function'){
                            try{ window.GeoVisionNativeUI.showStatus('V143: tap foto inviato'); }catch(e){}
                            console.log('GeoVision v143 native viewport tap',attempt,x,y,window.innerWidth,window.innerHeight,r.width,r.height);
                            window.GeoVisionNativeUI.tapViewportCss(x,y,window.innerWidth,window.innerHeight);
                            return;
                        }
                        try{ window.GeoVisionNativeUI?.showStatus?.('V143: bridge Android non disponibile'); }catch(e){}
                        return;
                    }
                }
            }catch(e){ console.log('GeoVision v143 geometry',e?.message||e); }
        }
        await sleep(300);
    }
    try{ window.GeoVisionNativeUI?.showStatus?.('V143: area foto non trovata'); }catch(e){}
}
'''
anchor='async function renderOfficialGoogleCard(p) {'
if anchor not in s:
    raise SystemExit('v143 patch aborted: renderOfficialGoogleCard anchor not found')
if 'function gvV143TapOfficialGooglePhoto(p)' not in s:
    replacement=helper+'\n'+anchor+' void gvV143TapOfficialGooglePhoto(p);'
    s=s.replace(anchor,replacement,1)

# Aggiunge metodi v143 al bridge Android esistente.
java_anchor='''    private class NativeUiBridge {\n        @JavascriptInterface\n        public void tapAtCss(double xCss, double yCss, double devicePixelRatio) {'''
if java_anchor not in j:
    raise SystemExit('v143 patch aborted: NativeUiBridge anchor not found')

insert='''    private class NativeUiBridge {\n        @JavascriptInterface\n        public void showStatus(String text) {\n            final String msg = (text == null || text.trim().isEmpty()) ? "GeoVision" : text;\n            main.post(() -> android.widget.Toast.makeText(MainActivity.this, msg, android.widget.Toast.LENGTH_SHORT).show());\n        }\n\n        @JavascriptInterface\n        public void tapViewportCss(double xCss, double yCss, double viewportWidthCss, double viewportHeightCss) {\n            main.post(() -> {\n                if (webView == null) return;\n                double vw = viewportWidthCss;\n                double vh = viewportHeightCss;\n                if (!Double.isFinite(vw) || vw < 100.0) vw = webView.getWidth();\n                if (!Double.isFinite(vh) || vh < 100.0) vh = webView.getHeight();\n                final float x = (float) (xCss * ((double) webView.getWidth() / vw));\n                final float y = (float) (yCss * ((double) webView.getHeight() / vh));\n                android.util.Log.i("GeoVisionUI", "V143 viewport tap css=" + xCss + "," + yCss + " native=" + x + "," + y);\n                dispatchNativeTap(x, y);\n            });\n        }\n\n        @JavascriptInterface\n        public void tapAtCss(double xCss, double yCss, double devicePixelRatio) {'''
j=j.replace(java_anchor,insert,1)

html_path.write_text(s,encoding='utf-8')
java_path.write_text(j,encoding='utf-8')
print('Applied v143 direct card intercept/native viewport tap',len(s),len(j))
