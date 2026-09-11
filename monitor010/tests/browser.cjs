const {chromium}=require('playwright'),fs=require('fs'),http=require('http'),assert=require('assert/strict'),path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../..');
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(fs.readFileSync(root+'/out/'+(req.url.includes('baseline')?'madre2-baseline.html':'LAB_011_FAILOVER.html')));});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:390,height:844}});
 let apiRequests=0,failoverMode=false;const failoverKeys=[],errors=[];
 await context.route('**/*',async route=>{
  const req=route.request(),u=req.url();if(u.startsWith(origin))return route.continue();
  if(u.includes('leaflet.js'))return route.fulfill({contentType:'application/javascript',body:fs.readFileSync(require.resolve('leaflet/dist/leaflet.js'),'utf8')});
  if(u.includes('leaflet.css'))return route.fulfill({contentType:'text/css',body:fs.readFileSync(require.resolve('leaflet/dist/leaflet.css'),'utf8')});
  if(u.includes('html2canvas'))return route.fulfill({contentType:'application/javascript',body:''});
  if(u.includes('places.googleapis.com')){
   apiRequests++;const key=(await req.allHeaders())['x-goog-api-key']||'';
   if(failoverMode){failoverKeys.push(key);if(key==='TEST_GOOGLE_1')return route.fulfill({status:429,contentType:'application/json',body:JSON.stringify({error:{code:429,status:'RESOURCE_EXHAUSTED',message:'Quota exceeded'}})});if(key==='TEST_GOOGLE_2')return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({places:[{id:'place-ok',displayName:{text:'Salerno'},formattedAddress:'Salerno, SA',location:{latitude:40.68,longitude:14.76}}]})});}
   return route.fulfill({status:200,contentType:'application/json',body:'{"places":[]}'});
  }
  if(u.includes('generativelanguage.googleapis.com')){apiRequests++;return route.fulfill({status:200,contentType:'application/json',body:'{"models":[]}'});}
  if(u.includes('youtube/v3')){apiRequests++;return route.fulfill({status:403,contentType:'application/json',body:'{"error":{"message":"test denied"}}'});}
  return route.abort();
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(origin);await page.locator('#keyStatus').waitFor();
 await page.locator('#keyStatus').click();assert.equal(await page.locator('#gvMonitor').count(),1);assert.equal(await page.locator('#gvMonitor input[type=password]').count(),5);assert.equal(await page.locator('.gv-key-toggle').count(),3);assert.equal(apiRequests,0,'opening Monitor must not call APIs');
 await page.getByRole('button',{name:'Importa da KeyBox',exact:true}).click();assert.match(await page.locator('#gvMonitorStatus').innerText(),/Android/);
 const fixture={google1:'TEST_GOOGLE_1',google2:'TEST_GOOGLE_2',google3:'TEST_GOOGLE_3',ai:'TEST_AI',youtube:'TEST_YT',revision:1,googleEnabled:[true,true,true]};
 await page.evaluate(k=>GVKeyState.create(localStorage).apply(k),fixture);
 await page.locator('#gvMonitor').getByRole('button',{name:'Chiudi',exact:true}).click();await page.locator('#keyStatus').click();assert.equal(await page.locator('#gvKey0').inputValue(),fixture.google1);assert(!await page.locator('#gvMonitor').innerText().then(t=>t.includes(fixture.google1)));
 await page.getByRole('button',{name:'Verifica API',exact:true}).click();await page.waitForFunction(()=>document.getElementById('gvMonitorStatus').textContent.startsWith('Verifica terminata'));assert.equal(apiRequests,5);assert.equal(await page.locator('.dot[data-state="ok"]').count(),4);assert.equal(await page.locator('.dot[data-state="bad"]').count(),1);
 // Manual OFF is authoritative and immediately moves the active slot.
 await page.locator('.gv-key-toggle').nth(0).uncheck();assert.deepEqual(await page.evaluate(()=>GVKeyState.create(localStorage).enabled()),[false,true,true]);assert.equal(await page.evaluate(()=>localStorage.getItem('geovision_google_active_key_index')),'1');assert.match(await page.locator('[data-name="google1"] .state').innerText(),/OFF manuale/);
 // Restore G1 and force it active so a simulated quota error can prove transparent G1 -> G2 retry.
 await page.locator('.gv-key-toggle').nth(0).check();await page.evaluate(()=>{localStorage.setItem('geovision_google_active_key_index','0');localStorage.setItem('geovision_google_maps_api_key','TEST_GOOGLE_1');window.__gvNoReload={alive:true};});
 failoverMode=true;failoverKeys.length=0;const result=await page.evaluate(async()=>GVPlacesFailover.searchText({textQuery:'Salerno',maxResultCount:1}));failoverMode=false;
 assert.equal(result.places[0].id,'place-ok');assert.deepEqual(failoverKeys.slice(0,2),['TEST_GOOGLE_1','TEST_GOOGLE_2']);assert.equal(await page.evaluate(()=>localStorage.getItem('geovision_google_active_key_index')),'1');assert.equal(await page.evaluate(()=>window.__gvNoReload&&window.__gvNoReload.alive),true,'Places failover must not reload page');
 // An OFF alternative is skipped by automatic failover.
 await page.evaluate(()=>{const s=GVKeyState.create(localStorage);s.setEnabled(1,false);localStorage.setItem('geovision_google_active_key_index','0');localStorage.setItem('geovision_google_maps_api_key','TEST_GOOGLE_1');});failoverMode=true;failoverKeys.length=0;await page.evaluate(async()=>GVPlacesFailover.searchText({textQuery:'Salerno'}).catch(e=>String(e)));failoverMode=false;assert(!failoverKeys.includes('TEST_GOOGLE_2'),'disabled G2 must never be called');
 // All OFF means no Google request can be issued and automation cannot re-enable them.
 const before=apiRequests;const allOff=await page.evaluate(async()=>{const s=GVKeyState.create(localStorage);s.setEnabled(0,false);s.setEnabled(1,false);s.setEnabled(2,false);try{await GVPlacesFailover.searchText({textQuery:'Salerno'});return 'unexpected';}catch(e){return e.message;}});assert.match(allOff,/Nessuna chiave Google abilitata/);assert.equal(apiRequests,before);assert.deepEqual(await page.evaluate(()=>GVKeyState.create(localStorage).enabled()),[false,false,false]);
 // Restore for remaining UI checks.
 await page.evaluate(()=>{const s=GVKeyState.create(localStorage);s.setEnabled(0,true);s.setEnabled(1,true);s.setEnabled(2,true);});
 await page.getByRole('button',{name:'Diagnostica schede e foto Google'}).click();await page.waitForFunction(()=>!document.getElementById('gvGoogleDetails').disabled);assert((await page.locator('#googleDiagRows').innerText()).includes('Maps JavaScript'));
 await page.evaluate(k=>gvMonitorSync({...k,google1:'UPDATED',revision:2}),fixture);assert.notEqual(await page.evaluate(()=>localStorage.getItem('geovision_google_maps_api_key')),'UPDATED');await page.locator('#gvApplyPending').waitFor({state:'visible'});await page.locator('#gvMonitor .monitor-card').evaluate(e=>e.scrollTop=0);await page.screenshot({path:root+'/out/Monitor_API_LAB_011.png',fullPage:true});
 for(let i=0;i<3;i++){await page.locator('#gvMonitor').getByRole('button',{name:'Chiudi',exact:true}).click();await page.locator('#keyStatus').click();assert.equal(await page.locator('#gvMonitor').count(),1);}
 assert.equal(await page.evaluate(()=>document.getElementById('gvMonitor').querySelector('.monitor-card').scrollWidth<=document.getElementById('gvMonitor').querySelector('.monitor-card').clientWidth),true,'no horizontal overflow');
 await page.getByRole('button',{name:'Applica chiavi ricevute',exact:true}).click();assert.equal(await page.evaluate(()=>localStorage.getItem('geovision_keys_pending_v1')),null);assert.equal(await page.evaluate(()=>GVKeyState.create(localStorage).read().google1),'UPDATED');
 // Original controls and official Google card markup remain unchanged when Monitor is closed.
 await page.locator('#gvMonitor').getByRole('button',{name:'Chiudi',exact:true}).click();await page.locator('#menu').click();await page.locator('#mapsSetup').click();assert.equal(await page.locator('#gvMonitor').count(),1);await page.locator('#gvMonitor').getByRole('button',{name:'Chiudi',exact:true}).click();
 const baseline=await context.newPage();await baseline.goto(origin+'/baseline');await baseline.locator('#keyStatus').waitFor();assert.equal(await baseline.locator('#sheet').innerHTML(),await page.locator('#sheet').innerHTML());assert.equal(await baseline.locator('#drawer').locator('.grid').innerHTML(),await page.locator('#drawer').locator('.grid').innerHTML());assert.equal(errors.length,0,errors.join('\n'));
 console.log('PASS browser: Monitor UI; 3 manual switches; OFF absolute priority; immediate quota G1->G2 retry; disabled key skipped; all-OFF stop; no Places reload; real API status checks; staged sync; official card/social markup preserved; zero page errors.');
 await browser.close();server.close();
})().catch(e=>{console.error(e);process.exit(1)});
