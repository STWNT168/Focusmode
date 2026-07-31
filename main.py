"""
Focus Mode
----------
Blocks Instagram, Snapchat, YouTube, and Messages while Focus Mode is ON,
and suppresses all notifications except phone calls (via the bundled
NotificationListenerService in java/org/focusmode/app/NotifListener.java).

App-blocking works by polling UsageStatsManager for the current foreground
app (once per second) and, if it's on the blocklist, sending the user back
to the Home screen. This does not require root.
"""

import time
from threading import Thread, Event

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

# ---- Package names of apps to block ----
BLOCKED_PACKAGES = {
    "com.instagram.android": "Instagram",
    "com.snapchat.android": "Snapchat",
    "com.google.android.youtube": "YouTube",
    "com.google.android.apps.messaging": "Messages",
    "com.samsung.android.messaging": "Messages",
}

POLL_INTERVAL = 1.0  # seconds

try:
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission, check_permission

    ANDROID = True
except Exception:
    ANDROID = False


class ForegroundWatcher:
    """Polls Android's UsageStatsManager to find the current foreground app."""

    def __init__(self, on_blocked_app):
        self.on_blocked_app = on_blocked_app
        self._stop = Event()
        self._thread = None

        if ANDROID:
            self.PythonActivity = autoclass("org.kivy.android.PythonActivity")
            self.Context = autoclass("android.content.Context")
            self.UsageStatsManager = autoclass("android.app.usage.UsageStatsManager")
            self.System = autoclass("java.lang.System")
            activity = self.PythonActivity.mActivity
            self.usm = activity.getSystemService(self.Context.USAGE_STATS_SERVICE)
            self.usm = cast("android.app.usage.UsageStatsManager", self.usm)

    def _get_foreground_package(self):
        end = self.System.currentTimeMillis()
        start = end - 5000  # look back 5s
        events = self.usm.queryEvents(start, end)
        Event_cls = autoclass("android.app.usage.UsageEvents$Event")
        event = Event_cls()
        last_pkg = None
        while events.hasNextEvent():
            events.getNextEvent(event)
            if event.getEventType() == Event_cls.MOVE_TO_FOREGROUND:
                last_pkg = event.getPackageName()
        return last_pkg

    def _go_home(self):
        Intent = autoclass("android.content.Intent")
        intent = Intent(Intent.ACTION_MAIN)
        intent.addCategory(Intent.CATEGORY_HOME)
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        self.PythonActivity.mActivity.startActivity(intent)

    def _loop(self):
        while not self._stop.is_set():
            if ANDROID:
                try:
                    pkg = self._get_foreground_package()
                    if pkg in BLOCKED_PACKAGES:
                        self._go_home()
                        Clock.schedule_once(
                            lambda dt, name=BLOCKED_PACKAGES[pkg]: self.on_blocked_app(name)
                        )
                except Exception as e:
                    print("ForegroundWatcher error:", e)
            time.sleep(POLL_INTERVAL)

    def start(self):
        if self._thread is None:
            self._stop.clear()
            self._thread = Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread = None


class FocusRoot(BoxLayout):
    pass


class FocusModeApp(App):
    def build(self):
        self.store = JsonStore("focus_mode.json")
        self.watcher = ForegroundWatcher(self.on_blocked_attempt)

        root = BoxLayout(orientation="vertical", padding=24, spacing=16)

        title = Label(text="[b]Focus Mode[/b]", markup=True, font_size=28, size_hint_y=None, height=60)
        root.add_widget(title)

        blocked_list = ", ".join(sorted(set(BLOCKED_PACKAGES.values())))
        root.add_widget(Label(text=f"Blocks: {blocked_list}\n+ all notifications except calls"))

        row = BoxLayout(size_hint_y=None, height=60, spacing=12)
        row.add_widget(Label(text="Focus Mode"))
        self.switch = Switch(active=self.store.get("state")["on"] if self.store.exists("state") else False)
        self.switch.bind(active=self.on_toggle)
        row.add_widget(self.switch)
        root.add_widget(row)

        self.status_label = Label(text="")
        root.add_widget(self.status_label)

        perm_btn = Button(text="Grant required permissions", size_hint_y=None, height=56)
        perm_btn.bind(on_release=lambda *_: self.request_perms())
        root.add_widget(perm_btn)

        usage_btn = Button(text="Open Usage Access settings", size_hint_y=None, height=56)
        usage_btn.bind(on_release=lambda *_: self.open_usage_access_settings())
        root.add_widget(usage_btn)

        notif_btn = Button(text="Open Notification Access settings", size_hint_y=None, height=56)
        notif_btn.bind(on_release=lambda *_: self.open_notification_access_settings())
        root.add_widget(notif_btn)

        if self.switch.active:
            self.watcher.start()

        return root

    def on_toggle(self, instance, value):
        self.store.put("state", on=value)
        self._write_focus_pref(value)
        if value:
            self.watcher.start()
            self.status_label.text = "Focus Mode is ON"
        else:
            self.watcher.stop()
            self.status_label.text = "Focus Mode is OFF"

    def _write_focus_pref(self, value):
        """Mirror the on/off state into SharedPreferences so the Java
        NotificationListenerService (which can't read JsonStore) can see it."""
        if not ANDROID:
            return
        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        prefs = activity.getSharedPreferences("focus_mode_prefs", Context.MODE_PRIVATE)
        editor = prefs.edit()
        editor.putBoolean("focus_on", bool(value))
        editor.commit()

    def on_blocked_attempt(self, app_name):
        self.status_label.text = f"Blocked: {app_name}"

    def request_perms(self):
        if not ANDROID:
            return
        request_permissions([
            Permission.POST_NOTIFICATIONS,
            Permission.READ_PHONE_STATE,
        ])

    def open_usage_access_settings(self):
        if not ANDROID:
            return
        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
        self.PythonActivity_start(intent)

    def open_notification_access_settings(self):
        if not ANDROID:
            return
        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        self.PythonActivity_start(intent)

    def PythonActivity_start(self, intent):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        PythonActivity.mActivity.startActivity(intent)


if __name__ == "__main__":
    FocusModeApp().run()
