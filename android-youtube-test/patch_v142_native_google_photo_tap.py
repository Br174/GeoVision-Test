from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v142: abbandona il viewer ricostruito e usa un vero tap Android nel WebView
# sulla zona fotografica della scheda Google. Storytelling invariato e indipendente.
helper=r'''
async function gvAutoOpenNativeGooglePhotoV142(p){
    const token=(window.gvNativePhotoTapToken=(window.gvNativePhotoTapToken||0)+1);
    const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));

    for(let attempt=0; attempt<32; attempt++){
        if(token!==window.gvNativePhotoTapToken || current!==p) return;

        const host=document.getElementById('googleCardHost');
        const details=host?.querySelector?.('gmp-place-details');
        const target=details||host;
        if(target){
            try{
                const r=target.getBoundingClientRect();
                const body=document.getElementById('sheetBody');
                const tallEnough=r.width>220 && r.height>240;

                if(tallEnough){
                    // Se la scheda Google e' scesa sotto il bordo visibile, la riportiamo
                    // nella viewport prima del tap. Non cambia struttura o grafica della scheda.
                    if((r.top+130)>window.innerHeight-40 || r.bottom<130){
                        try{ target.scrollIntoView({block:'start',inline:'nearest'}); }catch(e){}
                        await sleep(180);
                    }

                    const rr=target.getBoundingClientRect();
                    const x=rr.left + Math.min(Math.max(rr.width*0.27,90), Math.max(90,rr.width-90));
                    const y=Math.min(rr.bottom-70, rr.top+125);

                    if(y>70 && y<window.innerHeight-25){
                        if(window.GeoVisionNativeUI && typeof window.GeoVisionNativeUI.tapAtCss==='function'){
                            console.log('GeoVision v142: native Android photo tap',attempt,x,y,window.devicePixelRatio||1);
                            try{ toast('Foto: apertura automatica…'); }catch(e){}
                            window.GeoVisionNativeUI.tapAtCss(x,y,window.devicePixelRatio||1);
                            return;
                        }
                        console.log('GeoVision v142: native UI bridge unavailable');
                        try{ toast('Foto automatica: collegamento Android non disponibile'); }catch(e){}
                        return;
                    }
                }
            }catch(e){
                console.log('GeoVision v142: card geometry error',e?.message||e);
            }
        }
        await sleep(250);
    }

    console.log('GeoVision v142: Google photo area never became tappable');
    try{ toast('Foto automatica: area Google non pronta'); }catch(e){}
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvAutoOpenNativeGooglePhotoV142(p)' not in s:
    if anchor not in s:
        raise SystemExit('v142 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old='void enrichNarration(p); await cardPromise; void gvAutoOpenPhotoViewerV141(p);'
new='void enrichNarration(p); await cardPromise; void gvAutoOpenNativeGooglePhotoV142(p);'
if old not in s:
    raise SystemExit('v142 patch aborted: v141 openPlace hook not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Applied v142 native Google photo tap patch:',p,len(s))
