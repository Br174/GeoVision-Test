package it.geovision.keybox;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.widget.*;

public class MainActivity extends Activity {
    private final EditText[] fields = new EditText[5];
    private final String[] names = {"google1","google2","google3","ai","youtube"};
    private final String[] labels = {"Google 1","Google 2","Google 3","Intelligenza artificiale","YouTube"};
    private TextView status;

    private int dp(int v){ return Math.round(v*getResources().getDisplayMetrics().density); }
    private GradientDrawable box(int color,int radius){ GradientDrawable g=new GradientDrawable(); g.setColor(color); g.setCornerRadius(dp(radius)); g.setStroke(dp(1),0xffe2e8f0); return g; }
    private TextView text(String s,int size,boolean bold){ TextView t=new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(0xff1f2937); if(bold)t.setTypeface(Typeface.DEFAULT_BOLD); return t; }

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        ScrollView scroll=new ScrollView(this);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(20),dp(28),dp(20),dp(28)); root.setBackgroundColor(0xfff8fafc); scroll.addView(root);
        root.addView(text("GeoVision KeyBox",28,true));
        TextView note=text("Inserisci qui le chiavi una sola volta. Nelle app GeoVision usa Importa da KeyBox per copiarle.",14,false); note.setPadding(0,dp(8),0,dp(18)); root.addView(note);
        for(int i=0;i<5;i++){
            TextView lab=text(labels[i],14,true); lab.setPadding(0,dp(8),0,dp(5)); root.addView(lab);
            EditText e=new EditText(this); fields[i]=e; e.setSingleLine(true); e.setHint("Incolla la chiave"); e.setTextSize(14); e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD); e.setBackground(box(Color.WHITE,12)); e.setPadding(dp(12),dp(11),dp(12),dp(11));
            LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(-1,-2); ep.bottomMargin=dp(6); root.addView(e,ep);
        }
        Button save=new Button(this); save.setText("Salva chiavi"); save.setAllCaps(false); save.setTextColor(Color.WHITE); save.setBackground(box(0xff2f7de1,12)); LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1,dp(52)); bp.topMargin=dp(14); root.addView(save,bp);
        status=text("",13,true); status.setPadding(0,dp(14),0,0); root.addView(status);
        setContentView(scroll);
        load();
        save.setOnClickListener(v->{
            try{
                String[] values=new String[5]; for(int i=0;i<5;i++) values[i]=fields[i].getText().toString().trim();
                KeyVault.putAll(this,values); load(); Toast.makeText(this,"Chiavi salvate",Toast.LENGTH_SHORT).show();
            }catch(Exception e){ status.setText("Salvataggio non riuscito"); }
        });
    }

    private void load(){
        try{
            Bundle b=KeyVault.readAll(this); int count=0;
            for(int i=0;i<5;i++){ String v=b.getString(names[i],""); fields[i].setText(v); if(!v.isEmpty()) count++; }
            status.setText(count+" / 5 chiavi salvate");
        }catch(Exception e){ status.setText("Archivio non leggibile"); }
    }
}
