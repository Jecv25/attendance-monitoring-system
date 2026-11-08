import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';

import 'api.dart';
import 'workspace.dart';

void main() => runApp(const AttendanceApp());
const ink = Color(0xFF182B35);
const teal = Color(0xFF167D71);
const paper = Color(0xFFF5F7F8);

class AttendanceApp extends StatefulWidget {
  final Api? api;
  const AttendanceApp({super.key, this.api});
  @override
  State<AttendanceApp> createState() => _AttendanceAppState();
}

class _AttendanceAppState extends State<AttendanceApp> {
  late final SemanticsHandle semantics;
  late final Api api = widget.api ?? Api();
  Map<String, dynamic>? user;
  bool restoring = true;
  String? restoreError;
  @override
  void initState() {
    super.initState();
    semantics = SemanticsBinding.instance.ensureSemantics();
    restore();
  }

  @override
  void dispose() {
    semantics.dispose();
    super.dispose();
  }

  Future<void> restore() async {
    setState(() {
      restoring = true;
      restoreError = null;
    });
    try {
      user = await api.restore();
    } on ApiError catch (error) {
      if (error.status != 401) restoreError = error.message;
    }
    if (mounted) setState(() => restoring = false);
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Attendance Monitoring System',
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: teal,
        primary: teal,
        surface: Colors.white,
      ),
      scaffoldBackgroundColor: paper,
      fontFamily: 'Arial',
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 30,
          fontWeight: FontWeight.w700,
          color: ink,
        ),
        titleLarge: TextStyle(fontWeight: FontWeight.w700, color: ink),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Color(0xFFDCE3E7)),
        ),
        contentPadding: const EdgeInsets.all(16),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 19),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: Colors.white,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: Color(0xFFE0E7EA)),
        ),
      ),
      dividerTheme: const DividerThemeData(color: Color(0xFFE7ECEF)),
    ),
    home: restoring
        ? const Scaffold(
            body: Center(
              child: CircularProgressIndicator(
                semanticsLabel: 'Restoring session',
              ),
            ),
          )
        : user == null
        ? LoginPage(
            api: api,
            initialError: restoreError,
            onLogin: (value) => setState(() => user = value),
          )
        : Workspace(
            api: api,
            user: user!,
            onSignedOut: () => setState(() {
              user = null;
              api.csrf = null;
            }),
          ),
  );
}

class LoginPage extends StatefulWidget {
  final Api api;
  final ValueChanged<Map<String, dynamic>> onLogin;
  final String? initialError;
  const LoginPage({
    super.key,
    required this.api,
    required this.onLogin,
    this.initialError,
  });
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final form = GlobalKey<FormState>();
  final username = TextEditingController(), password = TextEditingController();
  bool busy = false, obscure = true;
  String? error;
  @override
  void initState() {
    super.initState();
    error = widget.initialError;
  }

  @override
  void dispose() {
    username.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (!form.currentState!.validate() || busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final result = await widget.api.login(username.text, password.text);
      if (mounted) widget.onLogin(result);
    } on ApiError catch (value) {
      if (mounted) setState(() => error = value.message);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: LayoutBuilder(
      builder: (context, bounds) {
        final formPanel = Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 410),
              child: Form(
                key: form,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.fact_check_rounded, color: teal, size: 38),
                    const SizedBox(height: 26),
                    Text(
                      'Welcome back',
                      style: Theme.of(context).textTheme.headlineLarge,
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Sign in to your attendance workspace.',
                      style: TextStyle(color: Color(0xFF657680), fontSize: 16),
                    ),
                    const SizedBox(height: 32),
                    TextFormField(
                      controller: username,
                      decoration: const InputDecoration(
                        labelText: 'Username',
                        prefixIcon: Icon(Icons.person_outline),
                      ),
                      autofillHints: const [AutofillHints.username],
                      textInputAction: TextInputAction.next,
                      maxLength: 40,
                      validator: (v) => (v ?? '').trim().length < 3
                          ? 'Enter your username (at least 3 characters)'
                          : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: password,
                      obscureText: obscure,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          tooltip: obscure ? 'Show password' : 'Hide password',
                          onPressed: () => setState(() => obscure = !obscure),
                          icon: Icon(
                            obscure
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                        ),
                      ),
                      autofillHints: const [AutofillHints.password],
                      onFieldSubmitted: (_) => submit(),
                      validator: (v) =>
                          (v ?? '').isEmpty ? 'Enter your password' : null,
                    ),
                    if (error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 18),
                        child: Semantics(
                          liveRegion: true,
                          child: Text(
                            error!,
                            style: const TextStyle(color: Color(0xFFB3261E)),
                          ),
                        ),
                      ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: busy ? null : submit,
                        child: Text(busy ? 'Signing in…' : 'Sign in'),
                      ),
                    ),
                    const SizedBox(height: 26),
                    const Text(
                      'Access is limited to authorized school personnel.\nAsk your administrator if you need an account.',
                      style: TextStyle(
                        color: Color(0xFF657680),
                        height: 1.7,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
        final branding = Container(
          color: ink,
          padding: const EdgeInsets.all(54),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(
                    Icons.fact_check_rounded,
                    color: Color(0xFF8DDFCD),
                    size: 30,
                  ),
                  SizedBox(width: 12),
                  Text(
                    'presence',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 28,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              const Text(
                'Every class.\nEvery learner.\nAccounted for.',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 46,
                  fontWeight: FontWeight.w700,
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'A clear view of attendance, with dependable\nrecords and reminders that keep you on track.',
                style: TextStyle(
                  color: Color(0xFFBFCFD5),
                  height: 1.8,
                  fontSize: 16,
                ),
              ),
              const Spacer(),
              const Text(
                'ATTENDANCE MONITORING SYSTEM',
                style: TextStyle(
                  color: Color(0xFF9EB8BD),
                  letterSpacing: 2,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        );
        return bounds.maxWidth >= 900
            ? Row(
                children: [
                  Expanded(child: branding),
                  Expanded(child: formPanel),
                ],
              )
            : formPanel;
      },
    ),
  );
}
