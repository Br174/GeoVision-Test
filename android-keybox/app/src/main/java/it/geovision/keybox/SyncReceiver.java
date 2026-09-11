package it.geovision.keybox;
import android.content.*;
import android.content.pm.PackageManager;
public class SyncReceiver extends BroadcastReceiver {
    public void onReceive(Context c,Intent request){
        if(!"it.geovision.keybox.GET_KEYS_V1".equals(request.getAction()))return;
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
