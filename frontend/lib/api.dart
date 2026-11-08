import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import 'client_factory.dart';

class ApiError implements Exception {
  final int status;
  final String message;
  ApiError(this.status, this.message);
  @override
  String toString() => message;
}

class Api {
  final http.Client client;
  final String base;
  String? csrf;
  Api({http.Client? client, String? base})
    : client = client ?? createClient(),
      base =
          base ??
          const String.fromEnvironment('API_BASE', defaultValue: '/api');

  String newKey() {
    final random = Random.secure();
    return List.generate(
      24,
      (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
    ).join();
  }

  Future<dynamic> request(
    String method,
    String path, {
    Object? body,
    String? key,
  }) async {
    final request = http.Request(method, Uri.parse('$base$path'));
    request.headers['Content-Type'] = 'application/json';
    if (csrf != null) request.headers['X-CSRF-Token'] = csrf!;
    if (key != null) request.headers['Idempotency-Key'] = key;
    if (body != null) request.body = jsonEncode(body);
    http.Response response;
    try {
      response = await http.Response.fromStream(await client.send(request))
          .timeout(const Duration(seconds: 12));
    } on TimeoutException {
      throw ApiError(
        0,
        'The service took too long. Your entries are preserved; retry safely.',
      );
    } on http.ClientException {
      throw ApiError(
        0,
        'Cannot reach the service. Check your connection and retry.',
      );
    }
    dynamic data;
    try {
      data = jsonDecode(response.body);
    } catch (_) {
      throw ApiError(
        response.statusCode,
        'The service returned an unexpected response. Please retry.',
      );
    }
    if (response.statusCode >= 400) {
      final details = data is Map ? data['detail'] : null;
      final fields = data is Map ? data['errors'] : null;
      final message = details is String
          ? details
          : 'The request could not be completed.';
      throw ApiError(
        response.statusCode,
        fields is List && fields.isNotEmpty
            ? '$message: ${fields.first['message']}'
            : message,
      );
    }
    return data;
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final user = Map<String, dynamic>.from(
      await request(
        'POST',
        '/auth/login',
        body: {'username': username.trim(), 'password': password},
      ),
    );
    csrf = user['csrf'];
    return user;
  }

  Future<Map<String, dynamic>> restore() async {
    final user = Map<String, dynamic>.from(await request('GET', '/auth/me'));
    csrf = user['csrf'];
    return user;
  }
}
