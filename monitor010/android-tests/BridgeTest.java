package it.geovision.test;
import android.app.Activity;
import android.content.*;
import android.os.SystemClock;
import android.view.ViewGroup;
import android.webkit.WebView;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.*;
import org.junit.runner.RunWith;
import java.util.concurrent.*;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class BridgeTest {
 private Activity activity; private WebView web;
 private String js(String script)throws Exception{CountDownLatch latch=new CountDownLatch(1);String[] out={null};InstrumentationRegistry.getInstrumentation().runOnMainSync(()->web.evaluateJavascript(script,s->{out[0]=s;latch.countDown();}));assertTrue(latch.await(10,TimeUnit.SECONDS));return out[0];}
 @Before public void start() throws Exception{Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();activity=InstrumentationRegistry.getInstrumentation().startActivitySync(new Intent(c,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));InstrumentationRegistry.getInstrumentation().runOnMainSync(()->web=(WebView)((ViewGroup)activity.findViewById(android.R.id.content)).getChildAt(0));long end=SystemClock.elapsedRealtime()+45000;while(SystemClock.elapsedRealtime()<end){if("true".equals(js("typeof GVMonitor==='object'")))return;SystemClock.sleep(250);}fail("Monitor script did not initialize on Android WebView");}
 @After public void stop(){if(activity!=null)InstrumentationRegistry.getInstrumentation().runOnMainSync(()->activity.finish());}
 @Test public void signedSyncCrossesActualApplicationBoundary() throws Exception{
  js("window.__received=null;window.gvMonitorSync=function(k){window.__received=k};GeoVisionKeyBox.pageReady();GeoVisionKeyBox.setSyncEnabled(true);");
  long end=SystemClock.elapsedRealtime()+12000;while(SystemClock.elapsedRealtime()<end){if("true".equals(js("!!window.__received")))break;SystemClock.sleep(200);}
  assertEquals("true",js("!!window.__received && ['google1','google2','google3','ai','youtube'].every(n=>typeof __received[n]==='string')"));
  assertEquals("true",js("Number.isInteger(__received.revision)"));
 }
 @Test public void unsolicitedStateCannotReplaceKeys() throws Exception{
  js("window.__received=null;window.gvMonitorSync=function(k){window.__received=k};GeoVisionKeyBox.pageReady();GeoVisionKeyBox.setSyncEnabled(false);");
  Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();Intent forged=new Intent("it.geovision.keybox.KEYS_V1").setPackage(c.getPackageName()).putExtra("nonce","unrequested").putExtra("google1","forged");c.sendBroadcast(forged);SystemClock.sleep(500);assertEquals("true",js("window.__received===null"));
 }
}
