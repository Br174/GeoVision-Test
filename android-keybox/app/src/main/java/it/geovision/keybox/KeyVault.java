package it.geovision.keybox;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class KeyVault {
    static final String G1="google1",G2="google2",G3="google3",AI="ai",YOUTUBE="youtube";
    private static final String PREFS="geovision_keybox_v1",ALIAS="GeoVisionKeyBoxMasterV1";
    private static final String[] EN={"google1_enabled_v1","google2_enabled_v1","google3_enabled_v1"};
    private KeyVault(){}
    private static SecretKey getOrCreateKey() throws Exception {KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);if(ks.containsAlias(ALIAS))return((KeyStore.SecretKeyEntry)ks.getEntry(ALIAS,null)).getSecretKey();KeyGenerator kg=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");kg.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());return kg.generateKey();}
    private static String encrypt(String value)throws Exception{Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,getOrCreateKey());byte[]iv=c.getIV(),enc=c.doFinal(value.getBytes(StandardCharsets.UTF_8)),p=new byte[1+iv.length+enc.length];p[0]=(byte)iv.length;System.arraycopy(iv,0,p,1,iv.length);System.arraycopy(enc,0,p,1+iv.length,enc.length);return Base64.encodeToString(p,Base64.NO_WRAP);}
    private static String decrypt(String s)throws Exception{if(s==null||s.isEmpty())return"";byte[]p=Base64.decode(s,Base64.NO_WRAP);if(p.length<2)throw new IllegalArgumentException("invalid vault");int n=p[0]&255;if(n<8||n>32||p.length<1+n+16)throw new IllegalArgumentException("invalid vault");byte[]iv=new byte[n],enc=new byte[p.length-1-n];System.arraycopy(p,1,iv,0,n);System.arraycopy(p,1+n,enc,0,enc.length);Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,getOrCreateKey(),new GCMParameterSpec(128,iv));return new String(c.doFinal(enc),StandardCharsets.UTF_8);}
    static synchronized android.os.Bundle readAll(Context c)throws Exception{SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);android.os.Bundle b=new android.os.Bundle();for(String n:new String[]{G1,G2,G3,AI,YOUTUBE})b.putString(n,decrypt(p.getString(n,"")));b.putLong("revision",p.getLong("keys_revision_v1",0));boolean[]e=enabled(c);b.putBooleanArray("googleEnabled",e);b.putBoolean("google1Enabled",e[0]);b.putBoolean("google2Enabled",e[1]);b.putBoolean("google3Enabled",e[2]);return b;}
    static synchronized void putAll(Context c,String[]values)throws Exception{putAll(c,values,enabled(c));}
    static synchronized void putAll(Context c,String[]values,boolean[]enabled)throws Exception{if(values==null||values.length!=5)throw new IllegalArgumentException("five keys required");if(enabled==null||enabled.length!=3)enabled=new boolean[]{true,true,true};String[]names={G1,G2,G3,AI,YOUTUBE};SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);SharedPreferences.Editor ed=p.edit();for(int i=0;i<5;i++){String v=values[i]==null?"":values[i].trim();if(v.length()>512||v.contains("\n")||v.contains("\r"))throw new IllegalArgumentException("invalid key");if(v.isEmpty())ed.remove(names[i]);else ed.putString(names[i],encrypt(v));}for(int i=0;i<3;i++)ed.putBoolean(EN[i],enabled[i]);ed.putLong("keys_revision_v1",p.getLong("keys_revision_v1",0)+1);if(!ed.commit())throw new java.io.IOException("vault commit failed");}
    static synchronized boolean[] enabled(Context c){SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);return new boolean[]{p.getBoolean(EN[0],true),p.getBoolean(EN[1],true),p.getBoolean(EN[2],true)};}
    static synchronized void setEnabled(Context c,int index,boolean on){if(index<0||index>2)return;SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);boolean old=p.getBoolean(EN[index],true);if(old==on)return;SharedPreferences.Editor e=p.edit().putBoolean(EN[index],on).putLong("keys_revision_v1",p.getLong("keys_revision_v1",0)+1);e.commit();}
    static void put(Context c,String n,String v)throws Exception{SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE);String x=v==null?"":v.trim();if(x.isEmpty())p.edit().remove(n).apply();else p.edit().putString(n,encrypt(x)).apply();}
    static String get(Context c,String n){try{return decrypt(c.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString(n,""));}catch(Exception e){return"";}}
    static int count(Context c){int n=0;for(String k:new String[]{G1,G2,G3,AI,YOUTUBE})if(!get(c,k).isEmpty())n++;return n;}
}
