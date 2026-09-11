package it.geovision.keybox;
import android.content.*;
import android.content.pm.PackageManager;
public class SyncReceiver extends BroadcastReceiver {
    public void onReceive(Context c,Intent request){
        String action=request.getAction();
        if("it.geovision.keybox.SET_GOOGLE_ENABLED_V1".equals(action)){
            String source=request.getStringExtra("sourcePackage");
            int index=request.getIntExtra("index",-1);boolean enabled=request.getBooleanExtra("enabled",true);
            if(source==null||index<0||index>2)return;
            int signature=c.getPackageManager().checkSignatures(c.getPackageName(),source);
            android.util.Log.i("GeoVisionKeySync","SET_GOOGLE_ENABLED_V1 signature="+signature+" index="+index+" enabled="+enabled);
            if(signature!=PackageManager.SIGNATURE_MATCH)return;
            KeyVault.setEnabled(c,index,enabled);return;
        }
        if(!"it.geovision.keybox.GET_KEYS_V1".equals(action))return;
        String target=request.getStringExtra("replyPackage"),nonce=request.getStringExtra("nonce");
        if(target==null||nonce==null||nonce.length()>100)return;
        int signature=c.getPackageManager().checkSignatures(c.getPackageName(),target);
        android.util.Log.i("GeoVisionKeySync","GET_KEYS_V1 signature="+signature);
        if(signature!=PackageManager.SIGNATURE_MATCH)return;
        Intent reply=new Intent("it.geovision.keybox.KEYS_V1").setPackage(target);
        reply.putExtra("nonce",nonce);
        try{reply.putExtras(KeyVault.readAll(c));}catch(Exception e){reply.putExtra("error","Archivio KeyBox non leggibile: dati locali conservati");}
        c.sendBroadcast(reply,"it.geovision.permission.KEYBOX_IMPORT");
    }
}
