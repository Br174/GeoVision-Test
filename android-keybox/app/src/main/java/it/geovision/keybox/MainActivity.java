package it.geovision.keybox;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
public class MainActivity extends Activity {
    private final EditText[] fields=new EditText[5];
    private final TextView[] dots=new TextView[5],states=new TextView[5];
    private TextView status; private boolean readable=true;
    private final String[] names={"google1","google2","google3","ai","youtube"};
    int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
    TextView text(String s,int size,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(Color.rgb(23,42,69));if(bold)t.setTypeface(Typeface.DEFAULT_BOLD);return t;}
    GradientDrawable bg(int color,int radius){GradientDrawable b=new GradientDrawable();b.setColor(color);b.setCornerRadius(dp(radius));b.setStroke(dp(1),0xffdfe7f1);return b;}
    @Override public void onCreate(Bundle b){super.onCreate(b);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(0xfff6f8fc);
        LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(22),dp(30),dp(22),dp(28));scroll.addView(body);
        body.addView(text("GEOVISION · KEYBOX 007",12,true));body.addView(text("Monitor chiavi",28,true));
        TextView note=text("Archivio condiviso. Verde: chiave salvata e leggibile. Rosso: chiave assente. La verifica dei servizi si trova in GeoVision.",13,false);note.setPadding(0,dp(10),0,dp(14));body.addView(note);
        String[] labels={"Google 1","Google 2","Google 3","Intelligenza artificiale","YouTube"};
        for(int i=0;i<5;i++){
            LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(14),dp(12),dp(14),dp(12));card.setBackground(bg(Color.WHITE,16));
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(10);body.addView(card,lp);
            LinearLayout head=new LinearLayout(this);head.setGravity(Gravity.CENTER_VERTICAL);dots[i]=text("●",20,true);dots[i].setPadding(0,0,dp(10),0);head.addView(dots[i]);head.addView(text(labels[i],16,true));card.addView(head);
            states[i]=text("",12,false);card.addView(states[i]);
            EditText e=new EditText(this);fields[i]=e;e.setSingleLine(true);e.setTextSize(15);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setHint("Incolla la chiave");e.setContentDescription(labels[i]);e.setSaveEnabled(false);e.setBackground(bg(0xfff9fbfe,9));e.setPadding(dp(10),dp(10),dp(10),dp(10));card.addView(e,new LinearLayout.LayoutParams(-1,-2));
        }
        Button save=new Button(this);save.setText("Salva le cinque chiavi");save.setAllCaps(false);save.setTextColor(Color.WHITE);save.setBackground(bg(0xff256bd7,12));body.addView(save,new LinearLayout.LayoutParams(-1,dp(52)));
        status=text("",13,true);status.setPadding(0,dp(16),0,0);body.addView(status);setContentView(scroll);load();
        save.setOnClickListener(v->{if(!readable){status.setText("Archivio non leggibile: salvataggio bloccato per conservare i dati.");return;}try{String[] values=new String[5];for(int i=0;i<5;i++)values[i]=fields[i].getText().toString();KeyVault.putAll(this,values);load();Toast.makeText(this,"Chiavi salvate",Toast.LENGTH_SHORT).show();}catch(Exception e){status.setText("Salvataggio non riuscito. Le chiavi precedenti sono conservate.");}});
    }
    private void load(){try{Bundle b=KeyVault.readAll(this);int count=0;for(int i=0;i<5;i++){String v=b.getString(names[i],"");fields[i].setText(v);boolean present=!v.isEmpty();if(present)count++;dots[i].setTextColor(present?0xff16a34a:0xffdc2626);states[i].setText(present?"Salvata · servizio da verificare in GeoVision":"Chiave assente");}status.setText(count+" / 5 chiavi salvate · revisione "+b.getLong("revision"));}catch(Exception e){readable=false;status.setText("Archivio non leggibile. Nessuna chiave è stata cancellata.");}}
}
