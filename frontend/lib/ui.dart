import 'package:flutter/material.dart';

import 'main.dart';

String titleCase(String value) => value.isEmpty
    ? value
    : value[0].toUpperCase() + value.substring(1).replaceAll('_', ' ');
String manila(dynamic value) {
  if (value == null) return '—';
  final date = value is num
      ? DateTime.fromMillisecondsSinceEpoch((value * 1000).round(), isUtc: true)
      : DateTime.tryParse(value.toString());
  if (date == null) return value.toString();
  final d = date.toUtc().add(const Duration(hours: 8));
  return '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}  ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}

class StatusPill extends StatelessWidget {
  final String label;
  const StatusPill(this.label, {super.key});
  @override
  Widget build(BuildContext context) {
    final color = switch (label.toLowerCase()) {
      'present' || 'delivered' || 'finalized' => teal,
      'late' || 'retry' || 'pending' || 'draft' => const Color(0xFF93621B),
      'absent' || 'action_required' => const Color(0xFFB74242),
      _ => const Color(0xFF556A9C),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .09),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        titleCase(label),
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class Panel extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  const Panel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(24),
  });
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(padding: padding, child: child),
  );
}

class EmptyState extends StatelessWidget {
  final String message;
  const EmptyState(this.message, {super.key});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(36),
    child: Column(
      children: [
        const Icon(Icons.inbox_outlined, color: Color(0xFF78909C), size: 36),
        const SizedBox(height: 12),
        Text(message, textAlign: TextAlign.center),
      ],
    ),
  );
}

Widget horizontalTable(List<String> headings, List<DataRow> rows) =>
    SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: const WidgetStatePropertyAll(Color(0xFFF7F9FA)),
        columnSpacing: 28,
        columns: headings
            .map(
              (x) => DataColumn(
                label: Text(
                  x,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF657680),
                  ),
                ),
              ),
            )
            .toList(),
        rows: rows,
      ),
    );
Future<bool> confirm(
  BuildContext context,
  String title,
  String message,
) async =>
    await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirm'),
          ),
        ],
      ),
    ) ??
    false;
