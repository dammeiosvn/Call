"""Sign generated workflows using Apple's documented macOS CLI.

Requires a Mac with working Shortcuts/iCloud signing access. Never accepts an
unsigned file as an installable output. No third-party signing credentials.
"""
from pathlib import Path
import hashlib
import json
import platform
import plistlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = {'mode': 'anyone', 'platform': platform.platform(), 'files': [],
              'signed': False, 'iPhoneImportVerified': False}
    if platform.system() != 'Darwin' or not shutil.which('shortcuts'):
        report['error'] = 'Apple shortcuts CLI on macOS is required.'
    else:
        for stem, name in [('Quick-Call-Image', 'Quick Call Image'), ('Quick-Call-Image-Test', 'Quick Call Image Test')]:
            xml = ROOT / 'dist' / (stem + '.unsigned.shortcut')
            dest = ROOT / 'dist' / (name + '.shortcut')
            dest.unlink(missing_ok=True)
            item = {'name': name, 'inputSHA256': hashlib.sha256(xml.read_bytes()).hexdigest(), 'attempts': []}
            for binary in (False, True):
                source = xml
                if binary:
                    source = ROOT / 'dist' / (stem + '.binary-input.shortcut')
                    source.write_bytes(plistlib.dumps(plistlib.loads(xml.read_bytes()), fmt=plistlib.FMT_BINARY))
                try:
                    completed = subprocess.run(['shortcuts', 'sign', '--mode', 'anyone', '--input', str(source), '--output', str(dest)],
                                               capture_output=True, text=True, timeout=40)
                    item['attempts'].append({'binary': binary, 'returnCode': completed.returncode,
                        'output': (completed.stdout + completed.stderr)[-1600:]})
                except subprocess.TimeoutExpired:
                    item['attempts'].append({'binary': binary, 'error': 'Signing exceeded 40 seconds; an iCloud session may be required.'})
                if dest.exists() and dest.read_bytes().startswith(b'AEA1'):
                    item['signed'] = True
                    item['size'] = dest.stat().st_size
                    item['sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
                    break
                dest.unlink(missing_ok=True)
            item.setdefault('signed', False)
            report['files'].append(item)
        report['signed'] = bool(report['files']) and all(x['signed'] for x in report['files'])
    (ROOT / 'qa/signing.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['signed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
