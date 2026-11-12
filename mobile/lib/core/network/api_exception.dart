enum ApiErrorKind {
  offline,
  timeout,
  validation,
  server,
  cancelled,
  parse,
}

class ApiException implements Exception {
  const ApiException({
    required this.kind,
    required this.message,
    this.statusCode,
  });

  final ApiErrorKind kind;
  final String message;
  final int? statusCode;

  bool get isNetworkRelated =>
      kind == ApiErrorKind.offline || kind == ApiErrorKind.timeout;

  @override
  String toString() => message;
}
