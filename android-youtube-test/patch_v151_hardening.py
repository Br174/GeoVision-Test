from pathlib import Path

p=Path('android-youtube-test/app/src/main/assets/geovision.html')
s=p.read_text(encoding='utf-8')

# v151 hardening: stessa identica funzione, nessuna feature nuova.
# - ignora loghi/icone piccoli nella scansione del media Google
# - aggancia gmp-load prima di inserire il componente nel DOM
# - mantiene visibile la diagnostica anche dopo il fallback Google

old_img="""            node.querySelectorAll?.('img').forEach(img=>{\n                if(items.length>=10) return;\n                let u=''; try{ u=img.currentSrc||img.src||''; }catch(e){}\n                gvV151UniquePush(items,u,[],'rendered-img');\n            });"""
new_img="""            node.querySelectorAll?.('img').forEach(img=>{\n                if(items.length>=10) return;\n                let large=false;\n                try{\n                    const r=img.getBoundingClientRect();\n                    large=(r.width>=120&&r.height>=80)||(img.naturalWidth>=240&&img.naturalHeight>=160);\n                }catch(e){}\n                if(!large) return;\n                let u=''; try{ u=img.currentSrc||img.src||''; }catch(e){}\n                gvV151UniquePush(items,u,[],'rendered-img');\n            });"""
if old_img not in s:
    raise SystemExit('v151 hardening aborted: rendered img block not found')
s=s.replace(old_img,new_img,1)

old_css="""    const addCss=(el)=>{\n        try{\n            const bg=getComputedStyle(el).backgroundImage||'';\n            const re=/url\\([\"']?([^\"')]+)[\"']?\\)/g; let m;\n            while((m=re.exec(bg)) && items.length<10) gvV151UniquePush(items,m[1],[],'rendered-css');\n        }catch(e){}\n    };"""
new_css="""    const addCss=(el)=>{\n        try{\n            const r=el.getBoundingClientRect();\n            if(!((r.width>=120&&r.height>=80))) return;\n            const bg=getComputedStyle(el).backgroundImage||'';\n            const re=/url\\([\"']?([^\"')]+)[\"']?\\)/g; let m;\n            while((m=re.exec(bg)) && items.length<10) gvV151UniquePush(items,m[1],[],'rendered-css');\n        }catch(e){}\n    };"""
if old_css not in s:
    raise SystemExit('v151 hardening aborted: rendered css block not found')
s=s.replace(old_css,new_css,1)

old_load="""        config.appendChild(media); config.appendChild(attr); details.appendChild(request); details.appendChild(config); wrap.appendChild(details);\n        await Promise.race([\n            new Promise((resolve,reject)=>{ details.addEventListener('gmp-load',()=>resolve(),{once:true}); details.addEventListener('gmp-error',()=>reject(new Error('gmp-error')),{once:true}); }),\n            new Promise((_,rej)=>setTimeout(()=>rej(new Error('gmp-load timeout')),10000))\n        ]);"""
new_load="""        config.appendChild(media); config.appendChild(attr); details.appendChild(request); details.appendChild(config);\n        const loaded=new Promise((resolve,reject)=>{\n            details.addEventListener('gmp-load',()=>resolve(),{once:true});\n            details.addEventListener('gmp-error',()=>reject(new Error('gmp-error')),{once:true});\n        });\n        wrap.appendChild(details);\n        await Promise.race([\n            loaded,\n            new Promise((_,rej)=>setTimeout(()=>rej(new Error('gmp-load timeout')),10000))\n        ]);"""
if old_load not in s:
    raise SystemExit('v151 hardening aborted: gmp-load block not found')
s=s.replace(old_load,new_load,1)

old_diag="""        title.textContent=name||'Luogo';\n        count.textContent='Google fallback · '+diagnostics.map(x=>x.split(':').slice(0,2).join(':')).join(' · ');\n        body.innerHTML='';\n        const selected={name:name||'Luogo',placeId:id,kind:'poi',category:'poi',type:'poi'};\n        await renderGoogleUiMediaFallback(selected,body);\n        if(!body.childNodes.length) throw new Error('official media empty');\n        console.log('GeoVision v151 fallback official media',id,diagnostics.join(' | '));"""
new_diag="""        title.textContent=name||'Luogo';\n        const diagText='Google fallback · '+diagnostics.map(x=>x.split(':').slice(0,2).join(':')).join(' · ');\n        count.textContent=diagText;\n        body.innerHTML='';\n        const selected={name:name||'Luogo',placeId:id,kind:'poi',category:'poi',type:'poi'};\n        await renderGoogleUiMediaFallback(selected,body);\n        if(!body.childNodes.length) throw new Error('official media empty');\n        count.textContent=diagText;\n        console.log('GeoVision v151 fallback official media',id,diagnostics.join(' | '));"""
if old_diag not in s:
    raise SystemExit('v151 hardening aborted: fallback diagnostic block not found')
s=s.replace(old_diag,new_diag,1)

p.write_text(s,encoding='utf-8')
print('Applied v151 hardening:',p,len(s))
