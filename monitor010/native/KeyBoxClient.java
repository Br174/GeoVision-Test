package it.geovision.test;
import android.app.Activity;
import android.content.*;
import android.os.*;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.UUID;
public final class KeyBoxClient {
    static final int REQUEST=7311;
    private static final String PERMISSION="it.geovision.permission.KEYBOX_IMPORT";
    private final Activity activity;private final WebView web;private final Handler handler=new Handler(Looper.getMainLooper());
    private boolean registered,ready,destroyed,importing;private String nonce,pending;
    KeyBoxClient(Activity a,WebView w){activity=a;web=w;}
    private boolean trusted(){String u=web.getUrl();return u!=null&&u.startsWith("https://appassets.androidplatform.net/assets/geovision.html");}
    private final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){
        if(!"it.geovision.keybox.KEYS_V1".equals(i.getAction())||nonce==null||!nonce.equals(i.getStringExtra("nonce")))return;
        nonce=null;if(i.hasExtra("error")){error("Archivio KeyBox non leggibile: chiavi locali conservate");return;}accept(i);
    }};
    @JavascriptInterface public void pageReady(){handler.post(()->{if(destroyed||!trusted())return;ready=true;deliver();resume();});}
    @JavascriptInterface public void setSyncEnabled(boolean enabled){handler.post(()->{if(destroyed||!trusted())return;activity.getPreferences(0).edit().putBoolean("sync_enabled_v1",enabled).apply();if(enabled)resume();else nonce=null;});}
    @JavascriptInterface public void setGoogleEnabled(int index,boolean enabled){handler.post(()->{if(destroyed||!trusted()||index<0||index>2)return;try{Intent i=new Intent("it.geovision.keybox.SET_GOOGLE_ENABLED_V1").setPackage("it.geovision.keybox");i.putExtra("sourcePackage",activity.getPackageName());i.putExtra("index",index);i.putExtra("enabled",enabled);activity.sendBroadcast(i,PERMISSION);}catch(Exception ignored){}});}
    void resume(){if(destroyed||!ready||!activity.getPreferences(0).getBoolean("sync_enabled_v1",false)||nonce!=null||importing)return;
        try{if(!registered){IntentFilter f=new IntentFilter("it.geovision.keybox.KEYS_V1");androidx.core.content.ContextCompat.registerReceiver(activity,receiver,f,PERMISSION,handler,androidx.core.content.ContextCompat.RECEIVER_EXPORTED);registered=true;}
            nonce=UUID.randomUUID().toString();String sent=nonce;Intent i=new Intent("it.geovision.keybox.GET_KEYS_V1").setPackage("it.geovision.keybox");i.putExtra("replyPackage",activity.getPackageName());i.putExtra("nonce",nonce);activity.sendBroadcast(i,PERMISSION);
            handler.postDelayed(()->{if(sent.equals(nonce)){nonce=null;error("Sync non disponibile. Importazione manuale sempre disponibile.");}},8000);
        }catch(Exception e){nonce=null;error("Sync non disponibile");}
    }
    @JavascriptInterface public void importKeys(){handler.post(()->{if(destroyed||importing||!trusted())return;importing=true;nonce=null;try{activity.startActivityForResult(new Intent("it.geovision.keybox.EXPORT_KEYS").setPackage("it.geovision.keybox"),REQUEST);}catch(Exception e){importing=false;error("Installa o aggiorna GeoVision KeyBox con la firma originale");}});}
    void result(int result,Intent data){importing=false;if(result!=Activity.RESULT_OK||data==null){error("Importazione annullata: chiavi locali conservate");return;}accept(data);}
    private void accept(Intent data){try{JSONObject p=new JSONObject();for(String n:new String[]{"google1","google2","google3","ai","youtube"}){String v=data.getStringExtra(n);if(v==null||v.length()>512)throw new IllegalArgumentException();p.put(n,v);}p.put("revision",data.getLongExtra("revision",0));boolean[] e=data.getBooleanArrayExtra("googleEnabled");if(e==null||e.length<3)e=new boolean[]{data.getBooleanExtra("google1Enabled",true),data.getBooleanExtra("google2Enabled",true),data.getBooleanExtra("google3Enabled",true)};JSONArray a=new JSONArray();a.put(e[0]);a.put(e[1]);a.put(e[2]);p.put("googleEnabled",a);pending=p.toString();deliver();}catch(Exception e){error("Risposta KeyBox incompleta: chiavi locali conservate");}}
    private void deliver(){if(destroyed||!ready||pending==null||!trusted())return;String p=pending;pending=null;web.evaluateJavascript("window.gvMonitorSync&&window.gvMonitorSync("+p+")",null);}
    private void error(String s){if(!destroyed&&ready&&trusted())web.evaluateJavascript("window.gvKeyBoxError&&window.gvKeyBoxError("+JSONObject.quote(s)+")",null);}
    void destroy(){destroyed=true;handler.removeCallbacksAndMessages(null);pending=null;nonce=null;if(registered){activity.unregisterReceiver(receiver);registered=false;}}
}
