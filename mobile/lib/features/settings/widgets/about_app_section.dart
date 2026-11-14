import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../../core/config/app_config.dart';

class AboutAppSection extends StatelessWidget {
  const AboutAppSection({
    super.key,
    this.loadPackageInfo = PackageInfo.fromPlatform,
  });

  final Future<PackageInfo> Function() loadPackageInfo;

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      key: const PageStorageKey('about-app'),
      tilePadding: EdgeInsets.zero,
      childrenPadding: const EdgeInsets.only(bottom: 24),
      expandedCrossAxisAlignment: CrossAxisAlignment.start,
      title: const Text('Acerca de'),
      subtitle: const Text('Propósito, versión y equipo de desarrollo'),
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(14),
              child: Image.asset(
                'assets/icon/app_icon.png',
                width: 56,
                height: 56,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    AppConfig.appTitle,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 2),
                  const Text(
                    'Edición v1.2 Pro · Cusco',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF8A6418),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        const Text(
          'Una herramienta académica para explorar rutas mínimas en redes '
          'viales de Cusco y comprender cómo los algoritmos y las colas de '
          'prioridad influyen en su cálculo.',
        ),
        const SizedBox(height: 20),
        Text(
          'Qué busca la app',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        const Text(
          'Comparar Dijkstra y A* y estudiar las colas binaria, 4-aria y '
          'Fibonacci. Puedes consultar rutas por tiempo o distancia, preparar '
          'grafos, ejecutar experimentos y guardar resultados para revisarlos '
          'después.',
        ),
        const SizedBox(height: 16),
        const Text(
          'Es un proyecto de estudio, no un servicio de navegación en tiempo '
          'real. Las redes cubren zonas delimitadas de Cusco y los tiempos '
          'son estimaciones del modelo, no mediciones de tráfico real.',
        ),
        const SizedBox(height: 20),
        Text(
          'Versión instalada',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        _InstalledVersion(loadPackageInfo: loadPackageInfo),
        const Divider(height: 32),
        Text(
          'Desarrollo móvil e integración',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        const Text('Noe Franklin Choquenaira Quispe'),
        const SizedBox(height: 20),
        Text(
          'Equipo del proyecto · Grupo 5',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        const Text('Noe Franklin Choquenaira Quispe'),
        const Text('Yeni Ruth Porroa Sivana'),
        const Text('Romario Quispe Rimachi'),
        const Text('Aldo Yaranga Achahui'),
        const SizedBox(height: 20),
        Text('UNSAAC', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        const Text('Universidad Nacional de San Antonio Abad del Cusco'),
        const SizedBox(height: 4),
        const Text('Ingeniería Informática y de Sistemas'),
        const Text('Algoritmos Avanzados · Semestre 2026-2'),
        const SizedBox(height: 16),
        TextButton.icon(
          onPressed: () => showLicensePage(
            context: context,
            applicationName: AppConfig.appTitle,
          ),
          icon: const Icon(Icons.description_outlined),
          label: const Text('Licencias de software'),
        ),
      ],
    );
  }
}

class _InstalledVersion extends StatefulWidget {
  const _InstalledVersion({required this.loadPackageInfo});

  final Future<PackageInfo> Function() loadPackageInfo;

  @override
  State<_InstalledVersion> createState() => _InstalledVersionState();
}

class _InstalledVersionState extends State<_InstalledVersion> {
  late Future<PackageInfo> _info = _load();

  Future<PackageInfo> _load() async {
    return await widget.loadPackageInfo().timeout(const Duration(seconds: 5));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<PackageInfo>(
      future: _info,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return Semantics(
            liveRegion: true,
            child: const Text('Leyendo versión instalada…'),
          );
        }
        final info = snapshot.data;
        if (snapshot.hasError || info == null || info.version.trim().isEmpty) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'No se pudo leer la versión. El resto de esta información está disponible sin internet.',
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _info = _load();
                  });
                },
                child: const Text('Reintentar lectura de versión'),
              ),
            ],
          );
        }
        return Wrap(
          spacing: 16,
          runSpacing: 6,
          children: [
            Text('Versión ${info.version}'),
            Text(
              'Compilación ${info.buildNumber.isEmpty ? 'no disponible' : info.buildNumber}',
            ),
          ],
        );
      },
    );
  }
}
