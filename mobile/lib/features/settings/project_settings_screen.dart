import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/config/app_config.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../data/repositories/server_repository.dart';
import 'widgets/about_app_section.dart';

class ProjectSettingsScreen extends StatefulWidget {
  const ProjectSettingsScreen({super.key});

  @override
  State<ProjectSettingsScreen> createState() => _ProjectSettingsScreenState();
}

class _ProjectSettingsScreenState extends State<ProjectSettingsScreen> {
  late final TextEditingController _urlController;
  String? _urlValidationError;
  bool _applying = false;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(
      text: context.read<ServerRepository>().baseUrl,
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _applyServerUrl([String? preset]) async {
    if (_applying) return;
    if (preset != null) _urlController.text = preset;
    final raw = _urlController.text.trim();
    final error = AppConfig.validateBaseUrl(raw);
    setState(() => _urlValidationError = error);
    if (error != null) return;
    FocusScope.of(context).unfocus();
    setState(() => _applying = true);
    try {
      await context.read<ServerRepository>().updateServerUrl(raw);
    } catch (_) {
      if (mounted) {
        setState(
          () => _urlValidationError =
              'No se pudo guardar la dirección. Vuelve a intentarlo.',
        );
      }
    } finally {
      if (mounted) setState(() => _applying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<ServerRepository>();
    final busy = _applying || repo.state == ServerLoadState.loading;
    final version = repo.version;
    final limits = repo.limits;

    return Scaffold(
      appBar: AppBar(title: const Text('Ajustes')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 760),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Conexión', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                ServerStatusBanner(repo: repo, compact: false),
                const SizedBox(height: 24),
                Text(
                  'Tu trabajo queda en este dispositivo',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                const Text(
                  'Los borradores y resultados que guardas se conservan en el teléfono. '
                  'No necesitas configurar una base de datos ni un servidor para usar la app.',
                ),
                const SizedBox(height: 16),
                const ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: EdgeInsets.only(bottom: 16),
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  title: Text('Qué puedes hacer sin internet'),
                  subtitle: Text('Ejemplos, edición y resultados guardados'),
                  children: [
                    _HelpItem(
                      icon: Icons.edit_outlined,
                      title: 'Preparar y consultar',
                      description:
                          'Explora los ejemplos, edita grafos y abre '
                          'rutas, experimentos y documentos ya guardados.',
                    ),
                    _HelpItem(
                      icon: Icons.route_outlined,
                      title: 'Para calcular algo nuevo',
                      description:
                          'Conéctate para calcular rutas, validar en el '
                          'servidor, generar redes o ejecutar experimentos nuevos.',
                    ),
                  ],
                ),
                const ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: EdgeInsets.only(bottom: 16),
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  title: Text('Cómo se conectan los mapas'),
                  subtitle: Text('Plano local y calles OpenStreetMap'),
                  children: [
                    _HelpItem(
                      icon: Icons.map_outlined,
                      title: 'Plano sin conexión',
                      description:
                          'Dibuja los nodos y las vías cuando hay una '
                          'vista previa cargada. No descarga imágenes de calles.',
                    ),
                    _HelpItem(
                      icon: Icons.public_outlined,
                      title: 'Calles OSM',
                      description:
                          'Las imágenes se descargan de OpenStreetMap '
                          'con internet, por separado del servicio de cálculo. '
                          'No se garantiza que queden disponibles sin conexión.',
                    ),
                    _HelpItem(
                      icon: Icons.cloud_outlined,
                      title: 'Rutas y condiciones actuales',
                      description:
                          'El servicio calcula Dijkstra y A* y consulta '
                          'clima o tráfico cuando lo solicitas. No se ejecuta '
                          'FastAPI dentro del teléfono.',
                    ),
                  ],
                ),
                const AboutAppSection(),
                const SizedBox(height: 8),
                ExpansionTile(
                  key: const ValueKey('advanced-connection'),
                  tilePadding: EdgeInsets.zero,
                  childrenPadding: const EdgeInsets.only(bottom: 24),
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  title: const Text('Conexión avanzada'),
                  subtitle: const Text(
                    'Solo para pruebas o un servidor propio',
                  ),
                  children: [
                    const Text(
                      'Por defecto se usa el servicio del proyecto alojado en Render. '
                      'No cambies esta dirección para el uso habitual.',
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _urlController,
                      enabled: !busy,
                      keyboardType: TextInputType.url,
                      autocorrect: false,
                      textInputAction: TextInputAction.done,
                      onSubmitted: busy ? null : (_) => _applyServerUrl(),
                      decoration: InputDecoration(
                        labelText: 'Dirección del servicio',
                        helperText:
                            'URL base con https:// o http://, sin /api/v1.',
                        helperMaxLines: 3,
                        errorText: _urlValidationError,
                        errorMaxLines: 3,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        FilledButton.icon(
                          onPressed: busy ? null : () => _applyServerUrl(),
                          icon: const Icon(Icons.check),
                          label: Text(
                            _applying ? 'Comprobando…' : 'Guardar y comprobar',
                          ),
                        ),
                        OutlinedButton(
                          onPressed: busy
                              ? null
                              : () => _applyServerUrl(
                                  AppConfig.productionBaseUrl,
                                ),
                          child: const Text(
                            'Restablecer servicio del proyecto',
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'En un teléfono físico, usa la IP del equipo con FastAPI '
                      'en la misma red Wi-Fi. «localhost» apunta al teléfono, no al equipo. '
                      'Una dirección HTTP local no cifra las solicitudes; úsala solo en una red de confianza.',
                    ),
                    TextButton(
                      onPressed: busy
                          ? null
                          : () => _applyServerUrl(
                              AppConfig.androidEmulatorLocalUrl,
                            ),
                      child: const Text(
                        'Usar servidor del emulador (10.0.2.2)',
                      ),
                    ),
                    const Divider(height: 24),
                    Text(
                      'Información técnica',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    SelectableText('Servicio actual: ${repo.baseUrl}'),
                    if (repo.errorMessage != null) ...[
                      const SizedBox(height: 8),
                      SelectableText(
                        'Detalle de conexión: ${repo.errorMessage}',
                      ),
                    ],
                    const SizedBox(height: 8),
                    Text(
                      repo.isUsingSavedFallback
                          ? 'Datos del último catálogo guardado, no de una conexión actual.'
                          : repo.catalog == null
                          ? 'Sin catálogo consultado. Los límites indicados son los valores predeterminados de la app.'
                          : 'Versiones y límites recibidos del servicio.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 8),
                    Text('API: ${version?.apiVersion ?? 'Sin consultar'}'),
                    if (version != null) ...[
                      Text('Datos: ${version.dataVersion}'),
                      Text('Documentación: ${version.docsVersion}'),
                      Text('Generador: ${version.generatorVersion}'),
                    ],
                    Text(
                      'Grafos: hasta ${limits.maxNodes} nodos y ${limits.maxEdges} aristas.',
                    ),
                    Text(
                      'Experimentos: ${limits.experimentSizeMin} a ${limits.experimentSizeMax} nodos; '
                      '${limits.experimentRunsMin} a ${limits.experimentRunsMax} repeticiones.',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _HelpItem extends StatelessWidget {
  const _HelpItem({
    required this.icon,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.mutedInk),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 4),
                Text(description),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
