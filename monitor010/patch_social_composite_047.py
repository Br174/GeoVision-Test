from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

HELPER=r'''
function platformQuery047(){
  const manual=clean(document.getElementById('manual')?.value||'');
  const poi=clean(document.getElementById('poi')?.value||'');
  if(manual || poi){
    const rawPlace=clean(document.getElementById('place')?.value||'');
    let place='';
    if(rawPlace){
      const parts=gv043Split(rawPlace).filter(Boolean);
      place=gv046CleanGeoPart(parts[0]||rawPlace);
    }
    return [manual,poi,place].filter(Boolean).join(' ');
  }
  return platformQuery046();
}
'''

def patch(path):
    s=path.read_text(encoding='utf-8')
    anchor='function launchPlatform(p) {'
    assert s.count(anchor)==1, 'launchPlatform anchor missing/duplicated'
    assert 'function platformQuery047()' not in s
    s=s.replace(anchor,HELPER+'\n'+anchor,1)

    assert s.count('const sq = platformQuery046();')==1
    assert s.count('const yq = platformQuery046();')==1
    assert s.count('const fq=platformQuery046();')==1
    s=s.replace('const sq = platformQuery046();','const sq = platformQuery047();',1)
    s=s.replace('const yq = platformQuery046();','const yq = platformQuery047();',1)
    s=s.replace('const fq=platformQuery046();','const fq=platformQuery047();',1)

    old="const q = platformQuery043(); if (!q)"
    new="const q = (p === 'instagram' || p === 'tiktok') ? platformQuery047() : platformQuery043(); if (!q)"
    assert s.count(old)==1, 'generic platform query anchor missing/duplicated'
    s=s.replace(old,new,1)

    checks=[
      s.count('function platformQuery047()')==1,
      'const sq = platformQuery047();' in s,
      'const yq = platformQuery047();' in s,
      'const fq=platformQuery047();' in s,
      "(p === 'instagram' || p === 'tiktok') ? platformQuery047()" in s,
      "return [manual,poi,place].filter(Boolean).join(' ');" in s,
      'function platformQuery046()' in s,
    ]
    assert all(checks),[i for i,x in enumerate(checks,1) if not x]
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB047: social query = Manual + POI + visible locality; LAB046 geographic fallback preserved')
