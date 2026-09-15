from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

s=J.read_text(encoding='utf-8')
# Actual generated chain is LAB029 return + LAB030 CLEAR_TOP. Replace that exact block.
old='''private void returnToGeoVision(){
        hideReturnBubble();
        Intent back=new Intent(this,MainActivity.class);
        back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(back);
    }'''
new='''private void returnToGeoVision(){
        try{
            Intent back=new Intent(getApplicationContext(), MainActivity.class);
            back.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            getApplicationContext().startActivity(back);
            // Do not hide here: hide only after GeoVision has genuinely resumed.
        }catch(Exception ignored){
            // Failed foreground request: leave the bubble visible for another tap.
        }
    }'''
assert old in s, 'Actual LAB036 returnToGeoVision block not found'
s=s.replace(old,new,1)

resume='@Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
replacement='@Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}'
assert resume in s, 'Expected LAB036 onResume not found'
s=s.replace(resume,replacement,1)

J.write_text(s,encoding='utf-8')
print('LAB037: return tap fixed against actual LAB036 chain; no premature bubble hide or CLEAR_TOP')
