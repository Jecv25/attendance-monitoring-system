import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:attendance_monitoring_system/api.dart';
import 'package:attendance_monitoring_system/main.dart';
import 'package:attendance_monitoring_system/attendance.dart';

class FakeApi extends Api {
  bool signedIn = true,
      failDashboard = false,
      failSave = false,
      denyAlerts = false;
  Completer<dynamic>? waiting;
  final List<Map<String, dynamic>> writes = [];
  final user = {
    'id': 2,
    'display_name': 'Demo Teacher',
    'username': 'teacher',
    'role': 'teacher',
    'csrf': 'test-only-placeholder',
  };
  @override
  Future<dynamic> request(
    String method,
    String path, {
    Object? body,
    String? key,
  }) async {
    if (waiting != null && path == '/auth/me') return waiting!.future;
    if (path == '/auth/me') {
      if (!signedIn) throw ApiError(401, 'Sign in to continue');
      return user;
    }
    if (path == '/auth/login') {
      signedIn = true;
      return user;
    }
    if (path == '/dashboard') {
      if (failDashboard) {
        throw ApiError(
          0,
          'Cannot reach the service. Check your connection and retry.',
        );
      }
      return {
        'sessions': 0,
        'finalized': 0,
        'pending_students': 0,
        'totals': {'present': 0, 'late': 0, 'absent': 0, 'excused': 0},
        'recent_sessions': [],
      };
    }
    if (path.startsWith('/alerts') && denyAlerts) {
      throw ApiError(403, 'Your role has read-only access');
    }
    if (method == 'PUT') {
      writes.add({'body': body, 'key': key});
      if (failSave) {
        throw ApiError(0, 'Connection lost; entries are preserved.');
      }
      return {'version': 1};
    }
    return <dynamic>[];
  }
}

Map<String, dynamic> session() => {
  'id': 1,
  'version': 0,
  'title': 'Test session',
  'class_code': 'BSIT-3A',
  'starts_at': '2026-11-08T01:00:00Z',
  'finalized_at': null,
  'students': [
    {
      'student_id': 1,
      'student_code': 'TEST-01',
      'display_name': 'Learner One',
      'status': null,
    },
    {
      'student_id': 2,
      'student_code': 'TEST-02',
      'display_name': 'Learner Two',
      'status': null,
    },
  ],
};

Future<void> width(WidgetTester tester, double value) async {
  tester.view.physicalSize = Size(value, 1000);
  tester.view.devicePixelRatio = 1;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

void main() {
  testWidgets('session restoration displays loading state', (tester) async {
    final api = FakeApi()..waiting = Completer();
    await tester.pumpWidget(AttendanceApp(api: api));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    api.waiting!.complete(api.user);
    await tester.pumpAndSettle();
  });
  testWidgets('unauthenticated login validates required inputs', (
    tester,
  ) async {
    await width(tester, 390);
    await tester.pumpWidget(AttendanceApp(api: FakeApi()..signedIn = false));
    await tester.pumpAndSettle();
    expect(find.text('Welcome back'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Enter your username'), findsOneWidget);
    expect(find.text('Enter your password'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('login opens real client success and empty states', (
    tester,
  ) async {
    await width(tester, 1400);
    await tester.pumpWidget(AttendanceApp(api: FakeApi()..signedIn = false));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).at(0), 'teacher');
    await tester.enterText(find.byType(TextFormField).at(1), 'test-input-only');
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Your attendance overview'), findsOneWidget);
    expect(find.text('No attendance sessions yet.'), findsOneWidget);
  });
  testWidgets('network failure can recover using Retry', (tester) async {
    final api = FakeApi()..failDashboard = true;
    await width(tester, 1400);
    await tester.pumpWidget(AttendanceApp(api: api));
    await tester.pumpAndSettle();
    expect(find.textContaining('Cannot reach the service'), findsOneWidget);
    api.failDashboard = false;
    await tester.tap(find.widgetWithText(OutlinedButton, 'Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Attendance at a glance'), findsOneWidget);
  });
  testWidgets('forbidden state is understandable', (tester) async {
    await width(tester, 1400);
    await tester.pumpWidget(AttendanceApp(api: FakeApi()..denyAlerts = true));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ListTile, 'Alerts'));
    await tester.pumpAndSettle();
    expect(find.text('Your role has read-only access'), findsOneWidget);
  });
  testWidgets('failed save preserves selections and retry idempotency key', (
    tester,
  ) async {
    final api = FakeApi()..failSave = true;
    await width(tester, 800);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: AttendanceEditor(
              api: api,
              session: session(),
              readOnly: false,
              onChanged: () {},
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Mark all present'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save attendance'));
    await tester.pumpAndSettle();
    expect(
      find.text('Connection lost; entries are preserved.'),
      findsOneWidget,
    );
    expect(find.text('Unsaved changes'), findsOneWidget);
    api.failSave = false;
    await tester.tap(find.text('Save attendance'));
    await tester.pumpAndSettle();
    expect(find.text('Saved to the attendance record.'), findsOneWidget);
    expect(find.text('Unsaved changes'), findsNothing);
    expect(api.writes.length, 2);
    expect(api.writes[0]['key'], api.writes[1]['key']);
    expect(api.writes[0]['body'], api.writes[1]['body']);
  });
  testWidgets('finalization requires explicit marking and saved changes', (
    tester,
  ) async {
    await width(tester, 800);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: AttendanceEditor(
              api: FakeApi(),
              session: session(),
              readOnly: false,
              onChanged: () {},
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Finalize session'));
    await tester.pumpAndSettle();
    expect(
      find.text('Explicitly mark every learner before finalizing.'),
      findsOneWidget,
    );
    await tester.tap(find.text('Mark all present'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Finalize session'));
    await tester.pumpAndSettle();
    expect(find.text('Save your changes before finalizing.'), findsOneWidget);
  });
  testWidgets('supervisor attendance has read-only controls', (tester) async {
    await width(tester, 390);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: AttendanceEditor(
              api: FakeApi(),
              session: session(),
              readOnly: true,
              onChanged: () {},
            ),
          ),
        ),
      ),
    );
    expect(find.text('Mark all present'), findsNothing);
    expect(find.text('Save attendance'), findsNothing);
    expect(tester.takeException(), isNull);
  });
  for (final size in [390.0, 768.0, 1440.0]) {
    testWidgets('overview responsive at width $size', (tester) async {
      await width(tester, size);
      await tester.pumpWidget(AttendanceApp(api: FakeApi()));
      await tester.pumpAndSettle();
      expect(find.text('Your attendance overview'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
