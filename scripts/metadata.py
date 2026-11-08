"""Secret-free execution metadata and source fingerprints."""
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.app.config import ROOT


def metadata(command, dataset='fictional demo data'):
    source = {}
    for folder in ['backend', 'frontend/lib', 'frontend/test', 'scripts', 'deployment']:
        for path in sorted((ROOT / folder).rglob('*')):
            if path.is_file() and path.suffix in ('.py', '.dart', '.sql', '.ps1', '.json', '.toml') and '__pycache__' not in str(path):
                source[str(path.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    digest = hashlib.sha256(str(source).encode()).hexdigest()
    return {'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'display_timezone': 'Asia/Manila',
            'platform': platform.platform(), 'python': platform.python_version(),
            'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'source_sha256': digest, 'source_files': source, 'command': command, 'dataset': dataset}


def write_json(relative, data):
    import json
    path = ROOT / Path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')
