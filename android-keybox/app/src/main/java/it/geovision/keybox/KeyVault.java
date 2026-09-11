package it.geovision.keybox;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

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
    private static final String ACTIVE = "active_index";
    private static final String GENERATION = "active_generation";
    private static final String DAY = "switch_day";
    private static final String TOTAL = "switch_total_day";
    private static final String LAST = "switch_last_time";

    private KeyVault() {}

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

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
        SharedPreferences p = prefs(context);
        String clean = value == null ? "" : value.trim();
        if (clean.isEmpty()) p.edit().remove(name).apply();
        else p.edit().putString(name, encrypt(clean)).apply();
    }

    static String get(Context context, String name) {
        try {
            return decrypt(prefs(context).getString(name, ""));
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

    static int activeIndex(Context context) {
        int i = prefs(context).getInt(ACTIVE, 0);
        if (i < 0 || i > 2) i = 0;
        String[] keys = { get(context, G1), get(context, G2), get(context, G3) };
        if (keys[i].isEmpty()) {
            for (int x = 0; x < 3; x++) if (!keys[x].isEmpty()) return x;
        }
        return i;
    }

    static long generation(Context context) {
        return prefs(context).getLong(GENERATION, 0L);
    }

    private static String today() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
    }

    private static void ensureDay(Context c) {
        SharedPreferences p = prefs(c);
        String now = today();
        if (!now.equals(p.getString(DAY, ""))) {
            p.edit().putString(DAY, now).putInt(TOTAL, 0).remove(LAST).apply();
        }
    }

    static int switchTotalToday(Context c) {
        ensureDay(c);
        return prefs(c).getInt(TOTAL, 0);
    }

    static String lastSwitchTime(Context c) {
        ensureDay(c);
        return prefs(c).getString(LAST, "");
    }

    static boolean setActiveIndex(Context c, int index) {
        if (index < 0 || index > 2) return false;
        String[] keys = { get(c, G1), get(c, G2), get(c, G3) };
        if (keys[index].isEmpty()) return false;
        SharedPreferences p = prefs(c);
        int old = activeIndex(c);
        if (old == index) return false;
        ensureDay(c);
        int total = p.getInt(TOTAL, 0) + 1;
        long gen = p.getLong(GENERATION, 0L) + 1L;
        String when = new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date());
        p.edit()
                .putInt(ACTIVE, index)
                .putLong(GENERATION, gen)
                .putInt(TOTAL, total)
                .putString(LAST, when)
                .apply();
        return true;
    }
}
