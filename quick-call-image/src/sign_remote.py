"""Optional build-time signing through Shortcuty's documented public API.

Only the public workflow source is uploaded; no user's photos/settings are read.
This module is NOT embedded in, or called by, the generated iOS shortcut.
API documentation: https://github.com/Shortcuty/Signing-Server-API-Documentation
"""
from pathlib import Path
import base64
import hashlib
import json
import plistlib
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://sign.shortcuty.app/api/v1/sign?response=json'


def sign(stem, name):
    destination = ROOT / 'dist' / (name + '.shortcut')
    destination.unlink(missing_ok=True)
    source = ROOT / 'dist' / (stem + '.unsigned.bplist')
    raw = source.read_bytes()
    xml = ROOT / 'dist' / (stem + '.unsigned.shortcut')
    assert plistlib.loads(raw) == plistlib.loads(xml.read_bytes()), 'Signing input differs from inspected source'
    boundary = 'QuickCall-' + uuid.uuid4().hex
    header = ('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="' + name
              + '.shortcut"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
    body = header + raw + ('\r\n--' + boundary + '--\r\n').encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers={
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'User-Agent': 'QuickCallImage-Build/1.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.load(response)
    if result.get('success') is not True:
        raise RuntimeError(str(result.get('error', 'Signing failed')))
    file = result['file']
    content = base64.b64decode(file['content_base64'], validate=True)
    actual_input = hashlib.sha256(raw).hexdigest()
    actual_signed = hashlib.sha256(content).hexdigest()
    if file['input_sha256'] != actual_input or file['signed_sha256'] != actual_signed:
        raise RuntimeError('Signing response hash mismatch')
    if file['format'] != 'AEA1' or file.get('signing_mode') != 'anyone' or not content.startswith(b'AEA1'):
        raise RuntimeError('Invalid signing envelope or sharing mode')
    if len(content) != file['size']:
        raise RuntimeError('Signing response length mismatch')
    destination.write_bytes(content)
    return {'name': name, 'signed': True, 'format': 'AEA1', 'mode': 'anyone',
            'inputFile': source.name, 'inputSHA256': actual_input, 'sha256': actual_signed,
            'size': len(content), 'path': destination.name}


def main():
    report = {'provider': 'Shortcuty public signing API', 'endpoint': ENDPOINT,
              'mode': 'anyone', 'signed': False, 'iPhoneImportVerified': False, 'files': []}
    for stem, name in [('Quick-Call-Image', 'Quick Call Image'), ('Quick-Call-Image-Test', 'Quick Call Image Test')]:
        try:
            item = sign(stem, name)
        except Exception as error:
            item = {'name': name, 'signed': False, 'error': str(error)[:600]}
        report['files'].append(item)
        print(json.dumps(item))
        (ROOT / 'qa/signing.json').write_text(json.dumps(report, indent=2) + '\n')
    report['signed'] = all(x['signed'] for x in report['files'])
    (ROOT / 'qa/signing.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['signed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
