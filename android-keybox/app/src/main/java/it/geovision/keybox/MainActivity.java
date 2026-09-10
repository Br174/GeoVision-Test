package it.geovision.keybox;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private EditText g1, g2, g3, ai, youtube;
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
        loadValues();
        updateStatus();
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private TextView text(String value, int sp, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(Color.rgb(31, 41, 55));
        if (bold) t.setTypeface(t.getTypeface(), android.graphics.Typeface.BOLD);
        return t;
    }

    private EditText field(String label) {
        EditText e = new EditText(this);
        e.setHint(label);
        e.setSingleLine(true);
        e.setTextSize(15);
        e.setPadding(dp(14), dp(12), dp(14), dp(12));
        e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(10);
        e.setLayoutParams(lp);
        return e;
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.WHITE);

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(22), dp(28), dp(22), dp(32));
        scroll.addView(box, new ScrollView.LayoutParams(
                ScrollView.LayoutParams.MATCH_PARENT,
                ScrollView.LayoutParams.WRAP_CONTENT));

        TextView title = text("GeoVision KeyBox", 26, true);
        box.addView(title);

        TextView subtitle = text("Archivio chiavi separato da GeoVision", 14, false);
        subtitle.setTextColor(Color.rgb(100, 116, 139));
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        slp.topMargin = dp(4);
        subtitle.setLayoutParams(slp);
        box.addView(subtitle);

        TextView note = text("Inserisci una volta le 5 chiavi. Ogni nuova GeoVision potrà importarle con un solo pulsante. Le chiavi vengono cifrate nel Keystore Android e restano solo su questo telefono.", 14, false);
        note.setTextColor(Color.rgb(71, 85, 105));
        note.setLineSpacing(0, 1.15f);
        LinearLayout.LayoutParams nlp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        nlp.topMargin = dp(18);
        note.setLayoutParams(nlp);
        box.addView(note);

        g1 = field("Google Maps API 1"); box.addView(g1);
        g2 = field("Google Maps API 2"); box.addView(g2);
        g3 = field("Google Maps API 3"); box.addView(g3);
        ai = field("API Intelligenza Artificiale"); box.addView(ai);
        youtube = field("YouTube Data API"); box.addView(youtube);

        Button save = new Button(this);
        save.setText("SALVA LE 5 CHIAVI");
        save.setAllCaps(false);
        save.setTextSize(16);
        save.setTextColor(Color.WHITE);
        save.setBackgroundColor(Color.rgb(47, 125, 225));
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(54));
        blp.topMargin = dp(20);
        save.setLayoutParams(blp);
        save.setOnClickListener(v -> saveValues());
        box.addView(save);

        status = text("", 14, true);
        status.setGravity(Gravity.CENTER_HORIZONTAL);
        LinearLayout.LayoutParams stlp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        stlp.topMargin = dp(16);
        status.setLayoutParams(stlp);
        box.addView(status);

        return scroll;
    }

    private void loadValues() {
        g1.setText(KeyVault.get(this, KeyVault.G1));
        g2.setText(KeyVault.get(this, KeyVault.G2));
        g3.setText(KeyVault.get(this, KeyVault.G3));
        ai.setText(KeyVault.get(this, KeyVault.AI));
        youtube.setText(KeyVault.get(this, KeyVault.YOUTUBE));
    }

    private void saveValues() {
        try {
            KeyVault.put(this, KeyVault.G1, g1.getText().toString());
            KeyVault.put(this, KeyVault.G2, g2.getText().toString());
            KeyVault.put(this, KeyVault.G3, g3.getText().toString());
            KeyVault.put(this, KeyVault.AI, ai.getText().toString());
            KeyVault.put(this, KeyVault.YOUTUBE, youtube.getText().toString());
            updateStatus();
            Toast.makeText(this, "Chiavi salvate", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Errore nel salvataggio", Toast.LENGTH_LONG).show();
        }
    }

    private void updateStatus() {
        int n = KeyVault.count(this);
        status.setText("Chiavi configurate: " + n + " / 5");
        status.setTextColor(n == 5 ? Color.rgb(22, 163, 74) : Color.rgb(217, 119, 6));
    }
}
