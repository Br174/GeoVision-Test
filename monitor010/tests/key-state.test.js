const {test}=require('node:test');const assert=require('node:assert/strict');
const {create,validate}=require('../web/key-state');
function memory(){const m=new Map();return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)};}
const keys=(r=1)=>({google1:'test-google-1',google2:'test-google-2',google3:'test-google-3',ai:'test-ai',youtube:'test-yt',revision:r});
test('five independent slots roundtrip',()=>{const s=create(memory());s.apply(keys());assert.deepEqual(s.read(),keys());});
test('invalid missing field rejected without mutations',()=>{const s=create(memory());s.apply(keys());assert.throws(()=>s.apply({google1:'bad'}));assert.deepEqual(s.read(),keys());});
test('empty export never erases configured keys',()=>{const s=create(memory());s.apply(keys());assert.throws(()=>s.stage({...keys(2),google1:'',google2:'',google3:'',ai:'',youtube:''}));assert.deepEqual(s.read(),keys());});
test('partial slot deletion removes legacy AI and youtube',()=>{const m=memory(),s=create(m);s.apply(keys());s.apply({...keys(2),ai:'',youtube:''});assert.equal(m.getItem('geovision_ai_api_key'),null);assert.equal(m.getItem('geovision_youtube_api_key'),null);});
test('google holes retain numbering',()=>{const m=memory(),s=create(m);s.apply({...keys(),google1:'',google2:''});assert.equal(m.getItem('geovision_google_active_key_index'),'2');assert.deepEqual(JSON.parse(m.getItem('geovision_google_maps_api_keys')),['','','test-google-3']);});
test('passive sync never modifies active SDK mirror',()=>{const m=memory(),s=create(m);s.apply(keys());s.stage({...keys(2),google1:'changed'});assert.equal(m.getItem('geovision_google_maps_api_key'),'test-google-1');assert.equal(s.read().revision,1);});
test('startup commits pending exactly once',()=>{const s=create(memory());s.apply(keys());s.stage({...keys(2),ai:'new-ai'});assert.equal(s.commitPending(),true);assert.equal(s.commitPending(),false);assert.equal(s.read().ai,'new-ai');});
test('same snapshot is a no-op',()=>{const s=create(memory());s.apply(keys());assert.equal(s.stage(keys()),false);assert.equal(s.pending(),null);});
test('stale revision cannot replace pending or active',()=>{const s=create(memory());s.apply(keys(5));assert.equal(s.stage({...keys(4),ai:'stale'}),false);assert.throws(()=>s.apply(keys(3)));s.stage({...keys(7),ai:'new'});assert.equal(s.stage({...keys(6),ai:'middle'}),false);assert.equal(s.pending().revision,7);});
test('active key preserved after reordering',()=>{const m=memory(),s=create(m);s.apply(keys());m.setItem('geovision_google_maps_api_key','test-google-2');s.apply({...keys(2),google2:'test-google-3',google3:'test-google-2'});assert.equal(m.getItem('geovision_google_active_key_index'),'2');});
test('storage failure rolls back full previous snapshot',()=>{const m=memory(),s=create(m);s.apply(keys());const set=m.setItem;let fails=true;m.setItem=(k,v)=>{if(k==='geovision_google_maps_api_key_2'&&fails){fails=false;throw Error('quota');}set(k,v);};assert.throws(()=>s.apply({...keys(2),google1:'new',ai:'new-ai'}));assert.deepEqual(s.read(),keys());assert.equal(m.getItem('geovision_google_maps_api_key'),'test-google-1');});
test('network failure never rotates credentials',()=>{const m=memory(),s=create(m);s.apply(keys());assert.equal(s.advance(Error('Failed to fetch')),false);assert.equal(m.getItem('geovision_google_active_key_index'),'0');});
test('quota failure exhausts all keys without circular reload',()=>{const m=memory(),s=create(m);s.apply(keys());assert.equal(s.advance(Error('RESOURCE_EXHAUSTED'),100),true);assert.equal(m.getItem('geovision_google_active_key_index'),'1');assert.equal(s.advance(Error('429'),200),true);assert.equal(m.getItem('geovision_google_active_key_index'),'2');assert.equal(s.advance(Error('429'),300),false);assert.equal(m.getItem('geovision_google_active_key_index'),'2');});
test('cooldown allows a later recovery attempt',()=>{const s=create(memory());s.apply(keys());s.advance(Error('429'),100);s.advance(Error('429'),200);s.advance(Error('429'),300);assert.equal(s.advance(Error('429'),61000),true);});
test('duplicate keys not selected as alternatives',()=>{const s=create(memory());s.apply({...keys(),google2:'test-google-1',google3:''});assert.equal(s.advance(Error('429')),false);});
test('errors containing keys are not persisted',()=>{const m=memory(),s=create(m);s.apply(keys());s.advance(Error('429 url?key=SECRET_SENTINEL'));assert(!m.getItem('geovision_key_cooldowns_v1').includes('SECRET_SENTINEL'));});
test('005 payload without revision supported',()=>{const k=keys();delete k.revision;assert.equal(validate(k).revision,0);});
test('bad revisions and oversized keys rejected',()=>{assert.throws(()=>validate({...keys(),revision:-1}));assert.throws(()=>validate({...keys(),ai:'x'.repeat(513)}));assert.throws(()=>validate({...keys(),google1:'line\nkey'}));});
test('replacing Google credentials clears old cooldown slots',()=>{const m=memory(),s=create(m);s.apply(keys());s.advance(Error('429'));s.apply({...keys(2),google1:'replacement'});assert.equal(m.getItem('geovision_key_cooldowns_v1'),null);});
test('unchanged newer sync still rejects an older changed response',()=>{const s=create(memory());s.apply(keys(1));assert.equal(s.stage(keys(8)),false);assert.equal(s.stage({...keys(7),ai:'stale-ai'}),false);assert.equal(s.pending(),null);});

const fs=require('fs'),vm=require('vm'),path=require('path');
function operationalSearch(storage){
 const html=fs.readFileSync(path.join(__dirname,'../../out/LAB_010_MONITOR_SYNC.html'),'utf8');
 const start=html.indexOf('async function gvPlacesSearch010('),end=html.indexOf('window.gm_authFailure',start);
 const context={gvDiagAdvanceGoogleKey:e=>create(storage).advance(e)};vm.createContext(context);vm.runInContext(html.slice(start,end),context);return context.gvPlacesSearch010;
}
test('actual Places search quota rejection advances the active key and preserves the error',async()=>{
 const storage=memory();create(storage).apply(keys());const search=operationalSearch(storage);
 const error=new Error('PLACES_SEARCH_TEXT: RESOURCE_EXHAUSTED: Quota exceeded SearchTextRequest per day');
 await assert.rejects(search({searchByText:async()=>{throw error;}},{textQuery:'Salerno'}),e=>e===error);
 assert.equal(storage.getItem('geovision_google_active_key_index'),'1');
});
test('operational search success and network errors do not rotate keys',async()=>{
 const storage=memory();create(storage).apply(keys());const search=operationalSearch(storage),result={places:[{id:'test-place'}]};
 assert.equal(await search({searchByText:async()=>result},{}),result);
 await assert.rejects(search({searchByText:async()=>{throw new Error('Failed to fetch');}},{}));
 assert.equal(storage.getItem('geovision_google_active_key_index'),'0');
});
