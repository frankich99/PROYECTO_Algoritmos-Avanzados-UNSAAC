import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../core/theme/app_theme.dart';
import '../core/widgets/state_views.dart';
import '../data/repositories/server_repository.dart';

class AppNavDestination {
  const AppNavDestination({
    required this.label,
    required this.icon,
    required this.selectedIcon,
    required this.semanticHint,
  });

  final String label;
  final IconData icon;
  final IconData selectedIcon;
  final String semanticHint;
}

const List<AppNavDestination> appDestinations = [
  AppNavDestination(
    label: 'Rutas',
    icon: Icons.alt_route_outlined,
    selectedIcon: Icons.alt_route,
    semanticHint: 'Cálculo de rutas, mapa y grafo',
  ),
  AppNavDestination(
    label: 'Instancias',
    icon: Icons.hub_outlined,
    selectedIcon: Icons.hub,
    semanticHint: 'Ejemplos, editor e importación',
  ),
  AppNavDestination(
    label: 'Análisis',
    icon: Icons.analytics_outlined,
    selectedIcon: Icons.analytics,
    semanticHint: 'Comparaciones y experimentos',
  ),
  AppNavDestination(
    label: 'Biblioteca',
    icon: Icons.bookmarks_outlined,
    selectedIcon: Icons.bookmarks,
    semanticHint: 'Consultas, instancias y documentos guardados',
  ),
  AppNavDestination(
    label: 'Proyecto',
    icon: Icons.school_outlined,
    selectedIcon: Icons.school,
    semanticHint: 'Evidencias, cobertura, servidor y ayuda',
  ),
];

class AppShell extends StatefulWidget {
  const AppShell({
    super.key,
    required this.navigationShell,
  });

  final StatefulNavigationShell navigationShell;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && mounted) {
      final serverRepo = context.read<ServerRepository>();
      if (serverRepo.state == ServerLoadState.offline ||
          serverRepo.state == ServerLoadState.loading ||
          serverRepo.state == ServerLoadState.error) {
        serverRepo.refreshStatus();
      }
    }
  }

  void _onSelectTab(int index) {
    widget.navigationShell.goBranch(
      index,
      initialLocation: index == widget.navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    final compact = AdaptiveLayout.isCompact(context);
    final expanded = AdaptiveLayout.isExpanded(context);
    final serverRepo = context.watch<ServerRepository>();

    final content = Column(
      children: [
        ServerStatusBanner(repo: serverRepo),
        Expanded(child: widget.navigationShell),
      ],
    );

    if (compact) {
      return Scaffold(
        body: SafeArea(bottom: false, child: content),
        bottomNavigationBar: NavigationBar(
          selectedIndex: widget.navigationShell.currentIndex,
          onDestinationSelected: _onSelectTab,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          destinations: [
            for (final dest in appDestinations)
              NavigationDestination(
                icon: Icon(dest.icon),
                selectedIcon: Icon(dest.selectedIcon),
                label: dest.label,
                tooltip: dest.semanticHint,
              ),
          ],
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            NavigationRail(
              selectedIndex: widget.navigationShell.currentIndex,
              onDestinationSelected: _onSelectTab,
              extended: expanded,
              minWidth: 76,
              minExtendedWidth: 210,
              leading: Padding(
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                child: Column(
                  children: [
                    Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: AppTheme.maroon,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: const Text(
                        'G5',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    if (expanded) ...[
                      const SizedBox(height: 6),
                      const Text(
                        'UNSAAC · Cusco',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.mutedInk,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              destinations: [
                for (final dest in appDestinations)
                  NavigationRailDestination(
                    icon: Icon(dest.icon),
                    selectedIcon: Icon(dest.selectedIcon),
                    label: Text(dest.label),
                  ),
              ],
            ),
            const VerticalDivider(width: 1),
            Expanded(child: content),
          ],
        ),
      ),
    );
  }
}
