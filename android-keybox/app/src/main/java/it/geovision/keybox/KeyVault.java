package it.geovision.keybox;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
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
    private static final String PREFS="geovision_keybox_v1";
    private static final String ALIAS="GeoVisionKeyBoxMasterV1";
    private static final String[] NAMES={"google1","google2","google3","ai","youtube"};
    private KeyVault(){}

    private static SecretKey key() throws Exception {
        KeyStore ks=KeyStore.getInstance("AndroidKeyStore"); ks.load(null);
        if(ks.containsAlias(ALIAS)) return ((KeyStore.SecretKeyEntry)ks.getEntry(ALIAS,null)).getSecretKey();
        KeyGenerator kg=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
        kg.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
        return kg.generateKey();
    }

    private static String enc(String value) throws Exception {
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding"); c.init(Cipher.ENCRYPT_MODE,key());
        byte[] iv=c.getIV(), data=c.doFinal(value.getBytes(StandardCharsets.UTF_8));
        byte[] out=new byte[1+iv.length+data.length]; out[0]=(byte)iv.length;
        System.arraycopy(iv,0,out,1,iv.length); System.arraycopy(data,0,out,1+iv.length,data.length);
        return Base64.encodeToString(out,Base64.NO_WRAP);
    }

    private static String dec(String value) throws Exception {
        if(value==null||value.isEmpty()) return "";
        byte[] raw=Base64.decode(value,Base64.NO_WRAP); int n=raw[0]&255;
        byte[] iv=new byte[n], data=new byte[raw.length-1-n];
        System.arraycopy(raw,1,iv,0,n); System.arraycopy(raw,1+n,data,0,data.length);
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding"); c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,iv));
        return new String(c.doFinal(data),StandardCharsets.UTF_8);
    }

    static synchronized void putAll(Context c,String[] values) throws Exception {
        if(values==null||values.length!=5) throw new IllegalArgumentException("five keys required");
        SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE); SharedPreferences.Editor e=p.edit();
        for(int i=0;i<5;i++){
            String v=values[i]==null?"":values[i].trim();
            if(v.length()>512||v.contains("\n")||v.contains("\r")) throw new IllegalArgumentException("invalid key");
            if(v.isEmpty()) e.remove(NAMES[i]); else e.putString(NAMES[i],enc(v));
        }
        if(!e.commit()) throw new java.io.IOException("save failed");
    }

    static synchronized Bundle readAll(Context c) throws Exception {
        SharedPreferences p=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE); Bundle b=new Bundle();
        for(String n:NAMES) b.putString(n,dec(p.getString(n,"")));
        return b;
    }
}
