from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def splice(s,start_token,end_token,new_text):
    a=s.index(start_token)
    b=s.index(end_token,a)
    return s[:a]+new_text+s[b:]

def patch(path):
    s=path.read_text(encoding='utf-8')

    new_intro=r'''function instantNarrationIntro(p) { const k = `${p.kind || ''} ${p.name || ''} ${p.summary || ''}`.toLowerCase(); const food=/restaurant|ristor|pizzer|trattor|oster|tavern|cafe|caff|bar\b|pub\b|bistrot|gelater|pasticcer|bakery|gastronom|enotec|sushi|burger|steakhouse/.test(k); if (food)
    return `Iniziamo questo viaggio all’insegna del gusto. Mettetevi comodi, si comincia.`; if (p.family === 'culture' || /monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k))
    return `Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta della storia e dell’arte.`; if (p.family === 'nature' || /parc|giardin|natura|lago|mont|spiaggia|baia|golfo|valle|riserva/.test(k))
    return `Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta della natura.`; if (!p.isPoi && /quartier|frazion|rione|contrada|borgo|sublocal/.test(k))
    return `Siamo a ${p.name}. Scopriamo questo territorio, la sua identità, la sua storia e le curiosità che lo rendono particolare. Mettetevi comodi, si comincia.`; if (p.isPoi)
    return `Ci troviamo ${p.parent ? `a ${p.parent}, ` : ''}da ${p.name}. Mettetevi comodi, si comincia.`; return `Siamo a ${p.name}. Iniziamo a scoprirne storia, tradizioni, sapori e curiosità. Mettetevi comodi, si comincia.`; }
'''
    s=splice(s,'function instantNarrationIntro(p) {','function preferredItalianVoice()',new_intro)

    new_ai=r'''function gvAiKey(){try{return clean(localStorage.getItem('geovision_ai_api_key')||localStorage.getItem('geovision_gemini_api_key')||'');}catch{return '';}}
function gvAiPrompt(p,mode,extract='',previous='',depth=0){
    const k=`${p.kind||''} ${p.name||''} ${p.summary||''}`.toLowerCase();
    const food=/restaurant|ristor|pizzer|trattor|oster|tavern|cafe|caff|bar\b|pub\b|bistrot|gelater|pasticcer|bakery|gastronom|enotec|sushi|burger|steakhouse/.test(k);
    const culture=p.family==='culture'||/monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k);
    const local=!p.isPoi||/quartier|frazion|rione|contrada|borgo|comune|città|paese|località/.test(k);
    const identity=`Nome: ${p.name||''}. Tipo: ${p.kind||''}. Località/contesto: ${p.parent||''}. Indirizzo: ${p.address||''}. Valutazione: ${p.rating||''}. Numero recensioni: ${p.ratingCount||''}. Descrizione disponibile: ${p.summary||''}.`;
    let rules='';
    if(food) rules=`È un locale o attività gastronomica. Spiega che tipo di locale è, atmosfera se nota, specialità e piatti caratteristici, indirizzo e zona, valutazione e impressione generale delle recensioni quando disponibili. NON parlare di arte. Il tono deve essere invitante ma informativo.`;
    else if(culture) rules=`È un monumento o luogo culturale. Racconta origine e periodo storico, eventi importanti, funzione, elementi artistici o architettonici, personaggi collegati e una curiosità significativa.`;
    else if(local) rules=`È una città, paese, comune, quartiere, frazione, rione, contrada o borgo. Non chiamarlo mai punto di interesse. Racconta per cosa è conosciuto, identità del luogo, eventi storici principali, monumenti o luoghi notevoli, cucina e specialità locali, tradizioni, artigianato e almeno una curiosità naturale introdotta in modo fluido come “Lo sapevi che…”.`;
    else rules=`Descrivi il luogo in modo utile: che cos'è, perché è interessante, contesto, storia o funzione, elementi distintivi e curiosità.`;
    const length=mode==='deepen'?'Scrivi circa 260-380 parole, aggiungendo informazioni nuove e senza ripetere quanto già detto.':'Scrivi circa 220-340 parole, ricche ma scorrevoli.';
    return `Sei l'audioguida di GeoVision. Devi scrivere in italiano naturale, pensato per essere letto ad alta voce. ${length} Niente markdown, elenchi, titoli, URL, sigle tecniche, coordinate o riferimenti al fatto di essere una IA. Usa frasi fluide e dati prudenti: se un dettaglio non è supportato dal contesto, non inventarlo. ${rules}\n${identity}\nContesto informativo disponibile: ${String(extract||'').slice(0,5200)}\nTesto già pronunciato, da non ripetere: ${String(previous||'').slice(0,6500)}\nLivello approfondimento: ${depth}.`;
}
async function aiNarration(p, mode, extract = '', previous = '', depth = 0) {
    const key=gvAiKey(); if(!key)return '';
    const prompt=gvAiPrompt(p,mode,extract,previous,depth);
    const models=['gemini-2.5-flash','gemini-2.5-flash-lite'];
    for(const model of models){
        const ctrl=new AbortController(), timer=setTimeout(()=>ctrl.abort(),mode==='deepen'?26000:16000);
        try{
            const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:.62,maxOutputTokens:1400}}),signal:ctrl.signal});
            if(!r.ok){if(r.status===401||r.status===403||r.status===429)return '';continue;}
            const data=await r.json();
            const text=clean(data?.candidates?.[0]?.content?.parts?.map(x=>x?.text||'').join(' ')||'').replace(/[*#_`]+/g,' ').replace(/\s{2,}/g,' ').trim();
            if(text)return text;
        }catch(_){}finally{clearTimeout(timer);}
    }
    return '';
}
'''
    s=splice(s,"async function aiNarration(p, mode, extract = '', previous = '', depth = 0) {",'function setFields(p)',new_ai)

    new_enrich=r'''async function enrichNarration(p) {
    const run=++narrationRun;
    const guide=$('#audioGuide'); if(!guide)return;
    guide.innerHTML='<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>';
    const transcript=$('#guideTranscript'), button=$('#deepenGuide');
    let told=instantNarrationIntro(p), depth=0;
    transcript.innerHTML=`<div class="narration narration-stage">${esc(told)}</div>`;
    setTimeout(()=>{if(run===narrationRun&&current===p)speak(told);},110);
    const wikiPromise=wikiInfo(p), metaPromise=enrichPlaceNarrationMeta(p);
    const w=await wikiPromise; await metaPromise;
    if(run!==narrationRun||current!==p)return;
    let continuation=await aiNarration(p,'guide',w.extract,told,0);
    if(run!==narrationRun||current!==p)return;
    if(!continuation) continuation=await aiNarration(p,'guide','',told,0);
    if(run!==narrationRun||current!==p)return;
    if(continuation){
        told+=' '+continuation;
        transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-stage">${esc(continuation)}</div>`);
        speak(continuation,true);
        button.disabled=false;
    }else{
        const msg=gvAiKey()?'Il racconto intelligente non è disponibile in questo momento.':'Inserisci la chiave dell’intelligenza artificiale nel pannello Chiavi API.';
        transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-stage">${esc(msg)}</div>`);
        button.disabled=!gvAiKey();
    }
    button.onclick=async()=>{
        if(run!==narrationRun||current!==p)return;
        button.disabled=true;button.textContent='Preparo l’approfondimento…';
        const extra=await aiNarration(p,'deepen',w.extract,told,++depth);
        if(run!==narrationRun||current!==p)return;
        if(extra){told+=' '+extra;transcript.insertAdjacentHTML('beforeend',`<div class="narration narration-deep">${esc(extra)}</div>`);speak(extra,true);const sc=$('#guideScroll');if(sc)sc.scrollTop=sc.scrollHeight;}
        else toast('Approfondimento non disponibile');
        button.textContent='Voglio saperne di più';button.disabled=false;
    };
}
'''
    s=splice(s,'async function enrichNarration(p) {','function setSelectionMarker(p)',new_enrich)

    new_swipe=r'''const sheet = $('#sheet'), sheetHead = $('#sheet .sheet-head'), sheetBody = $('#sheetBody');
let gvSwipeStartY=0,gvSwipeLastY=0,gvSwipeActive=false;
const gvSwipeBlocked=el=>!!el?.closest?.('button,input,select,a');
sheet.addEventListener('touchstart',e=>{if(e.touches.length!==1||gvSwipeBlocked(e.target))return;if(sheetBody&&sheetBody.scrollTop>1)return;gvSwipeStartY=gvSwipeLastY=e.touches[0].clientY;gvSwipeActive=true;sheet.style.transition='none';},{passive:true,capture:true});
sheet.addEventListener('touchmove',e=>{if(!gvSwipeActive||!e.touches.length)return;gvSwipeLastY=e.touches[0].clientY;const dy=Math.max(0,gvSwipeLastY-gvSwipeStartY);if(dy>8){e.preventDefault();sheet.style.transform=`translate(-50%,${Math.min(dy,300)}px)`;}},{passive:false,capture:true});
const gvFinishSwipe=()=>{if(!gvSwipeActive)return;gvSwipeActive=false;const dy=Math.max(0,gvSwipeLastY-gvSwipeStartY);sheet.style.transition='transform .22s ease';if(dy>58){closeSheet();}else{sheet.style.transform='';setTimeout(()=>{if(!gvSwipeActive)sheet.style.transition='';},240);}};
sheet.addEventListener('touchend',gvFinishSwipe,{capture:true});sheet.addEventListener('touchcancel',gvFinishSwipe,{capture:true});
sheetHead.addEventListener('pointerdown',e=>{if(gvSwipeBlocked(e.target))return;sheetDragStart=e.clientY;sheetDragging=true;sheet.style.transition='none';try{sheetHead.setPointerCapture(e.pointerId);}catch{}});
sheetHead.addEventListener('pointermove',e=>{if(!sheetDragging)return;const dy=Math.max(0,e.clientY-sheetDragStart);sheet.style.transform=`translate(-50%,${Math.min(dy,300)}px)`;});
const gvFinishPointer=e=>{if(!sheetDragging)return;const dy=Math.max(0,e.clientY-sheetDragStart);sheetDragging=false;sheet.style.transition='transform .22s ease';if(dy>58)closeSheet();else{sheet.style.transform='';setTimeout(()=>{if(!sheetDragging)sheet.style.transition='';},240);}};
sheetHead.addEventListener('pointerup',gvFinishPointer);sheetHead.addEventListener('pointercancel',gvFinishPointer);
'''
    s=splice(s,"const sheet = $('#sheet'), sheetHead = $('#sheet .sheet-head'), sheetBody = $('#sheetBody');",'updateReticleUi(false);',new_swipe)

    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB018 TTS automatico + Gemini diretto + swipe Google applicati')
