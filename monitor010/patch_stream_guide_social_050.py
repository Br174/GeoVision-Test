from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

HELPERS=r'''
const gv050GuideCache=new Map();
function gv050GuideKey(p){
  return [clean(p?.placeId||''),clean(p?.name||''),clean(p?.parent||''),clean(p?.kind||'')].join('|').toLowerCase();
}
function gv050PlaceClass(p){
  const k=norm(p?.kind||'');
  if(/restaurant|ristor|trattor|oster|pizzer|cafe|caff|bar|bakery|pasticc|gelater|food|pub|bistrot/.test(k)) return 'food';
  if(p?.family==='culture'||/monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k)) return 'culture';
  if(!p?.isPoi || /citta|comune|paese|quartiere|frazione|rione|borgo|contrada|municipio|localit|hamlet|suburb|quarter|neigh|sublocal/.test(k)) return 'locality';
  return 'poi';
}
function gv050BlockTopic(p,index){
  const cls=gv050PlaceClass(p);
  const plans={
    locality:[
      'Spiega subito perché questo luogo è importante o conosciuto e, se utile, il tratto storico o identitario essenziale.',
      'Prosegui naturalmente con cucina, specialità gastronomiche e il prodotto tipico più conosciuto, solo se realmente pertinente.',
      'Continua con artigianato o prodotto artigianale caratteristico e, se esiste ed è davvero significativa, una azienda o attività rappresentativa del luogo e perché è nota.',
      'Passa senza ricominciare da capo ai luoghi, monumenti o attrazioni più importanti da vedere.',
      'Concludi il racconto con feste, sagre, mercatini, tradizioni, personaggi importanti o una curiosità significativa. Scegli solo gli elementi realmente pertinenti.'
    ],
    culture:[
      'Spiega subito perché questo luogo culturale è importante e qual è il suo valore principale.',
      'Prosegui naturalmente con origine, periodo storico, funzione ed eventuali personaggi o eventi collegati.',
      'Continua con gli elementi più importanti da osservare durante la visita.',
      'Chiudi con una tradizione, un legame locale o una curiosità concreta, solo se pertinente.'
    ],
    food:[
      'Spiega subito che tipo di locale è e perché è conosciuto o interessante.',
      'Prosegui naturalmente con specialità, piatti o prodotti più caratteristici, senza inventare.',
      'Continua con posizione, atmosfera, servizio e il senso generale delle recensioni disponibili.',
      'Chiudi con un dettaglio utile o un legame concreto con il territorio, solo se supportato.'
    ],
    poi:[
      'Spiega subito che cos’è questo luogo o attività e perché è importante o interessante.',
      'Prosegui naturalmente con caratteristiche, storia o specialità principali, secondo il tipo di luogo.',
      'Continua con cosa vedere, fare o notare e con eventuali servizi rilevanti.',
      'Chiudi con una curiosità, una tradizione o un collegamento locale concreto, solo se pertinente.'
    ]
  };
  const arr=plans[cls]||plans.poi;
  return {topic:arr[Math.min(index,arr.length-1)],last:index>=arr.length-1,total:arr.length};
}
function gv050BlockPrompt(p,index,previous=''){
  const plan=gv050BlockTopic(p,index), prev=clean(previous||'');
  const rating=p?.rating?`Valutazione: ${p.rating}${p.ratingCount?` su ${p.ratingCount} recensioni`:''}.`:'';
  const summary=clean(p?.summary||'');
  return `Sei l'audioguida italiana di GeoVision. Stai scrivendo UN SOLO RACCONTO CONTINUO diviso tecnicamente in piccoli blocchi. Questo è il blocco ${index+1} di circa ${plan.total}. Scrivi SOLO 2 o 3 frasi brevi, circa 45-75 parole, pronte per essere lette ad alta voce. Niente markdown, niente titolo, niente elenco, niente saluti, niente formule di attesa. Non ripetere l'inizio del racconto e non ricominciare da capo. ${index===0?'Inizia immediatamente con l’informazione più importante, senza introduzioni artificiali.':'Collegati in modo naturale alle frasi precedenti come prosecuzione dello stesso racconto.'} ${plan.last?'Puoi chiudere in modo naturale e sintetico.':'NON fare una conclusione: il racconto continuerà nel blocco successivo.'} Non inventare fatti: se un dato non è abbastanza sicuro, omettilo.\nLuogo: ${p?.name||''}\nTipo: ${p?.kind||''}\nLocalità/contesto: ${p?.parent||''}\nIndirizzo: ${p?.address||''}\n${rating}\n${summary?`Informazioni disponibili: ${summary}`:''}\nObiettivo di questo blocco: ${plan.topic}\n${prev?`Racconto già pronunciato; continua senza ripeterlo: ${prev.slice(-5000)}`:''}`;
}
async function gv050FastBlock(p,index,previous='',force=false){
  const key=gvAiKey(); if(!key) return '';
  const ck=gv050GuideKey(p)+'#'+index;
  if(!force && ck && gv050GuideCache.has(ck)) return gv050GuideCache.get(ck);
  const prompt=gv050BlockPrompt(p,index,previous);
  const request=(async()=>{
    for(const model of ['gemini-3.5-flash-lite','gemini-2.5-flash-lite']){
      const ctl=new AbortController(), timer=setTimeout(()=>ctl.abort(),6000);
      try{
        const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/json'},signal:ctl.signal,body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:0.42,maxOutputTokens:190}})});
        clearTimeout(timer); if(!r.ok) continue;
        const j=await r.json(), text=clean((j.candidates?.[0]?.content?.parts||[]).map(x=>x.text||'').join(' '));
        if(text.length>=45) return text;
      }catch(_){clearTimeout(timer);}
    }
    try{
      const native=await Promise.race([gvNativeNarration(key,prompt),new Promise(resolve=>setTimeout(()=>resolve(''),8000))]);
      if(clean(native||'').length>=45) return clean(native);
    }catch(_){}
    return '';
  })();
  if(ck){gv050GuideCache.set(ck,request);while(gv050GuideCache.size>28) gv050GuideCache.delete(gv050GuideCache.keys().next().value);}
  const out=await request; if(!out && ck) gv050GuideCache.delete(ck); return out;
}

let gv050SearchContext={poi:'',geo:'',key:''};
function gv050IsLocalLevel(p){const k=norm(p?.kind||'');return /frazione|quartiere|rione|borgo|contrada|sublocal|neigh|localit|hamlet|suburb|quarter|borough/.test(k);}
function gv050Join(a,b){a=gv046CleanGeoPart(a||'');b=gv046CleanGeoPart(b||'');if(!a)return b||'';if(!b||norm(a)===norm(b))return a;return `${a} ${b}`;}
function gv050MunicipalityFallback(p){
  const direct=gv046Municipality(p); if(direct) return direct;
  const name=gv046Name(p);
  for(const raw of gv043Split(p?.parent||'')){
    if(gv043Country(raw)||/^(provincia di|citta metropolitana di|metropolitan city of)\b/i.test(norm(raw))) continue;
    const x=gv046CleanGeoPart(raw); if(x&&norm(x)!==norm(name)) return x;
  }
  return '';
}
function gv050GeoFor(p){
  if(!p) return '';
  if(p.isPoi) return gv050MunicipalityFallback(p)||gv046CleanGeoPart(gv043Split(p.parent||'')[0]||'');
  const name=gv046Name(p);
  if(gv050IsLocalLevel(p)) return gv050Join(name,gv050MunicipalityFallback(p));
  return gv050Join(name,gv046Region(p));
}
function gv050CaptureSearch(p){gv050SearchContext={poi:p?.isPoi?clean(p.name||''):'',geo:gv050GeoFor(p),key:[clean(p?.placeId||''),clean(p?.name||''),clean(p?.parent||'')].join('|')};}
function platformQuery050(){
  const manual=clean(document.getElementById('manual')?.value||''), visiblePoi=clean(document.getElementById('poi')?.value||'');
  const poi=visiblePoi||gv050SearchContext.poi||'';
  let geo=gv050SearchContext.geo||'';
  if(!geo&&typeof current!=='undefined'&&current) geo=gv050GeoFor(current);
  if(!geo){const raw=clean(document.getElementById('place')?.value||'');if(raw){const parts=gv043Split(raw).filter(Boolean);geo=gv050Join(parts[0]||raw,parts.length>1?parts[1]:'');}}
  return [manual,poi,geo].map(clean).filter(Boolean).filter((x,i,a)=>a.findIndex(y=>norm(y)===norm(x))===i).join(' ');
}
'''

NEW_ENRICH=r'''async function enrichNarration(p, prefetchedGuide = null) {
  const run=++narrationRun, guide=$('#audioGuide'); if(!guide) return;
  guide.innerHTML='<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"><div class="loading">Preparo l’audioguida…</div></div><div id="guideSource" class="source"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>';
  const transcript=$('#guideTranscript'),source=$('#guideSource'),button=$('#deepenGuide'); let told='',depth=0;
  let block=await (prefetchedGuide||gv050FastBlock(p,0,'')); if(run!==narrationRun||current!==p)return;
  if(!block){block=await gv050FastBlock(p,0,'',true);if(run!==narrationRun||current!==p)return;}
  if(!block){transcript.innerHTML='<div class="narration narration-stage">Audioguida temporaneamente non disponibile.</div>';return;}
  transcript.innerHTML='';told=block;transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-stage">${esc(block)}</div>`);
  const total=gv050BlockTopic(p,0).total;let nextPromise=total>1?gv050FastBlock(p,1,told):null;speak(block,false);
  for(let i=1;i<total;i++){
    let next=await nextPromise;if(run!==narrationRun||current!==p)return;
    if(!next)next=await gv050FastBlock(p,i,told,true);if(run!==narrationRun||current!==p)return;if(!next)continue;
    told=clean(told+' '+next);const following=(i+1<total)?gv050FastBlock(p,i+1,told):null;
    transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-stage">${esc(next)}</div>`);speak(next,true);const sc=$('#guideScroll');if(sc)sc.scrollTop=sc.scrollHeight;nextPromise=following;
  }
  source.innerHTML='';button.disabled=false;button.onclick=async()=>{if(run!==narrationRun||current!==p)return;button.disabled=true;button.textContent='Preparo…';const extra=await aiNarration(p,'deepen','',told,++depth);if(run!==narrationRun||current!==p)return;if(extra){told=clean(told+' '+extra);transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-deep">${esc(extra)}</div>`);speak(extra,true);const sc=$('#guideScroll');if(sc)sc.scrollTop=sc.scrollHeight;}else toast('Approfondimento non disponibile');button.textContent='Voglio saperne di più';button.disabled=false;};
}
'''

OLD_OPEN="""async function openPlace(p) {
  macroPrimary = '';
  current = p;
  const guidePromise = gv043PreloadGuide(p);
  closeNativeAudio();
  setFields(p);
  setSelectionMarker(p);
  const cardPromise = renderOfficialGoogleCard(p);
  void enrichNarration(p, guidePromise);
  await cardPromise;
}"""
NEW_OPEN="""async function openPlace(p) {
  macroPrimary = '';
  current = p;
  gv050CaptureSearch(p);
  const firstBlockPromise = gv050FastBlock(p,0,'');
  closeNativeAudio();
  setFields(p);
  setSelectionMarker(p);
  const cardPromise = renderOfficialGoogleCard(p);
  void enrichNarration(p, firstBlockPromise);
  await cardPromise;
}"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert 'function gv050BlockPrompt' not in s
    anchor='async function enrichNarration(p, prefetchedGuide = null) {'
    assert s.count(anchor)==1
    s=s.replace(anchor,HELPERS+'\n'+anchor,1)
    start=s.index(anchor);end=s.index('function setSelectionMarker(p)',start)
    s=s[:start]+NEW_ENRICH+s[end:]
    assert s.count(OLD_OPEN)==1
    s=s.replace(OLD_OPEN,NEW_OPEN,1)
    ls=s.index('function launchPlatform(p) {');le=s.index("document.querySelectorAll('[data-p]')",ls);block=s[ls:le].replace('platformQuery047()','platformQuery050()');s=s[:ls]+block+s[le:]
    checks=[
      'maxOutputTokens:190' in s,
      'UN SOLO RACCONTO CONTINUO' in s,
      'Racconto già pronunciato; continua senza ripeterlo' in s,
      'gv050CaptureSearch(p);' in s,
      'const yq = platformQuery050();' in s,
      'const sq = platformQuery050();' in s,
      'const fq=platformQuery050();' in s,
      "(p === 'instagram' || p === 'tiktok') ? platformQuery050()" in s,
      'return `${a} ${b}`;' in s,
      'function platformQuery047()' in s,
      'Importa da KeyBox' in s,
    ]
    assert all(checks),[i for i,x in enumerate(checks,1) if not x]
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists():patch(p)
print('LAB050: continuous micro-block audioguide + stable POI/locality social context')
