import 'dart:convert';

import 'package:flutter/material.dart';

import 'api.dart';
import 'forms.dart';
import 'main.dart';
import 'ui.dart';

class AttendanceEditor extends StatefulWidget {
  final Api api;
  final Map<String, dynamic> session;
  final bool readOnly;
  final VoidCallback onChanged;
  const AttendanceEditor({
    super.key,
    required this.api,
    required this.session,
    required this.readOnly,
    required this.onChanged,
  });
  @override
  State<AttendanceEditor> createState() => AttendanceEditorState();
}

class AttendanceEditorState extends State<AttendanceEditor> {
  late Map<int, String?> choices;
  late int version;
  bool busy = false, dirty = false;
  String? error, success, pendingKey, pendingPayload;
  bool get finalized => widget.session['finalized_at'] != null;
  @override
  void initState() {
    super.initState();
    reset();
  }

  @override
  void didUpdateWidget(covariant AttendanceEditor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.session != widget.session) reset();
  }

  void reset() {
    choices = {
      for (final student in widget.session['students'])
        student['student_id'] as int: student['status'] as String?,
    };
    version = widget.session['version'];
    dirty = false;
  }

  Future<bool> canLeave() async =>
      !dirty ||
      await confirm(
        context,
        'Leave unsaved attendance?',
        'Your unsaved changes will be discarded. Stay here to save them first.',
      );
  Future<void> save() async {
    if (busy) return;
    final items = choices.entries
        .where((x) => x.value != null)
        .map((x) => {'student_id': x.key, 'status': x.value})
        .toList();
    if (items.isEmpty) {
      setState(() => error = 'Mark at least one student before saving.');
      return;
    }
    final payload = {'version': version, 'items': items};
    final serialized = jsonEncode(payload);
    if (serialized != pendingPayload) {
      pendingKey = widget.api.newKey();
      pendingPayload = serialized;
    }
    setState(() {
      busy = true;
      error = null;
      success = null;
    });
    try {
      final result = await widget.api.request(
        'PUT',
        '/sessions/${widget.session['id']}/attendance',
        body: payload,
        key: pendingKey,
      );
      if (!mounted) return;
      setState(() {
        version = result['version'];
        dirty = false;
        success = 'Saved to the attendance record.';
        pendingKey = null;
        pendingPayload = null;
      });
    } on ApiError catch (value) {
      if (mounted) setState(() => error = value.message);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> finalize() async {
    if (dirty) {
      setState(() => error = 'Save your changes before finalizing.');
      return;
    }
    if (choices.values.any((x) => x == null)) {
      setState(
        () => error = 'Explicitly mark every learner before finalizing.',
      );
      return;
    }
    if (!await confirm(
      context,
      'Finalize attendance?',
      'Confirm that every entry is correct. Future changes will require a recorded correction reason.',
    )) {
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.request(
        'POST',
        '/sessions/${widget.session['id']}/finalize',
        body: {'version': version},
        key: widget.api.newKey(),
      );
      if (mounted) widget.onChanged();
    } on ApiError catch (value) {
      if (mounted) setState(() => error = value.message);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> correct(Map<String, dynamic> student) async {
    final changed = await showDialog<bool>(
      context: context,
      builder: (context) => EntityForm(
        title: 'Correct ${student['display_name']}',
        fields: [
          FieldSpec(
            'status',
            'Attendance status',
            initial: student['status'],
            options: const {
              'present': 'Present',
              'late': 'Late',
              'absent': 'Absent',
              'excused': 'Excused',
            },
          ),
          const FieldSpec(
            'reason',
            'Reason (avoid personal information)',
            maxLength: 240,
          ),
        ],
        submit: (values) async {
          await widget.api.request(
            'POST',
            '/sessions/${widget.session['id']}/corrections',
            body: {
              'version': version,
              'student_id': student['student_id'],
              'status': values['status'],
              'reason': values['reason'],
            },
            key: widget.api.newKey(),
          );
        },
      ),
    );
    if (changed == true && mounted) widget.onChanged();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Panel(
        child: Wrap(
          spacing: 28,
          runSpacing: 14,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.session['class_code'] ?? 'Class session',
                  style: const TextStyle(
                    color: teal,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text('${manila(widget.session['starts_at'])} · Manila time'),
              ],
            ),
            StatusPill(finalized ? 'finalized' : 'draft'),
            Text(
              '${choices.values.where((x) => x != null).length} / ${choices.length} marked',
            ),
            if (dirty)
              const Text(
                'Unsaved changes',
                style: TextStyle(
                  color: Color(0xFF93621B),
                  fontWeight: FontWeight.w600,
                ),
              ),
          ],
        ),
      ),
      const SizedBox(height: 20),
      if (error != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Semantics(
            liveRegion: true,
            child: Text(
              error!,
              key: const Key('attendance-error'),
              style: const TextStyle(color: Color(0xFFB3261E)),
            ),
          ),
        ),
      if (success != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Semantics(
            liveRegion: true,
            child: Text(success!, style: const TextStyle(color: teal)),
          ),
        ),
      Panel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 16,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text(
                  'Class attendance',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                if (!finalized && !widget.readOnly)
                  TextButton.icon(
                    onPressed: busy
                        ? null
                        : () => setState(() {
                            choices.updateAll((_, _) => 'present');
                            dirty = true;
                            success = null;
                          }),
                    icon: const Icon(Icons.done_all, size: 18),
                    label: const Text('Mark all present'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            for (final raw in widget.session['students'])
              Builder(
                builder: (context) {
                  final student = Map<String, dynamic>.from(raw);
                  final status = choices[student['student_id']];
                  return Container(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: const BoxDecoration(
                      border: Border(
                        bottom: BorderSide(color: Color(0xFFE7ECEF)),
                      ),
                    ),
                    child: LayoutBuilder(
                      builder: (context, bounds) {
                        final name = Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              student['display_name'],
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text(
                              student['student_code'],
                              style: const TextStyle(
                                color: Color(0xFF657680),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        );
                        final control = finalized || widget.readOnly
                            ? Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  StatusPill(status ?? 'pending'),
                                  if (finalized && !widget.readOnly)
                                    IconButton(
                                      tooltip:
                                          'Correct attendance for ${student['display_name']}',
                                      onPressed: () => correct(student),
                                      icon: const Icon(
                                        Icons.edit_outlined,
                                        size: 18,
                                      ),
                                    ),
                                ],
                              )
                            : SizedBox(
                                width: 170,
                                child: DropdownButtonFormField<String>(
                                  key: ValueKey(
                                    '${student['student_id']}-$status',
                                  ),
                                  initialValue: status,
                                  decoration: InputDecoration(
                                    labelText:
                                        'Status · ${student['student_code']}',
                                    isDense: true,
                                    contentPadding: const EdgeInsets.symmetric(
                                      horizontal: 12,
                                      vertical: 12,
                                    ),
                                  ),
                                  hint: const Text('Pending'),
                                  items:
                                      const [
                                            'present',
                                            'late',
                                            'absent',
                                            'excused',
                                          ]
                                          .map(
                                            (s) => DropdownMenuItem(
                                              value: s,
                                              child: Text(titleCase(s)),
                                            ),
                                          )
                                          .toList(),
                                  onChanged: busy
                                      ? null
                                      : (value) => setState(() {
                                          choices[student['student_id']] =
                                              value;
                                          dirty = true;
                                          success = null;
                                        }),
                                ),
                              );
                        return bounds.maxWidth < 380
                            ? Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  name,
                                  const SizedBox(height: 12),
                                  control,
                                ],
                              )
                            : Row(
                                children: [
                                  Expanded(child: name),
                                  control,
                                ],
                              );
                      },
                    ),
                  );
                },
              ),
            if (!finalized && !widget.readOnly)
              Padding(
                padding: const EdgeInsets.only(top: 24),
                child: Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton.icon(
                      onPressed: busy ? null : save,
                      icon: const Icon(Icons.save_outlined),
                      label: Text(busy ? 'Saving…' : 'Save attendance'),
                    ),
                    OutlinedButton.icon(
                      onPressed: busy ? null : finalize,
                      icon: const Icon(Icons.lock_outline),
                      label: const Text('Finalize session'),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            Text(
              widget.readOnly
                  ? 'Read-only access. Attendance changes are restricted to authorized staff.'
                  : finalized
                  ? 'Finalized record. Corrections retain their reason and audit history.'
                  : 'Pending means unmarked. It does not count as an absence.',
              style: const TextStyle(color: Color(0xFF657680), fontSize: 12),
            ),
          ],
        ),
      ),
    ],
  );
}
