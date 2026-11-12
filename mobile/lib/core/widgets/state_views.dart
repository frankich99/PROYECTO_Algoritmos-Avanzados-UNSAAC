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
                    border: Border.all(color: AppTheme.gold.withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.schedule, color: AppTheme.warnAmber),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'El servidor gratuito en Render puede tardar unos segundos en despertar tras inactividad. La app sigue usable mientras responde.',
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
              if (action != null) ...[
                const SizedBox(height: 16),
                action!,
              ],
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
  const ServerStatusBanner({super.key, required this.repo});

  final ServerRepository repo;

  @override
  Widget build(BuildContext context) {
    switch (repo.state) {
      case ServerLoadState.initial:
      case ServerLoadState.loading:
        return Container(
          width: double.infinity,
          color: AppTheme.goldSoft,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: [
              const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppTheme.maroon,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  repo.slowWakeup
                      ? 'Render está despertando… puedes explorar ejemplos o borradores mientras responde.'
                      : 'Verificando conexión y catálogo con FastAPI…',
                  style: const TextStyle(fontSize: 12.5, color: AppTheme.ink),
                ),
              ),
            ],
          ),
        );
      case ServerLoadState.ready:
        if (!repo.isVersionCompatible) {
          return Container(
            width: double.infinity,
            color: AppTheme.warnBg,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Text(
              'Versión de API distinta (${repo.version?.apiVersion}). Revisa compatibilidad en Proyecto.',
              style: const TextStyle(fontSize: 12.5, color: AppTheme.ink),
            ),
          );
        }
        return const SizedBox.shrink();
      case ServerLoadState.saved:
        return Container(
          width: double.infinity,
          color: AppTheme.warnBg,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.offline_bolt_outlined,
                  size: 18, color: AppTheme.warnAmber),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Sin conexión actual: usando catálogo guardado localmente.',
                  style: TextStyle(fontSize: 12.5, color: AppTheme.ink),
                ),
              ),
              TextButton(
                onPressed: repo.refreshStatus,
                child: const Text('Conectar'),
              ),
            ],
          ),
        );
      case ServerLoadState.offline:
      case ServerLoadState.error:
        return Container(
          width: double.infinity,
          color: AppTheme.errorBg,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.cloud_off, size: 18, color: AppTheme.errorRed),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  repo.errorMessage ?? 'Sin conexión al servidor.',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12.5, color: AppTheme.ink),
                ),
              ),
              TextButton(
                onPressed: repo.refreshStatus,
                child: const Text('Reintentar'),
              ),
            ],
          ),
        );
      case ServerLoadState.empty:
        return const SizedBox.shrink();
    }
  }
}
