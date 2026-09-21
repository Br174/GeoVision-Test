from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
MAN=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'


def patch_html(path):
    s=path.read_text(encoding='utf-8')

    # LAB037 is the proven base. Re-enable the already-existing native YouTube bridge
    # only for the YouTube button; every other platform keeps LAB037 behavior.
    old="function launchPlatform(p) {\n  if(p === 'youtube') gv029ShowReturnBubble();"
    new="function launchPlatform(p) {\n  if(p === 'youtube' && gv035OpenYouTube(social)) return;"
    assert old in s, 'LAB037 launchPlatform anchor not found'
    s=s.replace(old,new,1)

    # The bridge helper must already come from LAB035 in the proven chain.
    assert 'function gv035OpenYouTube(q)' in s
    assert "if(p === 'youtube' && gv035OpenYouTube(social)) return;" in s
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
                    Intent search=new Intent(Intent.ACTION_SEARCH);
                    search.setPackage("com.google.android.youtube");
                    search.putExtra(android.app.SearchManager.QUERY,q);
                    startActivity(search);
                    return;
                }catch(Exception searchUnavailable){
                    try{
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

    # Preserve the already-verified LAB037 return implementation verbatim.
    assert 'private void returnToGeoVision()' in s
    assert 'private void hideReturnBubble()' in s
    assert 'Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP' in s
    assert 'getApplicationContext().startActivity(back);' in s
    assert '@Override protected void onResume(){super.onResume();hideReturnBubble();' in s
    assert 'task.moveToFront()' not in s and 'ActivityManager.AppTask' not in s

    # Direct-app rule: the YouTube bridge has no generic browser intent.
    a=s.index('private class YouTubeExternalBridge')
    b=s.index('private void initTts()',a)
    section=s[a:b]
    assert 'search.setPackage("com.google.android.youtube")' in section
    assert 'yt.setPackage("com.google.android.youtube")' in section
    assert 'Intent web=' not in section

    J.write_text(s,encoding='utf-8')


def patch_manifest():
    s=MAN.read_text(encoding='utf-8')
    pkg='<package android:name="com.google.android.youtube"/>'
    if pkg not in s:
        assert '</queries>' in s, 'queries block not found after LAB037 prepare chain'
        s=s.replace('</queries>',pkg+'</queries>',1)
    assert pkg in s
    MAN.write_text(s,encoding='utf-8')


patch_html(H1)
if H2.exists():
    patch_html(H2)
patch_java()
patch_manifest()
print('LAB041: direct native YouTube search applied on proven LAB037 base')
