from pathlib import Path

p = Path("android-youtube-test/app/src/main/assets/geovision.html")
s = p.read_text(encoding="utf-8")

# UI: solo numerino accanto a ciascuna delle 3 chiavi Google Maps.
for i in (1, 2, 3):
    old = (
        f'<div class="key-input-wrap"><input id="mapsKey{i}" type="password" '
        f'placeholder="Chiave Google Maps {i}"><button class="key-eye" type="button" '
        f'data-target="mapsKey{i}" aria-label="Mostra chiave">◉</button></div>'
    )
    new = (
        f'<div class="key-input-wrap"><input id="mapsKey{i}" type="password" '
        f'placeholder="Chiave Google Maps {i}"><button class="key-eye" type="button" '
        f'data-target="mapsKey{i}" aria-label="Mostra chiave">◉</button>'
        f'<span id="mapsSwitchCount{i}" aria-label="Switch automatici oggi chiave {i}" '
        f'style="margin-left:8px;min-width:18px;text-align:center;font-weight:800;color:#64748b;font-size:12px">0</span></div>'
    )
    if old not in s:
        raise SystemExit(f"UI chiave {i} non trovata")
    s = s.replace(old, new, 1)

old_total_anchor = '<small id="mapsKeyActive">Chiave attiva: —</small>'
new_total_anchor = old_total_anchor + '\n  <small id="mapsSwitchTotal">Totale oggi: 0</small>'
if old_total_anchor not in s:
    raise SystemExit("Anchor totale switch non trovato")
s = s.replace(old_total_anchor, new_total_anchor, 1)

# Statistiche giornaliere locali: 3 contatori + totale.
stats_js = r'''
function gvGoogleSwitchDay(){
    const d=new Date();
    const y=d.getFullYear();
    const m=String(d.getMonth()+1).padStart(2,'0');
    const day=String(d.getDate()).padStart(2,'0');
    return `${y}-${m}-${day}`;
}
function gvLoadGoogleSwitchStats(){
    const today=gvGoogleSwitchDay();
    let stats={day:today,counts:[0,0,0],total:0};
    try{
        const raw=localStorage.getItem('geovision_google_switch_stats_daily');
        if(raw){
            const parsed=JSON.parse(raw);
            if(parsed && parsed.day===today && Array.isArray(parsed.counts)){
                stats={
                    day:today,
                    counts:[0,1,2].map(i=>Math.max(0,Number(parsed.counts[i])||0)),
                    total:Math.max(0,Number(parsed.total)||0)
                };
            }
        }
        if(stats.day!==today){ stats={day:today,counts:[0,0,0],total:0}; }
        localStorage.setItem('geovision_google_switch_stats_daily',JSON.stringify(stats));
    }catch{}
    return stats;
}
function gvRenderGoogleSwitchStats(){
    const stats=gvLoadGoogleSwitchStats();
    stats.counts.forEach((n,i)=>{
        const el=document.getElementById(`mapsSwitchCount${i+1}`);
        if(el) el.textContent=String(n);
    });
    const total=document.getElementById('mapsSwitchTotal');
    if(total) total.textContent=`Totale oggi: ${stats.total}`;
}
function gvRecordGoogleAutoSwitch(fromIndex){
    if(fromIndex<0 || fromIndex>2) return;
    const stats=gvLoadGoogleSwitchStats();
    stats.counts[fromIndex]=(stats.counts[fromIndex]||0)+1;
    stats.total=(stats.total||0)+1;
    try{localStorage.setItem('geovision_google_switch_stats_daily',JSON.stringify(stats));}catch{}
    gvRenderGoogleSwitchStats();
}
'''
anchor = 'function saveActiveGoogleMapKeyIndex(){'
if anchor not in s:
    raise SystemExit("Anchor funzioni chiavi non trovato")
s = s.replace(anchor, stats_js + '\n' + anchor, 1)

old_switch = r'''function switchGoogleMapKey(reason='manuale',reload=true){
    const next=findNextConfiguredGoogleKey(googleMapKeyIndex);
    if(next<0 || next===googleMapKeyIndex) return false;
    googleMapKeyIndex=next;
    refreshActiveGoogleMapKey();
    try{localStorage.setItem('geovision_google_maps_last_switch_reason',reason)}catch{}
    if(reload) location.reload();
    return true;
}'''
new_switch = r'''function switchGoogleMapKey(reason='manuale',reload=true){
    const next=findNextConfiguredGoogleKey(googleMapKeyIndex);
    if(next<0 || next===googleMapKeyIndex) return false;
    const previous=googleMapKeyIndex;
    if(reason!=='manuale') gvRecordGoogleAutoSwitch(previous);
    googleMapKeyIndex=next;
    refreshActiveGoogleMapKey();
    try{localStorage.setItem('geovision_google_maps_last_switch_reason',reason)}catch{}
    if(reload) location.reload();
    return true;
}'''
if old_switch not in s:
    raise SystemExit("Funzione switchGoogleMapKey non trovata")
s = s.replace(old_switch, new_switch, 1)

# Ogni apertura/refresh del pannello mostra i contatori del giorno corrente.
fill_anchor = "document.getElementById('mapsKeyActive').textContent = googleKey ? `Chiave attiva: ${googleMapKeyIndex+1}` : 'Chiave attiva: —';"
if fill_anchor not in s:
    raise SystemExit("Anchor fillKeysPanel non trovato")
s = s.replace(fill_anchor, fill_anchor + "\n    gvRenderGoogleSwitchStats();", 1)

# Controlli strutturali.
for token in ('mapsSwitchCount1','mapsSwitchCount2','mapsSwitchCount3','mapsSwitchTotal','gvRecordGoogleAutoSwitch(previous)'):
    if token not in s:
        raise SystemExit(f"Controllo fallito: {token}")

p.write_text(s, encoding="utf-8")
print("Candidate key counters applied", p, len(s))
