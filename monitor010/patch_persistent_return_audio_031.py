from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
MAN=ROOT/'android-youtube-test/app/src/main/AndroidManifest.xml'

def patch_java():
 s=JAVA.read_text(encoding='utf-8')
 s=s.replace('import android.media.AudioManager;', 'import android.media.AudioManager;\nimport android.media.AudioAttributes;\nimport android.media.AudioFocusRequest;') if 'import android.media.AudioManager;' in s else s.replace('import android.net.Uri;','import android.net.Uri;\nimport android.media.AudioManager;\nimport android.media.AudioAttributes;\nimport android.media.AudioFocusRequest;')
 s=s.replace('import android.graphics.drawable.GradientDrawable;','import android.graphics.drawable.GradientDrawable;\nimport android.text.SpannableString;\nimport android.text.Spanned;\nimport android.text.style.ForegroundColorSpan;')
 s=s.replace('b.setText("●  GeoVision"); b.setTextSize(16); b.setGravity(Gravity.CENTER);', '''SpannableString label=new SpannableString("●  GeoVision");
            label.setSpan(new ForegroundColorSpan(0xff1677ff),0,1,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            b.setText(label); b.setTextSize(15); b.setGravity(Gravity.CENTER);''',1)
 s=s.replace('int h=(int)(52*getResources().getDisplayMetrics().density);\n            int w=(int)(168*getResources().getDisplayMetrics().density);','int h=(int)(46*getResources().getDisplayMetrics().density);\n            int w=(int)(150*getResources().getDisplayMetrics().density);',1)
 old='''Intent back=new Intent(this,MainActivity.class);
        back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(back);'''
 new='''Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){
            back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(back);
        }'''
 s=s.replace(old,new,1)
 marker='    private void initTts() {'
 audio=r'''    private AudioManager gvAudioManager;
    private AudioFocusRequest gvAudioFocusRequest;
    private final AudioManager.OnAudioFocusChangeListener gvAudioFocusListener = focus -> {
        if(focus==AudioManager.AUDIOFOCUS_LOSS || focus==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT){ stopNative(); }
    };
    private void gvRequestNarrationAudioFocus(){
        try{
            gvAudioManager=(AudioManager)getSystemService(AUDIO_SERVICE);
            if(android.os.Build.VERSION.SDK_INT>=26){
                AudioAttributes aa=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build();
                gvAudioFocusRequest=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN).setAudioAttributes(aa).setOnAudioFocusChangeListener(gvAudioFocusListener).build();
                gvAudioManager.requestAudioFocus(gvAudioFocusRequest);
            }else gvAudioManager.requestAudioFocus(gvAudioFocusListener,AudioManager.STREAM_MUSIC,AudioManager.AUDIOFOCUS_GAIN);
        }catch(Exception ignored){}
    }
    private void gvAbandonNarrationAudioFocus(){
        try{if(gvAudioManager==null)return;if(android.os.Build.VERSION.SDK_INT>=26&&gvAudioFocusRequest!=null)gvAudioManager.abandonAudioFocusRequest(gvAudioFocusRequest);else gvAudioManager.abandonAudioFocus(gvAudioFocusListener);}catch(Exception ignored){}
    }

'''
 if 'gvRequestNarrationAudioFocus' not in s:s=s.replace(marker,audio+marker,1)
 speak='private void speakNative(String text, boolean append) {'
 if speak in s and 'gvRequestNarrationAudioFocus();' not in s[s.find(speak):s.find(speak)+250]:s=s.replace(speak,speak+'\n        gvRequestNarrationAudioFocus();',1)
 s=s.replace('stopNative();\n        hideReturnBubble();','stopNative();\n        gvAbandonNarrationAudioFocus();\n        hideReturnBubble();',1)
 JAVA.write_text(s,encoding='utf-8')

def patch_manifest():
 s=MAN.read_text(encoding='utf-8')
 # Enforce singleTask on MainActivity even when the baseline already declares another launchMode.
 activity=re.search(r'<activity\b[^>]*android:name="\.MainActivity"[^>]*>',s,re.S)
 if not activity: raise SystemExit('MainActivity manifest declaration not found')
 tag=activity.group(0)
 if 'android:launchMode=' in tag:
  tag=re.sub(r'android:launchMode="[^"]*"','android:launchMode="singleTask"',tag,1)
 else:
  tag=tag[:-1]+' android:launchMode="singleTask">'
 s=s[:activity.start()]+tag+s[activity.end():]
 MAN.write_text(s,encoding='utf-8')

patch_java();patch_manifest()
print('LAB031: persistent Activity/WebView return + blue compact bubble + audio focus')
