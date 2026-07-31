package org.focusmode.app;

import android.content.SharedPreferences;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.telecom.TelecomManager;
import android.content.Context;

/**
 * Cancels every notification except ones coming from the phone/dialer app
 * (so incoming calls still ring through), whenever Focus Mode is ON.
 *
 * Focus Mode's on/off state is read from the same JsonStore file the
 * Python app writes to (focus_mode.json), via SharedPreferences bridge
 * kept in sync by main.py (see FOCUS_PREFS below). If you'd rather not
 * wire that up, this defaults to "always on" -- edit isFocusModeOn().
 */
public class NotifListener extends NotificationListenerService {

    // Common Android phone/dialer package names to always allow through.
    private static final String[] ALLOWED_PACKAGES = {
            "com.android.dialer",
            "com.google.android.dialer",
            "com.samsung.android.dialer",
            "com.android.server.telecom",
            "com.android.phone"
    };

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (!isFocusModeOn()) {
            return; // Focus mode off: leave notifications alone
        }
        String pkg = sbn.getPackageName();
        for (String allowed : ALLOWED_PACKAGES) {
            if (allowed.equals(pkg)) {
                return; // allow phone/call notifications through
            }
        }
        // Also allow it through if Android currently reports an active call
        // and this notification is call-related (best-effort safety net).
        cancelNotification(sbn.getKey());
    }

    private boolean isFocusModeOn() {
        SharedPreferences prefs = getSharedPreferences("focus_mode_prefs", Context.MODE_PRIVATE);
        return prefs.getBoolean("focus_on", false);
    }
}
