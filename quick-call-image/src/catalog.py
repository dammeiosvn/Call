"""Reproducible, offline catalog compiler. Python standard library only."""
from pathlib import Path
import hashlib
import gzip
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REVISION = '8593ab70fa4fadffc042b2714034f4c52bef7daf'
VERSION = '1.0.0-beta.2'
REGIONS = [
    ('VN', 'Việt Nam', 'vi'), ('TH', 'ไทย', 'th'), ('SG', 'Singapore', 'en'),
    ('MY', 'Malaysia', 'ms'), ('ID', 'Indonesia', 'id'), ('PH', 'Philippines', 'en'),
    ('KH', 'កម្ពុជា', 'km'), ('LA', 'ລາວ', 'lo'), ('CN', '中国', 'zh-Hans'),
    ('TW', '台灣', 'zh-Hant'), ('HK', '香港', 'zh-Hant'), ('JP', '日本', 'ja'),
    ('KR', '대한민국', 'ko'), ('IN', 'India', 'en'), ('AU', 'Australia', 'en'),
    ('US', 'United States', 'en'), ('CA', 'Canada', 'en'), ('GB', 'United Kingdom', 'en'),
    ('DE', 'Deutschland', 'de'), ('FR', 'France', 'fr'),
]


def flag(region):
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in region)


def lengths(spec):
    result = []
    for item in spec.split(','):
        if item.startswith('['):
            lo, hi = map(int, item[1:-1].split('-'))
            result.extend(range(lo, hi + 1))
        else:
            result.append(int(item))
    return sorted(set(result))


def compact_pattern(element, name):
    value = ''.join(element.findtext(name, '').split())
    return value.replace(r'\d', '[0-9]')


def compile_catalog():
    raw = gzip.decompress((ROOT / 'vendor/PhoneNumberMetadata.xml.gz').read_bytes())
    territories = {t.attrib['id']: t for t in ET.fromstring(raw).find('territories')}
    countries = {}
    for region, name, language in REGIONS:
        t = territories[region]
        mobile = t.find('mobile')
        nsn_lengths = lengths(mobile.find('possibleLengths').attrib['national'])
        length_regex = '(?:' + '|'.join('[0-9]{%d}' % n for n in nsn_lengths) + ')'
        general = compact_pattern(t, 'generalDesc/nationalNumberPattern')
        pattern = compact_pattern(mobile, 'nationalNumberPattern')
        # Full-string intersection: allowed lengths AND general numbering plan AND mobile range.
        # Shared fixed/mobile ranges in US/CA are intentionally accepted; no carrier guessing.
        countries[region] = {
            'regionCode': region, 'name': name, 'icon': flag(region),
            'callingCode': '+' + t.attrib['countryCode'], 'defaultLanguage': language,
            'nationalPrefix': t.attrib.get('nationalPrefix', ''),
            # Some plans normally print mobile numbers without a trunk prefix.
            # Elsewhere require the national prefix; don't guess a missing zero.
            'acceptBareNSN': '1' if region in ('SG', 'HK', 'CN', 'IN', 'US', 'CA') else '0',
            'internationalPrefixPattern': r'\A(?:' + t.attrib['internationalPrefix'] + r')(?=[1-9][0-9]{6,}\z)',
            'nationalPattern': r'\A(?=' + length_regex + r'\z)(?=(?:' + general + r')\z)(?:' + pattern + r')\z',
            'possibleLengths': nsn_lengths,
            'numberType': 'FIXED_LINE_OR_MOBILE' if region in ('US', 'CA') else 'MOBILE',
            'exampleNSN': mobile.findtext('exampleNumber'),
            'rulesRevision': 'libphonenumber-9.0.42',
        }
    unicode_digits = {}
    for start in (0xFF10, 0x0E50, 0x17E0, 0x0ED0, 0x0966, 0x0660, 0x06F0):
        unicode_digits.update({chr(start + n): str(n) for n in range(10)})
    icons = dict(camera='📸', photos='🖼️', settings='⚙️', about='ℹ️', cancel='⏹️',
                 manual='✏️', retry='🔄', country='🌍', language='🌐', restore='♻️', call='📞')

    def items(*ids):
        return [{'id': x, 'labelKey': x, 'iconKey': x, 'handler': x, 'enabled': '1'} for x in ids]

    return {
        'meta': {'schemaVersion': '1', 'engineRevision': '1', 'configVersion': VERSION,
                 'metadataRevision': REVISION, 'metadataSHA256': hashlib.sha256(raw).hexdigest(),
                 'metadataSource': 'https://github.com/google/libphonenumber/tree/' + REVISION,
                 'license': 'Apache-2.0'},
        'defaults': {'region': 'VN', 'language': 'vi', 'singleResult': 'call'},
        'countryOrder': [x[0] for x in REGIONS],
        'languageOrder': ['vi', 'en', 'th', 'ms', 'id', 'km', 'lo', 'zh-Hans', 'zh-Hant', 'ja', 'ko', 'de', 'fr'],
        'countries': countries,
        'languages': json.loads((ROOT / 'config/languages.json').read_text(encoding='utf-8')),
        'icons': icons,
        'menus': {'main': items('camera', 'photos', 'settings', 'about', 'cancel'),
                  'recovery': items('camera', 'photos', 'manual', 'cancel'),
                  'results': items('manual', 'retry', 'cancel'),
                  'settings': items('country', 'language', 'restore', 'cancel')},
        'behavior': {'maxInteractions': 20, 'maxTextCharacters': 120000,
                     'e164Pattern': r'\A\+[1-9][0-9]{6,14}\z',
                     'unicodeDigitPattern': '[０-９๐-๙០-៩໐-໙०-९٠-٩۰-۹]',
                     'candidatePattern': r'(?<![\p{L}\p{N}+])\+?[0-9](?:[ \u00A0\u202F().‐‑‒–—-]*[0-9]){6,}(?![\p{L}\p{N}])',
                     'ignorePrefixPattern': r'(?i)(?:\b(?:MST|tax\s*(?:id|code|number)|VAT\s*(?:id|no|number)|order\s*(?:id|no\.?|number)|invoice\s*(?:id|no\.?|number)|account\s*(?:no\.?|number)|IBAN|total|subtotal|amount|quantity|NPWP|jumlah)\b|mã\s*(?:số\s*thuế|đơn|vận\s*đơn)|tổng\s*(?:cộng|tiền)|số\s*tài\s*khoản|订单号|訂單號|税号|稅號|合计|合計|注文番号|請求書番号|주문번호|사업자등록번호|총액|ยอดรวม|เลขที่ใบเสร็จ|[$€£¥₫₹₩฿])\s*[:：#=]?\s*\z',
                     'currencySuffixPattern': r'(?i)\A\s*(?:[$€£¥₫₹₩฿]|VND\b|USD\b|EUR\b|GBP\b|JPY\b|CNY\b|KRW\b|THB\b|INR\b|đồng\b)',
                     'bootstrapCountryPrompt': '🌍 Bạn chọn quốc gia/vùng nào? / Choose your country or region',
                     'bootstrapLanguagePrompt': '🌐 Bạn muốn dùng ngôn ngữ nào? / Choose your language'},
        'digitMap': unicode_digits,
    }


def main():
    target = ROOT / 'config/catalog.json'
    data = compile_catalog()
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'countries': len(data['countries']), 'languages': len(data['languages']),
                      'configBytes': target.stat().st_size, 'metadataRevision': REVISION}))


if __name__ == '__main__':
    main()
