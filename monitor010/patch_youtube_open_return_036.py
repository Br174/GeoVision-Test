from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

def html(path):
 s=path.read_text(encoding='utf-8')
 # LAB035 intercepted YouTube through a dedicated bridge and could swallow the launch.
 # Keep the bridge available, but restore the proven normal launchPlatform URL path.
 old="function launchPlatform(p) {\n  if(p === 'youtube' && gv035OpenYouTube(social)) return;"
 assert old in s, 'LAB035 YouTube interception not found'
 s=s.replace(old,"function launchPlatform(p) {\n  if(p === 'youtube') gv029ShowReturnBubble();",1)
 path.write_text(s,encoding='utf-8')

def java():
 s=J.read_text(encoding='utf-8')
 # Do not force the YouTube package. If this bridge is reached elsewhere, use Android's
 # normal ACTION_VIEW resolver so installed YouTube can open, with browser fallback naturally available.
 old='''Intent yt=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    yt.setPackage("com.google.android.youtube");
                    yt.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(yt);'''
 new='''Intent yt=new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    yt.addCategory(Intent.CATEGORY_BROWSABLE);
                    startActivity(yt);'''
 assert old in s, 'LAB035 forced YouTube package block not found'
 s=s.replace(old,new,1)
 J.write_text(s,encoding='utf-8')

html(H1)
if H2.exists(): html(H2)
java()
print('LAB036: YouTube normal opening restored; existing floating return bubble armed only for YouTube')
