import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import 'api_exception.dart';

class ApiClient {
  ApiClient({
    required String baseUrl,
    http.Client? httpClient,
    Duration? defaultTimeout,
  })  : _baseUrl = AppConfig.normalizeBaseUrl(baseUrl),
        _client = httpClient ?? http.Client(),
        _defaultTimeout = defaultTimeout ?? AppConfig.standardTimeout;

  String _baseUrl;
  final http.Client _client;
  final Duration _defaultTimeout;

  String get baseUrl => _baseUrl;

  void updateBaseUrl(String newBaseUrl) {
    _baseUrl = AppConfig.normalizeBaseUrl(newBaseUrl);
  }

  Uri buildUri(String apiPath, {Map<String, String>? queryParameters}) {
    final normalizedPath = apiPath.startsWith('/') ? apiPath : '/$apiPath';
    final uri = Uri.parse('$_baseUrl/api/v1$normalizedPath');
    if (queryParameters == null || queryParameters.isEmpty) {
      return uri;
    }
    return uri.replace(queryParameters: queryParameters);
  }

  Future<Map<String, dynamic>> getJson(
    String path, {
    Map<String, String>? queryParameters,
    Duration? timeout,
    void Function()? onSlowRequest,
  }) {
    return _send(
      method: 'GET',
      path: path,
      queryParameters: queryParameters,
      timeout: timeout,
      onSlowRequest: onSlowRequest,
    );
  }

  Future<Map<String, dynamic>> postJson(
    String path, {
    required Map<String, dynamic> body,
    Map<String, String>? queryParameters,
    Duration? timeout,
    void Function()? onSlowRequest,
  }) {
    return _send(
      method: 'POST',
      path: path,
      body: body,
      queryParameters: queryParameters,
      timeout: timeout,
      onSlowRequest: onSlowRequest,
    );
  }

  Future<Map<String, dynamic>> _send({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    Map<String, String>? queryParameters,
    Duration? timeout,
    void Function()? onSlowRequest,
  }) async {
    final uri = buildUri(path, queryParameters: queryParameters);
    final effectiveTimeout = timeout ?? _defaultTimeout;
    Timer? slowTimer;
    if (onSlowRequest != null) {
      slowTimer = Timer(AppConfig.slowWarningThreshold, onSlowRequest);
    }

    try {
      final http.Response response;
      if (method == 'GET') {
        response = await _client
            .get(uri, headers: const {'Accept': 'application/json'})
            .timeout(effectiveTimeout);
      } else {
        response = await _client
            .post(
              uri,
              headers: const {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
              },
              body: jsonEncode(body ?? const <String, dynamic>{}),
            )
            .timeout(effectiveTimeout);
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = _tryDecodeJson(response.body);
        if (decoded is Map<String, dynamic>) {
          return decoded;
        }
        throw const ApiException(
          kind: ApiErrorKind.parse,
          message: 'El servidor devolvió un formato JSON inesperado.',
        );
      }

      throw _mapHttpError(response);
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw const ApiException(
        kind: ApiErrorKind.timeout,
        message:
            'El servidor tardó demasiado en responder. Si usa Render gratuito, puede estar despertando; reintente en unos segundos.',
      );
    } on SocketException {
      throw ApiException(
        kind: ApiErrorKind.offline,
        message: _offlineHint(_baseUrl),
      );
    } on http.ClientException catch (err) {
      throw ApiException(
        kind: ApiErrorKind.offline,
        message: '${_offlineHint(_baseUrl)} (${err.message})',
      );
    } on FormatException {
      throw const ApiException(
        kind: ApiErrorKind.parse,
        message: 'La respuesta del servidor no pudo interpretarse como JSON.',
      );
    } finally {
      slowTimer?.cancel();
    }
  }

  String _offlineHint(String url) {
    if (AppConfig.isLoopbackHost(url)) {
      return 'No hay conexión con $url. En un teléfono o emulador, localhost apunta al propio dispositivo; usa la URL de Render o la IP de tu PC.';
    }
    return 'No se pudo conectar con el servidor ($url). Verifica tu conexión a Internet o usa la biblioteca local.';
  }

  dynamic _tryDecodeJson(String body) {
    if (body.trim().isEmpty) return null;
    try {
      return jsonDecode(body);
    } on FormatException {
      return null;
    }
  }

  ApiException _mapHttpError(http.Response response) {
    final decoded = _tryDecodeJson(response.body);
    String? detailMessage;
    if (decoded is Map<String, dynamic> && decoded.containsKey('detail')) {
      final detail = decoded['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        detailMessage = detail.trim();
      } else if (detail is List) {
        final parts = detail
            .whereType<Map<String, dynamic>>()
            .map((item) => item['msg']?.toString() ?? 'Entrada no válida')
            .toList();
        if (parts.isNotEmpty) {
          detailMessage = parts.join('; ');
        }
      }
    }

    if (response.statusCode >= 500) {
      return ApiException(
        kind: ApiErrorKind.server,
        statusCode: response.statusCode,
        message: detailMessage ??
            'El servidor backend devolvió HTTP ${response.statusCode}. Si está despertando en Render, intenta de nuevo en unos segundos.',
      );
    }

    return ApiException(
      kind: ApiErrorKind.validation,
      statusCode: response.statusCode,
      message: detailMessage ??
          'La solicitud fue rechazada (HTTP ${response.statusCode}).',
    );
  }

  void dispose() {
    _client.close();
  }
}
