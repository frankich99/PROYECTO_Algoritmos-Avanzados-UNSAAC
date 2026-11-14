import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

class SavedInstanceRecord {
  const SavedInstanceRecord({
    required this.id,
    required this.name,
    required this.sourceKind,
    required this.format,
    required this.metric,
    required this.directed,
    required this.payloadJson,
    this.generatorMetaJson,
    required this.nodesCount,
    required this.edgesCount,
    required this.isValidServer,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String name;
  final String sourceKind;
  final String format;
  final String metric;
  final bool directed;
  final String payloadJson;
  final String? generatorMetaJson;
  final int nodesCount;
  final int edgesCount;
  final bool isValidServer;
  final String createdAt;
  final String updatedAt;

  Map<String, Object?> toRow() => {
        'id': id,
        'name': name,
        'source_kind': sourceKind,
        'format': format,
        'metric': metric,
        'directed': directed ? 1 : 0,
        'payload_json': payloadJson,
        'generator_meta_json': generatorMetaJson,
        'nodes_count': nodesCount,
        'edges_count': edgesCount,
        'is_valid_server': isValidServer ? 1 : 0,
        'created_at': createdAt,
        'updated_at': updatedAt,
      };

  factory SavedInstanceRecord.fromRow(Map<String, Object?> row) {
    return SavedInstanceRecord(
      id: row['id'] as String,
      name: row['name'] as String,
      sourceKind: row['source_kind'] as String,
      format: row['format'] as String,
      metric: row['metric'] as String,
      directed: (row['directed'] as int) == 1,
      payloadJson: row['payload_json'] as String,
      generatorMetaJson: row['generator_meta_json'] as String?,
      nodesCount: row['nodes_count'] as int,
      edgesCount: row['edges_count'] as int,
      isValidServer: (row['is_valid_server'] as int) == 1,
      createdAt: row['created_at'] as String,
      updatedAt: row['updated_at'] as String,
    );
  }
}

class SavedRouteRecord {
  const SavedRouteRecord({
    required this.id,
    required this.title,
    required this.instanceName,
    required this.metric,
    required this.unit,
    required this.sourceLabel,
    required this.targetLabel,
    this.cost,
    required this.requestJson,
    required this.responseJson,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String instanceName;
  final String metric;
  final String unit;
  final String sourceLabel;
  final String targetLabel;
  final double? cost;
  final String requestJson;
  final String responseJson;
  final String createdAt;

  Map<String, Object?> toRow() => {
        'id': id,
        'title': title,
        'instance_name': instanceName,
        'metric': metric,
        'unit': unit,
        'source_label': sourceLabel,
        'target_label': targetLabel,
        'cost': cost,
        'request_json': requestJson,
        'response_json': responseJson,
        'created_at': createdAt,
      };

  factory SavedRouteRecord.fromRow(Map<String, Object?> row) {
    return SavedRouteRecord(
      id: row['id'] as String,
      title: row['title'] as String,
      instanceName: row['instance_name'] as String,
      metric: row['metric'] as String,
      unit: row['unit'] as String,
      sourceLabel: row['source_label'] as String,
      targetLabel: row['target_label'] as String,
      cost: (row['cost'] as num?)?.toDouble(),
      requestJson: row['request_json'] as String,
      responseJson: row['response_json'] as String,
      createdAt: row['created_at'] as String,
    );
  }
}

class SavedExperimentRecord {
  const SavedExperimentRecord({
    required this.id,
    required this.profile,
    required this.seed,
    required this.runs,
    required this.responseJson,
    required this.createdAt,
  });

  final String id;
  final String profile;
  final int seed;
  final int runs;
  final String responseJson;
  final String createdAt;

  Map<String, Object?> toRow() => {
        'id': id,
        'profile': profile,
        'seed': seed,
        'runs': runs,
        'response_json': responseJson,
        'created_at': createdAt,
      };

  factory SavedExperimentRecord.fromRow(Map<String, Object?> row) {
    return SavedExperimentRecord(
      id: row['id'] as String,
      profile: row['profile'] as String,
      seed: row['seed'] as int,
      runs: row['runs'] as int,
      responseJson: row['response_json'] as String,
      createdAt: row['created_at'] as String,
    );
  }
}

/// Base de datos SQLite interna del dispositivo (sin servidor de BD externo).
/// Almacena borradores, instancias completas exportadas/importadas, consultas
/// guardadas y experimentos de sesión con esquema versionado.
class AppDatabase {
  AppDatabase({
    this.factory,
    this.customPath,
  });

  static const int schemaVersion = 1;
  static const String defaultDbName = 'rutas_cusco_local.db';

  final DatabaseFactory? factory;
  final String? customPath;
  Database? _db;

  Future<Database> open() async {
    if (_db != null && _db!.isOpen) return _db!;

    final effectiveFactory = factory ?? databaseFactory;
    final String path;
    if (customPath != null) {
      path = customPath!;
    } else {
      final dbDir = await effectiveFactory.getDatabasesPath();
      path = p.join(dbDir, defaultDbName);
    }

    _db = await effectiveFactory.openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: schemaVersion,
        onCreate: (db, version) async => _createSchema(db),
        onUpgrade: (db, oldVersion, newVersion) async {
          // Preparado para migraciones incrementales sin perder datos del usuario.
          if (oldVersion < 1) {
            await _createSchema(db);
          }
        },
      ),
    );
    return _db!;
  }

  Future<void> _createSchema(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS saved_instances (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_kind TEXT NOT NULL,
        format TEXT NOT NULL,
        metric TEXT NOT NULL,
        directed INTEGER NOT NULL,
        payload_json TEXT NOT NULL,
        generator_meta_json TEXT,
        nodes_count INTEGER NOT NULL,
        edges_count INTEGER NOT NULL,
        is_valid_server INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS saved_routes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        instance_name TEXT NOT NULL,
        metric TEXT NOT NULL,
        unit TEXT NOT NULL,
        source_label TEXT NOT NULL,
        target_label TEXT NOT NULL,
        cost REAL,
        request_json TEXT NOT NULL,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS saved_experiments (
        id TEXT PRIMARY KEY,
        profile TEXT NOT NULL,
        seed INTEGER NOT NULL,
        runs INTEGER NOT NULL,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    ''');
  }

  Future<List<SavedInstanceRecord>> listInstances() async {
    final db = await open();
    final rows = await db.query(
      'saved_instances',
      orderBy: 'updated_at DESC',
    );
    return rows.map(SavedInstanceRecord.fromRow).toList();
  }

  Future<void> upsertInstance(SavedInstanceRecord record) async {
    final db = await open();
    await db.insert(
      'saved_instances',
      record.toRow(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> deleteInstance(String id) async {
    final db = await open();
    await db.delete('saved_instances', where: 'id = ?', whereArgs: [id]);
  }

  Future<List<SavedRouteRecord>> listRoutes() async {
    final db = await open();
    final rows = await db.query(
      'saved_routes',
      orderBy: 'created_at DESC',
    );
    return rows.map(SavedRouteRecord.fromRow).toList();
  }

  Future<void> upsertRoute(SavedRouteRecord record) async {
    final db = await open();
    await db.insert(
      'saved_routes',
      record.toRow(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> deleteRoute(String id) async {
    final db = await open();
    await db.delete('saved_routes', where: 'id = ?', whereArgs: [id]);
  }

  Future<List<SavedExperimentRecord>> listExperiments() async {
    final db = await open();
    final rows = await db.query(
      'saved_experiments',
      orderBy: 'created_at DESC',
    );
    return rows.map(SavedExperimentRecord.fromRow).toList();
  }

  Future<void> upsertExperiment(SavedExperimentRecord record) async {
    final db = await open();
    await db.insert(
      'saved_experiments',
      record.toRow(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> deleteExperiment(String id) async {
    final db = await open();
    await db.delete('saved_experiments', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> close() async {
    if (_db != null && _db!.isOpen) {
      await _db!.close();
      _db = null;
    }
  }
}
