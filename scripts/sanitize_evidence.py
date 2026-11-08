"""Redact ephemeral test credentials from preserved failure output, not test outcomes."""
import re
from pathlib import Path

from backend.app.config import ROOT


def text(path: Path):
    raw = path.read_bytes()
    return raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')


def main():
    changed = []
    for path in (ROOT / 'evidence').rglob('*'):
        if path.suffix not in ('.log', '.xml', '.json', '.txt'): continue
        content = re.sub(r'\r+\n', '\n', text(path)).replace('\r', '\n')
        redacted = re.sub(r"(['\"]password['\"]\s*:\s*)['\"][^'\"\r\n]*['\"]", r"\1'[REDACTED TEST CREDENTIAL]'", content)
        if redacted != content: changed.append(str(path.relative_to(ROOT)))
        redacted = '\n'.join(line.rstrip() for line in redacted.split('\n')).rstrip('\n')+'\n'
        path.write_text(redacted, encoding='utf-8', newline='\n')
    print('Redacted credential values from: '+', '.join(changed))


if __name__ == '__main__': main()
