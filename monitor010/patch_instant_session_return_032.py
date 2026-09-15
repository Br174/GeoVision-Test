from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
H=ROOT/'out/LAB_012_FAILOVER.html'
M=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'

def pj():
 s=J.read_text(encoding='utf-8')
 # Make the overlay a small circular launcher: it recalls the retained task; it is not Back navigation.
 s=s.replace('SpannableString label=new SpannableString("●  GeoVision");','SpannableString label=new SpannableString("●");')
 s=s.replace('label.setSpan(new ForegroundColorSpan(0xff1677ff),0,1,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);','label.setSpan(new ForegroundColorSpan(0xff1677ff),0,1,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);')
 s=s.replace('b.setText(label); b.setTextSize(15); b.setGravity(Gravity.CENTER);','b.setText(label); b.setTextSize(24); b.setGravity(Gravity.CENTER);')
 s=s.replace('int h=(int)(46*getResources().getDisplayMetrics().density);\n            int w=(int)(150*getResources().getDisplayMetrics().density);','int h=(int)(46*getResources().getDisplayMetrics().density);\n            int w=h;')
 # Return directly to the already-running task/activity. Never navigate WebView history.
 old='''Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){
            back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(back);
        }'''
 new='''ActivityManager am=(ActivityManager)getSystemService(ACTIVITY_SERVICE);
        if(am!=null){
            for(ActivityManager.AppTask task:am.getAppTasks()){
                try{ task.moveToFront(); return; }catch(Exception ignored){}
            }
        }
        Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){ back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP); startActivity(back); }'''
 s=s.replace(old,new,1)
 if 'import android.app.ActivityManager;' not in s:s=s.replace('import android.app.Activity;','import android.app.Activity;\nimport android.app.ActivityManager;')
 # Centralize overlay activation in the native external URL bridge so Photos/Google/YT/social all get it.
 # Insert before every ACTION_VIEW start from this activity, avoiding dependence on individual JS buttons.
 s=s.replace('startActivity(intent);','showReturnBubble();\n                startActivity(intent);')
 s=s.replace('startActivity(i);','showReturnBubble();\n                startActivity(i);')
 J.write_text(s,encoding='utf-8')

def ph():
 s=H.read_text(encoding='utf-8')
 # Also catch generic external anchors before navigation; native bridge remains authoritative.
 hook=r'''<script id="gv032-external-return">
document.addEventListener('click',function(e){
 const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;if(!a)return;
 const u=(a.getAttribute('href')||'').trim();
 if(/^https?:\/\//i.test(u)){try{if(window.GeoVisionReturnBubble)GeoVisionReturnBubble.show();}catch(_){}}
},true);
</script>
'''
 if 'gv032-external-return' not in s:s=s.replace('</body>',hook+'</body>',1)
 H.write_text(s,encoding='utf-8')

def pm():
 s=M.read_text(encoding='utf-8')
 # Keep one retained MainActivity task; do not clear/recreate it on return.
 if 'android:name=".MainActivity"' in s and 'android:launchMode="singleTask"' not in s:
  s=s.replace('android:name=".MainActivity"','android:name=".MainActivity" android:launchMode="singleTask"',1)
 M.write_text(s,encoding='utf-8')
pj();ph();pm();print('LAB032 instant persistent session return applied')
