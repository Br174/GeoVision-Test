from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
H1=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
H2=ROOT/'out/LAB_012_FAILOVER.html'
J=ROOT/'android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java'


def patch_html(path):
    s=path.read_text(encoding='utf-8')

    # The floating control is not Back. It remembers the currently visible Google card
    # and later asks the SAME GeoVision session to show that card again.
    anchor='function gv029ShowReturnBubble(){'
    assert anchor in s, 'floating return helper not found'
    helpers=r'''let gv038CardWasOpen=false;
function gv038ClearRememberedGoogleCard(){
  gv038CardWasOpen=false;
  try{localStorage.removeItem('gv038_return_card');}catch(_){}
}
function gv038RememberGoogleCardState(){
  try{
    const sheet=document.getElementById('sheet');
    if(sheet&&sheet.classList.contains('show')&&typeof current!=='undefined'&&current){
      gv038CardWasOpen=true;
      try{localStorage.setItem('gv038_return_card',JSON.stringify({t:Date.now(),p:current}));}catch(_){}
      return true;
    }
  }catch(_){}
  gv038ClearRememberedGoogleCard();
  return false;
}
function gv038RestoreGoogleCardState(){
  try{
    let should=gv038CardWasOpen, saved=null;
    try{
      const raw=localStorage.getItem('gv038_return_card');
      if(raw){
        const data=JSON.parse(raw);
        if(data&&data.p&&Date.now()-Number(data.t||0)<1800000){saved=data.p;should=true;}
      }
    }catch(_){}
    if(!should)return false;
    let p=(typeof current!=='undefined'&&current)?current:saved;
    if(!p)return false;
    if(typeof current!=='undefined'&&!current)current=p;
    const sheet=document.getElementById('sheet'), body=document.getElementById('sheetBody');
    if(!sheet)return false;
    sheet.style.transition='';
    sheet.style.transform='';
    sheet.classList.add('show');
    if(body&&body.children.length)return true;
    if(typeof renderOfficialGoogleCard==='function'){
      renderOfficialGoogleCard(p);
      return true;
    }
  }catch(_){}
  return false;
}

'''
    if 'function gv038RestoreGoogleCardState()' not in s:
        s=s.replace(anchor,helpers+anchor,1)

    old="function gv029ShowReturnBubble(){\n  try{ if(window.GeoVisionReturnBubble&&typeof window.GeoVisionReturnBubble.remember==='function') window.GeoVisionReturnBubble.remember(); }catch(_){}"
    new="function gv029ShowReturnBubble(){\n  try{ gv038RememberGoogleCardState(); }catch(_){}\n  try{ if(window.GeoVisionReturnBubble&&typeof window.GeoVisionReturnBubble.remember==='function') window.GeoVisionReturnBubble.remember(); }catch(_){}"
    assert old in s, 'LAB030 return bubble helper form not found'
    s=s.replace(old,new,1)

    # Manual close means the user no longer wants that card restored.
    old_close="function closeSheet() { narrationRun++; stopSpeech(); $('#videoPicker').classList.remove('show');"
    new_close="function closeSheet() { gv038ClearRememberedGoogleCard(); narrationRun++; stopSpeech(); $('#videoPicker').classList.remove('show');"
    assert old_close in s, 'closeSheet anchor not found'
    s=s.replace(old_close,new_close,1)

    path.write_text(s,encoding='utf-8')


def patch_java():
    s=J.read_text(encoding='utf-8')

    if 'import android.app.PendingIntent;' not in s:
        s=s.replace('import android.app.Activity;','import android.app.Activity;\nimport android.app.PendingIntent;',1)

    # State used only to recognize a genuine user-requested return. The overlay itself
    # also remains a second signal when the original Activity survived in memory.
    class_anchor='public class MainActivity extends Activity {'
    assert class_anchor in s
    if 'GV_RETURN_CARD_ACTION' not in s:
        s=s.replace(class_anchor,class_anchor+'\n    private static final String GV_RETURN_CARD_ACTION="it.geovision.action.RETURN_GOOGLE_CARD";\n    private boolean gvReturnCardRequested=false;',1)

    # If Android ever recreates the Activity, keep enough intent state to restore the
    # remembered card after the WebView has loaded. Normal case remains the same Activity.
    create_anchor='''protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);'''
    assert create_anchor in s
    if 'gvReturnCardRequested = getIntent()!=null' not in s:
        s=s.replace(create_anchor,create_anchor+'\n        gvReturnCardRequested = getIntent()!=null && GV_RETURN_CARD_ACTION.equals(getIntent().getAction());',1)

    # Central native show path also remembers the card. This covers native external
    # launches that do not pass through the JavaScript platform launcher.
    show_anchor='''private void showReturnBubble() {
        main.post(() -> {'''
    assert show_anchor in s, 'showReturnBubble not found'
    if 'gv038RememberGoogleCardState' not in s[s.find(show_anchor):s.find(show_anchor)+600]:
        s=s.replace(show_anchor,show_anchor+'''\n            try{if(webView!=null)webView.evaluateJavascript("try{if(typeof gv038RememberGoogleCardState==='function')gv038RememberGoogleCardState();}catch(e){}",null);}catch(Exception ignored){}''',1)

    old_return='''private void returnToGeoVision(){
        hideReturnBubble();
        Intent back=getPackageManager().getLaunchIntentForPackage(getPackageName());
        if(back!=null){
            back.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(back);
        }
    }'''
    new_return='''private void returnToGeoVision(){
        try{
            Intent back=new Intent(this,MainActivity.class);
            back.setAction(GV_RETURN_CARD_ACTION);
            back.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pending=PendingIntent.getActivity(this,38038,back,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            pending.send();
            // Do NOT hide the bubble here. It disappears only after GeoVision has real window focus.
        }catch(Exception ignored){
            // Failed request: keep the bubble visible so the user can tap again.
        }
    }'''
    assert old_return in s, 'LAB036 returnToGeoVision block not found'
    s=s.replace(old_return,new_return,1)
    assert 'private void hideReturnBubble(){' in s, 'hideReturnBubble must remain intact'

    lifecycle_anchor='    @Override protected void onResume(){super.onResume();if(keyBoxClient!=null)keyBoxClient.resume();}'
    assert lifecycle_anchor in s, 'LAB036 onResume anchor not found'
    lifecycle=r'''    @Override
    protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        if(intent!=null&&GV_RETURN_CARD_ACTION.equals(intent.getAction()))gvReturnCardRequested=true;
    }

    private void gv038RestoreGoogleCardAfterReturn(){
        main.post(()->{try{if(webView!=null)webView.evaluateJavascript("try{if(typeof gv038RestoreGoogleCardState==='function')gv038RestoreGoogleCardState();}catch(e){}",null);}catch(Exception ignored){}});
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus){
        super.onWindowFocusChanged(hasFocus);
        if(!hasFocus)return;
        if(gvReturnCardRequested||gvReturnBubble!=null){
            gvReturnCardRequested=false;
            gv038RestoreGoogleCardAfterReturn();
            main.postDelayed(this::gv038RestoreGoogleCardAfterReturn,350);
            main.postDelayed(this::gv038RestoreGoogleCardAfterReturn,1000);
            hideReturnBubble();
        }
    }

'''
    if 'gv038RestoreGoogleCardAfterReturn' not in s:
        s=s.replace(lifecycle_anchor,lifecycle+lifecycle_anchor,1)

    J.write_text(s,encoding='utf-8')


patch_html(H1)
if H2.exists(): patch_html(H2)
patch_java()
print('LAB038 native PendingIntent return + exact Google card restore applied')
