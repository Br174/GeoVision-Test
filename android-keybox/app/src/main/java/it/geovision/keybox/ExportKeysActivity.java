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

        try {
            Intent out = new Intent();
            out.putExtras(KeyVault.readAll(this));
            out.putExtra("count",KeyVault.count(this));
            setResult(RESULT_OK,out);
        } catch(Exception e){setResult(RESULT_CANCELED);}
        finish();
    }
}

