from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v137: rimuove soltanto la frase artificiale iniziale dell'audioguida.
# Non modifica prompt AI, contenuti, scheda Google, POI, ricerca o TTS nativo.
old="""function instantNarrationIntro(p) {
    const k = `${p.kind || ''} ${p.name || ''} ${p.summary || ''}`.toLowerCase();
    const food = /restaurant|ristor|pizzer|trattor|oster|tavern|cafe|caff|bar\\b|pub\\b|bistrot|bistro|gelater|pasticcer|bakery|panific|street food|gastronom|enotec|steakhouse|sushi|hamburger|burger|friggitor|rosticcer|pescheria con cucina/.test(k);
    if (food)
        return `Iniziamo questo viaggio all'insegna del gusto. Mettetevi comodi, si comincia.`;
    if (p.family === 'culture' || /monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k))
        return `Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta dell’arte.`;
    if (p.family === 'nature' || /parc|giardin|natura|lago|mont|spiaggia|baia|golfo|valle|riserva/.test(k))
        return `Mettetevi comodi, si comincia. Iniziamo questo viaggio alla scoperta della natura.`;
    if (p.isPoi)
        return `Ci troviamo ${p.parent ? `a ${p.parent} ` : ''}al ${p.name}. Qui ci raccontano la loro passione. Mettetevi comodi, si comincia.`;
    return `Siamo a ${p.name}. Iniziamo a scoprirne storia, tradizioni e curiosità. Mettetevi comodi, si comincia.`;
}
"""
new="""function instantNarrationIntro(p) {
    return '';
}
"""
if old not in s:
    raise SystemExit('v137 patch aborted: instantNarrationIntro block not found')
s=s.replace(old,new,1)

old_line='    transcript.innerHTML = `<div class="narration narration-stage">${esc(told)}</div>`;'
new_line="    transcript.innerHTML = '';"
if old_line not in s:
    raise SystemExit('v137 patch aborted: intro transcript line not found')
s=s.replace(old_line,new_line,1)

old_speak="""    /* Solo ora parte la frase iniziale: l'AI principale sta già lavorando. */
    speak(told);
"""
new_speak="""    /* v137: nessuna frase artificiale di attesa; parte direttamente il primo testo AI disponibile. */
"""
if old_speak not in s:
    raise SystemExit('v137 patch aborted: intro speak block not found')
s=s.replace(old_speak,new_speak,1)

p.write_text(s,encoding='utf-8')
print('Applied v137 remove narration intro patch:',p,len(s))
