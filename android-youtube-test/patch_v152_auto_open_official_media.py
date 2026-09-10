from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v152: un solo obiettivo funzionale.
# Quando v151 ricade sul media ufficiale Google (che sul dispositivo funziona),
# aspetta il vero gmp-place-media, misura il suo rettangolo reale nella viewport
# e invia UN tap Android nativo dentro la prima foto tramite il bridge v143.
# Nessun autoplay, musica, Radar o modifica alla scheda Google principale.

helper=r'''
async function gvV152AutoOpenOfficialMedia(body){
    const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
    if(!body) return false;

    for(let attempt=0; attempt<30; attempt++){
        let media=null;
        try{ media=body.querySelector('gmp-place-media'); }catch(e){}
        if(media && media.isConnected){
            try{
                const r=media.getBoundingClientRect();
                const vw=window.innerWidth||document.documentElement.clientWidth||0;
                const vh=window.innerHeight||document.documentElement.clientHeight||0;
                if(r.width>220 && r.height>160 && vw>200 && vh>300){
                    // Il primo riquadro e quello grande a sinistra del mosaico Google.
                    // Usiamo un punto interno, lontano da badge e bordi.
                    const x=r.left + r.width*0.24;
                    const y=r.top + r.height*0.58;
                    if(x>10 && x<vw-10 && y>40 && y<vh-20){
                        const bridge=window.GeoVisionNativeUI;
                        if(bridge && typeof bridge.tapViewportCss==='function'){
                            console.log('GeoVision v152 native tap official media',attempt,
                                Math.round(x),Math.round(y),Math.round(r.left),Math.round(r.top),
                                Math.round(r.width),Math.round(r.height),vw,vh);
                            try{ bridge.showStatus?.('V152: apro la prima foto'); }catch(e){}
                            bridge.tapViewportCss(x,y,vw,vh);
                            return true;
                        }
                        console.log('GeoVision v152 tapViewportCss bridge unavailable');
                        return false;
                    }
                }
            }catch(e){
                console.log('GeoVision v152 media geometry failed',e?.message||e);
            }
        }
        await sleep(220);
    }
    console.log('GeoVision v152 official media rect not found');
    try{ window.GeoVisionNativeUI?.showStatus?.('V152: area foto non trovata'); }catch(e){}
    return false;
}
'''

anchor='function googlePlaceUrl(p) {'
if 'async function gvV152AutoOpenOfficialMedia(body)' not in s:
    if anchor not in s:
        raise SystemExit('v152 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old="""        await renderGoogleUiMediaFallback(selected,body);\n        if(!body.childNodes.length) throw new Error('official media empty');\n        count.textContent=diagText;\n        console.log('GeoVision v151 fallback official media',id,diagnostics.join(' | '));"""
new="""        await renderGoogleUiMediaFallback(selected,body);\n        if(!body.childNodes.length) throw new Error('official media empty');\n        count.textContent=diagText;\n        console.log('GeoVision v151 fallback official media',id,diagnostics.join(' | '));\n        await gvV152AutoOpenOfficialMedia(body);"""
if old not in s:
    raise SystemExit('v152 patch aborted: v151 fallback block not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Applied v152 auto-open official media photo:',p,len(s))
