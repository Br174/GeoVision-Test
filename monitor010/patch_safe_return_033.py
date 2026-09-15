from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'
H=ROOT/'out/LAB_012_FAILOVER.html'

def java():
 s=J.read_text(encoding='utf-8')
 # Small round minimal overlay, retaining LAB031's proven Activity return mechanism.
 s=s.replace('SpannableString label=new SpannableString("●  GeoVision");','SpannableString label=new SpannableString("●");',1)
 s=s.replace('b.setText(label); b.setTextSize(15); b.setGravity(Gravity.CENTER);','b.setText(label); b.setTextSize(23); b.setGravity(Gravity.CENTER);',1)
 s=s.replace('int h=(int)(46*getResources().getDisplayMetrics().density);\n            int w=(int)(150*getResources().getDisplayMetrics().density);','int h=(int)(44*getResources().getDisplayMetrics().density);\n            int w=h;',1)
 # Centralize bubble activation at native URL opening. This covers Photos/Google/socials
 # without forcing task movement or altering WebView navigation/state.
 # Limit replacements to known ACTION_VIEW launch forms if present.
 s=s.replace('Intent i=new Intent(Intent.ACTION_VIEW, Uri.parse(url));\n                startActivity(i);','Intent i=new Intent(Intent.ACTION_VIEW, Uri.parse(url));\n                showReturnBubble();\n                startActivity(i);')
 s=s.replace('Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));\n                startActivity(intent);','Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));\n                showReturnBubble();\n                startActivity(intent);')
 J.write_text(s,encoding='utf-8')

def html():
 s=H.read_text(encoding='utf-8')
 # Universal pre-open hook: show overlay for external HTTP(S) anchors only.
 # It does not navigate back, reload, close or recreate the Google card.
 hook=r'''<script id="gv033-safe-external-bubble">
document.addEventListener('click',function(e){
 try{
  const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;if(!a)return;
  const u=(a.getAttribute('href')||'').trim();
  if(/^https?:\/\//i.test(u)&&window.GeoVisionReturnBubble)window.GeoVisionReturnBubble.show();
 }catch(_){ }
},true);
</script>
'''
 if 'gv033-safe-external-bubble' not in s:s=s.replace('</body>',hook+'</body>',1)
 H.write_text(s,encoding='utf-8')
java();html();print('LAB033 safe return applied')
