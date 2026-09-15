from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'


def patch_html(path):
    s=path.read_text(encoding='utf-8')

    # When the Google sheet is manually closed while shown as a system overlay,
    # detach the live WebView overlay and reveal the external app underneath.
    old="function closeSheet() { narrationRun++; stopSpeech(); $('#videoPicker').classList.remove('show');"
    new="function closeSheet() { try{ if(window.GeoVisionReturnBubble&&typeof window.GeoVisionReturnBubble.dismissOverlay==='function') setTimeout(()=>window.GeoVisionReturnBubble.dismissOverlay(),60); }catch(_){} narrationRun++; stopSpeech(); $('#videoPicker').classList.remove('show');"
    assert old in s, 'closeSheet anchor not found'
    s=s.replace(old,new,1)

    path.write_text(s,encoding='utf-8')


def patch_java():
    s=J.read_text(encoding='utf-8')

    if 'import android.view.ViewGroup;' not in s:
        s=s.replace('import android.view.WindowManager;','import android.view.WindowManager;\nimport android.view.ViewGroup;',1)

    # Replace the old task-return behavior entirely. The dot now shows the SAME live
    # GeoVision WebView as a TYPE_APPLICATION_OVERLAY over YouTube/Google/AI/Shopping.
    old_return='''private void returnToGeoVision(){
        hideReturnBubble();
        Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){
            back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(back);
        }
    }'''
    new_return='''private void returnToGeoVision(){
        gv039ShowLiveCardOverlay();
    }'''
    assert old_return in s, 'LAB036 returnToGeoVision block not found'
    s=s.replace(old_return,new_return,1)

    marker='    private void returnToGeoVision(){\n        gv039ShowLiveCardOverlay();\n    }\n'
    assert marker in s
    code=r'''
    private ViewGroup gv039OriginalParent;
    private ViewGroup.LayoutParams gv039OriginalLayoutParams;
    private int gv039OriginalIndex=-1;
    private WindowManager gv039OverlayWindow;
    private boolean gv039OverlayVisible=false;

    private void gv039ShowLiveCardOverlay(){
        main.post(() -> {
            if(webView==null || gv039OverlayVisible) return;
            if(!Settings.canDrawOverlays(this)){
                showReturnBubble();
                return;
            }
            try{
                android.view.ViewParent parent=webView.getParent();
                if(parent instanceof ViewGroup){
                    gv039OriginalParent=(ViewGroup)parent;
                    gv039OriginalIndex=gv039OriginalParent.indexOfChild(webView);
                    gv039OriginalLayoutParams=webView.getLayoutParams();
                    gv039OriginalParent.removeView(webView);
                }

                gv039OverlayWindow=(WindowManager)getApplicationContext().getSystemService(WINDOW_SERVICE);
                WindowManager.LayoutParams lp=new WindowManager.LayoutParams(
                        WindowManager.LayoutParams.MATCH_PARENT,
                        WindowManager.LayoutParams.MATCH_PARENT,
                        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN |
                                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS |
                                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                        PixelFormat.TRANSLUCENT);
                lp.gravity=Gravity.TOP|Gravity.START;
                gv039OverlayWindow.addView(webView,lp);
                gv039OverlayVisible=true;

                // The original Google sheet never left this WebView: force only its
                // visibility, without navigation, history, reload or reconstruction.
                webView.evaluateJavascript(
                        "try{var s=document.getElementById('sheet');if(s){s.style.transition='';s.style.transform='';s.classList.add('show');}}catch(e){}",
                        null);
                webView.requestFocus();
                webView.bringToFront();
                hideReturnBubble();
            }catch(Exception ignored){
                gv039ReattachWebViewNow();
                showReturnBubble();
            }
        });
    }

    private void gv039DismissLiveCardOverlay(){
        main.post(this::gv039ReattachWebViewNow);
    }

    private void gv039ReattachWebViewNow(){
        if(webView==null) return;
        try{
            if(gv039OverlayVisible && gv039OverlayWindow!=null){
                try{gv039OverlayWindow.removeView(webView);}catch(Exception ignored){}
            }
            if(webView.getParent()==null){
                if(gv039OriginalParent!=null){
                    int index=gv039OriginalIndex;
                    if(index<0 || index>gv039OriginalParent.getChildCount()) index=gv039OriginalParent.getChildCount();
                    if(gv039OriginalLayoutParams!=null) gv039OriginalParent.addView(webView,index,gv039OriginalLayoutParams);
                    else gv039OriginalParent.addView(webView,index);
                }else{
                    setContentView(webView);
                }
            }
        }catch(Exception ignored){}
        gv039OverlayVisible=false;
        gv039OverlayWindow=null;
    }
'''
    s=s.replace(marker,marker+code,1)

    # Extend the already existing JavaScript bridge rather than creating another one.
    old_bridge='''@JavascriptInterface public void remember(){}
        @JavascriptInterface public void show(){showReturnBubble();}
        @JavascriptInterface public void hide(){hideReturnBubble();}'''
    new_bridge='''@JavascriptInterface public void remember(){}
        @JavascriptInterface public void show(){showReturnBubble();}
        @JavascriptInterface public void hide(){hideReturnBubble();}
        @JavascriptInterface public void dismissOverlay(){gv039DismissLiveCardOverlay();}'''
    assert old_bridge in s, 'ReturnBubbleBridge block not found'
    s=s.replace(old_bridge,new_bridge,1)

    # If the user returns to GeoVision normally via recents/launcher, put the live
    # WebView back into the Activity before showing it there.
    old_resume='    @Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
    new_resume='    @Override protected void onResume(){super.onResume();if(gv039OverlayVisible)gv039ReattachWebViewNow();if(keyBoxClient!=null)keyBoxClient.resume();}'
    assert old_resume in s, 'onResume anchor not found'
    s=s.replace(old_resume,new_resume,1)

    # Cleanup must never leave the live WebView attached to an overlay window.
    old_destroy='''protected void onDestroy() {
        stopNative();'''
    new_destroy='''protected void onDestroy() {
        gv039ReattachWebViewNow();
        stopNative();'''
    assert old_destroy in s, 'onDestroy anchor not found'
    s=s.replace(old_destroy,new_destroy,1)

    J.write_text(s,encoding='utf-8')


patch_html(H1)
if H2.exists(): patch_html(H2)
patch_java()
print('LAB039 live card overlay applied: floating dot shows the same live GeoVision WebView over external apps')
