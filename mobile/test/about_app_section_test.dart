import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:rutas_cusco_mobile/core/config/app_config.dart';
import 'package:rutas_cusco_mobile/core/theme/app_theme.dart';
import 'package:rutas_cusco_mobile/features/settings/widgets/about_app_section.dart';

PackageInfo _package({String version = '2.7.1', String build = '42'}) =>
    PackageInfo(
      appName: AppConfig.appTitle,
      packageName: 'com.unsaac.rutas_cusco_mobile',
      version: version,
      buildNumber: build,
    );

Future<void> _showAbout(
  WidgetTester tester, {
  required Future<PackageInfo> Function() loader,
  Size size = const Size(390, 844),
  double scale = 1,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.light(),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context)
            .copyWith(textScaler: TextScaler.linear(scale)),
        child: child!,
      ),
      home: Scaffold(
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: AboutAppSection(loadPackageInfo: loader),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'Acerca de carga bajo demanda y distingue versión instalada de API',
    (tester) async {
      var reads = 0;
      await _showAbout(
        tester,
        loader: () async {
          reads++;
          return _package();
        },
      );
      expect(reads, 0);
      expect(find.text(AppConfig.appTitle), findsNothing);
      await tester.tap(find.text('Acerca de'));
      await tester.pumpAndSettle();
      expect(reads, 1);
      expect(find.text(AppConfig.appTitle), findsOneWidget);
      expect(find.text('Versión 2.7.1'), findsOneWidget);
      expect(find.text('Compilación 42'), findsOneWidget);
      expect(
        find.text('Versión ${AppConfig.expectedApiVersion}'),
        findsNothing,
      );
      expect(find.text('Desarrollo móvil e integración'), findsOneWidget);
      expect(find.text('Noe Franklin Choquenaira Quispe'), findsNWidgets(2));
      expect(find.text('Yeni Ruth Porroa Sivana'), findsOneWidget);
      expect(find.text('Romario Quispe Rimachi'), findsOneWidget);
      expect(find.text('Aldo Yaranga Achahui'), findsOneWidget);
      expect(
        find.textContaining('no un servicio de navegación'),
        findsOneWidget,
      );
      expect(find.textContaining('Bitácora'), findsNothing);
    },
  );

  testWidgets('Una lectura fallida no inventa versión y permite reintentar', (
    tester,
  ) async {
    var fail = true;
    await _showAbout(
      tester,
      loader: () async {
        if (fail) throw PlatformException(code: 'unavailable');
        return _package();
      },
    );
    await tester.tap(find.text('Acerca de'));
    await tester.pumpAndSettle();
    expect(find.textContaining('No se pudo leer la versión.'), findsOneWidget);
    expect(find.text('Versión ${AppConfig.expectedApiVersion}'), findsNothing);
    expect(find.text('Equipo del proyecto · Grupo 5'), findsOneWidget);
    fail = false;
    await tester.ensureVisible(find.text('Reintentar lectura de versión'));
    await tester.tap(find.text('Reintentar lectura de versión'));
    await tester.pumpAndSettle();
    expect(find.text('Versión 2.7.1'), findsOneWidget);
    expect(find.text('Reintentar lectura de versión'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Lectura pendiente tiene límite de espera y mantiene el contenido',
    (tester) async {
      final pending = Completer<PackageInfo>();
      await _showAbout(tester, loader: () => pending.future);
      await tester.tap(find.text('Acerca de'));
      await tester.pump();
      expect(find.text('Leyendo versión instalada…'), findsOneWidget);
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('No se pudo leer la versión.'),
        findsOneWidget,
      );
      expect(find.text('Equipo del proyecto · Grupo 5'), findsOneWidget);
      pending.complete(_package());
      await tester.pump();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Licencias abre la página local y permite volver', (
    tester,
  ) async {
    await _showAbout(tester, loader: () async => _package());
    await tester.tap(find.text('Acerca de'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Licencias de software'));
    await tester.tap(find.text('Licencias de software'));
    await tester.pumpAndSettle();
    expect(find.byType(LicensePage), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(LicensePage), findsNothing);
    expect(find.text('Acerca de'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final (size, scale) in [
    (const Size(320, 700), 1.4),
    (const Size(390, 844), 2.0),
    (const Size(1100, 800), 1.4),
  ]) {
    testWidgets('Acerca de se adapta a ${size.width} px y texto ×$scale', (
      tester,
    ) async {
      await _showAbout(
        tester,
        loader: () async => _package(),
        size: size,
        scale: scale,
      );
      await tester.tap(find.text('Acerca de'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Licencias de software'));
      await tester.pumpAndSettle();
      expect(
        find.text('Algoritmos Avanzados · Semestre 2026-2'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }
}
