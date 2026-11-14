import 'package:flutter/material.dart';

import '../../data/repositories/server_repository.dart';
import '../theme/app_theme.dart';

class LoadingStateView extends StatelessWidget {
  const LoadingStateView({
    super.key,
    required this.title,
    this.subtitle,
    this.showWakeupNotice = false,
  });

  final String title;
  final String? subtitle;
  final bool showWakeupNotice;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(color: AppTheme.maroon),
              const SizedBox(height: 16),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 8),
                Text(
                  subtitle!,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              if (showWakeupNotice) ...[
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.warnBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: AppTheme.gold.withValues(alpha: 0.4),
                    ),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.schedule, color: AppTheme.warnAmber),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'El servicio está tardando en iniciar. Puedes consultar tu biblioteca mientras responde.',
                          style: TextStyle(fontSize: 13, color: AppTheme.ink),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class EmptyStateView extends StatelessWidget {
  const EmptyStateView({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 42, color: AppTheme.mutedInk),
              const SizedBox(height: 12),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 6),
              Text(
                message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              if (action != null) ...[const SizedBox(height: 16), action!],
            ],
          ),
        ),
      ),
    );
  }
}

class ErrorStateBanner extends StatelessWidget {
  const ErrorStateBanner({
    super.key,
    required this.message,
    this.isOffline = false,
    this.onRetry,
  });

  final String message;
  final bool isOffline;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final bg = isOffline ? AppTheme.warnBg : AppTheme.errorBg;
    final fg = isOffline ? AppTheme.warnAmber : AppTheme.errorRed;
    final icon = isOffline ? Icons.cloud_off_outlined : Icons.error_outline;

    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: fg.withValues(alpha: 0.45)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon, color: fg),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    message,
                    style: const TextStyle(
                      color: AppTheme.ink,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: OutlinedButton.icon(
                  onPressed: onRetry,
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('Reintentar'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class SavedDataBadge extends StatelessWidget {
  const SavedDataBadge({
    super.key,
    this.label = 'Resultado guardado · sin conexión',
  });

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppTheme.goldSoft,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppTheme.gold.withValues(alpha: 0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.bookmark_outline, size: 15, color: AppTheme.gold),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppTheme.ink,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class ServerStatusBanner extends StatelessWidget {
  const ServerStatusBanner({
    super.key,
    required this.repo,
    this.compact = true,
  });

  final ServerRepository repo;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final busy =
        repo.state == ServerLoadState.initial ||
        repo.state == ServerLoadState.loading;
    final ready =
        repo.state == ServerLoadState.ready && repo.isVersionCompatible;
    if (compact && ready) return const SizedBox.shrink();

    final (
      title,
      description,
      icon,
      foreground,
      background,
    ) = switch (repo.state) {
      ServerLoadState.initial || ServerLoadState.loading => (
        'Comprobando conexión…',
        repo.slowWakeup
            ? 'El servicio está iniciando. Puedes seguir usando la biblioteca.'
            : 'Esto no impide abrir tus datos guardados.',
        Icons.sync,
        AppTheme.gold,
        AppTheme.goldSoft,
      ),
      ServerLoadState.ready when repo.isVersionCompatible => (
        'Servicio disponible',
        'Puedes calcular rutas y consultar condiciones actuales.',
        Icons.cloud_done_outlined,
        AppTheme.okGreen,
        AppTheme.okBg,
      ),
      ServerLoadState.ready => (
        'El servicio necesita revisión',
        'La versión no es compatible. Revisa Conexión avanzada en Ajustes.',
        Icons.warning_amber_outlined,
        AppTheme.warnAmber,
        AppTheme.warnBg,
      ),
      ServerLoadState.saved => (
        'Sin conexión al servicio',
        'Usando el catálogo guardado. Los cálculos nuevos necesitan conexión.',
        Icons.cloud_off_outlined,
        AppTheme.warnAmber,
        AppTheme.warnBg,
      ),
      ServerLoadState.offline => (
        'Sin conexión al servicio',
        'Revisa internet o la dirección del servicio. Tu biblioteca sigue disponible.',
        Icons.cloud_off_outlined,
        AppTheme.warnAmber,
        AppTheme.warnBg,
      ),
      ServerLoadState.error => (
        'No se pudo consultar el servicio',
        'Inténtalo de nuevo. Si continúa, revisa Conexión avanzada en Ajustes.',
        Icons.error_outline,
        AppTheme.errorRed,
        AppTheme.errorBg,
      ),
      ServerLoadState.empty => (
        'Servicio sin redes disponibles',
        'No se recibió un catálogo utilizable. Puedes abrir los ejemplos incluidos.',
        Icons.info_outline,
        AppTheme.warnAmber,
        AppTheme.warnBg,
      ),
    };

    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.all(compact ? 12 : 16),
        decoration: BoxDecoration(
          color: background,
          borderRadius: compact ? null : BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (busy)
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: foreground,
                    ),
                  )
                else
                  Icon(icon, color: foreground),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleSmall
                            ?.copyWith(color: foreground),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: Theme.of(context).textTheme.bodySmall
                            ?.copyWith(color: AppTheme.ink),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (!busy)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: TextButton.icon(
                  onPressed: repo.refreshStatus,
                  icon: const Icon(Icons.refresh, size: 18),
                  label: Text(
                    ready ? 'Comprobar de nuevo' : 'Reintentar conexión',
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
