from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def html(path):
 s=path.read_text(encoding='utf-8')
 anchor='function launchPlatform(p)'
 assert anchor in s
 helper="""function gv035OpenYouTube(q){
  try{
    if(window.GeoVisionYouTube&&typeof window.GeoVisionYouTube.openSearch==='function'){
      window.GeoVisionYouTube.openSearch(String(q||'')); return true;
    }
  }catch(_){}
  return false;
}
"""
 if 'function gv035OpenYouTube(q)' not in s:s=s.replace(anchor,helper+'\n'+anchor,1)
 # Intercept YouTube at the start of the existing platform launcher. Other platforms unchanged.
 s=s.replace('function launchPlatform(p) {','function launchPlatform(p) {\n  if(p === \'youtube\' && gv035OpenYouTube(social)) return;',1)
 path.write_text(s,encoding='utf-8')

def java():
 s=J.read_text(encoding='utf-8')
 anchor='webView.addJavascriptInterface(new ReturnBubbleBridge(), "GeoVisionReturnBubble");'
 assert anchor in s, 'Return bubble bridge missing'
 s=s.replace(anchor,anchor+'\n        webView.addJavascriptInterface(new YouTubeExternalBridge(), "GeoVisionYouTube");',1)
 marker='    private void initTts() {'
 bridge=r'''    private class YouTubeExternalBridge {
        @JavascriptInterface public void openSearch(String query){
            main.post(() -> {
                String q=query==null?"":query.trim();
                String url="https://www.youtube.com/results?search_query="+android.net.Uri.encode(q);
                showReturnBubble();
                try{
                    Intent yt=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    yt.setPackage("com.google.android.youtube");
                    yt.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(yt);
                }catch(Exception noYoutube){
                    try{
                        Intent web=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        web.addCategory(Intent.CATEGORY_BROWSABLE);
                        startActivity(web);
                    }catch(Exception ignored){}
                }
            });
        }
    }

'''
 assert marker in s
 if 'class YouTubeExternalBridge' not in s:s=s.replace(marker,bridge+marker,1)
 J.write_text(s,encoding='utf-8')

html(H1)
if H2.exists():html(H2)
java()
print('LAB035 native YouTube external bridge + return bubble applied')
