from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

OLD_FACEBOOK="p === 'facebook' ? `https://www.facebook.com/watch/search/?q=${encodeURIComponent(q)}`"

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    helper="""function gvFacebookLegacySearch(q){
    const web=`https://www.facebook.com/watch/search/?q=${encodeURIComponent(q)}`;
    try{
        if(window.GeoVisionFacebook&&typeof window.GeoVisionFacebook.openUrl==='function'){
            window.GeoVisionFacebook.openUrl(web);
            return true;
        }
    }catch(e){}
    openUrl(web);
    return true;
}
"""
    anchor='function launchPlatform(p)'
    assert anchor in s, 'launchPlatform anchor not found'
    if 'function gvFacebookLegacySearch(q)' not in s:
        s=s.replace(anchor,helper+'\n'+anchor,1)
    old_block="""if (p === 'tiktok') {
    const web = `https://www.tiktok.com/search?q=${enc}`, intent = `intent://search/?keyword=${enc}#Intent;scheme=snssdk1233;package=com.zhiliaoapp.musically;S.browser_fallback_url=${encodeURIComponent(web)};end`;
    return openIntent(intent);
} const u = p === 'youtube' ? `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` : p === 'facebook' ? `https://www.facebook.com/watch/search/?q=${encodeURIComponent(q)}` :"""
    new_block="""if (p === 'tiktok') {
    const web = `https://www.tiktok.com/search?q=${enc}`, intent = `intent://search/?keyword=${enc}#Intent;scheme=snssdk1233;package=com.zhiliaoapp.musically;S.browser_fallback_url=${encodeURIComponent(web)};end`;
    return openIntent(intent);
} if (p === 'facebook') return gvFacebookLegacySearch(social);
const u = p === 'youtube' ? `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` :"""
    assert old_block in s, 'Facebook legacy anchor not found'
    s=s.replace(old_block,new_block,1)
    assert "gvFacebookLegacySearch(social)" in s
    assert 'facebook.com/watch/search/?q=' in s
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    anchor='webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");'
    assert anchor in s, 'TTS bridge anchor not found'
    s=s.replace(anchor,anchor+'\n        webView.addJavascriptInterface(new FacebookExternalBridge(), "GeoVisionFacebook");',1)
    method_anchor='    private void initTts() {'
    bridge=r'''    private class FacebookExternalBridge {
        @android.webkit.JavascriptInterface
        public void openUrl(String url) {
            if (url == null || url.trim().isEmpty()) return;
            main.post(() -> {
                try {
                    android.content.Intent intent = new android.content.Intent(
                            android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url));
                    intent.addCategory(android.content.Intent.CATEGORY_BROWSABLE);
                    startActivity(intent);
                } catch (Exception ignored) {
                    try {
                        startActivity(new android.content.Intent(
                                android.content.Intent.ACTION_VIEW, android.net.Uri.parse(url)));
                    } catch (Exception ignoredAgain) { }
                }
            });
        }
    }

'''
    assert method_anchor in s, 'initTts anchor not found'
    s=s.replace(method_anchor,bridge+method_anchor,1)
    assert 'GeoVisionFacebook' in s
    JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists(): patch_html(OUT)
patch_java()
print('LAB023 historical Facebook watch search + Android external bridge restored')
