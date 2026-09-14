from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

# Facebook's old Watch search route can fall back to the home page.
# Use the dedicated video-results route and the cleaned GeoVision query.
OLD="p === 'facebook' ? `https://www.facebook.com/watch/search/?q=${encodeURIComponent(q)}`"
NEW="p === 'facebook' ? `https://www.facebook.com/search/videos/?q=${encodeURIComponent(social)}`"

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert OLD in s, 'Facebook search anchor not found'
    s=s.replace(OLD,NEW,1)
    assert 'https://www.facebook.com/search/videos/?q=' in s
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB022 Facebook video search route applied')
