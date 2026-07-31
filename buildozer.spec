[app]
title = Focus Mode
package.name = focusmode
package.domain = org.focusmode
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xml,json
version = 0.1

requirements = python3,kivy,pyjnius

# Bundle our custom Java service into the APK
android.add_src = java

# Extra manifest entries (permissions + NotificationListenerService)
android.extra_manifest_xml = manifest_extra.xml

orientation = portrait
fullscreen = 0

android.permissions = PACKAGE_USAGE_STATS,READ_PHONE_STATE,POST_NOTIFICATIONS

android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
