from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
MAN=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'

def patch_html(path):
    s=path.read_text(encoding='utf-8')
    anchor='function launchPlatform(p)'
    assert anchor in s
    helper="""function gv029ShowReturnBubble(){
  try{ if(window.GeoVisionReturnBubble&&typeof window.GeoVisionReturnBubble.show==='function') window.GeoVisionReturnBubble.show(); }catch(_){}
}
"""
    if 'function gv029ShowReturnBubble()' not in s:s=s.replace(anchor,helper+'\n'+anchor,1)
    s=s.replace('function launchPlatform(p) {','function launchPlatform(p) {\n  gv029ShowReturnBubble();',1)
    # Facebook uses its own external bridge, so request the bubble there too.
    s=s.replace("function gvFacebookLegacySearch(q){\n    const web=", "function gvFacebookLegacySearch(q){\n    gv029ShowReturnBubble();\n    const web=",1)
    path.write_text(s,encoding='utf-8')

def patch_java():
    s=JAVA.read_text(encoding='utf-8')
    s=s.replace('import android.os.Looper;','import android.os.Looper;\nimport android.provider.Settings;\nimport android.graphics.PixelFormat;\nimport android.view.Gravity;\nimport android.view.WindowManager;\nimport android.widget.TextView;\nimport android.content.Intent;\nimport android.net.Uri;')
    anchor='webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");'
    assert anchor in s
    s=s.replace(anchor,anchor+'\n        webView.addJavascriptInterface(new ReturnBubbleBridge(), "GeoVisionReturnBubble");',1)
    method_anchor='    private void initTts() {'
    code=r'''    private WindowManager gvBubbleWindow;
    private TextView gvReturnBubble;

    private void showReturnBubble() {
        main.post(() -> {
            if (!Settings.canDrawOverlays(this)) {
                try {
                    Intent i=new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:"+getPackageName()));
                    startActivity(i);
                } catch(Exception ignored) {}
                return;
            }
            if(gvReturnBubble!=null)return;
            gvBubbleWindow=(WindowManager)getSystemService(WINDOW_SERVICE);
            TextView b=new TextView(this);
            b.setText("↩"); b.setTextSize(25); b.setGravity(Gravity.CENTER);
            b.setTextColor(0xff1677ff); b.setBackgroundColor(0xffffffff);
            int size=(int)(54*getResources().getDisplayMetrics().density);
            WindowManager.LayoutParams lp=new WindowManager.LayoutParams(size,size,
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                    PixelFormat.TRANSLUCENT);
            lp.gravity=Gravity.END|Gravity.CENTER_VERTICAL;
            lp.x=(int)(12*getResources().getDisplayMetrics().density);
            b.setOnClickListener(v -> {
                hideReturnBubble();
                Intent back=new Intent(this,MainActivity.class);
                back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
                startActivity(back);
            });
            try{gvBubbleWindow.addView(b,lp);gvReturnBubble=b;}catch(Exception ignored){}
        });
    }
    private void hideReturnBubble(){
        main.post(()->{if(gvReturnBubble!=null&&gvBubbleWindow!=null){try{gvBubbleWindow.removeView(gvReturnBubble);}catch(Exception ignored){}gvReturnBubble=null;}});
    }
    private class ReturnBubbleBridge {
        @JavascriptInterface public void show(){showReturnBubble();}
        @JavascriptInterface public void hide(){hideReturnBubble();}
    }

'''
    assert method_anchor in s
    s=s.replace(method_anchor,code+method_anchor,1)
    # Bubble disappears whenever GeoVision itself is foreground again.
    resume='    @Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
    if resume in s:s=s.replace(resume,'    @Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}',1)
    s=s.replace('    protected void onDestroy() {','    protected void onDestroy() {\n        hideReturnBubble();',1)
    JAVA.write_text(s,encoding='utf-8')

def patch_manifest():
    s=MAN.read_text(encoding='utf-8')
    if 'android.permission.SYSTEM_ALERT_WINDOW' not in s:
        s=s.replace('<application','<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>\n    <application',1)
    MAN.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists():patch_html(OUT)
patch_java();patch_manifest()
print('LAB029 floating return bubble added; Google card remains alive underneath')
