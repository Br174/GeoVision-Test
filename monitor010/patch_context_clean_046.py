from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

OLD="""function gv045ParentPair(v){
  const parts=gv043Split(v).filter(x=>!gv043Noise(x));
  if(parts.length<=2) return parts.join(' ');
  return [parts[0],parts[parts.length-1]].filter(Boolean).join(' ');
}
function platformQuery045(){
  if(typeof current!=='undefined' && current){
    if(current.isPoi){
      const parent=gv045ParentPair(current.parent||'');
      if(parent) return parent;
    }
    const geo=gv043GeoPair(current);
    if(geo) return geo;
  }
  const place=clean(document.getElementById('place').value);
  if(place){
    const pair=gv045ParentPair(place);
    if(pair) return pair;
  }
  return '';
}
"""

NEW="""function gv046CleanGeoPart(v){
  let x=clean(v||'');
  x=x.replace(/\\b\\d{5}\\b/g,' ').replace(/\\b[A-Z]{2}\\b/g,' ');
  x=x.replace(/\\s+/g,' ').trim();
  const w=x.split(' ').filter(Boolean);
  if(w.length>=2 && w.length%2===0){
    const h=w.length/2;
    if(norm(w.slice(0,h).join(' '))===norm(w.slice(h).join(' '))) x=w.slice(0,h).join(' ');
  }
  return clean(x);
}
function gv046Name(p){
  let x=clean(p?.name||'');
  const postal=x.match(/^(.*?)\\s+\\d{5}\\b/);
  if(postal && clean(postal[1])) x=clean(postal[1]);
  return gv046CleanGeoPart(x);
}
function gv046Region(p){
  const name=gv046Name(p);
  const parent=gv043Split(p?.parent||'');
  for(let i=parent.length-1;i>=0;i--){
    const raw=clean(parent[i]);
    if(gv043Country(raw) || /^(provincia di|città metropolitana di|metropolitan city of)\\b/i.test(raw)) continue;
    const x=gv046CleanGeoPart(raw);
    if(x && norm(x)!==norm(name)) return x;
  }
  const addr=gv043Split(p?.address||'');
  for(let i=addr.length-1;i>=0;i--){
    const raw=clean(addr[i]);
    if(gv043Country(raw) || /\\b\\d{5}\\b/.test(raw)) continue;
    const x=gv046CleanGeoPart(raw);
    if(x && norm(x)!==norm(name)) return x;
  }
  return '';
}
function gv046Municipality(p){
  const name=gv046Name(p);
  for(const raw of gv043Split(p?.address||'')){
    if(!/\\b\\d{5}\\b/.test(raw)) continue;
    const x=gv046CleanGeoPart(raw);
    if(x && norm(x)!==norm(name)) return x;
  }
  for(const raw of gv043Split(p?.parent||'')){
    if(gv043Country(raw) || /^(provincia di|città metropolitana di|metropolitan city of)\\b/i.test(raw)) continue;
    const x=gv046CleanGeoPart(raw);
    if(x && norm(x)!==norm(name)) return x;
  }
  return '';
}
function gv046Pair(a,b){
  a=gv046CleanGeoPart(a); b=gv046CleanGeoPart(b);
  if(!a) return b||'';
  if(!b || norm(a)===norm(b)) return a;
  return `${a}, ${b}`;
}
function platformQuery046(){
  if(typeof current!=='undefined' && current){
    if(current.isPoi){
      const town=gv046Municipality(current) || gv046CleanGeoPart((gv043Split(current.parent||'')[0]||''));
      const region=gv046Region(current);
      const q=gv046Pair(town,region);
      if(q) return q;
    }
    const name=gv046Name(current);
    const kind=norm(current.kind||'');
    const localLevel=/frazione|quartiere|rione|borgo|contrada|sublocal|neighborhood|localit/.test(kind);
    const second=localLevel ? gv046Municipality(current) : gv046Region(current);
    const q=gv046Pair(name,second);
    if(q) return q;
  }
  const place=clean(document.getElementById('place').value);
  if(place){
    const parts=gv043Split(place).filter(x=>!gv043Country(x));
    if(parts.length>=2){
      const first=gv046CleanGeoPart(parts[0]);
      const last=gv046CleanGeoPart(parts[parts.length-1]);
      return gv046Pair(first,last);
    }
    return gv046CleanGeoPart(place);
  }
  return '';
}
"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count(OLD)==1, 'LAB045 query block missing/duplicated'
    s=s.replace(OLD,NEW,1)
    s=s.replace('const sq = platformQuery045();','const sq = platformQuery046();',1)
    s=s.replace('const yq = platformQuery045();','const yq = platformQuery046();',1)
    s=s.replace("const fq=platformQuery045();","const fq=platformQuery046();",1)
    assert s.count('function platformQuery046()')==1
    assert 'const sq = platformQuery046();' in s
    assert 'const yq = platformQuery046();' in s
    assert 'const fq=platformQuery046();' in s
    assert 'const lead = gv043GuideLead(p);' not in s
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB046: clean locality query; CAP/province/duplicates removed; city->region, district->municipality')
