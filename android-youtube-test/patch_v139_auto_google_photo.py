from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v139: apre automaticamente la prima foto GRANDE della scheda Google.
# Non ferma, ritarda o modifica TTS/AI. Non cambia la grafica della scheda Google.
helper=r'''
function gvClickGooglePhotoCandidate(el){
    if(!el) return false;
    try{
        const r=el.getBoundingClientRect?.();
        if(r && (r.width < 70 || r.height < 70)) return false;
    }catch(e){}
    try{
        const evOpts={bubbles:true,cancelable:true,composed:true,view:window};
        el.dispatchEvent(new MouseEvent('mousedown',evOpts));
        el.dispatchEvent(new MouseEvent('mouseup',evOpts));
        el.dispatchEvent(new MouseEvent('click',evOpts));
        return true;
    }catch(e){
        try{ el.click(); return true; }catch(_){ return false; }
    }
}
function gvFindAndOpenFirstGooglePhoto(root){
    const seen=new Set();
    const walk=(node)=>{
        if(!node || seen.has(node)) return false;
        seen.add(node);
        let candidates=[];
        try{
            if(node.matches?.('gmp-place-media')) candidates.push(node);
            node.querySelectorAll?.('gmp-place-media').forEach(x=>candidates.push(x));
            node.querySelectorAll?.('img').forEach(img=>{
                try{
                    const r=img.getBoundingClientRect();
                    if(r.width>=120 && r.height>=90 && img.offsetParent!==null) candidates.push(img);
                }catch(e){}
            });
        }catch(e){}
        for(const c of candidates){
            try{
                const clickable=c.closest?.('button,[role="button"],a') || c;
                if(gvClickGooglePhotoCandidate(clickable)) return true;
            }catch(e){}
        }
        try{
            const all=node.querySelectorAll?.('*')||[];
            for(const el of all){
                if(el.shadowRoot && walk(el.shadowRoot)) return true;
            }
        }catch(e){}
        return false;
    };
    return walk(root);
}
function gvAutoOpenFirstGooglePhoto(p){
    const token=(window.gvGooglePhotoAutoToken=(window.gvGooglePhotoAutoToken||0)+1);
    let tries=0;
    const attempt=()=>{
        if(token!==window.gvGooglePhotoAutoToken || current!==p) return;
        const host=document.getElementById('googleCardHost');
        if(host && gvFindAndOpenFirstGooglePhoto(host)){
            console.log('GeoVision v139: Google photo lightbox auto-open requested');
            return;
        }
        tries++;
        if(tries<18) setTimeout(attempt,250);
        else console.log('GeoVision v139: Google photo lightbox not available for this place');
    };
    setTimeout(attempt,180);
}
'''

anchor='function googlePlaceUrl(p) {'
if 'function gvAutoOpenFirstGooglePhoto(p)' not in s:
    if anchor not in s:
        raise SystemExit('v139 patch aborted: googlePlaceUrl anchor not found')
    s=s.replace(anchor,helper+'\n'+anchor,1)

old="async function openPlace(p) { setTopbarForSheet(true); macroPrimary = ''; current = p; closeNativeAudio(); setFields(p); setSelectionMarker(p); const cardPromise = renderOfficialGoogleCard(p); void enrichNarration(p); await cardPromise; }"
new="async function openPlace(p) { setTopbarForSheet(true); macroPrimary = ''; current = p; closeNativeAudio(); setFields(p); setSelectionMarker(p); const cardPromise = renderOfficialGoogleCard(p); void enrichNarration(p); gvAutoOpenFirstGooglePhoto(p); await cardPromise; }"
if old not in s:
    raise SystemExit('v139 patch aborted: openPlace exact anchor not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Applied v139 auto Google photo patch:',p,len(s))
