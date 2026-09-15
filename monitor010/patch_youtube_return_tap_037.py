from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

s=J.read_text(encoding='utf-8')
# Replace the generated return method by boundaries instead of depending on earlier patch formatting.
pat=r'private void returnToGeoVision\(\)\s*\{.*?\n\s*\}\n\s*private class ReturnBubbleBridge'
new='''private void returnToGeoVision(){
        try{
            Intent back=new Intent(getApplicationContext(), MainActivity.class);
            back.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            getApplicationContext().startActivity(back);
            // Bubble stays visible until GeoVision really resumes.
        }catch(Exception ignored){
            // Keep bubble visible when foregrounding fails.
        }
    }
    private class ReturnBubbleBridge'''
s,n=re.subn(pat,new,s,count=1,flags=re.S)
assert n==1, 'returnToGeoVision method boundaries not found'

# Hide only once the retained GeoVision Activity has actually resumed.
old='@Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
new_resume='@Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}'
if old in s:
    s=s.replace(old,new_resume,1)
elif new_resume not in s:
    raise AssertionError('GeoVision onResume hook not found')

J.write_text(s,encoding='utf-8')
print('LAB037 robust return tap patch applied; no premature bubble hide, no CLEAR_TOP')
