from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
 s=path.read_text(encoding='utf-8')
 # YouTube is handled explicitly because its launch path can bypass generic external-anchor hooks.
 old="const u = p === 'youtube' ? `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` :"
 new="""if (p === 'youtube') {
    gv029ShowReturnBubble();
    const yt=`https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`;
    return openUrl(yt);
}
const u ="""
 assert old in s, 'YouTube launch anchor not found'
 s=s.replace(old,new,1)
 # Also arm the bubble when a concrete YouTube/watch/shorts link is selected.
 hook=r'''<script id="gv034-youtube-return">
document.addEventListener('click',function(e){
 try{
  const a=e.target&&e.target.closest?e.target.closest('a[href]'):null;if(!a)return;
  const u=(a.href||a.getAttribute('href')||'');
  if(/(?:youtube\.com|youtu\.be)/i.test(u)&&window.GeoVisionReturnBubble)window.GeoVisionReturnBubble.show();
 }catch(_){ }
},true);
</script>
'''
 if 'gv034-youtube-return' not in s:s=s.replace('</body>',hook+'</body>',1)
 path.write_text(s,encoding='utf-8')
patch(HTML)
if OUT.exists():patch(OUT)
print('LAB034 YouTube return hook applied; other LAB033 behavior unchanged')
