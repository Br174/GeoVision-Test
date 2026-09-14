from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'

def patch(path):
    s=path.read_text(encoding='utf-8')

    intro=r'''function instantNarrationIntro(p) {
    const k = String(p.kind || '').toLowerCase();
    const food = /restaurant|ristor|trattor|oster|pizzer|cafe|caff|bar|bakery|pasticc|gelater|food|pub|bistrot/.test(k);
    if (food) return 'Iniziamo questo viaggio all’insegna del gusto. Mettetevi comodi, si comincia.';
    if (p.family === 'culture' || /monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k))
        return 'Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta della storia e delle curiosità di questo luogo.';
    if (p.family === 'nature' || /parc|giardin|natura|lago|mont|spiaggia|baia|golfo|valle|riserva/.test(k))
        return 'Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta della natura.';
    if (!p.isPoi)
        return `Siamo a ${p.name}. Iniziamo a scoprirne identità, storia, cucina, tradizioni e curiosità. Mettetevi comodi, si comincia.`;
    return `Ci troviamo ${p.parent ? `a ${p.parent} ` : ''}al ${p.name}. Scopriamo che cos’è, cosa lo rende interessante e qualche curiosità. Mettetevi comodi, si comincia.`;
}
'''
    a=s.index('function instantNarrationIntro(p)')
    b=s.index('function preferredItalianVoice()',a)
    s=s[:a]+intro+s[b:]

    ai=r'''function gvAiKey(){
    try{
        const en=gvLocalApiEnabled();
        if(en && en.ai===false) return '';
        return clean(localStorage.getItem('geovision_ai_api_key')||'');
    }catch{return '';}
}
function gvNarrationPrompt(p, mode, extract='', previous='', depth=0){
    const k=String(p.kind||'').toLowerCase();
    const food=/restaurant|ristor|trattor|oster|pizzer|cafe|caff|bar|bakery|pasticc|gelater|food|pub|bistrot/.test(k);
    const culture=p.family==='culture'||/monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k);
    const locality=!p.isPoi || /città|comune|paese|quartiere|frazione|rione|borgo|contrada|municipio|localit/.test(k);
    let focus='';
    if(food){
        focus=`È un'attività di ristorazione. Spiega in modo concreto che tipo di locale è, le specialità o i piatti per cui è noto quando supportati dai dati, dove si trova, atmosfera e servizio, e riassumi il senso delle recensioni disponibili senza inventare. NON parlare di arte o di storia generale della città, salvo un dettaglio strettamente legato al locale.`;
    }else if(locality){
        focus=`È una località territoriale, non chiamarla mai "punto di interesse". Identificala correttamente come città, comune, paese, quartiere, frazione, rione, borgo o contrada in base ai dati. Racconta: per cosa è famosa, identità geografica, eventi storici essenziali, cucina e specialità locali, tradizioni e feste, artigianato o attività tipiche, poi una curiosità introdotta con "Lo sapevi che…".`;
    }else if(culture){
        focus=`È un monumento o luogo culturale. Racconta origine e periodo storico, funzione, elementi architettonici o artistici importanti, eventi o personaggi collegati, cosa osservare durante la visita e almeno una curiosità concreta.`;
    }else{
        focus=`È un luogo o un'attività. Spiega con precisione che cos'è, dove si trova, perché può interessare, caratteristiche principali, eventuali servizi o specialità e una curiosità utile, senza inventare dati mancanti.`;
    }
    const length = mode==='deepen'
      ? 'Aggiungi informazioni NUOVE, senza ripetere il testo precedente. Circa 180-280 parole.'
      : 'Produci un racconto completo ma scorrevole, circa 280-450 parole.';
    const rating = p.rating ? `Valutazione: ${p.rating}${p.ratingCount?` su ${p.ratingCount} recensioni`:''}.` : '';
    const summary = clean(p.summary||'');
    const context = clean(extract||'');
    const prev = clean(previous||'');
    return `Sei l'audioguida italiana di GeoVision. Scrivi SOLO il testo da leggere ad alta voce, niente markdown, niente elenchi puntati, niente titoli tecnici, niente link, niente riferimenti a API o fonti. Usa un tono naturale, informativo e piacevole, con frasi abbastanza brevi per il Text-to-Speech. Non inventare fatti: quando un dato non è supportato, omettilo.
Luogo: ${p.name||''}
Tipo: ${p.kind||''}
Località/contesto: ${p.parent||''}
Indirizzo: ${p.address||''}
${rating}
${summary?`Informazioni disponibili: ${summary}`:''}
${context?`Contesto enciclopedico: ${context.slice(0,5000)}`:''}
${focus}
${length}
${mode==='deepen' && prev ? `Testo già raccontato, da NON ripetere: ${prev.slice(-6500)}` : ''}
Chiudi in modo naturale, senza formule promozionali.`;
}
async function gvGeminiNarration(p, mode, extract='', previous='', depth=0){
    const key=gvAiKey(); if(!key) return '';
    const prompt=gvNarrationPrompt(p,mode,extract,previous,depth);
    const models=['gemini-2.5-flash','gemini-2.0-flash'];
    for(const model of models){
        try{
            const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,{
                method:'POST',headers:{'Content-Type':'application/json'},
                body:JSON.stringify({contents:[{role:'user',parts:[{text:prompt}]}],generationConfig:{temperature:0.55,maxOutputTokens:mode==='deepen'?900:1400}})
            });
            if(!r.ok) continue;
            const j=await r.json();
            const text=clean((j.candidates?.[0]?.content?.parts||[]).map(x=>x.text||'').join(' '));
            if(text.length>80) return text;
        }catch{}
    }
    return '';
}
async function aiNarration(p, mode, extract = '', previous = '', depth = 0) {
    const direct=await gvGeminiNarration(p,mode,extract,previous,depth);
    if(direct) return direct;
    try {
        const { data } = await api.post('/api/narrate', { name: p.name, kind: p.kind, address: p.address, parent: p.parent, extract: extract.slice(0, 5000), isPoi: p.isPoi, rating: p.rating, ratingCount: p.ratingCount, summary: p.summary, mode, previous: previous.slice(0, 7000), depth });
        return clean(data?.text || '');
    } catch { return ''; }
}
'''
    a=s.index('async function aiNarration(')
    b=s.index('function setFields(',a)
    s=s[:a]+ai+s[b:]

    s=s.replace('disabled>Approfondisci</button>','disabled>Voglio saperne di più</button>',1)
    s=s.replace("if (w.url)\n    source.innerHTML = `Fonte di approfondimento: <a href=\"${esc(w.url)}\" target=\"_blank\" rel=\"noopener\">Wikipedia</a>`;","source.innerHTML = '';",1)
    s=s.replace("button.textContent = 'Approfondisco…';","button.textContent = 'Preparo…';",1)
    s=s.replace("button.textContent = 'Approfondisci ancora';","button.textContent = 'Voglio saperne di più';",1)

    anchor="sheet.addEventListener('pointercancel', finishSheetDrag);"
    touch=r'''
let gvSwipeY=0, gvSwipeX=0, gvSwipeLastY=0, gvSwipeOn=false;
sheet.addEventListener('touchstart', e=>{
    if(e.touches.length!==1) return;
    const t=e.target;
    if(t?.closest?.('button,input,select,a')) return;
    if(sheetBody && sheetBody.scrollTop>2) return;
    gvSwipeY=e.touches[0].clientY; gvSwipeLastY=gvSwipeY; gvSwipeX=e.touches[0].clientX; gvSwipeOn=true;
}, {capture:true,passive:true});
sheet.addEventListener('touchmove', e=>{
    if(!gvSwipeOn || e.touches.length!==1) return;
    const y=e.touches[0].clientY, x=e.touches[0].clientX, dy=y-gvSwipeY, dx=Math.abs(x-gvSwipeX);
    gvSwipeLastY=y;
    if(dy>8 && dy>dx && (!sheetBody || sheetBody.scrollTop<=2)){
        try{e.preventDefault();}catch{}
        sheet.style.transition='none';
        sheet.style.transform=`translate(-50%,${Math.min(dy,300)}px)`;
    }
}, {capture:true,passive:false});
sheet.addEventListener('touchend', e=>{
    if(!gvSwipeOn) return;
    gvSwipeOn=false;
    const p=e.changedTouches?.[0], dy=(p?p.clientY:gvSwipeLastY)-gvSwipeY, dx=p?Math.abs(p.clientX-gvSwipeX):0;
    sheet.style.transition='';
    if(dy>68 && dy>dx) closeSheet(); else sheet.style.transform='';
}, {capture:true,passive:true});
sheet.addEventListener('touchcancel', ()=>{gvSwipeOn=false;sheet.style.transition='';sheet.style.transform='';}, {capture:true,passive:true});
'''
    assert anchor in s
    s=s.replace(anchor,anchor+touch,1)

    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB018 AI narration + robust downward swipe applied')
