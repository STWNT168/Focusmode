# Focus Mode

A Kivy Android app that blocks Instagram, Snapchat, YouTube, and Messages,
and mutes all notifications except calls, while turned on.

## How it works
- **App blocking**: polls `UsageStatsManager` once a second for the
  foreground app; if it's on the blocklist, sends you to the Home screen.
  No root required.
- **Notification blocking**: a small bundled Java `NotificationListenerService`
  (`java/org/focusmode/app/NotifListener.java`) cancels every notification
  except ones from the phone/dialer app, so calls still ring.

## Build via GitHub (no local Android SDK needed)
1. Create a new GitHub repo and push this whole folder to it (including
   `.github/workflows/build.yml`).
2. Go to the repo's **Actions** tab → the "Build Focus Mode APK" workflow
   runs automatically on push (first build takes ~15–25 min, it's
   downloading the Android SDK/NDK).
3. When it finishes, open the workflow run → **Artifacts** → download
   `focus-mode-apk`, which contains the `.apk`.
4. Transfer the APK to your phone and install it (you'll need to allow
   "install from unknown sources" once).

## After installing, on your phone
Open the app and tap:
1. **Grant required permissions** — allows POST_NOTIFICATIONS / phone state.
2. **Open Usage Access settings** — find "Focus Mode" in the list and
   enable it. Required for foreground-app detection.
3. **Open Notification Access settings** — find "Focus Mode Notification
   Filter" and enable it. Required for notification blocking.
4. Flip the **Focus Mode** switch on.

These two settings screens are Android system screens the app can open
for you but can't toggle itself — that's an Android security restriction,
not something the app can bypass.

## Editing what's blocked
Package names live at the top of `main.py` in `BLOCKED_PACKAGES`. Add or
remove entries as `"com.package.name": "Display Name"`.

## Known limitations
- Detection polls every second, so there can be a brief flash of a
  blocked app before it's kicked to Home.
- Some OEM Android skins (Samsung, Xiaomi, etc.) require you to also
  disable battery optimization for the app, or the OS may suspend the
  polling thread in the background.
- This is a self-control tool, not a tamper-proof parental control —
  a user with the permissions above can always re-disable them for their
  own device.
