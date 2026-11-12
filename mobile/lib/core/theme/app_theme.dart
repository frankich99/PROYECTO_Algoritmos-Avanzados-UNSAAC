import 'package:flutter/material.dart';

/// Identidad visual UNSAAC definida en DESIGN.md:
/// granate #681C32, dorado oscuro #8A6418, tinta #1F1B1C y papel claro #F7F3EA.
class AppTheme {
  const AppTheme._();

  static const Color maroon = Color(0xFF681C32);
  static const Color maroonDark = Color(0xFF4B1223);
  static const Color maroonSoft = Color(0xFFF3E7EA);
  static const Color gold = Color(0xFF8A6418);
  static const Color goldSoft = Color(0xFFF6EFE0);
  static const Color ink = Color(0xFF1F1B1C);
  static const Color mutedInk = Color(0xFF5A5254);
  static const Color paper = Color(0xFFF7F3EA);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color border = Color(0xFFDAD1C2);
  static const Color okGreen = Color(0xFF1F6A42);
  static const Color okBg = Color(0xFFE7F3EC);
  static const Color warnAmber = Color(0xFF8A5300);
  static const Color warnBg = Color(0xFFFFF4E0);
  static const Color errorRed = Color(0xFF9F1D2C);
  static const Color errorBg = Color(0xFFFCEBEC);

  static const List<FontFeature> tabularFigures = [FontFeature.tabularFigures()];

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: maroon,
      brightness: Brightness.light,
      primary: maroon,
      onPrimary: Colors.white,
      secondary: gold,
      onSecondary: Colors.white,
      surface: surfaceWhite,
      onSurface: ink,
      error: errorRed,
      onError: Colors.white,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: paper,
    );

    return base.copyWith(
      appBarTheme: const AppBarTheme(
        backgroundColor: paper,
        foregroundColor: ink,
        elevation: 0,
        scrolledUnderElevation: 1,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: TextStyle(
          color: ink,
          fontSize: 19,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
        ),
      ),
      cardTheme: CardThemeData(
        color: surfaceWhite,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: border),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceWhite,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: gold, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: errorRed, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: maroon,
          foregroundColor: Colors.white,
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: maroon,
          minimumSize: const Size(48, 48),
          side: const BorderSide(color: border),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: maroon,
          minimumSize: const Size(48, 44),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: surfaceWhite,
        indicatorColor: maroonSoft,
        surfaceTintColor: Colors.transparent,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? maroon : mutedInk,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? maroon : mutedInk);
        }),
      ),
      navigationRailTheme: const NavigationRailThemeData(
        backgroundColor: surfaceWhite,
        indicatorColor: maroonSoft,
        selectedIconTheme: IconThemeData(color: maroon),
        unselectedIconTheme: IconThemeData(color: mutedInk),
        selectedLabelTextStyle: TextStyle(color: maroon, fontWeight: FontWeight.w700),
        unselectedLabelTextStyle: TextStyle(color: mutedInk),
      ),
      dividerTheme: const DividerThemeData(color: border, thickness: 1),
      textTheme: base.textTheme.copyWith(
        headlineMedium: base.textTheme.headlineMedium?.copyWith(
          fontFamily: 'serif',
          fontWeight: FontWeight.w700,
          color: ink,
        ),
        headlineSmall: base.textTheme.headlineSmall?.copyWith(
          fontFamily: 'serif',
          fontWeight: FontWeight.w700,
          color: ink,
        ),
        titleLarge: base.textTheme.titleLarge?.copyWith(
          fontFamily: 'serif',
          fontWeight: FontWeight.w700,
          color: ink,
        ),
        titleMedium: base.textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w700,
          color: ink,
        ),
        bodyMedium: base.textTheme.bodyMedium?.copyWith(color: ink, height: 1.4),
        bodySmall: base.textTheme.bodySmall?.copyWith(color: mutedInk, height: 1.35),
      ),
    );
  }
}

/// Puntos de quiebre adaptativos para teléfonos, tabletas y horizontal.
class AdaptiveLayout {
  const AdaptiveLayout._();

  static bool isCompact(BuildContext context) => MediaQuery.sizeOf(context).width < 600;
  static bool isMedium(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    return width >= 600 && width < 1024;
  }

  static bool isExpanded(BuildContext context) => MediaQuery.sizeOf(context).width >= 1024;
}
