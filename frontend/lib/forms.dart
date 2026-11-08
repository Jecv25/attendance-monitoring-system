import 'package:flutter/material.dart';

import 'api.dart';

class FieldSpec {
  final String name, label;
  final String initial;
  final Map<String, String>? options;
  final int maxLength;
  final bool password;
  const FieldSpec(
    this.name,
    this.label, {
    this.initial = '',
    this.options,
    this.maxLength = 100,
    this.password = false,
  });
}

class EntityForm extends StatefulWidget {
  final String title;
  final List<FieldSpec> fields;
  final Future<void> Function(Map<String, String>) submit;
  const EntityForm({
    super.key,
    required this.title,
    required this.fields,
    required this.submit,
  });
  @override
  State<EntityForm> createState() => _EntityFormState();
}

class _EntityFormState extends State<EntityForm> {
  final form = GlobalKey<FormState>();
  late final controllers = {
    for (final field in widget.fields)
      field.name: TextEditingController(text: field.initial),
  };
  String? error;
  bool busy = false;
  @override
  void dispose() {
    for (final controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  String? validate(FieldSpec field, String? raw) {
    final value = field.password ? (raw ?? '') : (raw ?? '').trim();
    if (value.isEmpty) return '${field.label} is required';
    if (field.password && value.length < 12) {
      return 'Use at least 12 characters';
    }
    if (field.name == 'username' &&
        !RegExp(r'^[a-z][a-z0-9_.-]{2,39}$').hasMatch(value)) {
      return 'Use 3–40 lowercase letters, numbers, dots, dashes or underscores';
    }
    if ((field.name == 'student_code' || field.name == 'code') &&
        !RegExp(r'^[A-Za-z0-9-]{2,30}$').hasMatch(value)) {
      return 'Use 2–30 letters, numbers or dashes';
    }
    if ((field.name == 'display_name' || field.name == 'title') &&
        value.length < 2) {
      return 'Use at least 2 characters';
    }
    if (field.name == 'reason' && value.length < 8) {
      return 'Explain the correction in at least 8 characters';
    }
    if (field.name.endsWith('_at')) {
      if (DateTime.tryParse(value) == null ||
          !RegExp(r'(Z|[+-]\d\d:\d\d)$').hasMatch(value)) {
        return 'Use a valid date/time with +08:00 or Z timezone';
      }
    }
    return null;
  }

  Future<void> save() async {
    if (!form.currentState!.validate() || busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.submit({
        for (final field in widget.fields)
          field.name: field.password
              ? controllers[field.name]!.text
              : controllers[field.name]!.text.trim(),
      });
      if (mounted) Navigator.pop(context, true);
    } on ApiError catch (value) {
      if (mounted) setState(() => error = value.message);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(widget.title),
    content: SizedBox(
      width: 450,
      child: SingleChildScrollView(
        child: Form(
          key: form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final field in widget.fields)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: field.options == null
                      ? TextFormField(
                          controller: controllers[field.name],
                          decoration: InputDecoration(labelText: field.label),
                          maxLength: field.maxLength,
                          obscureText: field.password,
                          validator: (v) => validate(field, v),
                        )
                      : DropdownButtonFormField<String>(
                          initialValue: field.initial.isEmpty
                              ? null
                              : field.initial,
                          isExpanded: true,
                          decoration: InputDecoration(labelText: field.label),
                          items: field.options!.entries
                              .map(
                                (x) => DropdownMenuItem(
                                  value: x.key,
                                  child: Text(
                                    x.value,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              )
                              .toList(),
                          onChanged: (value) =>
                              controllers[field.name]!.text = value ?? '',
                          validator: (v) => validate(field, v),
                        ),
                ),
              if (error != null)
                Semantics(
                  liveRegion: true,
                  child: Text(
                    error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
            ],
          ),
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: busy ? null : () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      FilledButton(
        onPressed: busy ? null : save,
        child: Text(busy ? 'Saving…' : 'Save'),
      ),
    ],
  );
}
