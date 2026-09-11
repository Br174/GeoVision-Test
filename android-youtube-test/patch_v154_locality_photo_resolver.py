from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v154 LAB — risoluzione fotografica territoriale.
# Obiettivo unico: recuperare foto anche per frazioni/rioni/contrade/localita e
# per localita il cui Place geografico non espone direttamente photos, senza
# modificare struttura/grafica/comportamento della scheda Google principale.
# Mantiene il percorso v153/v149 e lo usa come prima scelta dove gia funziona.

anchor='function googlePlaceUrl(p) {'
if anchor not in s:
    raise SystemExit('v154 aborted: googlePlaceUrl anchor not found')

helper=r'''
function gvV154IsTerritorialPhotoPlace(p){
    if(!p || p.isPoi) return false;
    const k=String(p.kind||'').toLowerCase();
    return /citt[aà]|paese|comune|frazione|rione|contrada|quartiere|borgo|localit|sublocalit|village|town|city|municip/.test(k);
}

function gvV154Norm(v){
    try{ if(typeof norm==='function') return norm(v||''); }catch(e){}
    return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
}

function gvV154PlaceLatLng(pl,p){
    try{
        const loc=pl?.location;
        const lat=loc ? (typeof loc.lat==='function'?loc.lat():Number(loc.lat)) : Number(p?.lat);
        const lng=loc ? (typeof loc.lng==='function'?loc.lng():Number(loc.lng)) : Number(p?.lon);
        return {lat,lng};
    }catch(e){ return {lat:Number(p?.lat),lng:Number(p?.lon)}; }
}

function gvV154DistanceMeters(a,b){
    try{ if(typeof metersBetween==='function') return metersBetween(a,b); }catch(e){}
    if(!Number.isFinite(a?.lat)||!Number.isFinite(a?.lng)||!Number.isFinite(b?.lat)||!Number.isFinite(b?.lng)) return 999999;
    const R=6371000,dLat=(b.lat-a.lat)*Math.PI/180,dLng=(b.lng-a.lng)*Math.PI/180,la1=a.lat*Math.PI/180,la2=b.lat*Math.PI/180;
    const x=Math.sin(dLat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dLng/2)**2;
    return 2*R*Math.asin(Math.min(1,Math.sqrt(x)));
}

function gvV154IsTerritoryType(types){
    return (Array.isArray(types)?types:[]).some(t=>{
        t=String(t||'');
        return t==='locality'||t==='postal_town'||t==='neighborhood'||t==='administrative_area_level_3'||t==='administrative_area_level_4'||t==='administrative_area_level_5'||t==='sublocality'||t.startsWith('sublocality_level_');
    });
}

function gvV154AddPhoto(out,raw,maxCount=3){
    if(out.length>=maxCount) return false;
    let u='';
    try{
        if(typeof raw==='string') u=raw;
        else if(typeof raw?.getURI==='function') u=raw.getURI({maxWidth:1600,maxHeight:1000})||'';
        else if(typeof raw?.getUrl==='function') u=raw.getUrl({maxWidth:1600,maxHeight:1000})||'';
    }catch(e){}
    try{ u=clean(u||''); }catch(e){ u=String(u||'').trim(); }
    if(!u || !/^https?:/i.test(u) || out.includes(u)) return false;
    out.push(u);
    return true;
}

async function gvV154HydratePlace(P,pl){
    if(!pl?.id) return pl;
    try{
        let target=pl;
        if(typeof target.fetchFields!=='function') target=new P({id:String(pl.id)});
        await Promise.race([
            target.fetchFields({fields:['displayName','formattedAddress','location','types','photos']}),
            new Promise((_,rej)=>setTimeout(()=>rej(new Error('v154 fields timeout')),6000))
        ]);
        return target;
    }catch(e){ return pl; }
}

function gvV154CandidateScore(pl,p){
    const target=gvV154Norm(p?.name),parent=gvV154Norm(p?.parent),name=gvV154Norm(pl?.displayName),address=gvV154Norm(pl?.formattedAddress);
    const pos=gvV154PlaceLatLng(pl,p),origin={lat:Number(p?.lat),lng:Number(p?.lon)},dist=gvV154DistanceMeters(origin,pos);
    let score=0;
    if(target && name===target) score+=520;
    else if(target && (name.includes(target)||target.includes(name))) score+=220;
    else score-=260;
    if(parent && (address.includes(parent)||name.includes(parent))) score+=130;
    if(gvV154IsTerritoryType(pl?.types)) score+=190; else score-=220;
    if(Number.isFinite(dist)) score+=Math.max(-180,150-Math.min(330,dist/45));
    const pc=Array.isArray(pl?.photos)?pl.photos.length:0;
    score+=Math.min(120,pc*20);
    return {score,dist,pc};
}

async function gvV154SearchTerritoryCandidates(P,p,diag){
    const found=new Map();
    const queries=[];
    const pushQ=q=>{ q=String(q||'').trim(); if(q&&!queries.includes(q)) queries.push(q); };
    pushQ([p?.name,p?.parent].filter(Boolean).join(', '));
    pushQ([p?.name,p?.address].filter(Boolean).join(', '));
    pushQ(p?.name||'');
    const bias=Number.isFinite(Number(p?.lat))&&Number.isFinite(Number(p?.lon))?{lat:Number(p.lat),lng:Number(p.lon)}:undefined;

    for(const textQuery of queries){
        try{
            const req={textQuery,fields:['id','displayName','formattedAddress','location','types','photos'],language:'it',region:'IT',maxResultCount:8};
            if(bias) req.locationBias=bias;
            const res=await P.searchByText(req);
            const arr=Array.isArray(res?.places)?res.places:[];
            diag.push(`q:${textQuery}:${arr.length}`);
            for(const pl of arr){ if(pl?.id&&!found.has(String(pl.id))) found.set(String(pl.id),pl); }
        }catch(e){ diag.push(`qerr:${textQuery}:${String(e?.message||e)}`); }
    }

    const ranked=[];
    for(const pl0 of found.values()){
        const pl=await gvV154HydratePlace(P,pl0);
        const r=gvV154CandidateScore(pl,p);
        if(r.score>40) ranked.push({pl,...r});
    }
    ranked.sort((a,b)=>b.score-a.score);
    return ranked;
}

async function gvV154LocalityPhotos(p){
    const out=[];
    const diag=[];

    // 1) Conserva esattamente il motore gia funzionante per le citta supportate.
    try{
        if(typeof googleLocalityPhotos==='function'){
            const old=await googleLocalityPhotos(p);
            for(const u of (old||[])){ gvV154AddPhoto(out,u,3); if(out.length>=3) break; }
            diag.push(`base:${out.length}`);
            if(out.length>=3){ window.gvV154LastPhotoDiag={name:p?.name,source:'base',diag}; return out; }
        }
    }catch(e){ diag.push(`baseerr:${String(e?.message||e)}`); }

    if(!googleReady||!gvV154IsTerritorialPhotoPlace(p)){
        window.gvV154LastPhotoDiag={name:p?.name,source:'not-territorial',diag};
        return out;
    }

    try{
        const lib=await google.maps.importLibrary('places'),P=lib.Place;

        // 2) Prima il PlaceId gia noto, anche se e una frazione/sublocalita.
        if(p?.placeId){
            try{
                const direct=await gvV154HydratePlace(P,new P({id:String(p.placeId)}));
                const photos=Array.isArray(direct?.photos)?direct.photos:[];
                diag.push(`direct:${String(p.placeId)}:${photos.length}:${(direct?.types||[]).join('|')}`);
                for(const ph of photos){ gvV154AddPhoto(out,ph,3); if(out.length>=3) break; }
            }catch(e){ diag.push(`directerr:${String(e?.message||e)}`); }
        }

        // 3) Se il Place geografico non espone foto, cerca l'entita territoriale
        // corretta senza forzare includedType=locality/useStrictTypeFiltering.
        if(out.length<3){
            const ranked=await gvV154SearchTerritoryCandidates(P,p,diag);
            for(const item of ranked.slice(0,4)){
                diag.push(`cand:${item.pl?.displayName||''}:${Math.round(item.score)}:${Math.round(item.dist||0)}:${item.pc}`);
                for(const ph of (Array.isArray(item.pl?.photos)?item.pl.photos:[])){
                    gvV154AddPhoto(out,ph,3); if(out.length>=3) break;
                }
                if(out.length>=3) break;
            }
        }

        // 4) Google Maps per le localita puo mostrare media del territorio anche
        // quando il Place amministrativo non ha photos proprie. Emuliamo quel caso
        // raccogliendo UNA foto per luogo vicino, senza cambiare la scheda Google.
        if(out.length<3){
            const base=[p?.name,p?.parent].filter(Boolean).join(' ');
            const queries=[`${base} luoghi di interesse`,`${base} monumenti`,`${base} attrazioni`];
            const big=/citt[aà]|paese|comune/i.test(String(p?.kind||''));
            const maxDist=big?12000:7500;
            const seen=new Set();
            for(const textQuery of queries){
                if(out.length>=3) break;
                try{
                    const req={textQuery,fields:['id','displayName','formattedAddress','location','photos'],language:'it',region:'IT',maxResultCount:10};
                    if(Number.isFinite(Number(p?.lat))&&Number.isFinite(Number(p?.lon))) req.locationBias={lat:Number(p.lat),lng:Number(p.lon)};
                    const res=await P.searchByText(req);
                    for(const pl0 of (res?.places||[])){
                        if(out.length>=3) break;
                        const id=String(pl0?.id||''); if(!id||seen.has(id)) continue; seen.add(id);
                        const pos=gvV154PlaceLatLng(pl0,p),dist=gvV154DistanceMeters({lat:Number(p.lat),lng:Number(p.lon)},pos);
                        if(Number.isFinite(dist)&&dist>maxDist) continue;
                        const pl=await gvV154HydratePlace(P,pl0);
                        const ph=(Array.isArray(pl?.photos)?pl.photos:[])[0];
                        if(ph) gvV154AddPhoto(out,ph,3);
                    }
                }catch(e){ diag.push(`areaerr:${String(e?.message||e)}`); }
            }
        }

        // 5) Fallback legacy gia presente nel progetto, solo se serve ancora.
        if(out.length<3 && typeof legacyGoogleTextPhotos==='function'){
            const q=[p?.name,p?.parent].filter(Boolean).join(', ');
            try{
                const rows=await legacyGoogleTextPhotos(q,p);
                for(const r of (rows||[])){
                    if(out.length>=3) break;
                    for(const ph of (Array.isArray(r?.photos)?r.photos:[])){
                        gvV154AddPhoto(out,ph,3); if(out.length>=3) break;
                    }
                }
                diag.push(`legacy:${out.length}`);
            }catch(e){ diag.push(`legacyerr:${String(e?.message||e)}`); }
        }
    }catch(e){ diag.push(`fatal:${String(e?.message||e)}`); }

    try{
        if(out.length && p?.placeId && typeof googlePhotoCache!=='undefined') googlePhotoCache.set(String(p.placeId),out.slice(0,3));
    }catch(e){}
    window.gvV154LastPhotoDiag={name:p?.name,source:out.length?'resolved':'empty',count:out.length,diag};
    console.log('GeoVision v154 locality photo resolver',p?.name||'',out.length,diag.join(' | '));
    return out;
}
'''

if 'function gvV154IsTerritorialPhotoPlace(p)' in s:
    raise SystemExit('v154 aborted: patch already present')
s=s.replace(anchor,helper+'\n'+anchor,1)

# La scheda Google non cambia struttura: allarghiamo solo CHI puo usare la striscia
# fotografica e instradiamo quel recupero nel resolver v154.
old_city='cityLocality = isOfficialCityLocality(p)'
if s.count(old_city)!=1:
    raise SystemExit(f'v154 aborted: expected one main-card cityLocality anchor, found {s.count(old_city)}')
s=s.replace(old_city,'cityLocality = gvV154IsTerritorialPhotoPlace(p)',1)

old_call='void googleLocalityPhotos(p).then(urls => {'
if s.count(old_call)!=1:
    raise SystemExit(f'v154 aborted: expected one main-card photo call, found {s.count(old_call)}')
s=s.replace(old_call,'void gvV154LocalityPhotos(p).then(urls => {',1)

# Anche la galleria Foto v145 tratta frazioni/rioni/contrade come territorio,
# senza cambiare la classificazione geografica generale dell'app.
old_v145="const locality=(typeof isOfficialCityLocality==='function') && isOfficialCityLocality(p);"
if old_v145 not in s:
    raise SystemExit('v154 aborted: v145 locality routing anchor not found')
s=s.replace(old_v145,"const locality=gvV154IsTerritorialPhotoPlace(p);",1)

# Controlli statici anti-regressione.
checks={
    'resolver':'async function gvV154LocalityPhotos(p)',
    'territory predicate':'function gvV154IsTerritorialPhotoPlace(p)',
    'main card route':'void gvV154LocalityPhotos(p).then(urls => {',
    'broad territory kinds':'frazione|rione|contrada|quartiere|borgo|localit',
    'candidate search':'gvV154SearchTerritoryCandidates',
    'direct place':'direct=await gvV154HydratePlace',
    'area fallback':'luoghi di interesse',
    'diagnostics':'window.gvV154LastPhotoDiag',
    'stable v149':'GeoVision v149 selected territory -> official Place media',
    'original classifier retained':'function isOfficialCityLocality(p)'
}
missing=[name for name,val in checks.items() if val not in s]
if missing:
    raise SystemExit('v154 static checks failed: '+repr(missing))
if "includedType:'locality',useStrictTypeFiltering:true" in helper.replace(' ',''):
    raise SystemExit('v154 resolver accidentally contains strict locality filter')
if s.count('function gvV154IsTerritorialPhotoPlace(p)')!=1 or s.count('async function gvV154LocalityPhotos(p)')!=1:
    raise SystemExit('v154 duplicate function regression')

p.write_text(s,encoding='utf-8')
print('Applied v154 locality photo resolver:',p,len(s))
print('v154 checks: 10/10 OK')
