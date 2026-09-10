package it.geovision.keybox;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class KeyVault {
    static final String G1 = "google1";
    static final String G2 = "google2";
    static final String G3 = "google3";
    static final String AI = "ai";
    static final String YOUTUBE = "youtube";

    private static final String PREFS = "geovision_keybox_v1";
    private static final String ALIAS = "GeoVisionKeyBoxMasterV1";

    private KeyVault() {}

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        if (ks.containsAlias(ALIAS)) {
            return ((KeyStore.SecretKeyEntry) ks.getEntry(ALIAS, null)).getSecretKey();
        }
        KeyGenerator kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
                ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build();
        kg.init(spec);
        return kg.generateKey();
    }

    private static String encrypt(String value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] iv = cipher.getIV();
        byte[] encrypted = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
        byte[] packed = new byte[1 + iv.length + encrypted.length];
        packed[0] = (byte) iv.length;
        System.arraycopy(iv, 0, packed, 1, iv.length);
        System.arraycopy(encrypted, 0, packed, 1 + iv.length, encrypted.length);
        return Base64.encodeToString(packed, Base64.NO_WRAP);
    }

    private static String decrypt(String packed64) throws Exception {
        if (packed64 == null || packed64.isEmpty()) return "";
        byte[] packed = Base64.decode(packed64, Base64.NO_WRAP);
        int ivLen = packed[0] & 0xff;
        if (ivLen < 8 || ivLen > 32 || packed.length <= 1 + ivLen) return "";
        byte[] iv = new byte[ivLen];
        byte[] encrypted = new byte[packed.length - 1 - ivLen];
        System.arraycopy(packed, 1, iv, 0, ivLen);
        System.arraycopy(packed, 1 + ivLen, encrypted, 0, encrypted.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
    }

    static void put(Context context, String name, String value) throws Exception {
        SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String clean = value == null ? "" : value.trim();
        if (clean.isEmpty()) p.edit().remove(name).apply();
        else p.edit().putString(name, encrypt(clean)).apply();
    }

    static String get(Context context, String name) {
        try {
            SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            return decrypt(p.getString(name, ""));
        } catch (Exception e) {
            return "";
        }
    }

    static int count(Context context) {
        int n = 0;
        if (!get(context, G1).isEmpty()) n++;
        if (!get(context, G2).isEmpty()) n++;
        if (!get(context, G3).isEmpty()) n++;
        if (!get(context, AI).isEmpty()) n++;
        if (!get(context, YOUTUBE).isEmpty()) n++;
        return n;
    }
}
