import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app/router.dart';
import 'core/config/app_config.dart';
import 'core/network/api_client.dart';
import 'core/services/device_files_service.dart';
import 'core/services/location_service.dart';
import 'core/theme/app_theme.dart';
import 'data/local/app_database.dart';
import 'data/repositories/analysis_repository.dart';
import 'data/repositories/conditions_repository.dart';
import 'data/repositories/docs_repository.dart';
import 'data/repositories/instance_repository.dart';
import 'data/repositories/route_repository.dart';
import 'data/repositories/server_repository.dart';
import 'data/repositories/settings_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final settingsRepository = SettingsRepository();
  final apiClient = ApiClient(baseUrl: AppConfig.configuredBaseUrl);
  final database = AppDatabase();
  final serverRepository = ServerRepository(
    apiClient: apiClient,
    settingsRepository: settingsRepository,
  )..initialize();
  final instanceRepository = InstanceRepository(
    apiClient: apiClient,
    database: database,
  )..initialize();
  final routeRepository = RouteRepository(
    apiClient: apiClient,
    database: database,
  )..initialize();
  final conditionsRepository = ConditionsRepository(
    apiClient: apiClient,
    settingsRepository: settingsRepository,
  )..initialize();
  final analysisRepository = AnalysisRepository(
    apiClient: apiClient,
    database: database,
  )..initialize();
  final docsRepository = DocsRepository()..initialize();

  runApp(
    RutasCuscoApp(
      serverRepository: serverRepository,
      settingsRepository: settingsRepository,
      instanceRepository: instanceRepository,
      routeRepository: routeRepository,
      conditionsRepository: conditionsRepository,
      analysisRepository: analysisRepository,
      docsRepository: docsRepository,
      deviceFilesService: DeviceFilesService(),
      locationService: LocationService(),
    ),
  );
}

class RutasCuscoApp extends StatefulWidget {
  const RutasCuscoApp({
    super.key,
    required this.serverRepository,
    required this.settingsRepository,
    required this.instanceRepository,
    required this.routeRepository,
    required this.conditionsRepository,
    required this.analysisRepository,
    required this.docsRepository,
    required this.deviceFilesService,
    required this.locationService,
  });

  final ServerRepository serverRepository;
  final SettingsRepository settingsRepository;
  final InstanceRepository instanceRepository;
  final RouteRepository routeRepository;
  final ConditionsRepository conditionsRepository;
  final AnalysisRepository analysisRepository;
  final DocsRepository docsRepository;
  final DeviceFilesService deviceFilesService;
  final LocationService locationService;

  @override
  State<RutasCuscoApp> createState() => _RutasCuscoAppState();
}

class _RutasCuscoAppState extends State<RutasCuscoApp> {
  late final _router = createAppRouter();

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<SettingsRepository>.value(value: widget.settingsRepository),
        Provider<DeviceFilesService>.value(value: widget.deviceFilesService),
        Provider<LocationService>.value(value: widget.locationService),
        ChangeNotifierProvider<ServerRepository>.value(
          value: widget.serverRepository,
        ),
        ChangeNotifierProvider<InstanceRepository>.value(
          value: widget.instanceRepository,
        ),
        ChangeNotifierProvider<RouteRepository>.value(
          value: widget.routeRepository,
        ),
        ChangeNotifierProvider<ConditionsRepository>.value(
          value: widget.conditionsRepository,
        ),
        ChangeNotifierProvider<AnalysisRepository>.value(
          value: widget.analysisRepository,
        ),
        ChangeNotifierProvider<DocsRepository>.value(
          value: widget.docsRepository,
        ),
      ],
      child: MaterialApp.router(
        title: AppConfig.appTitle,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        routerConfig: _router,
      ),
    );
  }
}
