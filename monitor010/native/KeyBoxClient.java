package it.geovision.test;

import android.app.Activity;
import android.content.Intent;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import org.json.JSONObject;

public final class KeyBoxClient {
    static final int REQUEST=7311;
    private final Activity activity;
    private final WebView web;

    KeyBoxClient(Activity activity,WebView web){this.activity=activity;this.web=web;}

    @JavascriptInterface public void importKeys(){
        activity.runOnUiThread(()->{
            try{
                Intent i=new Intent("it.geovision.keybox.EXPORT_KEYS").setPackage("it.geovision.keybox");
                activity.startActivityForResult(i,REQUEST);
            }catch(Exception e){ error("GeoVision KeyBox non disponibile"); }
        });
    }

    void result(int resultCode,Intent data){
        if(resultCode!=Activity.RESULT_OK||data==null){ error("Importazione annullata"); return; }
        try{
            JSONObject j=new JSONObject();
            for(String n:new String[]{"google1","google2","google3","ai","youtube"}){
                String v=data.getStringExtra(n); if(v==null)v=""; j.put(n,v.trim());
            }
            final String payload=j.toString();
            web.post(()->web.evaluateJavascript("window.gvReceiveKeyBox&&window.gvReceiveKeyBox("+payload+")",null));
        }catch(Exception e){ error("Chiavi KeyBox non leggibili"); }
    }

    private void error(String text){
        web.post(()->web.evaluateJavascript("window.gvKeyBoxError&&window.gvKeyBoxError("+JSONObject.quote(text)+")",null));
    }

    void resume(){}
    void destroy(){}
}
