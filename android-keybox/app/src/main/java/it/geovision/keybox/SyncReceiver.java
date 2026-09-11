package it.geovision.keybox;
import android.content.*;

public class SyncReceiver extends BroadcastReceiver {
    private static final String PERMISSION = "it.geovision.permission.KEYBOX_IMPORT";

    public void onReceive(Context c, Intent request) {
        String action = request.getAction();

        // Security boundary: this receiver is exported but protected in the manifest
        // by a signature-level permission. Android therefore rejects callers not
        // signed with the GeoVision certificate before this method is invoked.
        if ("it.geovision.keybox.SET_GOOGLE_ENABLED_V1".equals(action)) {
            int index = request.getIntExtra("index", -1);
            boolean enabled = request.getBooleanExtra("enabled", true);
            if (index < 0 || index > 2) return;
            KeyVault.setEnabled(c, index, enabled);
            android.util.Log.i("GeoVisionKeySync", "SET_GOOGLE_ENABLED_V1 index=" + index + " enabled=" + enabled);
            return;
        }

        if (!"it.geovision.keybox.GET_KEYS_V1".equals(action)) return;

        String target = request.getStringExtra("replyPackage");
        String nonce = request.getStringExtra("nonce");
        if (target == null || target.length() == 0 || target.length() > 255 || nonce == null || nonce.length() == 0 || nonce.length() > 100) return;

        // Do not call PackageManager.checkSignatures(packageName, target) here:
        // on Android 11 package-visibility rules can return SIGNATURE_UNKNOWN_PACKAGE
        // even for a correctly signed sibling app. The manifest signature permission
        // is the authoritative authentication mechanism. The reply is additionally
        // protected with the same signature permission, preventing key disclosure to
        // unsigned packages even if a trusted caller supplied a different target.
        Intent reply = new Intent("it.geovision.keybox.KEYS_V1").setPackage(target);
        reply.putExtra("nonce", nonce);
        try {
            reply.putExtras(KeyVault.readAll(c));
        } catch (Exception e) {
            reply.putExtra("error", "Archivio KeyBox non leggibile: dati locali conservati");
        }
        c.sendBroadcast(reply, PERMISSION);
        android.util.Log.i("GeoVisionKeySync", "GET_KEYS_V1 reply=" + target);
    }
}
