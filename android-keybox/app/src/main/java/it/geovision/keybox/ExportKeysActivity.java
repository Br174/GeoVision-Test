package it.geovision.keybox;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class ExportKeysActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        try{
            Bundle b=KeyVault.readAll(this);
            Intent out=new Intent();
            out.putExtra("google1",b.getString("google1",""));
            out.putExtra("google2",b.getString("google2",""));
            out.putExtra("google3",b.getString("google3",""));
            out.putExtra("ai",b.getString("ai",""));
            out.putExtra("youtube",b.getString("youtube",""));
            setResult(RESULT_OK,out);
        }catch(Exception e){ setResult(RESULT_CANCELED); }
        finish();
    }
}
