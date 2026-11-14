import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rutas_cusco_mobile/core/widgets/responsive_data_view.dart';

void main() {
  const headers = ['Cola', 'Insertar', 'Tipo de cota'];
  const rows = [
    ResponsiveRowItem(
      title: 'Binaria',
      badge: 'Peor caso',
      cells: ['Binaria', 'O(log n)', 'Peor caso'],
      mobileColumns: [1],
    ),
  ];

  testWidgets('Tarjeta evita repetir título y etiqueta con letra grande', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: SizedBox(
              width: 280,
              child: MediaQuery(
                data: const MediaQueryData(textScaler: TextScaler.linear(2)),
                child: const ResponsiveDataView(headers: headers, rows: rows),
              ),
            ),
          ),
        ),
      ),
    );
    expect(find.text('Binaria'), findsOneWidget);
    expect(find.text('Peor caso'), findsOneWidget);
    expect(find.text('O(log n)'), findsOneWidget);
    expect(find.text('Tipo de cota'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Tabla ancha conserva todas las columnas y valores', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: ResponsiveDataView(headers: headers, rows: rows),
        ),
      ),
    );
    expect(find.byType(Table), findsOneWidget);
    for (final header in headers) {
      expect(find.text(header), findsOneWidget);
    }
    expect(find.text('Binaria'), findsOneWidget);
    expect(find.text('Peor caso'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
