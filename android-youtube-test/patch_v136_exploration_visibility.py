from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v136: una sola modifica funzionale.
# L'interruttore nasconde soltanto mirino/puntino/badge; non tocca ricerca, mappa, POI o Google card.
needle='<div class="reticle-tools"><small id="zoomMode">Scala geografica</small></div>'
replacement='''<div class="reticle-tools"><small id="zoomMode">Scala geografica</small><label class="gv-exploration-visibility" title="Mostra o nasconde solo gli elementi grafici di esplorazione"><span>Livello esplorazione</span><input id="gvExplorationVisibility" type="checkbox" checked aria-label="Mostra livello esplorazione"><i aria-hidden="true"></i></label></div>'''
if 'id="gvExplorationVisibility"' not in s:
    if needle not in s:
        raise SystemExit('v136 patch aborted: reticle-tools anchor not found')
    s=s.replace(needle,replacement,1)

style=r'''
<style id="gv-exploration-visibility-style">
.gv-exploration-visibility{margin-top:9px;display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:12px;color:#667085;user-select:none}
.gv-exploration-visibility input{position:absolute;opacity:0;pointer-events:none}
.gv-exploration-visibility i{position:relative;width:38px;height:22px;flex:0 0 38px;border-radius:999px;background:#d7dce5;transition:.16s ease}
.gv-exploration-visibility i::after{content:'';position:absolute;left:3px;top:3px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.16s ease;box-shadow:0 1px 3px rgba(15,23,42,.18)}
.gv-exploration-visibility input:checked+i{background:#2f7de1}
.gv-exploration-visibility input:checked+i::after{transform:translateX(16px)}
html.gv-hide-exploration #ring,
html.gv-hide-exploration #reticleDot,
html.gv-hide-exploration #reticleBadge,
html.gv-hide-exploration #centerBadge,
html.gv-hide-exploration #locationBadge,
html.gv-hide-exploration .reticle-badge,
html.gv-hide-exploration .center-badge,
html.gv-hide-exploration .map-badge,
html.gv-hide-exploration [data-gv-reticle-badge]{opacity:0!important;visibility:hidden!important;pointer-events:none!important}
</style>
'''
if 'id="gv-exploration-visibility-style"' not in s:
    if '</head>' not in s:
        raise SystemExit('v136 patch aborted: </head> not found')
    s=s.replace('</head>',style+'\n</head>',1)

script=r'''
<script id="gv-exploration-visibility-script">
(function(){
  var key='gvExplorationVisible';
  var toggle=document.getElementById('gvExplorationVisibility');
  if(!toggle)return;
  var saved=null;
  try{saved=localStorage.getItem(key)}catch(e){}
  toggle.checked=saved!=='0';
  function apply(){
    var visible=!!toggle.checked;
    document.documentElement.classList.toggle('gv-hide-exploration',!visible);
    try{localStorage.setItem(key,visible?'1':'0')}catch(e){}
  }
  toggle.addEventListener('change',apply);
  apply();
})();
</script>
'''
if 'id="gv-exploration-visibility-script"' not in s:
    if '</body>' not in s:
        raise SystemExit('v136 patch aborted: </body> not found')
    s=s.replace('</body>',script+'\n</body>',1)

p.write_text(s,encoding='utf-8')
print('Applied v136 exploration visibility patch:',p,len(s))
