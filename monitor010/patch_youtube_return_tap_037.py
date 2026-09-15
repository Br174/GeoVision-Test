from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

s=J.read_text(encoding='utf-8')

# Surgical replacement: change ONLY returnToGeoVision(), preserving every following method.
sig='private void returnToGeoVision()'
start=s.find(sig)
assert start>=0, 'returnToGeoVision signature not found'
brace=s.find('{', start)
assert brace>=0, 'returnToGeoVision opening brace not found'

depth=0
end=None
for i in range(brace, len(s)):
    c=s[i]
    if c=='{':
        depth+=1
    elif c=='}':
        depth-=1
        if depth==0:
            end=i+1
            break
assert end is not None, 'returnToGeoVision closing brace not found'

new_method='''private void returnToGeoVision(){
        try{
            Intent back=new Intent(getApplicationContext(), MainActivity.class);
            back.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            getApplicationContext().startActivity(back);
            // Do not hide here: keep the overlay until GeoVision really resumes.
        }catch(Exception ignored){
            // If foregrounding fails, keep the bubble visible for another tap.
        }
    }'''

s=s[:start]+new_method+s[end:]

# The existing hide method MUST survive this patch.
assert 'private void hideReturnBubble()' in s, 'hideReturnBubble method was lost'
assert '@JavascriptInterface public void hide(){hideReturnBubble();}' in s, 'ReturnBubbleBridge.hide hook missing'

# Hide the bubble only after the retained GeoVision Activity really resumes.
old='@Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
new_resume='@Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}'
if old in s:
    s=s.replace(old,new_resume,1)
elif new_resume not in s:
    raise AssertionError('GeoVision onResume hook not found')

# Final safety checks before Gradle.
assert 'private void returnToGeoVision()' in s
assert 'private void hideReturnBubble()' in s
assert 'Intent.FLAG_ACTIVITY_CLEAR_TOP' not in s[s.find('private void returnToGeoVision()'):s.find('private void hideReturnBubble()')]

J.write_text(s,encoding='utf-8')
print('LAB037 surgical return tap patch applied; hideReturnBubble preserved')
