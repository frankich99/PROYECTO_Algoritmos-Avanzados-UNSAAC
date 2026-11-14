import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

class PickedTextFile {
  const PickedTextFile({required this.name, required this.content});

  final String name;
  final String content;
}

class DeviceFilesService {
  Future<PickedTextFile?> pickGraphFile() async {
    final file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: const ['json', 'txt', 'csv', 'edges'],
    );
    if (file == null) return null;

    final bytes = await file.xFile.readAsBytes();
    final content = utf8.decode(bytes);
    return PickedTextFile(name: file.name, content: content);
  }

  Future<void> copyToClipboard(String text) async {
    await Clipboard.setData(ClipboardData(text: text));
  }

  Future<void> shareTextFile({
    required String filename,
    required String content,
    String? subject,
  }) async {
    final dir = await getTemporaryDirectory();
    final safeName = filename.replaceAll(RegExp(r'[^a-zA-Z0-9._-]'), '_');
    final file = File(p.join(dir.path, safeName));
    await file.writeAsString(content, encoding: utf8);
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path)],
        subject: subject ?? filename,
        text: subject ?? 'Instancia exportada desde Rutas Cusco UNSAAC',
      ),
    );
  }

  Future<void> shareAssetBinary({
    required String assetPath,
    required String outputFilename,
    String? subject,
  }) async {
    final byteData = await rootBundle.load(assetPath);
    final dir = await getTemporaryDirectory();
    final safeName = outputFilename.replaceAll(RegExp(r'[^a-zA-Z0-9._-]'), '_');
    final file = File(p.join(dir.path, safeName));
    await file.writeAsBytes(
      byteData.buffer.asUint8List(
        byteData.offsetInBytes,
        byteData.lengthInBytes,
      ),
      flush: true,
    );
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path)],
        subject: subject ?? outputFilename,
        text: subject ?? outputFilename,
      ),
    );
  }
}
