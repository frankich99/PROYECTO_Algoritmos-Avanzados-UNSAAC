import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app/router.dart';
import 'core/config/app_config.dart';
import 'core/network/api_client.dart';
import 'core/services/device_files_service.dart';
import 'core/theme/app_theme.dart';
import 'data/local/app_database.dart';
import 'data/repositories/instance_repository.dart';
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

  runApp(
    RutasCuscoApp(
      serverRepository: serverRepository,
      settingsRepository: settingsRepository,
      instanceRepository: instanceRepository,
      deviceFilesService: DeviceFilesService(),
    ),
  );
}

class RutasCuscoApp extends StatefulWidget {
  const RutasCuscoApp({
    super.key,
    required this.serverRepository,
    required this.settingsRepository,
    required this.instanceRepository,
    required this.deviceFilesService,
  });

  final ServerRepository serverRepository;
  final SettingsRepository settingsRepository;
  final InstanceRepository instanceRepository;
  final DeviceFilesService deviceFilesService;

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
        ChangeNotifierProvider<ServerRepository>.value(
          value: widget.serverRepository,
        ),
        ChangeNotifierProvider<InstanceRepository>.value(
          value: widget.instanceRepository,
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
