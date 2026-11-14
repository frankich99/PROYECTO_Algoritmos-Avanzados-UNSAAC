import 'package:geolocator/geolocator.dart';

import '../../data/models/instance_models.dart';

class LocationResult {
  const LocationResult({
    required this.point,
    required this.accuracyM,
  });

  final PointCoord point;
  final double accuracyM;
}

class LocationService {
  /// Solicita permiso únicamente cuando el usuario pulsa «Usar mi ubicación».
  Future<LocationResult> getCurrentCuscoPoint() async {
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) {
      throw StateError(
        'La ubicación del teléfono está desactivada. Activa el GPS para usar tu posición.',
      );
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied) {
      throw StateError(
        'Permiso de ubicación denegado. Puedes elegir origen tocando el mapa o por ID.',
      );
    }
    if (permission == LocationPermission.deniedForever) {
      throw StateError(
        'Permiso de ubicación bloqueado en ajustes del sistema. Selecciónalo manualmente en el mapa.',
      );
    }

    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: 15),
      ),
    );
    return LocationResult(
      point: PointCoord(lat: position.latitude, lon: position.longitude),
      accuracyM: position.accuracy,
    );
  }
}
