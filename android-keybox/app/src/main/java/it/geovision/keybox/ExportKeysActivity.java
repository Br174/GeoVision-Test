package it.geovision.keybox;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class ExportKeysActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        String caller = getCallingPackage();
        if (caller == null || caller.trim().isEmpty()) {
            setResult(RESULT_CANCELED);
            finish();
            return;
        }

        Intent out = new Intent();
        out.putExtra("google1", KeyVault.get(this, KeyVault.G1));
        out.putExtra("google2", KeyVault.get(this, KeyVault.G2));
        out.putExtra("google3", KeyVault.get(this, KeyVault.G3));
        out.putExtra("ai", KeyVault.get(this, KeyVault.AI));
        out.putExtra("youtube", KeyVault.get(this, KeyVault.YOUTUBE));
        out.putExtra("count", KeyVault.count(this));
        setResult(RESULT_OK, out);
        finish();
    }
}
