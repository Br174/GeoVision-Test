#!/usr/bin/env bash
set -euo pipefail
SRC='android-youtube-test/madre001/build_keybox_003_monitor.sh'
TMP='/tmp/build_keybox_004_full_monitor.sh'
cp "$SRC" "$TMP"
python - <<'PY'
from pathlib import Path
p=Path('/tmp/build_keybox_004_full_monitor.sh')
s=p.read_text()
s=s.replace("versionCode 2003; versionName '3.0-key-monitor'", "versionCode 2004; versionName '4.0-full-monitor'")
s=s.replace('android:label="KEYBOX 003 MONITOR"', 'android:label="KEYBOX 004 MONITOR"')
s=s.replace('GeoVision KeyBox 003', 'GeoVision KeyBox 004')
s=s.replace('Chiavi condivise + stato attivo + contatore switch giornaliero', 'Stato live delle 5 chiavi + sincronizzazione Google + contatori switch')
old="""String[][] rows={{\"google1\",\"Google Maps API 1\"},{\"google2\",\"Google Maps API 2\"},{\"google3\",\"Google Maps API 3\"},{\"ai\",\"API Intelligenza Artificiale\"},{\"youtube\",\"YouTube Data API\"}};int gi=0;for(String[] r:rows){if(gi<3){LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);TextView d=t(\"●\",25,true);d.setPadding(0,0,dp(10),0);dots[gi]=d;head.addView(d);TextView lab=t(r[1],14,true);head.addView(lab);l.addView(head);TextView st=t(\"\",12,false);stats[gi]=st;l.addView(st);}else l.addView(t(r[1],14,true));EditText e=new EditText(this);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setText(KeyVault.get(this,r[0]));l.addView(e);f.put(r[0],e);gi++;}"""
new="""String[][] rows={{\"google1\",\"Google Maps API 1\"},{\"google2\",\"Google Maps API 2\"},{\"google3\",\"Google Maps API 3\"},{\"ai\",\"API Intelligenza Artificiale\"},{\"youtube\",\"YouTube Data API\"}};int gi=0;for(String[] r:rows){LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);TextView d=t(\"●\",25,true);d.setPadding(0,0,dp(10),0);if(gi<3)dots[gi]=d;head.addView(d);TextView lab=t(r[1],14,true);head.addView(lab);l.addView(head);if(gi<3){TextView st=t(\"\",12,false);stats[gi]=st;l.addView(st);}else{final String keyName=r[0];d.setTag(keyName);TextView st=t(\"\",12,false);st.setTag(\"status_\"+keyName);l.addView(st);}EditText e=new EditText(this);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);e.setText(KeyVault.get(this,r[0]));l.addView(e);f.put(r[0],e);gi++;}"""
if old not in s: raise SystemExit('rows block not found')
s=s.replace(old,new,1)
old2="""void update(){KeyVault.ensureDay(this);int c=0;for(String k:f.keySet())if(!KeyVault.get(this,k).isEmpty())c++;int a=KeyVault.active(this);for(int i=0;i<3;i++){boolean on=i==a;dots[i].setTextColor(on?Color.rgb(22,163,74):Color.rgb(220,38,38));stats[i].setText((on?\"ATTIVA ORA\":\"INATTIVA\")+\"  •  Switch oggi: \"+KeyVault.keyToday(this,i));stats[i].setTextColor(on?Color.rgb(22,101,52):Color.rgb(127,29,29));}long ls=KeyVault.lastSwitchAt(this);String when=ls>0?new SimpleDateFormat(\"HH:mm\",Locale.getDefault()).format(new Date(ls)):\"nessuno\";status.setText(\"Chiavi configurate: \"+c+\" / 5\\nChiave Google attiva globale: \"+(a+1)+\"\\nSwitch totali oggi: \"+KeyVault.totalToday(this)+\"\\nUltimo switch: \"+when+\"\\nGenerazione sync: \"+KeyVault.generation(this));}"""
new2="""void update(){KeyVault.ensureDay(this);int c=0;for(String k:f.keySet())if(!KeyVault.get(this,k).isEmpty())c++;int a=KeyVault.active(this);for(int i=0;i<3;i++){boolean on=i==a;dots[i].setTextColor(on?Color.rgb(34,197,94):Color.rgb(239,68,68));stats[i].setText((on?\"ATTIVA ORA\":\"INATTIVA\")+\"  •  Switch oggi: \"+KeyVault.keyToday(this,i));stats[i].setTextColor(on?Color.rgb(22,101,52):Color.rgb(127,29,29));}View root=((ViewGroup)findViewById(android.R.id.content)).getChildAt(0);updateServiceDot(root,\"ai\",!KeyVault.get(this,\"ai\").isEmpty());updateServiceDot(root,\"youtube\",!KeyVault.get(this,\"youtube\").isEmpty());long ls=KeyVault.lastSwitchAt(this);String when=ls>0?new SimpleDateFormat(\"HH:mm\",Locale.getDefault()).format(new Date(ls)):\"nessuno\";status.setText(\"Chiavi configurate: \"+c+\" / 5\\nChiave Google attiva globale: \"+(a+1)+\"\\nSwitch totali oggi: \"+KeyVault.totalToday(this)+\"\\nUltimo switch: \"+when+\"\\nGenerazione sync: \"+KeyVault.generation(this));}\n void updateServiceDot(View v,String key,boolean on){if(v==null)return;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)updateServiceDot(g.getChildAt(i),key,on);}Object tag=v.getTag();if(key.equals(tag)&&v instanceof TextView)((TextView)v).setTextColor(on?Color.rgb(34,197,94):Color.rgb(239,68,68));if((\"status_\"+key).equals(tag)&&v instanceof TextView){TextView t=(TextView)v;t.setText(on?\"ATTIVA · chiave configurata\":\"INATTIVA · chiave assente\");t.setTextColor(on?Color.rgb(22,101,52):Color.rgb(127,29,29));}}"""
if old2 not in s: raise SystemExit('update block not found')
s=s.replace(old2,new2,1)
s=s.replace('GeoVision_KEYBOX_003_MONITOR.apk','GeoVision_KEYBOX_004_MONITOR.apk')
s=s.replace('README_KEYBOX_003_MONITOR.txt','README_KEYBOX_004_MONITOR.txt')
s=s.replace('GeoVision_KEYBOX_003_MONITOR.zip','GeoVision_KEYBOX_004_MONITOR.zip')
s=s.replace('GeoVision KEYBOX 003 MONITOR','GeoVision KEYBOX 004 MONITOR')
s=s.replace("grep -q \"application-label:'KEYBOX 003 MONITOR'\"", "grep -q \"application-label:'KEYBOX 004 MONITOR'\"")
s=s.replace('Indicatori: verde = chiave Google attiva globale; rosso = chiave non attiva.', 'Indicatori Google: verde = chiave attiva globale; rosso = chiave non attiva. Indicatori AI/YouTube: verde = chiave configurata e disponibile all’app; rosso = chiave assente/non configurata.')
p.write_text(s)
PY
bash "$TMP"
