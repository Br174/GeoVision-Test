from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

CSS=r'''<style id="gv026-gallery-style">
#photoGallery{background:#fff!important}
#photoGallery .photo-gallery-head{min-height:46px!important;padding:5px 8px!important;border:0!important;background:#fff!important}
#photoGalleryTitle,#photoGalleryCount{display:none!important}
#photoGalleryBody{padding:0!important;gap:2px!important;background:#fff!important;display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important}
#photoGalleryBody .photo-gallery-item{border:0!important;border-radius:0!important;margin:0!important;padding:0!important;background:#fff!important;overflow:hidden!important;aspect-ratio:1/1!important}
#photoGalleryBody .photo-gallery-item img{width:100%!important;height:100%!important;object-fit:cover!important;display:block!important}
#photoGallery .photo-gallery-empty{grid-column:1/-1;text-align:center;padding:48px 18px;color:#64748b;background:#fff}
</style>'''

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert 'async function openPhotoGallery()' in s, 'gallery missing'
    assert 'const gv024PhotoButton' in s, 'photo button missing'
    start=s.index('gv024PhotoButton.onclick=e=>{')
    end=s.index('\n  };',start)+len('\n  };')
    handler="""gv024PhotoButton.onclick=e=>{
    e.preventDefault();e.stopPropagation();
    if(typeof openPhotoGallery==='function') openPhotoGallery();
  };"""
    s=s[:start]+handler+s[end:]
    if 'id="gv026-gallery-style"' not in s:
        s=s.replace('</head>',CSS+'</head>',1)
    assert 'openPhotoGallery();' in s
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB026: photo button opens clean proprietary in-app gallery')
