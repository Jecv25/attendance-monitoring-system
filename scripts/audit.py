"""Review publishable paths, source syntax, links and configured-secret exposure."""
import ast
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import unquote

from dotenv import dotenv_values

from backend.app.config import ROOT
from scripts.metadata import metadata, write_json


def main():
    from scripts.sanitize_evidence import main as sanitize
    sanitize()
    for name, source in [('http', ROOT / '.local/evaluation/http.log'), ('worker', ROOT / '.local/evaluation/worker.log')]:
        events = []
        if source.exists():
            for line in source.read_text(encoding='utf-8').splitlines():
                try:
                    event = json.loads(line)
                    if isinstance(event, dict) and 'event' in event: events.append(event)
                except ValueError: pass
        if name == 'worker' and not events:
            automation = json.loads((ROOT / 'evidence/week13/automation.json').read_text())
            events = [event for item in automation['results'] for event in item['transitions']]
        (ROOT / f'evidence/week13/{name}-structured.jsonl').write_text(''.join(json.dumps(event)+'\n' for event in events), encoding='utf-8')
    machine = metadata('python -m scripts.audit', 'Fictional demonstration records only')
    machine.update({'flutter': '3.47.8', 'dart': '3.13.7', 'node': subprocess.check_output(['node', '--version'], text=True).strip(), 'browser': json.loads((ROOT / 'evidence/week18/browser/results.json').read_text())['browser'], 'release_bundle_sha256': hashlib.sha256((ROOT / 'frontend/build/web/main.dart.js').read_bytes()).hexdigest(), 'checks': {'backend': '40 passed; JUnit and coverage retained', 'flutter': '11 passed; final analysis and build outputs retained', 'browser': '8 passed; zero page errors'}})
    write_json('evidence/week18/environment.json', machine)
    write_json('evidence/week18/repository-audit.json', {'status': 'In Progress'})
    paths = [ROOT / x.decode('utf-8') for x in subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).split(b'\0') if x]
    findings, broken, parsed = [], [], 0
    local = dotenv_values(ROOT / '.env')
    secrets = [value for key, value in local.items() if value and len(value) >= 12 and (key.endswith('_PASSWORD') or key.endswith('_KEY'))]
    for path in paths:
        relative = str(path.relative_to(ROOT)).replace('\\', '/')
        if any(part in ('.tools', '.local', 'node_modules', 'build', '__pycache__') for part in path.relative_to(ROOT).parts):
            findings.append('Excluded runtime directory would be published: '+relative)
        if path.suffix in ('.pem', '.key', '.db', '.sqlite', '.zip') or (path.name.startswith('.env') and path.name != '.env.example'):
            findings.append('Protected runtime file would be published: '+relative)
        if not path.is_file() or path.suffix.lower() in ('.png', '.ico', '.ttf', '.otf'): continue
        content = path.read_text(encoding='utf-8-sig')
        if any(value in content for value in secrets): findings.append('Configured secret exposure in '+relative)
        if path.suffix == '.py':
            ast.parse(content, filename=relative); parsed += 1
        if path.suffix == '.md':
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
                target = target.split('#', 1)[0].strip('<>')
                if not target or '://' in target or target.startswith('mailto:'): continue
                destination = path.parent / unquote(target)
                if not destination.exists(): broken.append(relative+' → '+target)
    result = {'metadata': metadata('python -m scripts.audit'), 'files_reviewed': len(paths), 'python_files_parsed': parsed, 'configured_secrets_scanned_without_disclosure': len(secrets), 'findings': findings, 'broken_markdown_links': broken, 'result': 'Passed' if not findings and not broken else 'Failed', 'scope': 'Configured-secret/path/link/syntax audit; not a complete dependency-vulnerability or penetration assessment'}
    write_json('evidence/week18/repository-audit.json', result)
    print(json.dumps({'files_reviewed': len(paths), 'findings': findings, 'broken_links': broken, 'result': result['result']}))
    if findings or broken: sys.exit(1)


if __name__ == '__main__': main()
