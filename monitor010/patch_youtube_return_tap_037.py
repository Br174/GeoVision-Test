from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'

s=J.read_text(encoding='utf-8')
old='''private void returnToGeoVision(){
        Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){
            back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(back);
        }
    }'''
new='''private void returnToGeoVision(){
        try{
            Intent back=new Intent(getApplicationContext(), MainActivity.class);
            back.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            getApplicationContext().startActivity(back);
            // Do not hide here. The overlay is removed only after GeoVision actually resumes.
        }catch(Exception ignored){
            // Keep the bubble visible if Android cannot foreground GeoVision.
        }
    }'''
assert old in s, 'LAB031 returnToGeoVision block not found'
s=s.replace(old,new,1)

# LAB030 removed the old onResume auto-hide. For LAB037 restore a controlled hide only
# after MainActivity is genuinely in foreground, so a failed tap never loses the bubble.
resume='@Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
replacement='@Override protected void onResume(){super.onResume();hideReturnBubble();if(keyBoxClient!=null)keyBoxClient.resume();}'
assert resume in s, 'Expected retained onResume not found'
s=s.replace(resume,replacement,1)

J.write_text(s,encoding='utf-8')
print('LAB037: bubble tap foregrounds retained GeoVision Activity; bubble hides only on actual resume')
