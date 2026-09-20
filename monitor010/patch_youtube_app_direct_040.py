from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
MAN=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'


def patch_html(path):
    s=path.read_text(encoding='utf-8')
    anchor='function launchPlatform(p)'
    assert anchor in s, 'launchPlatform not found'

    helper="""function gv040OpenYouTubeApp(q){
  try{
    if(window.GeoVisionYouTube&&typeof window.GeoVisionYouTube.openSearch==='function'){
      window.GeoVisionYouTube.openSearch(String(q||''));
      return true;
    }
  }catch(_){}
  return false;
}
"""
    if 'function gv040OpenYouTubeApp(q)' not in s:
        s=s.replace(anchor,helper+'\n'+anchor,1)

    # LAB037 still builds a normal https YouTube search URL. Replace only that
    # YouTube branch: search now goes to the native YouTube bridge and never to a browser.
    old="const u = p === 'youtube' ? `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` :"
    new="if (p === 'youtube') { gv040OpenYouTubeApp(q); return; }\nconst u ="
    assert old in s, 'LAB037 YouTube web search branch not found'
    s=s.replace(old,new,1)

    assert 'function gv040OpenYouTubeApp(q)' in s
    assert "if (p === 'youtube') { gv040OpenYouTubeApp(q); return; }" in s
    assert "p === 'youtube' ? `https://www.youtube.com/results?search_query=" not in s
    path.write_text(s,encoding='utf-8')


def replace_balanced_class(s, signature, replacement):
    start=s.find(signature)
    assert start>=0, signature+' not found'
    brace=s.find('{',start)
    assert brace>=0, 'opening brace not found for '+signature
    depth=0
    end=None
    for i in range(brace,len(s)):
        c=s[i]
        if c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    assert end is not None, 'closing brace not found for '+signature
    return s[:start]+replacement+s[end:]


def patch_java():
    s=J.read_text(encoding='utf-8')

    bridge=r'''private class YouTubeExternalBridge {
        @JavascriptInterface public void openSearch(String query){
            main.post(() -> {
                String q=query==null?"":query.trim();
                if(q.isEmpty()) return;
                showReturnBubble();
                try{
                    // Primary path: ask the installed YouTube app to perform the search itself.
                    Intent search=new Intent(Intent.ACTION_SEARCH);
                    search.setPackage("com.google.android.youtube");
                    search.putExtra(android.app.SearchManager.QUERY,q);
                    startActivity(search);
                    return;
                }catch(Exception searchUnavailable){
                    try{
                        // Compatibility path: still force the installed YouTube app.
                        // There is deliberately NO generic browser fallback in LAB040.
                        String url="https://www.youtube.com/results?search_query="+android.net.Uri.encode(q);
                        Intent yt=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        yt.setPackage("com.google.android.youtube");
                        yt.addCategory(Intent.CATEGORY_BROWSABLE);
                        startActivity(yt);
                        return;
                    }catch(Exception appMissing){
                        android.widget.Toast.makeText(MainActivity.this,
                                "App YouTube non disponibile",
                                android.widget.Toast.LENGTH_SHORT).show();
                    }
                }
            });
        }
    }'''

    s=replace_balanced_class(s,'private class YouTubeExternalBridge',bridge)

    # Safety: preserve LAB037 return implementation exactly; LAB040 changes only YouTube opening.
    assert 'private void returnToGeoVision()' in s
    assert 'Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP' in s
    assert 'getApplicationContext().startActivity(back);' in s
    assert 'task.moveToFront()' not in s and 'ActivityManager.AppTask' not in s

    J.write_text(s,encoding='utf-8')


def patch_manifest():
    s=MAN.read_text(encoding='utf-8')
    pkg='<package android:name="com.google.android.youtube"/>'
    if pkg not in s:
        assert '</queries>' in s, 'queries block not found'
        s=s.replace('</queries>',pkg+'</queries>',1)
    MAN.write_text(s,encoding='utf-8')


patch_html(H1)
if H2.exists(): patch_html(H2)
patch_java()
patch_manifest()
print('LAB040 direct YouTube app search applied; no browser fallback')
