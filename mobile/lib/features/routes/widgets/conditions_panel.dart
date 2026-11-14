import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_select_field.dart';
import '../../../core/widgets/state_views.dart';
import '../../../data/models/analysis_models.dart';
import '../../../data/models/instance_models.dart';
import '../../../data/models/route_models.dart';
import '../../../data/repositories/conditions_repository.dart';
import '../../../data/repositories/server_repository.dart';

class ConditionsSelection {
  const ConditionsSelection({
    this.weatherEnabled = false,
    this.weatherMode = 'historical',
    this.weatherProvider = 'open-meteo',
    this.trafficEnabled = false,
    this.trafficMode = 'simulated',
    this.simulatedTime = const TimeOfDay(hour: 8, minute: 30),
    this.trafficUseTomTom = false,
  });

  final bool weatherEnabled;
  final String weatherMode;
  final String weatherProvider;
  final bool trafficEnabled;
  final String trafficMode;
  final TimeOfDay simulatedTime;
  final bool trafficUseTomTom;

  ConditionsSelection copyWith({
    bool? weatherEnabled,
    String? weatherMode,
    String? weatherProvider,
    bool? trafficEnabled,
    String? trafficMode,
    TimeOfDay? simulatedTime,
    bool? trafficUseTomTom,
  }) {
    return ConditionsSelection(
      weatherEnabled: weatherEnabled ?? this.weatherEnabled,
      weatherMode: weatherMode ?? this.weatherMode,
      weatherProvider: weatherProvider ?? this.weatherProvider,
      trafficEnabled: trafficEnabled ?? this.trafficEnabled,
      trafficMode: trafficMode ?? this.trafficMode,
      simulatedTime: simulatedTime ?? this.simulatedTime,
      trafficUseTomTom: trafficUseTomTom ?? this.trafficUseTomTom,
    );
  }

  ScenarioSpec toScenarioSpec({
    required ConditionsRepository condRepo,
    required PointCoord queryPoint,
    required bool isGeographic,
  }) {
    String weather = 'none';
    Map<String, dynamic>? weatherObs;
    PointCoord? weatherReqPoint;
    String? weatherKey;

    if (weatherEnabled) {
      weather = weatherMode;
      if (weatherMode == 'live' && condRepo.liveWeather?.observation != null) {
        weatherObs = condRepo.liveWeather!.observation!.toJson();
        weatherReqPoint = condRepo.liveWeather!.requested;
      } else if (weatherMode == 'saved' &&
          condRepo.savedWeather?.observation != null) {
        weatherObs = condRepo.savedWeather!.observation!.toJson();
        weatherReqPoint = condRepo.savedWeather!.requested;
      }
      if (weatherMode == 'live' && weatherProvider == 'openweathermap') {
        final k = condRepo.keyFor('openweathermap').trim();
        if (k.isNotEmpty) weatherKey = k;
      }
    }

    double? trafficHour;
    String? trafficModeVal;
    var trafficLive = false;
    String? trafficKey;

    if (trafficEnabled) {
      trafficModeVal = trafficMode;
      if (trafficMode == 'simulated') {
        trafficHour = simulatedTime.hour + simulatedTime.minute / 60.0;
      } else if (trafficMode == 'current' && isGeographic && trafficUseTomTom) {
        trafficLive = true;
        final k = condRepo.keyFor('tomtom').trim();
        if (k.isNotEmpty) trafficKey = k;
      }
    }

    return ScenarioSpec(
      weather: weather,
      weatherProvider: weatherProvider,
      weatherKey: weatherKey,
      weatherObservation: weatherObs,
      weatherRequestPoint: weatherReqPoint ?? (weatherEnabled ? queryPoint : null),
      trafficHour: trafficHour,
      trafficMode: trafficModeVal,
      trafficLive: trafficLive,
      trafficLiveKey: trafficKey,
    );
  }
}

class ConditionsPanel extends StatelessWidget {
  const ConditionsPanel({
    super.key,
    required this.selection,
    required this.onChanged,
    required this.metric,
    required this.isAbstractWeights,
    required this.isGeographic,
    required this.queryPoint,
  });

  final ConditionsSelection selection;
  final void Function(ConditionsSelection next) onChanged;
  final String metric;
  final bool isAbstractWeights;
  final bool isGeographic;
  final PointCoord queryPoint;

  String _simulatedScheduleLabel(TimeOfDay t) {
    final h = t.hour + t.minute / 60.0;
    if ((h >= 7.0 && h <= 9.0) || (h >= 12.0 && h <= 14.0) || (h >= 17.5 && h <= 20.0)) {
      return 'Hora punta (supuesto ×2.20)';
    }
    if ((h >= 9.0 && h < 12.0) || (h > 14.0 && h < 17.5)) {
      return 'Tráfico alto/moderado según franja';
    }
    return 'Flujo nocturno / valle (supuesto ×1.00)';
  }

  @override
  Widget build(BuildContext context) {
    final condRepo = context.watch<ConditionsRepository>();
    final serverRepo = context.watch<ServerRepository>();
    final providerKeys = serverRepo.catalog?.providerKeys;

    if (isAbstractWeights || metric != 'time') {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.paper,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppTheme.border),
        ),
        child: Text(
          isAbstractWeights
              ? 'Clima y tráfico no aplican a instancias de pesos abstractos («peso»).'
              : 'Clima y tráfico solo modifican tiempos de viaje (métrica «Tiempo»), no distancias en metros.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      );
    }

    final savedSamePoint = condRepo.savedWeather != null &&
        ConditionsRepository.samePoint(
          condRepo.savedWeather!.requested,
          queryPoint,
        );
    final liveSamePoint = condRepo.liveWeather != null &&
        ConditionsRepository.samePoint(
          condRepo.liveWeather!.requested,
          queryPoint,
        );

    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text(
        '04 / Clima y tráfico (factor uniforme)',
        style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
      ),
      subtitle: Text(
        selection.weatherEnabled || selection.trafficEnabled
            ? 'Escenario activo · escala costos sin cambiar la ruta óptima'
            : 'Opcional · tiempo nominal sin ajustes',
        style: Theme.of(context).textTheme.bodySmall,
      ),
      children: [
        const SizedBox(height: 4),
        Text(
          'Un factor global multiplica todas las aristas por igual: altera el costo temporal, pero no cambia el orden de los caminos.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text('Ajustar por clima meteorológico'),
          value: selection.weatherEnabled,
          onChanged: (v) => onChanged(selection.copyWith(weatherEnabled: v)),
        ),
        if (selection.weatherEnabled) ...[
          AppSelectField<String>(
            label: 'Fuente climática',
            value: selection.weatherMode,
            leadingIcon: Icons.cloud_outlined,
            options: [
              const SelectOption(
                value: 'historical',
                label: 'Histórica del informe (Open-Meteo 28/10/2026)',
                subtitle: 'Observación canónica congelada para reproducibilidad',
                icon: Icons.history,
              ),
              const SelectOption(
                value: 'snapshot',
                label: 'Snapshot incluido (OpenWeatherMap)',
                subtitle: 'Lectura local posterior guardada en el proyecto',
                icon: Icons.inventory_2_outlined,
              ),
              const SelectOption(
                value: 'live',
                label: 'Consulta actual en el origen (en vivo)',
                subtitle: 'Consulta al proveedor para el punto seleccionado',
                icon: Icons.cloud_download_outlined,
              ),
              SelectOption(
                value: 'saved',
                enabled: condRepo.savedWeather != null,
                label: condRepo.savedWeather == null
                    ? 'Lectura guardada (ninguna aún)'
                    : 'Lectura guardada en dispositivo',
                subtitle: condRepo.savedWeather == null
                    ? 'Guarda una lectura en vivo primero'
                    : 'Escenario reproducible guardado en este teléfono',
                icon: Icons.bookmark_outline,
              ),
            ],
            onChanged: (v) => onChanged(selection.copyWith(weatherMode: v)),
          ),
          if (selection.weatherMode == 'live') ...[
            const SizedBox(height: 10),
            AppSelectField<String>(
              label: 'Proveedor de clima',
              value: selection.weatherProvider,
              leadingIcon: Icons.public_outlined,
              options: [
                const SelectOption(
                  value: 'open-meteo',
                  label: 'Open-Meteo (sin clave)',
                  subtitle: 'Datos de modelo meteorológico sin credenciales',
                ),
                SelectOption(
                  value: 'openweathermap',
                  label: providerKeys?.openweathermap == true
                      ? 'OpenWeatherMap (clave en servidor)'
                      : 'OpenWeatherMap (requiere clave)',
                  subtitle: 'Lectura actual vía API v2.5',
                ),
              ],
              onChanged: (v) =>
                  onChanged(selection.copyWith(weatherProvider: v)),
            ),
            if (selection.weatherProvider == 'openweathermap') ...[
              const SizedBox(height: 8),
              _ProviderKeyField(
                label: 'Clave personal OpenWeatherMap (opcional)',
                initialValue: condRepo.keyFor('openweathermap'),
                serverConfigured: providerKeys?.openweathermap ?? false,
                onChanged: (val) =>
                    condRepo.updatePersonalKey('openweathermap', val),
              ),
            ],
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: condRepo.loading
                      ? null
                      : () => condRepo.fetchCondition(
                            point: queryPoint,
                            provider: selection.weatherProvider,
                          ),
                  icon: const Icon(Icons.cloud_download_outlined, size: 18),
                  label: Text(
                    condRepo.loading
                        ? 'Consultando…'
                        : 'Consultar clima (${queryPoint.lat.toStringAsFixed(4)}, ${queryPoint.lon.toStringAsFixed(4)})',
                  ),
                ),
                if (condRepo.liveWeather?.observation != null)
                  OutlinedButton.icon(
                    onPressed: condRepo.saveLiveWeatherLocally,
                    icon: const Icon(Icons.bookmark_add_outlined, size: 18),
                    label: const Text('Guardar lectura'),
                  ),
              ],
            ),
            if (condRepo.liveWeather?.observation != null) ...[
              const SizedBox(height: 8),
              if (!liveSamePoint)
                const Text(
                  'Aviso: la lectura actual corresponde a otro origen. Vuelve a consultar antes de calcular.',
                  style: TextStyle(color: AppTheme.warnAmber, fontSize: 12.5),
                ),
              _WeatherReadingCard(data: condRepo.liveWeather!),
            ],
          ],
          if (selection.weatherMode == 'saved' &&
              condRepo.savedWeather?.observation != null) ...[
            const SizedBox(height: 8),
            const SavedDataBadge(
              label: 'Escenario guardado · no es medición en vivo',
            ),
            if (!savedSamePoint)
              const Padding(
                padding: EdgeInsets.only(top: 6),
                child: Text(
                  'La lectura guardada corresponde a otro punto de origen. Cambia el origen o usa otro modo.',
                  style: TextStyle(color: AppTheme.errorRed, fontSize: 12.5),
                ),
              ),
            const SizedBox(height: 6),
            _WeatherReadingCard(data: condRepo.savedWeather!),
            TextButton.icon(
              onPressed: () {
                condRepo.forgetSavedWeather();
                onChanged(selection.copyWith(weatherMode: 'historical'));
              },
              icon: const Icon(Icons.delete_outline, size: 18),
              label: const Text('Eliminar lectura guardada'),
            ),
          ],
        ],
        if (condRepo.errorMessage != null) ...[
          const SizedBox(height: 8),
          ErrorStateBanner(message: condRepo.errorMessage!),
        ],
        const Divider(height: 20),
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text('Ajustar por tráfico horario'),
          value: selection.trafficEnabled,
          onChanged: (v) => onChanged(selection.copyWith(trafficEnabled: v)),
        ),
        if (selection.trafficEnabled) ...[
          AppSelectField<String>(
            label: 'Modo de horario',
            value: selection.trafficMode,
            leadingIcon: Icons.traffic_outlined,
            options: const [
              SelectOption(
                value: 'simulated',
                label: 'Hora programada (supuesto)',
                subtitle: 'Simula franja horaria de Cusco (no es aforo medido)',
                icon: Icons.schedule,
              ),
              SelectOption(
                value: 'current',
                label: 'Hora actual de Cusco (servidor)',
                subtitle: 'Usa el reloj America/Lima y opcionalmente TomTom',
                icon: Icons.access_time_filled,
              ),
            ],
            onChanged: (v) => onChanged(selection.copyWith(trafficMode: v)),
          ),
          const SizedBox(height: 8),
          if (selection.trafficMode == 'simulated')
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(
                'Hora programada: ${selection.simulatedTime.format(context)}',
              ),
              subtitle: Text(
                '${_simulatedScheduleLabel(selection.simulatedTime)} · Supuesto horario, no aforo medido.',
              ),
              trailing: OutlinedButton(
                onPressed: () async {
                  final picked = await showTimePicker(
                    context: context,
                    initialTime: selection.simulatedTime,
                  );
                  if (picked != null) {
                    onChanged(selection.copyWith(simulatedTime: picked));
                  }
                },
                child: const Text('Cambiar'),
              ),
            )
          else ...[
            Text(
              'Usa el reloj actual de Cusco (America/Lima) en el servidor.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (isGeographic) ...[
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Consultar TomTom puntual en origen (opcional)'),
                subtitle: const Text(
                  'Consulta un segmento cercano al origen; no representa toda la red.',
                ),
                value: selection.trafficUseTomTom,
                onChanged: (v) =>
                    onChanged(selection.copyWith(trafficUseTomTom: v ?? false)),
              ),
              if (selection.trafficUseTomTom)
                _ProviderKeyField(
                  label: 'Clave personal TomTom (opcional)',
                  initialValue: condRepo.keyFor('tomtom'),
                  serverConfigured: providerKeys?.tomtom ?? false,
                  onChanged: (val) => condRepo.updatePersonalKey('tomtom', val),
                ),
            ],
          ],
        ],
        if ((selection.weatherEnabled &&
                selection.weatherMode == 'live' &&
                selection.weatherProvider == 'openweathermap') ||
            (selection.trafficEnabled &&
                selection.trafficMode == 'current' &&
                selection.trafficUseTomTom)) ...[
          const SizedBox(height: 8),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Recordar claves opcionales en este dispositivo'),
            subtitle: const Text(
              'Las claves del servidor nunca se envían al teléfono.',
            ),
            value: condRepo.rememberKeys,
            onChanged: (v) => condRepo.setRememberKeys(v ?? false),
          ),
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton(
              onPressed: condRepo.forgetKeys,
              child: const Text('Olvidar claves del dispositivo'),
            ),
          ),
        ],
      ],
    );
  }
}

class _ProviderKeyField extends StatefulWidget {
  const _ProviderKeyField({
    required this.label,
    required this.initialValue,
    required this.serverConfigured,
    required this.onChanged,
  });

  final String label;
  final String initialValue;
  final bool serverConfigured;
  final ValueChanged<String> onChanged;

  @override
  State<_ProviderKeyField> createState() => _ProviderKeyFieldState();
}

class _ProviderKeyFieldState extends State<_ProviderKeyField> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.initialValue);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _ctrl,
      obscureText: true,
      onChanged: widget.onChanged,
      decoration: InputDecoration(
        labelText: widget.label,
        helperText: widget.serverConfigured
            ? 'El servidor ya tiene una clave configurada; este campo es opcional.'
            : 'Sin clave en servidor: introduce una clave válida para esta consulta.',
      ),
    );
  }
}

class _WeatherReadingCard extends StatelessWidget {
  const _WeatherReadingCard({required this.data});

  final ConditionsResponse data;

  @override
  Widget build(BuildContext context) {
    final obs = data.observation!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.paper,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${obs.source} · ${obs.observedAt} (${obs.timezone})',
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5),
          ),
          const SizedBox(height: 4),
          Text(
            'Temp: ${obs.temperatureC} °C · Lluvia: ${obs.precipitationMm} mm · Visibilidad: ${obs.visibilityM} m · Ráfagas: ${obs.windGustsKmh} km/h · Humedad: ${obs.relativeHumidityPct}%',
            style: const TextStyle(
              fontSize: 12.5,
              fontFeatures: AppTheme.tabularFigures,
            ),
          ),
          Text(
            'Grilla proveedor: (${obs.gridPoint.lat.toStringAsFixed(4)}, ${obs.gridPoint.lon.toStringAsFixed(4)}) · Factor climático: ${data.multiplier?.toStringAsFixed(4) ?? '—'}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
