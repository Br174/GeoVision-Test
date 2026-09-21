from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHS=[ROOT/'android-youtube-test/app/src/main/assets/geovision.html',ROOT/'out/LAB_012_FAILOVER.html']

INTRO_OLD="""function instantNarrationIntro(p) {\n    return '';\n}"""
INTRO_NEW="""function instantNarrationIntro(p) {\n    const name = clean(p?.name || '');\n    const k = String(p?.kind || '').toLowerCase();\n    const food = /restaurant|ristor|trattor|oster|pizzer|cafe|caff|bar|bakery|pasticc|gelater|food|pub|bistrot/.test(k);\n    const culture = p?.family === 'culture' || /monument|muse|chies|castell|palazz|sito arche|rovine|tempio|cattedral|basilic|teatro|anfiteatro|stor/.test(k);\n    const locality = !p?.isPoi || /città|comune|paese|quartiere|frazione|rione|borgo|contrada|municipio|localit/.test(k);\n    if (food) return 'Iniziamo questo viaggio all’insegna del gusto. Mettetevi comodi, si comincia.';\n    if (locality) return name ? `Siamo a ${name}. Cominciamo subito a scoprirne identità, storia e curiosità.` : 'Cominciamo subito a scoprire questo luogo.';\n    if (culture) return name ? `Siamo davanti a ${name}. Cominciamo subito dalla sua storia.` : 'Cominciamo subito dalla storia di questo luogo.';\n    return name ? `Siamo a ${name}. Vediamo subito che cosa rende interessante questo luogo.` : 'Cominciamo subito a scoprire questo luogo.';\n}"""

HELPER=r'''
function gv043ParentParts(v) {
    return String(v || '').split(',').map(x => clean(x)).filter(Boolean).filter(x => !/^(italia|italy)$/i.test(x));
}
function gv043PlatformQuery() {
    try {
        const manual = clean(document.getElementById('manual')?.value || '');
        if (manual) return manual;
    } catch (_) {}
    try {
        const c = current;
        if (c && c.name) {
            const name = clean(c.name);
            const parts = gv043ParentParts(c.parent || '');
            const kind = String(c.kind || '').toLowerCase();
            if (c.isPoi) {
                const parent = parts[0] || clean(document.getElementById('place')?.value || '');
                return [name, parent].filter(Boolean).slice(0, 2).join(' ');
            }
            const localLevel = /quartiere|frazione|rione|borgo|contrada|localit|sublocalit|neigh/.test(kind);
            const second = localLevel ? parts[0] : parts[parts.length - 1];
            return [name, second].filter(Boolean).slice(0, 2).join(' ');
        }
    } catch (_) {}
    const raw = clean(query());
    if (!raw) return '';
    const parts = raw.split(/\s*[,|·;]+\s*/).map(x => clean(x)).filter(Boolean);
    if (parts.length >= 4) return [parts[0], parts[1]].join(' ');
    if (parts.length >= 3) return [parts[0], parts[parts.length - 1]].join(' ');
    return raw;
}
'''

ENRICH_OLD="""async function enrichNarration(p) { const run = ++narrationRun; const guide = $('#audioGuide'); if (!guide)
    return; guide.innerHTML = '<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"><div class="loading">Preparo l’audioguida…</div></div><div id="guideSource" class="source"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = '', depth = 0; let continuation = await aiNarration(p, 'guide', '', '');"""
ENRICH_NEW="""async function enrichNarration(p) { const run = ++narrationRun; const guide = $('#audioGuide'); if (!guide)
    return; const gv043Intro = instantNarrationIntro(p); guide.innerHTML = '<div class="audio-title">Audioguida AI</div><div id="guideScroll" class="guide-scroll"><div id="guideTranscript"><div class="narration narration-stage">'+esc(gv043Intro)+'</div></div><div id="guideSource" class="source"></div></div><button id="deepenGuide" class="deepen-guide" type="button" disabled>Voglio saperne di più</button>'; const transcript = $('#guideTranscript'), source = $('#guideSource'), button = $('#deepenGuide'); let told = gv043Intro, depth = 0; if (gv043Intro) speak(gv043Intro); let continuation = await aiNarration(p, 'guide', '', told);"""

def patch(path):
    s=path.read_text(encoding='utf-8')
    assert s.count('function launchPlatform(p) {')==1
    assert s.count(INTRO_OLD)==1, 'instantNarrationIntro anchor missing/duplicated'
    s=s.replace(INTRO_OLD,INTRO_NEW,1)

    anchor='function launchPlatform(p) {'
    assert 'function gv043PlatformQuery()' not in s
    s=s.replace(anchor,HELPER+'\n'+anchor,1)

    start=s.index('function launchPlatform(p) {')
    end=s.index("document.querySelectorAll('[data-p]')",start)
    block=s[start:end]
    assert block.count('query()')==2,'launchPlatform query anchors changed'
    block=block.replace('query()','gv043PlatformQuery()')
    s=s[:start]+block+s[end:]

    assert s.count(ENRICH_OLD)==1,'audioguide anchor missing/duplicated'
    s=s.replace(ENRICH_OLD,ENRICH_NEW,1)

    checks=[
        s.count('function launchPlatform(p) {')==1,
        s.count('function gv043PlatformQuery()')==1,
        'package=com.google.android.youtube;end' in s,
        'gvFacebookLegacySearch' in s,
        'instagram://search?query=' in s,
        'package=com.zhiliaoapp.musically' in s,
        'if (gv043Intro) speak(gv043Intro)' in s,
        "aiNarration(p, 'guide', '', told)" in s,
    ]
    assert all(checks),[i for i,x in enumerate(checks,1) if not x]
    path.write_text(s,encoding='utf-8')

for p in PATHS:
    if p.exists(): patch(p)
print('LAB043 fixed: 2-level platform context + immediate audioguide intro; LAB042 social launch preserved')
