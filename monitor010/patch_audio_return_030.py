from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def patch_html(path):
 s=path.read_text(encoding='utf-8')
 # LAB028 click hook stopped narration on media links before actual external audio started: remove it.
 start="document.addEventListener('click',e=>{\n  const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;"
 i=s.find(start)
 if i>=0:
  j=s.find("},true);",i)
  if j>=0:s=s[:i]+s[j+8:]
 # Ask native layer to preserve exact sheet state before any external destination.
 s=s.replace("function gv029ShowReturnBubble(){\n  try{", "function gv029ShowReturnBubble(){\n  try{ if(window.GeoVisionReturnBubble&&typeof window.GeoVisionReturnBubble.remember==='function') window.GeoVisionReturnBubble.remember(); }catch(_){}\n  try{",1)
 # Closing the Google sheet must stop its narration.
 old="$('#sheetClose').onclick ="
 if old in s and 'gv030StopOnSheetClose' not in s:
  s=s.replace(old,"const gv030StopOnSheetClose=()=>{try{if(window.GeoVisionTTS)window.GeoVisionTTS.stop();}catch(_){}};\n  "+old,1)
  # capture close button independently, leaving existing handler untouched
  s=s.replace("</body>","<script>document.getElementById('sheetClose')?.addEventListener('click',()=>{try{window.GeoVisionTTS?.stop();}catch(_){}},true);</script></body>",1)
 path.write_text(s,encoding='utf-8')

def patch_java():
 s=JAVA.read_text(encoding='utf-8')
 # Capsule instead of square TextView; still draggable.
 s=s.replace('import android.widget.TextView;','import android.widget.TextView;\nimport android.graphics.drawable.GradientDrawable;')
 s=s.replace('b.setText("↩"); b.setTextSize(25); b.setGravity(Gravity.CENTER);\n            b.setTextColor(0xff1677ff); b.setBackgroundColor(0xffffffff);\n            int size=(int)(54*getResources().getDisplayMetrics().density);\n            WindowManager.LayoutParams lp=new WindowManager.LayoutParams(size,size,',
'''b.setText("●  GeoVision"); b.setTextSize(16); b.setGravity(Gravity.CENTER);\n            b.setTextColor(0xff101828);\n            GradientDrawable bg=new GradientDrawable(); bg.setColor(0xffffffff);\n            bg.setCornerRadius(32*getResources().getDisplayMetrics().density); b.setBackground(bg);\n            int h=(int)(52*getResources().getDisplayMetrics().density);\n            int w=(int)(168*getResources().getDisplayMetrics().density);\n            WindowManager.LayoutParams lp=new WindowManager.LayoutParams(w,h,''',1)
 s=s.replace('lp.x=getResources().getDisplayMetrics().widthPixels-size-(int)(12*getResources().getDisplayMetrics().density);\n            lp.y=(getResources().getDisplayMetrics().heightPixels-size)/2;',
             'lp.x=getResources().getDisplayMetrics().widthPixels-w-(int)(12*getResources().getDisplayMetrics().density);\n            lp.y=(getResources().getDisplayMetrics().heightPixels-h)/2;',1)
 # Do not hide bubble merely because permission screen/external transition resumes; hide on explicit return.
 s=s.replace('@Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}',
             '@Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}',1)
 # Return must reorder the SAME activity instance; do not recreate state.
 s=s.replace('back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);',
             'back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP|Intent.FLAG_ACTIVITY_CLEAR_TOP);',1)
 # Bridge remember is deliberately native/no-op: activity+WebView are retained in task.
 s=s.replace('@JavascriptInterface public void show(){showReturnBubble();}', '@JavascriptInterface public void remember(){}\n        @JavascriptInterface public void show(){showReturnBubble();}',1)
 # True app destruction must stop TTS immediately.
 s=s.replace('protected void onDestroy() {\n        hideReturnBubble();','protected void onDestroy() {\n        stopNative();\n        hideReturnBubble();',1)
 JAVA.write_text(s,encoding='utf-8')

patch_html(HTML)
if OUT.exists():patch_html(OUT)
patch_java()
print('LAB030 capsule overlay + preserved Google sheet + corrected TTS lifecycle')
