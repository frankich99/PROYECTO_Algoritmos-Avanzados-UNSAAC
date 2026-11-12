import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/config/app_config.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../data/repositories/server_repository.dart';

class ProjectSettingsScreen extends StatefulWidget {
  const ProjectSettingsScreen({super.key});

  @override
  State<ProjectSettingsScreen> createState() => _ProjectSettingsScreenState();
}

class _ProjectSettingsScreenState extends State<ProjectSettingsScreen> {
  late TextEditingController _urlController;
  String? _urlValidationError;

  @override
  void initState() {
    super.initState();
    final repo = context.read<ServerRepository>();
    _urlController = TextEditingController(text: repo.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _applyServerUrl() async {
    final raw = _urlController.text.trim();
    final uri = Uri.tryParse(raw);
    if (raw.isEmpty || uri == null || !uri.hasScheme || !uri.hasAuthority) {
      setState(() {
        _urlValidationError =
            'Ingresa una URL completa válida (ej. https://rutas-cusco-unsaac.onrender.com).';
      });
      return;
    }
    setState(() => _urlValidationError = null);
    await context.read<ServerRepository>().updateServerUrl(raw);
  }

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<ServerRepository>();
    final catalog = repo.catalog;
    final version = repo.version;
    final limits = repo.limits;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Proyecto y servidor'),
        actions: [
          IconButton(
            onPressed: repo.state == ServerLoadState.loading
                ? null
                : repo.refreshStatus,
            tooltip: 'Actualizar estado del servidor',
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 780;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1080),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _SectionHeader(
                      kicker: 'CONEXIÓN Y CONTRATO',
                      title: 'Estado del backend FastAPI',
                      subtitle:
                          'La aplicación móvil reutiliza los algoritmos y validaciones oficiales de FastAPI.',
                    ),
                    const SizedBox(height: 12),
                    if (repo.state == ServerLoadState.loading)
                      LoadingStateView(
                        title: 'Conectando con FastAPI…',
                        subtitle: repo.baseUrl,
                        showWakeupNotice: repo.slowWakeup,
                      )
                    else if (repo.state == ServerLoadState.offline ||
                        repo.state == ServerLoadState.error) ...[
                      ErrorStateBanner(
                        message: repo.errorMessage ?? 'No se pudo consultar el servidor.',
                        isOffline: repo.state == ServerLoadState.offline,
                        onRetry: repo.refreshStatus,
                      ),
                      const SizedBox(height: 12),
                    ] else if (repo.state == ServerLoadState.saved) ...[
                      const SavedDataBadge(
                        label: 'Catálogo guardado en caché · sin conexión actual',
                      ),
                      const SizedBox(height: 12),
                    ],
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: isWide ? 520 : double.infinity,
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Versiones y estado',
                                    style:
                                        Theme.of(context).textTheme.titleMedium,
                                  ),
                                  const SizedBox(height: 10),
                                  _KeyValueRow(
                                    label: 'Estado',
                                    value: _stateLabel(repo.state),
                                  ),
                                  _KeyValueRow(
                                    label: 'API FastAPI',
                                    value: version?.apiVersion ?? 'Sin consultar',
                                  ),
                                  _KeyValueRow(
                                    label: 'Datos canónicos',
                                    value: version?.dataVersion.isNotEmpty == true
                                        ? version!.dataVersion
                                        : '—',
                                  ),
                                  _KeyValueRow(
                                    label: 'Documentación',
                                    value: version?.docsVersion.isNotEmpty == true
                                        ? version!.docsVersion
                                        : '—',
                                  ),
                                  _KeyValueRow(
                                    label: 'Generador',
                                    value:
                                        version?.generatorVersion.isNotEmpty == true
                                            ? version!.generatorVersion
                                            : '—',
                                  ),
                                  _KeyValueRow(
                                    label: 'Colas disponibles',
                                    value: catalog == null
                                        ? '—'
                                        : catalog.queues.join(', '),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        SizedBox(
                          width: isWide ? 520 : double.infinity,
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Coberturas y límites unificados',
                                    style:
                                        Theme.of(context).textTheme.titleMedium,
                                  ),
                                  const SizedBox(height: 10),
                                  if (catalog != null)
                                    for (final net in catalog.networks)
                                      _KeyValueRow(
                                        label: net.kind == 'center'
                                            ? 'Centro OSM'
                                            : 'Ampliada OSM',
                                        value: net.available
                                            ? 'Disponible'
                                            : 'No verificada',
                                      ),
                                  _KeyValueRow(
                                    label: 'Máx. grafo',
                                    value:
                                        '${limits.maxNodes} nodos / ${limits.maxEdges} aristas',
                                  ),
                                  _KeyValueRow(
                                    label: 'Experimentos',
                                    value:
                                        '${limits.experimentSizeMin}–${limits.experimentSizeMax} nodos (máx. ${limits.experimentSizesMaxCount})',
                                  ),
                                  _KeyValueRow(
                                    label: 'Repeticiones',
                                    value:
                                        '${limits.experimentRunsMin}–${limits.experimentRunsMax} por instancia',
                                  ),
                                  _KeyValueRow(
                                    label: 'Generadores',
                                    value:
                                        '${limits.generatorNodesMin}–${limits.generatorNodesMax} nodos · malla ${limits.generatorGridMin}–${limits.generatorGridMax}',
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Dirección del servidor FastAPI',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Producción apunta a Render. En pruebas locales desde emulador Android usa http://10.0.2.2:8000 (localhost apunta al teléfono).',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _urlController,
                              keyboardType: TextInputType.url,
                              autocorrect: false,
                              decoration: InputDecoration(
                                labelText: 'URL base del backend',
                                errorText: _urlValidationError,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                FilledButton.icon(
                                  onPressed: _applyServerUrl,
                                  icon: const Icon(Icons.check),
                                  label: const Text('Aplicar y comprobar'),
                                ),
                                OutlinedButton(
                                  onPressed: () {
                                    _urlController.text =
                                        AppConfig.productionBaseUrl;
                                    _applyServerUrl();
                                  },
                                  child: const Text('Usar Render oficial'),
                                ),
                                OutlinedButton(
                                  onPressed: () {
                                    _urlController.text =
                                        AppConfig.androidEmulatorLocalUrl;
                                    _applyServerUrl();
                                  },
                                  child: const Text('Usar emulador local'),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  String _stateLabel(ServerLoadState state) {
    switch (state) {
      case ServerLoadState.initial:
        return 'Inicializando';
      case ServerLoadState.loading:
        return 'Consultando servidor';
      case ServerLoadState.ready:
        return 'Conectado';
      case ServerLoadState.empty:
        return 'Catálogo vacío';
      case ServerLoadState.offline:
        return 'Sin conexión';
      case ServerLoadState.error:
        return 'Error de respuesta';
      case ServerLoadState.saved:
        return 'Caché guardada (sin conexión)';
    }
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.kicker,
    required this.title,
    required this.subtitle,
  });

  final String kicker;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          kicker,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.1,
            color: AppTheme.maroon,
          ),
        ),
        const SizedBox(height: 4),
        Text(title, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 4),
        Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _KeyValueRow extends StatelessWidget {
  const _KeyValueRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 132,
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.mutedInk,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: AppTheme.ink,
                fontFeatures: AppTheme.tabularFigures,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
