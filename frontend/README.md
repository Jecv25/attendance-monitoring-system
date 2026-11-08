# Presence — Flutter Web client

Responsive Attendance Monitoring System client. See the [root README](../README.md) for accounts, backend/worker setup and same-origin release serving.

```powershell
flutter pub get
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 7357 --dart-define=API_BASE=http://127.0.0.1:8000/api
flutter analyze
flutter test
flutter build web --no-web-resources-cdn
```

The release uses `/api` by default. Credentials are held in HttpOnly backend cookies; only the CSRF value is retained in memory. No confidential API or report keys belong in `--dart-define` or compiled assets. Real HTTP requests go through `lib/api.dart`; tests inject a client fixture to isolate UI states. Persistent accessibility semantics support keyboard/screen-reader navigation.

The required target is web. Android/iOS builds are not part of the assessment deliverable.
