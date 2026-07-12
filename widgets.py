[app]
title = Mandy
package.name = mandy
package.domain = com.santosh.mandy

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json

version = 0.1

requirements = python3,kivy==2.3.0,pyjnius

orientation = landscape
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = RECORD_AUDIO,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,CALL_PHONE,READ_CONTACTS,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
