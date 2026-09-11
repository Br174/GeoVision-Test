package it.geovision.keybox;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.*;
import org.junit.runner.RunWith;
import android.content.*;
import android.os.Bundle;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class VaultTest {
 Context c;
 @Before public void setup(){c=InstrumentationRegistry.getInstrumentation().getTargetContext();c.getSharedPreferences("geovision_keybox_v1",0).edit().clear().commit();}
 @After public void clear(){c.getSharedPreferences("geovision_keybox_v1",0).edit().clear().commit();}
 @Test public void legacy005CiphertextStillReadable() throws Exception{KeyVault.put(c,"google1","SYNTHETIC_005");assertEquals("SYNTHETIC_005",KeyVault.readAll(c).getString("google1"));assertFalse(c.getSharedPreferences("geovision_keybox_v1",0).getString("google1","").contains("SYNTHETIC"));}
 @Test public void fiveKeysAtomicRoundtrip() throws Exception{KeyVault.putAll(c,new String[]{"g1","g2","g3","ai","yt"});Bundle b=KeyVault.readAll(c);assertEquals("g1",b.getString("google1"));assertEquals("g2",b.getString("google2"));assertEquals("g3",b.getString("google3"));assertEquals("ai",b.getString("ai"));assertEquals("yt",b.getString("youtube"));assertEquals(1,b.getLong("revision"));}
 @Test public void invalidBatchLeavesPreviousVault() throws Exception{KeyVault.putAll(c,new String[]{"g1","g2","g3","ai","yt"});try{KeyVault.putAll(c,new String[]{"changed","invalid\nkey","g3","ai","yt"});fail();}catch(IllegalArgumentException expected){}assertEquals("g1",KeyVault.readAll(c).getString("google1"));assertEquals(1,KeyVault.readAll(c).getLong("revision"));}
 @Test public void deletingOneSlotPreservesOthers() throws Exception{KeyVault.putAll(c,new String[]{"g1","g2","g3","ai","yt"});KeyVault.putAll(c,new String[]{"g1","","g3","ai","yt"});assertEquals("",KeyVault.readAll(c).getString("google2"));assertEquals("g3",KeyVault.readAll(c).getString("google3"));assertEquals(2,KeyVault.readAll(c).getLong("revision"));}
 @Test public void corruptCiphertextRejectsWholeSnapshot() throws Exception{c.getSharedPreferences("geovision_keybox_v1",0).edit().putString("ai","AA==").commit();try{KeyVault.readAll(c);fail("Corruption must not export empty keys");}catch(Exception expected){}assertEquals("AA==",c.getSharedPreferences("geovision_keybox_v1",0).getString("ai",""));}
 @Test public void emptyAndWrongCountRejected() throws Exception{try{KeyVault.putAll(c,new String[]{"one"});fail();}catch(IllegalArgumentException expected){}assertEquals(0,KeyVault.readAll(c).getLong("revision"));}
 @Test public void signaturePermissionProtectsReceiver() throws Exception{android.content.pm.ActivityInfo i=c.getPackageManager().getReceiverInfo(new ComponentName(c,SyncReceiver.class),0);assertEquals("it.geovision.permission.KEYBOX_IMPORT",i.permission);assertTrue(i.exported);android.content.pm.PermissionInfo p=c.getPackageManager().getPermissionInfo(i.permission,0);assertEquals(android.content.pm.PermissionInfo.PROTECTION_SIGNATURE,p.protectionLevel);}
 @Test public void rejectedRequestDoesNotSendKeys(){int count=KeyVault.count(c);new SyncReceiver().onReceive(c,new Intent("unexpected"));new SyncReceiver().onReceive(c,new Intent("it.geovision.keybox.GET_KEYS_V1").putExtra("replyPackage","other.package").putExtra("nonce","test"));assertEquals(count,KeyVault.count(c));}
}
