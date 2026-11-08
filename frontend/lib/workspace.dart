import 'package:flutter/material.dart';

import 'api.dart';
import 'attendance.dart';
import 'forms.dart';
import 'main.dart';
import 'ui.dart';

class Workspace extends StatefulWidget {
  final Api api;
  final Map<String, dynamic> user;
  final VoidCallback onSignedOut;
  const Workspace({
    super.key,
    required this.api,
    required this.user,
    required this.onSignedOut,
  });
  @override
  State<Workspace> createState() => _WorkspaceState();
}

class _WorkspaceState extends State<Workspace> {
  String page = 'Overview', search = '';
  bool loading = true;
  String? error;
  dynamic data;
  int offset = 0;
  int? selected;
  final editor = GlobalKey<AttendanceEditorState>();
  final scaffold = GlobalKey<ScaffoldState>();
  final searchController = TextEditingController();
  bool get isAdmin => widget.user['role'] == 'admin';
  bool get readOnly => widget.user['role'] == 'supervisor';
  final icons = const {
    'Overview': Icons.grid_view_rounded,
    'Sessions': Icons.fact_check_outlined,
    'Students': Icons.people_outline,
    'Classes': Icons.school_outlined,
    'Reports': Icons.bar_chart_rounded,
    'Alerts': Icons.notifications_none_rounded,
    'Audit history': Icons.history_rounded,
    'Accounts': Icons.manage_accounts_outlined,
  };
  List<String> get pages => [
    'Overview',
    'Sessions',
    'Students',
    'Classes',
    'Reports',
    'Alerts',
    'Audit history',
    if (isAdmin) 'Accounts',
  ];
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() {
      loading = true;
      error = null;
    });
    final path = selected != null
        ? '/sessions/$selected'
        : switch (page) {
            'Overview' => '/dashboard',
            'Sessions' => '/sessions?limit=20&offset=$offset',
            'Students' => '/students?limit=20&offset=$offset',
            'Classes' => '/classes?limit=20&offset=$offset',
            'Reports' => '/reports?limit=20&offset=$offset',
            'Alerts' => '/alerts?limit=20&offset=$offset',
            'Audit history' => '/audit?limit=20&offset=$offset',
            _ => '/users?limit=20&offset=$offset',
          };
    try {
      final result = await widget.api.request('GET', path);
      if (mounted) setState(() => data = result);
    } on ApiError catch (value) {
      if (mounted) setState(() => error = value.message);
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<bool> canLeave() async =>
      await editor.currentState?.canLeave() ?? true;
  Future<void> navigate(String next) async {
    if (!await canLeave() || !mounted) return;
    setState(() {
      page = next;
      selected = null;
      offset = 0;
      data = null;
      search = '';
      searchController.clear();
    });
    if (scaffold.currentState?.isDrawerOpen ?? false) Navigator.pop(context);
    await load();
  }

  void message(String text) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
    }
  }

  Future<void> signOut() async {
    if (!await canLeave()) return;
    try {
      await widget.api.request('POST', '/auth/logout');
      if (mounted) widget.onSignedOut();
    } on ApiError catch (value) {
      if (value.status == 401) {
        widget.onSignedOut();
      } else {
        message(value.message);
      }
    }
  }

  Future<void> form(
    String title,
    List<FieldSpec> fields,
    String method,
    String path, {
    Map<String, dynamic> Function(Map<String, String>)? transform,
  }) async {
    final changed = await showDialog<bool>(
      context: context,
      builder: (context) => EntityForm(
        title: title,
        fields: fields,
        submit: (values) async {
          await widget.api.request(
            method,
            path,
            body: transform != null ? transform(values) : values,
          );
        },
      ),
    );
    if (changed == true && mounted) {
      await load();
      message('Changes saved.');
    }
  }

  Future<void> studentForm([Map<String, dynamic>? row]) => form(
    row == null ? 'Add student' : 'Edit student',
    [
      FieldSpec(
        'student_code',
        'Student identifier',
        initial: row?['student_code'] ?? '',
        maxLength: 30,
      ),
      FieldSpec(
        'display_name',
        'Display name',
        initial: row?['display_name'] ?? '',
        maxLength: 80,
      ),
      if (row != null)
        FieldSpec(
          'active',
          'Account status',
          initial: '${row['active'] == 1}',
          options: const {'true': 'Active', 'false': 'Inactive'},
        ),
    ],
    row == null ? 'POST' : 'PUT',
    '/students${row == null ? '' : '/${row['id']}'}',
    transform: (v) => {
      'student_code': v['student_code'],
      'display_name': v['display_name'],
      'active': v['active'] != 'false',
    },
  );
  Future<void> classForm([Map<String, dynamic>? row]) async {
    try {
      final users = await widget.api.request('GET', '/users') as List;
      final teachers = {
        for (final u in users.where(
          (u) => u['role'] == 'teacher' && u['active'] == 1,
        ))
          '${u['id']}': '${u['display_name']}',
      };
      if (!mounted) return;
      if (teachers.isEmpty) {
        message('Create an active teacher account first.');
        return;
      }
      await form(
        row == null ? 'Add class' : 'Edit class and assignment',
        [
          FieldSpec(
            'code',
            'Class code',
            initial: row?['code'] ?? '',
            maxLength: 30,
          ),
          FieldSpec('title', 'Class title', initial: row?['title'] ?? ''),
          FieldSpec(
            'teacher_id',
            'Assigned teacher',
            initial: row == null ? '' : '${row['teacher_id']}',
            options: teachers,
          ),
        ],
        row == null ? 'POST' : 'PUT',
        '/classes${row == null ? '' : '/${row['id']}'}',
        transform: (v) => {
          'code': v['code'],
          'title': v['title'],
          'teacher_id': int.parse(v['teacher_id']!),
        },
      );
    } on ApiError catch (e) {
      message(e.message);
    }
  }

  Future<void> rosterForm(Map<String, dynamic> row) async {
    try {
      final all = await widget.api.request('GET', '/students') as List;
      final roster = await widget.api.request(
        'GET',
        '/classes/${row['id']}/roster',
      ) as List;
      final chosen = roster.map((x) => x['id'] as int).toSet();
      if (!mounted) return;
      final changed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, refresh) => AlertDialog(
            title: Text('Roster · ${row['code']}'),
            content: SizedBox(
              width: 450,
              height: 380,
              child: all.isEmpty
                  ? const EmptyState('Add students before editing the roster.')
                  : ListView(
                      children: [
                        for (final student in all.where(
                          (x) => x['active'] == 1,
                        ))
                          CheckboxListTile(
                            value: chosen.contains(student['id']),
                            title: Text(student['display_name']),
                            subtitle: Text(student['student_code']),
                            onChanged: (value) => refresh(() {
                              value == true
                                  ? chosen.add(student['id'])
                                  : chosen.remove(student['id']);
                            }),
                          ),
                      ],
                    ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () async {
                  try {
                    await widget.api.request(
                      'PUT',
                      '/classes/${row['id']}/roster',
                      body: {'student_ids': chosen.toList()},
                    );
                    if (dialogContext.mounted) {
                      Navigator.pop(dialogContext, true);
                    }
                  } on ApiError catch (e) {
                    message(e.message);
                  }
                },
                child: const Text('Save roster'),
              ),
            ],
          ),
        ),
      );
      if (changed == true) await load();
    } on ApiError catch (e) {
      message(e.message);
    }
  }

  Future<void> sessionForm() async {
    try {
      final classes = await widget.api.request('GET', '/classes') as List;
      if (!mounted) return;
      if (classes.isEmpty) {
        message('Create a class and roster first.');
        return;
      }
      final local = DateTime.now().toUtc().add(const Duration(hours: 8));
      final start =
          '${manila(local.toUtc().subtract(const Duration(hours: 8)).toIso8601String()).replaceFirst('  ', 'T')}:00+08:00';
      final end =
          '${manila(local.toUtc().subtract(const Duration(hours: 7)).toIso8601String()).replaceFirst('  ', 'T')}:00+08:00';
      await form(
        'Schedule attendance session',
        [
          FieldSpec(
            'class_id',
            'Class',
            options: {
              for (final c in classes)
                '${c['id']}': '${c['code']} · ${c['title']}',
            },
          ),
          const FieldSpec('title', 'Session title'),
          FieldSpec(
            'starts_at',
            'Starts at (+08:00 Manila)',
            initial: start,
            maxLength: 40,
          ),
          FieldSpec(
            'ends_at',
            'Ends at (+08:00 Manila)',
            initial: end,
            maxLength: 40,
          ),
        ],
        'POST',
        '/sessions',
        transform: (v) {
          final startTime = DateTime.parse(v['starts_at']!),
              endTime = DateTime.parse(v['ends_at']!);
          if (!endTime.isAfter(startTime) ||
              endTime.difference(startTime) > const Duration(hours: 24)) {
            throw ApiError(422, 'End must follow start within 24 hours.');
          }
          return {...v, 'class_id': int.parse(v['class_id']!)};
        },
      );
    } on ApiError catch (e) {
      message(e.message);
    }
  }

  Future<void> accountForm([Map<String, dynamic>? row]) => form(
    row == null ? 'Create account' : 'Edit account',
    [
      if (row == null) const FieldSpec('username', 'Username', maxLength: 40),
      FieldSpec(
        'display_name',
        'Display name',
        initial: row?['display_name'] ?? '',
        maxLength: 80,
      ),
      if (row == null)
        const FieldSpec(
          'password',
          'Initial password',
          password: true,
          maxLength: 128,
        ),
      FieldSpec(
        'role',
        'Role',
        initial: row?['role'] ?? 'teacher',
        options: const {
          'admin': 'Admin',
          'teacher': 'Teacher',
          'supervisor': 'Supervisor',
        },
      ),
      if (row != null)
        FieldSpec(
          'active',
          'Status',
          initial: '${row['active'] == 1}',
          options: const {'true': 'Active', 'false': 'Inactive'},
        ),
    ],
    row == null ? 'POST' : 'PUT',
    '/users${row == null ? '' : '/${row['id']}'}',
    transform: (v) => {...v, if (row != null) 'active': v['active'] == 'true'},
  );
  Future<void> openSession(int id) async {
    if (!await canLeave() || !mounted) return;
    setState(() {
      selected = id;
      page = 'Sessions';
      data = null;
    });
    await load();
  }

  Widget sidebar() => Material(
    color: ink,
    child: SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 26),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.only(left: 12),
              child: Row(
                children: [
                  Icon(
                    Icons.fact_check_rounded,
                    color: Color(0xFF8DDFCD),
                    size: 28,
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'presence',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 25,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(14, 8, 0, 32),
              child: Text(
                'ATTENDANCE WORKSPACE',
                style: TextStyle(
                  color: Color(0xFF8FAAB4),
                  letterSpacing: 1.3,
                  fontSize: 9,
                ),
              ),
            ),
            Expanded(
              child: ListView(
                children: [
                  for (final item in pages)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 5),
                      child: ListTile(
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(9),
                        ),
                        selected: page == item,
                        selectedTileColor: const Color(0xFF284B50),
                        selectedColor: const Color(0xFFB0E8DA),
                        textColor: const Color(0xFFBCCBD1),
                        iconColor: const Color(0xFF9CB3BE),
                        leading: Icon(icons[item], size: 21),
                        title: Text(item, style: const TextStyle(fontSize: 14)),
                        onTap: () => navigate(item),
                      ),
                    ),
                ],
              ),
            ),
            const Divider(color: Color(0xFF35505D)),
            ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 10),
              leading: CircleAvatar(
                backgroundColor: const Color(0xFF35505D),
                child: Text(
                  widget.user['display_name'].toString()[0],
                  style: const TextStyle(color: Colors.white),
                ),
              ),
              title: Text(
                widget.user['display_name'],
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
              subtitle: Text(
                titleCase(widget.user['role']),
                style: const TextStyle(color: Color(0xFF9CB3BE), fontSize: 11),
              ),
            ),
            TextButton.icon(
              onPressed: signOut,
              icon: const Icon(Icons.logout, size: 16),
              label: const Text('Sign out'),
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFFBCCBD1),
              ),
            ),
          ],
        ),
      ),
    ),
  );
  Widget sessionCards(List<dynamic> rows) => rows.isEmpty
      ? const EmptyState('No attendance sessions yet.')
      : Column(
          children: rows.map((raw) {
            final row = Map<String, dynamic>.from(raw);
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Card(
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: () => openSession(row['id']),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: const Color(0xFFEDF5F2),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(
                            Icons.fact_check_outlined,
                            color: teal,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                row['title'],
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${row['class_code']} · ${manila(row['starts_at'])}',
                                style: const TextStyle(
                                  color: Color(0xFF657680),
                                  fontSize: 12,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                '${row['roster_count'] - row['pending_count']} of ${row['roster_count']} learners marked',
                                style: const TextStyle(
                                  color: Color(0xFF657680),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Column(
                          children: [
                            StatusPill(
                              row['finalized_at'] == null
                                  ? 'draft'
                                  : 'finalized',
                            ),
                            const SizedBox(height: 8),
                            const Icon(
                              Icons.arrow_forward,
                              color: Color(0xFF78909C),
                              size: 18,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        );
  Widget stats(Map<String, dynamic> values) => LayoutBuilder(
    builder: (context, bounds) {
      final columns = bounds.maxWidth >= 850
          ? 4
          : bounds.maxWidth >= 460
          ? 2
          : 1;
      final items = [
        ('Sessions', values['sessions'] ?? 0, Icons.calendar_today_outlined),
        ('Finalized', values['finalized'] ?? 0, Icons.verified_outlined),
        (
          'Pending entries',
          values['pending_students'] ?? 0,
          Icons.pending_actions,
        ),
        (
          'Marked present',
          values['totals']?['present'] ?? 0,
          Icons.person_outline,
        ),
      ];
      return Wrap(
        spacing: 16,
        runSpacing: 16,
        children: [
          for (final item in items)
            SizedBox(
              width: (bounds.maxWidth - 16 * (columns - 1)) / columns,
              child: Panel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            item.$1,
                            style: const TextStyle(
                              color: Color(0xFF657680),
                              fontSize: 12,
                            ),
                          ),
                        ),
                        Icon(item.$3, size: 19, color: teal),
                      ],
                    ),
                    const SizedBox(height: 18),
                    Text(
                      '${item.$2}',
                      style: const TextStyle(
                        color: ink,
                        fontSize: 32,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 5),
                    const Text(
                      'Within your access scope',
                      style: TextStyle(color: Color(0xFF657680), fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
        ],
      );
    },
  );
  Widget overview() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      stats(Map<String, dynamic>.from(data)),
      const SizedBox(height: 24),
      Panel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Attendance at a glance',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 6),
            const Text(
              'Recorded statuses across the latest 100 accessible sessions.',
              style: TextStyle(color: Color(0xFF657680), fontSize: 12),
            ),
            const SizedBox(height: 22),
            Wrap(
              spacing: 28,
              runSpacing: 18,
              children: [
                for (final status in ['present', 'late', 'absent', 'excused'])
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      StatusPill(status),
                      const SizedBox(width: 10),
                      Text(
                        '${data['totals'][status] ?? 0}',
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 22,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ],
        ),
      ),
      const SizedBox(height: 26),
      Row(
        children: [
          Expanded(
            child: Text(
              'Recent sessions',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
          TextButton(
            onPressed: () => navigate('Sessions'),
            child: const Text('View all'),
          ),
        ],
      ),
      const SizedBox(height: 12),
      sessionCards(data['recent_sessions']),
      const SizedBox(height: 20),
      const Text(
        'Scheduled monitoring runs independently of this browser. Pending entries require staff review.',
        style: TextStyle(color: Color(0xFF657680), fontSize: 12),
      ),
    ],
  );
  List<dynamic> get filteredRows {
    final List raw = data is List ? data : (data?['sessions'] as List? ?? []);
    return raw
        .where(
          (x) =>
              search.isEmpty ||
              x.toString().toLowerCase().contains(search.toLowerCase()),
        )
        .toList();
  }

  Widget records() {
    final rows = filteredRows;
    if (page == 'Sessions') return sessionCards(rows);
    if (rows.isEmpty) {
      return const Panel(child: EmptyState('No records found on this page.'));
    }
    if (page == 'Students') {
      return Panel(
        child: horizontalTable(
          ['Student ID', 'Display name', 'Status', if (isAdmin) 'Actions'],
          [
            for (final r in rows)
              DataRow(
                cells: [
                  DataCell(Text(r['student_code'])),
                  DataCell(Text(r['display_name'])),
                  DataCell(
                    StatusPill(r['active'] == 1 ? 'active' : 'inactive'),
                  ),
                  if (isAdmin)
                    DataCell(
                      IconButton(
                        tooltip: 'Edit ${r['student_code']}',
                        onPressed: () =>
                            studentForm(Map<String, dynamic>.from(r)),
                        icon: const Icon(Icons.edit_outlined, size: 18),
                      ),
                    ),
                ],
              ),
          ],
        ),
      );
    }
    if (page == 'Classes') {
      return Column(
        children: [
          for (final r in rows)
            Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Panel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      r['code'],
                      style: const TextStyle(
                        color: teal,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      r['title'],
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '${r['teacher_name']} · ${r['roster_count']} students',
                    ),
                    if (isAdmin)
                      Wrap(
                        spacing: 8,
                        children: [
                          TextButton.icon(
                            onPressed: () =>
                                classForm(Map<String, dynamic>.from(r)),
                            icon: const Icon(Icons.edit_outlined, size: 16),
                            label: const Text('Edit assignment'),
                          ),
                          TextButton.icon(
                            onPressed: () =>
                                rosterForm(Map<String, dynamic>.from(r)),
                            icon: const Icon(Icons.people_outline, size: 16),
                            label: const Text('Manage roster'),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
        ],
      );
    }
    if (page == 'Reports') {
      return Panel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Attendance summary',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            const Text(
              'Totals apply to this page. Draft sessions are identified separately.',
              style: TextStyle(color: Color(0xFF657680), fontSize: 12),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 14,
              runSpacing: 8,
              children: [
                for (final s in ['present', 'late', 'absent', 'excused'])
                  Chip(label: Text('${titleCase(s)}: ${data['totals'][s]}')),
              ],
            ),
            horizontalTable(
              [
                'Class / session',
                'Date · Manila',
                'State',
                'Present',
                'Late',
                'Absent',
                'Excused',
                'Pending',
              ],
              [
                for (final r in rows)
                  DataRow(
                    cells: [
                      DataCell(Text('${r['class_code']} / ${r['title']}')),
                      DataCell(Text(manila(r['starts_at']))),
                      DataCell(
                        StatusPill(
                          r['finalized_at'] == null ? 'draft' : 'finalized',
                        ),
                      ),
                      for (final s in ['present', 'late', 'absent', 'excused'])
                        DataCell(Text('${r['counts'][s] ?? 0}')),
                      DataCell(Text('${r['pending_count']}')),
                    ],
                  ),
              ],
            ),
          ],
        ),
      );
    }
    if (page == 'Alerts') {
      return Column(
        children: [
          for (final r in rows)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Panel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 12,
                      runSpacing: 8,
                      children: [
                        StatusPill(r['status']),
                        Text(
                          titleCase(r['kind']),
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(r['message']),
                    const SizedBox(height: 8),
                    Text(
                      '${r['recipient']} · ${r['attempts']} attempts · ${manila(r['updated_at'])}',
                      style: const TextStyle(
                        color: Color(0xFF657680),
                        fontSize: 12,
                      ),
                    ),
                    if (r['status'] == 'action_required' && !readOnly)
                      TextButton.icon(
                        onPressed: () async {
                          if (!await confirm(
                            context,
                            'Request recovery?',
                            'Confirm the underlying delivery issue has been reviewed. A separate bounded delivery will be queued.',
                          )) {
                            return;
                          }
                          try {
                            await widget.api.request(
                              'POST',
                              '/alerts/${r['id']}/retry',
                            );
                            await load();
                          } on ApiError catch (e) {
                            message(e.message);
                          }
                        },
                        icon: const Icon(Icons.refresh),
                        label: const Text('Queue recovery'),
                      ),
                  ],
                ),
              ),
            ),
        ],
      );
    }
    if (page == 'Audit history') {
      return Panel(
        child: horizontalTable(
          ['Time · Manila', 'Actor', 'Action', 'Target', 'Details'],
          [
            for (final r in rows)
              DataRow(
                cells: [
                  DataCell(Text(manila(r['created_at']))),
                  DataCell(Text(r['actor'] ?? 'Worker')),
                  DataCell(Text(titleCase(r['action']))),
                  DataCell(Text(r['target'])),
                  DataCell(
                    SizedBox(
                      width: 240,
                      child: Text(
                        r['detail'],
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
          ],
        ),
      );
    }
    return Panel(
      child: horizontalTable(
        ['Username', 'Name', 'Role', 'Status', 'Actions'],
        [
          for (final r in rows)
            DataRow(
              cells: [
                DataCell(Text(r['username'])),
                DataCell(Text(r['display_name'])),
                DataCell(StatusPill(r['role'])),
                DataCell(Text(r['active'] == 1 ? 'Active' : 'Inactive')),
                DataCell(
                  Row(
                    children: [
                      IconButton(
                        tooltip: 'Edit account',
                        onPressed: () =>
                            accountForm(Map<String, dynamic>.from(r)),
                        icon: const Icon(Icons.edit_outlined, size: 18),
                      ),
                      IconButton(
                        tooltip: 'Reset password',
                        onPressed: () => form(
                          'Reset account password',
                          [
                            const FieldSpec(
                              'password',
                              'New password',
                              password: true,
                              maxLength: 128,
                            ),
                          ],
                          'POST',
                          '/users/${r['id']}/password',
                        ),
                        icon: const Icon(Icons.lock_reset, size: 18),
                      ),
                    ],
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget? addButton() {
    if (!isAdmin || selected != null) return null;
    final action = switch (page) {
      'Students' => () => studentForm(),
      'Classes' => () => classForm(),
      'Sessions' => sessionForm,
      'Accounts' => () => accountForm(),
      _ => null,
    };
    if (action == null) return null;
    return FilledButton.icon(
      onPressed: action,
      icon: const Icon(Icons.add, size: 18),
      label: Text(switch (page) {
        'Students' => 'Add student',
        'Classes' => 'Add class',
        'Accounts' => 'Create account',
        _ => 'Schedule session',
      }),
    );
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, bounds) {
      final wide = bounds.maxWidth >= 1050;
      final add = addButton();
      return Scaffold(
        key: scaffold,
        drawer: wide ? null : Drawer(child: sidebar()),
        body: Row(
          children: [
            if (wide) SizedBox(width: 236, child: sidebar()),
            Expanded(
              child: Column(
                children: [
                  Container(
                    height: 72,
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      border: Border(
                        bottom: BorderSide(color: Color(0xFFE0E7EA)),
                      ),
                    ),
                    child: Row(
                      children: [
                        if (!wide)
                          IconButton(
                            tooltip: 'Open navigation',
                            onPressed: () =>
                                scaffold.currentState!.openDrawer(),
                            icon: const Icon(Icons.menu),
                          ),
                        const Expanded(
                          child: Text(
                            'Attendance Monitoring System',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: ink,
                              fontSize: 14,
                            ),
                          ),
                        ),
                        StatusPill(widget.user['role']),
                      ],
                    ),
                  ),
                  if (loading)
                    const LinearProgressIndicator(
                      minHeight: 2,
                      semanticsLabel: 'Loading records',
                    ),
                  Expanded(
                    child: RefreshIndicator(
                      onRefresh: () async {
                        if (await canLeave()) await load();
                      },
                      child: ListView(
                        padding: EdgeInsets.all(
                          bounds.maxWidth < 600 ? 18 : 32,
                        ),
                        children: [
                          if (selected != null)
                            Align(
                              alignment: Alignment.centerLeft,
                              child: TextButton.icon(
                                onPressed: () => navigate('Sessions'),
                                icon: const Icon(Icons.arrow_back, size: 18),
                                label: const Text('All sessions'),
                              ),
                            ),
                          Wrap(
                            alignment: WrapAlignment.spaceBetween,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            spacing: 20,
                            runSpacing: 16,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    selected == null
                                        ? page == 'Overview'
                                              ? 'Your attendance overview'
                                              : page
                                        : data?['title'] ??
                                              'Attendance session',
                                    style: Theme.of(context)
                                        .textTheme
                                        .headlineLarge,
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    selected != null
                                        ? 'Review attendance and keep a reliable record.'
                                        : page == 'Overview'
                                        ? 'Welcome, ${widget.user['display_name']}. Here is where things stand.'
                                        : 'Manage and review your ${page.toLowerCase()}.',
                                    style: const TextStyle(
                                      color: Color(0xFF657680),
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                              ?add,
                            ],
                          ),
                          const SizedBox(height: 24),
                          if (error != null)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 20),
                              child: Panel(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Semantics(
                                      liveRegion: true,
                                      child: Text(
                                        error!,
                                        style: const TextStyle(
                                          color: Color(0xFFB3261E),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 12),
                                    Wrap(
                                      spacing: 12,
                                      children: [
                                        OutlinedButton(
                                          onPressed: load,
                                          child: const Text('Retry'),
                                        ),
                                        TextButton(
                                          onPressed: widget.onSignedOut,
                                          child: const Text(
                                            'Return to sign in',
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          if (data == null && loading)
                            const Padding(
                              padding: EdgeInsets.all(60),
                              child: Center(child: CircularProgressIndicator()),
                            ),
                          if (data != null && selected != null)
                            AttendanceEditor(
                              key: editor,
                              api: widget.api,
                              session: Map<String, dynamic>.from(data),
                              readOnly: readOnly,
                              onChanged: load,
                            ),
                          if (data != null &&
                              selected == null &&
                              page == 'Overview')
                            overview(),
                          if (data != null &&
                              selected == null &&
                              page != 'Overview') ...[
                            TextField(
                              controller: searchController,
                              onChanged: (v) => setState(() => search = v),
                              decoration: const InputDecoration(
                                hintText: 'Search this page',
                                prefixIcon: Icon(Icons.search),
                                isDense: true,
                              ),
                            ),
                            const SizedBox(height: 18),
                            records(),
                            const SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                Text(
                                  'Page ${offset ~/ 20 + 1}',
                                  style: const TextStyle(
                                    color: Color(0xFF657680),
                                    fontSize: 12,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                IconButton(
                                  tooltip: 'Previous page',
                                  onPressed: offset == 0
                                      ? null
                                      : () {
                                          offset -= 20;
                                          load();
                                        },
                                  icon: const Icon(Icons.chevron_left),
                                ),
                                IconButton(
                                  tooltip: 'Next page',
                                  onPressed:
                                      (data is List
                                              ? (data as List).length
                                              : (data['sessions'] as List)
                                                    .length) <
                                          20
                                      ? null
                                      : () {
                                          offset += 20;
                                          load();
                                        },
                                  icon: const Icon(Icons.chevron_right),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );
}
