"""Behavioral tests of the serialized shipping graph with ICU and simulated I/O."""
from pathlib import Path
import copy
import hashlib
import json
import plistlib
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from catalog import compile_catalog
from build import build
from interpreter import run, File
from icu import Pattern, matches

CAT = json.loads((ROOT / 'config/catalog.json').read_text(encoding='utf-8'))
NORMAL = plistlib.loads((ROOT / 'dist/Quick-Call-Image.unsigned.shortcut').read_bytes())
TEST = plistlib.loads((ROOT / 'dist/Quick-Call-Image-Test.unsigned.shortcut').read_bytes())
CASES = []


def disk(region='VN', language='vi', catalog=None, single='call'):
    settings = {'schemaVersion': '1', 'region': region, 'language': language, 'singleResult': single}
    return {'QuickCall/catalog.json': File('catalog.json', json.dumps(catalog or CAT, ensure_ascii=False)),
            'QuickCall/settings.json': File('settings.json', json.dumps(settings))}


def image(body):
    return File('synthetic.jpg', kind='image', ocr=body)


def scenario(name, body, expected, region='VN', **kwargs):
    state = run(NORMAL, incoming=image(body), disk=disk(region, 'en'), menus=['cancel'], **kwargs)
    CASES.append({'id': name, 'region': region, 'input': body, 'expected': expected,
                  'actual': state['destinations'], 'passed': state['destinations'] == expected})
    return state


class NativeWorkflowTests(unittest.TestCase):
    def test_native_condition_storage_and_explicit_dictionary_walks(self):
        for workflow in (NORMAL, TEST):
            for action in workflow['WFWorkflowActions']:
                kind = action['WFWorkflowActionIdentifier'].split('.')[-1]
                p = action['WFWorkflowActionParameters']
                if kind == 'conditional' and p.get('WFControlFlowMode') == 0:
                    if p['WFCondition'] == 2:
                        rhs = p['WFNumberValue']
                        self.assertTrue(isinstance(rhs, (int, float)) or rhs.get('WFSerializationType') == 'WFTextTokenAttachment')
                    elif p['WFCondition'] == 4:
                        rhs = p['WFConditionalActionString']
                        self.assertTrue(isinstance(rhs, str) or rhs['Value']['attachmentsByRange'])
                if kind == 'getvalueforkey' and 'WFDictionaryKey' in p:
                    key = p['WFDictionaryKey']
                    self.assertNotIn('.', key if isinstance(key, str) else key['Value']['string'])

    def test_incompatible_catalog_is_backed_up_and_recovers_without_resetting_settings(self):
        for key in ('schemaVersion', 'engineRevision'):
            cat = copy.deepcopy(CAT)
            cat['meta'][key] = 'unsupported'
            d = disk(catalog=cat)
            st = run(TEST, incoming=image('0912345678'), disk=d)
            self.assertEqual(st['menus'], [])
            self.assertEqual(st['alerts'], [])
            self.assertEqual(st['disk']['QuickCall/settings.json'], d['QuickCall/settings.json'])
            self.assertEqual(json.loads(st['disk']['QuickCall/catalog.previous.json'].body), cat)
            self.assertEqual(json.loads(st['disk']['QuickCall/catalog.json'].body), CAT)
            self.assertTrue(st['previews'][0].endswith('+84912345678'))

    def test_bundled_schema_failure_reports_origin_before_disk_or_ocr(self):
        workflow = copy.deepcopy(TEST)
        for action in workflow['WFWorkflowActions']:
            if action['WFWorkflowActionIdentifier'] == 'is.workflow.actions.dictionary':
                item = action['WFWorkflowActionParameters']['WFItems']['Value']['WFDictionaryFieldValueItems'][0]
                cat = copy.deepcopy(CAT)
                cat['meta']['schemaVersion'] = '9'
                item['WFValue']['Value']['string'] = json.dumps(cat)
                break
        st = run(workflow, incoming=image('0912345678'))
        self.assertIn('QC101-B', st['alerts'][0])
        self.assertIn('Actual: [9]', st['alerts'][0])
        self.assertEqual(st['writes'], [])
        self.assertEqual(st['ocrCalls'], 0)
        self.assertEqual(st['destinations'], [])

    def test_reproducible_source_and_payloads(self):
        self.assertEqual(CAT, compile_catalog())
        self.assertEqual(NORMAL, build(False))
        self.assertEqual(TEST, build(True))

    def test_all_20_regions_domestic_and_international(self):
        for region in CAT['countryOrder']:
            p = CAT['countries'][region]
            nsn, cc, trunk = p['exampleNSN'], p['callingCode'], p['nationalPrefix']
            expected = [cc + nsn]
            forms = {'national': trunk + nsn, 'bareNSN': nsn, 'international': cc + nsn,
                     'grouped': cc + ' ' + nsn[:3] + ' ' + nsn[3:],
                     'dots': trunk + nsn[:3] + '.' + nsn[3:6] + '.' + nsn[6:],
                     'duplicate': trunk + nsn + '\n' + cc + nsn,
                     'foreignRegion': cc + nsn}
            if trunk:
                forms['optionalTrunk'] = cc + ' (' + trunk + ') ' + nsn
            for variant, raw in forms.items():
                with self.subTest(region=region, variant=variant):
                    destination = [] if variant == 'bareNSN' and p['acceptBareNSN'] != '1' else expected
                    st = scenario(region + '/' + variant, 'Phone: ' + raw, destination,
                                  'VN' if variant == 'foreignRegion' else region)
                    self.assertEqual(st['destinations'], destination)
                    if destination:
                        self.assertEqual(st['menus'], [])

    def test_special_cases(self):
        cases = [
            ('vn-idd', '0084 912 345 678', ['+84912345678'], 'VN'),
            ('jp-idd', '01084 912 345 678', ['+84912345678'], 'JP'),
            ('us-idd', '01184 912 345 678', ['+84912345678'], 'US'),
            ('au-idd', '001184 912 345 678', ['+84912345678'], 'AU'),
            ('sg-idd', '00184 912 345 678', ['+84912345678'], 'SG'),
            ('thai-digits', '๐๙๑๒๓๔๕๖๗๘', ['+84912345678'], 'VN'),
            ('khmer-digits', '០៩១២៣៤៥៦៧៨', ['+84912345678'], 'VN'),
            ('lao-digits', '໐໙໑໒໓໔໕໖໗໘', ['+84912345678'], 'VN'),
            ('fullwidth', '＋８４ ９１２ ３４５ ６７８', ['+84912345678'], 'VN'),
            ('tax-plus-phone', 'MST: 0312345678\nSĐT: 0912345678', ['+84912345678'], 'VN'),
            ('invoice-plus-phone', 'Order ID: 0912345678\nPhone: 0987654321', ['+84987654321'], 'VN'),
            ('tax-only', 'MST: 0312345678', [], 'VN'),
            ('currency-prefix', 'Total: 0912345678', [], 'VN'),
            ('currency-suffix', '0912345678 VND', [], 'VN'),
            ('too-short', '091234567', [], 'VN'),
            ('too-long', '09123456789', [], 'VN'),
            ('embedded-order', 'ABC0912345678XYZ', [], 'VN'),
            ('never-substring', '123450912345678990000', [], 'VN'),
            ('no-ocr-guess', 'O912345678', [], 'VN'),
            ('no-ocr-guess-middle', '09123I5678', [], 'VN'),
            ('masked', '0912***678', [], 'VN'),
            ('wrong-double-code', '+840912345678', [], 'VN'),
            ('no-global-00', '0084912345678', [], 'US'),
            ('unsupported-country', '+358401234567', [], 'VN'),
            ('emergency', '112\n113\n114\n115\n911', [], 'VN'),
            ('hotline', '18001090\n19001090', [], 'VN'),
            ('non-vn-explicit', '+819012345678', ['+819012345678'], 'VN'),
            ('us-valid', '+12015550123', ['+12015550123'], 'VN'),
            ('ca-valid', '+15062345678', ['+15062345678'], 'VN'),
            ('other-nanp', '+12425550123', [], 'VN'),
            ('local-seven-digit-nanp', '5550123', [], 'US'),
        ]
        for name, body, expected, region in cases:
            with self.subTest(case=name):
                self.assertEqual(scenario(name, body, expected, region)['destinations'], expected)

    def test_multiple_result_selection_and_editing(self):
        body = 'Người nhận: 0912.345.678\nCửa hàng: 0987 654 321'
        st = run(NORMAL, incoming=image(body), disk=disk(), menus=['+84987654321'])
        self.assertEqual(st['destinations'], ['+84987654321'])
        self.assertEqual(len(st['menus']), 1)
        self.assertTrue(st['menus'][0]['options'][0].startswith('📞 +84'))
        st = run(NORMAL, incoming=image(body), disk=disk(), menus=['manual'], answers=['0912345678'])
        self.assertEqual(st['destinations'], ['+84912345678'])
        self.assertEqual(st['ocrCalls'], 1)
        st = run(NORMAL, incoming=image(body), disk=disk(), menus=[None])
        self.assertEqual(st['destinations'], [])

    def test_unknown_international_never_silently_reduces_to_auto_one(self):
        st = run(NORMAL, incoming=image('0912345678\n+358401234567'), disk=disk(), menus=['cancel'])
        self.assertEqual(st['destinations'], [])
        self.assertEqual(len(st['menus']), 1)
        self.assertIn('quốc tế', st['menus'][0]['prompt'])

    def test_first_run_saves_settings_and_preserves_shared_image(self):
        st = run(NORMAL, incoming=image('0912345678'), menus=['VN', 'vi'])
        self.assertEqual(st['destinations'], ['+84912345678'])
        settings = json.loads(st['disk']['QuickCall/settings.json'].body)
        self.assertEqual(settings['region'], 'VN')
        self.assertEqual(settings['language'], 'vi')
        self.assertEqual(st['ocrCalls'], 1)
        self.assertEqual([len(m['options']) for m in st['menus']], [20, 13])
        st2 = run(NORMAL, incoming=image('0912345678'), disk=st['disk'])
        self.assertEqual(st2['menus'], [])
        self.assertEqual(st2['writes'], [])

    def test_first_run_cancel_and_io_failure_never_calls(self):
        st = run(NORMAL, incoming=image('0912345678'), menus=[None])
        self.assertEqual(st['destinations'], [])
        self.assertNotIn('QuickCall/settings.json', st['disk'])
        st = run(NORMAL, incoming=image('0912345678'), fail_save=True)
        self.assertEqual(st['status'], 'io-error')
        self.assertEqual(st['destinations'], [])

    def test_multiple_shared_images_only_selected_image_is_read(self):
        st = run(NORMAL, incoming=[image('0912345678'), image('0987654321')], disk=disk(), menus=[1])
        self.assertEqual(st['destinations'], ['+84987654321'])
        self.assertEqual(st['ocrCalls'], 1)

    def test_camera_photos_and_recovery(self):
        st = run(NORMAL, disk=disk(), menus=['camera'], camera=[image('0912345678')])
        self.assertEqual(st['destinations'], ['+84912345678'])
        st = run(NORMAL, disk=disk(), menus=['photos'], photos=[image('0912345678')])
        self.assertEqual(st['destinations'], ['+84912345678'])
        st = run(NORMAL, incoming=image('not a number'), disk=disk(), menus=['manual'], answers=['0912345678'])
        self.assertEqual(st['destinations'], ['+84912345678'])
        st = run(NORMAL, incoming=image('not a number'), disk=disk(), menus=['photos'], photos=[image('0912345678')])
        self.assertEqual(st['destinations'], ['+84912345678'])

    def test_menu_configuration_can_be_reordered_renamed_and_disabled(self):
        cat = copy.deepcopy(CAT)
        cat['menus']['main'].reverse()
        cat['languages']['vi']['photos'] = 'Ảnh. Phiên bản 1.2'
        cat['icons']['photos'] = '🧋'
        for item in cat['menus']['main']:
            if item['id'] == 'about':
                item['enabled'] = '0'
        st = run(NORMAL, disk=disk(catalog=cat), menus=['photos'], photos=[image('0912345678')])
        self.assertEqual(st['destinations'], ['+84912345678'])
        self.assertEqual(len(st['menus'][0]['options']), 4)
        self.assertTrue(any('🧋 Ảnh. Phiên bản 1.2' == x for x in st['menus'][0]['options']))

    def test_language_is_independent_and_settings_changes_persist(self):
        st = run(NORMAL, disk=disk(), menus=['settings', 'country', 'JP', 'vi', 'photos'], photos=[image('09012345678')])
        self.assertEqual(st['destinations'], ['+819012345678'])
        settings = json.loads(st['disk']['QuickCall/settings.json'].body)
        self.assertEqual((settings['region'], settings['language']), ('JP', 'vi'))
        self.assertIn('Bạn muốn lấy ảnh', st['menus'][-1]['prompt'])
        self.assertIn('QuickCall/settings.previous.json', st['disk'])

    def test_invalid_settings_restart_setup_without_guessing_country(self):
        for raw in ['not-json', '{"region":"VN"', '{"schemaVersion":"1","region":"ZZ","language":"vi","singleResult":"call"}',
                    '{"schemaVersion":"1","region":"VN","language":"unknown","singleResult":"call"}',
                    '{"schemaVersion":"9","region":"VN","language":"vi","singleResult":"call"}']:
            with self.subTest(raw=raw):
                d = disk()
                d['QuickCall/settings.json'] = File('settings.json', raw)
                st = run(NORMAL, disk=d, incoming=image('09012345678'), menus=['JP', 'vi'])
                self.assertEqual(st['destinations'], ['+819012345678'])

    def test_single_result_choose_preference(self):
        st = run(NORMAL, incoming=image('0912345678'), disk=disk(single='choose'), menus=['cancel'])
        self.assertEqual(st['destinations'], [])
        self.assertEqual(len(st['menus']), 1)

    def test_single_result_default_is_data_driven(self):
        cat = copy.deepcopy(CAT)
        cat['defaults']['singleResult'] = 'choose'
        d = {'QuickCall/catalog.json': File('catalog.json', json.dumps(cat, ensure_ascii=False))}
        st = run(NORMAL, incoming=image('0912345678'), disk=d, menus=['VN', 'vi', 'cancel'])
        self.assertEqual(st['destinations'], [])
        self.assertEqual(json.loads(st['disk']['QuickCall/settings.json'].body)['singleResult'], 'choose')

    def test_test_variant_never_contains_or_executes_call(self):
        self.assertNotIn('com.apple.mobilephone.call', [a['WFWorkflowActionIdentifier'] for a in TEST['WFWorkflowActions']])
        for region in CAT['countryOrder']:
            p = CAT['countries'][region]
            target = p['callingCode'] + p['exampleNSN']
            st = run(TEST, incoming=image(target), disk=disk(region, 'en'))
            self.assertEqual(st['destinations'], [])
            self.assertTrue(st['previews'][0].endswith(target))

    def test_all_languages_have_complete_labels_and_no_personal_addressing(self):
        keys = set(CAT['languages']['en'])
        self.assertEqual(len(CAT['countries']), 20)
        self.assertEqual(len(CAT['languages']), 13)
        for lang, strings in CAT['languages'].items():
            self.assertEqual(set(strings), keys, lang)
            for value in strings.values():
                self.assertTrue(value.strip())
                self.assertNotIn('Sếp', value)
                self.assertNotIn('Sếp Sen', value)
            for group, items in CAT['menus'].items():
                labels = [strings[i['labelKey']] for i in items]
                self.assertEqual(len(labels), len(set(labels)), (lang, group))

    def test_plist_integrity_and_no_network_or_web_runtime(self):
        forbidden = ['downloadurl', 'openurl', 'showwebpage', 'runjavascript', 'sendmessage', 'sendemail', 'getclipboard']
        for workflow in [NORMAL, TEST]:
            identifiers = [a['WFWorkflowActionIdentifier'] for a in workflow['WFWorkflowActions']]
            for kind in forbidden:
                self.assertFalse(any(kind in x for x in identifiers))
            uuids = [a['WFWorkflowActionParameters']['UUID'] for a in workflow['WFWorkflowActions']]
            self.assertEqual(len(uuids), len(set(uuids)))
            seen = set()
            def check(value):
                if isinstance(value, dict):
                    if value.get('Type') == 'ActionOutput':
                        self.assertIn(value['OutputUUID'], seen)
                    if value.get('WFSerializationType') == 'WFTextTokenString':
                        encoded = value['Value']['string'].encode('utf-16-le')
                        for span in value['Value']['attachmentsByRange']:
                            lo, n = map(int, span.strip('{}').split(','))
                            self.assertEqual(encoded[2 * lo:2 * (lo + n)].decode('utf-16-le'), '\ufffc')
                    for item in value.values():
                        check(item)
                elif isinstance(value, list):
                    for item in value:
                        check(item)
            for action in workflow['WFWorkflowActions']:
                check(action['WFWorkflowActionParameters'])
                seen.add(action['WFWorkflowActionParameters']['UUID'])

    def test_regex_metadata_and_randomized_oracle(self):
        try:
            import phonenumbers as pn
        except ImportError:
            self.skipTest('Optional independent oracle: install phonenumbers==9.0.42')
        self.assertEqual(pn.__version__, '9.0.42')
        rng = random.Random(84)
        comparisons = 0
        for region, profile in CAT['countries'].items():
            pattern = Pattern(profile['nationalPattern'])
            pool = [profile['exampleNSN']]
            for _ in range(80):
                size = rng.choice(profile['possibleLengths'])
                pool.append(''.join(str(rng.randrange(10)) for _ in range(size)))
            for nsn in pool:
                number = pn.parse(profile['callingCode'] + nsn, None)
                # parse() can silently strip a trunk prefix even after +CC. Our
                # validator deliberately requires an already-canonical NSN.
                canonical = pn.format_number(number, pn.PhoneNumberFormat.E164) == profile['callingCode'] + nsn
                oracle = canonical and pn.is_valid_number_for_region(number, region) and pn.number_type(number) in (pn.PhoneNumberType.MOBILE, pn.PhoneNumberType.FIXED_LINE_OR_MOBILE)
                self.assertEqual(bool(pattern.matches(nsn)), oracle, (region, nsn))
                comparisons += 1
        (ROOT / 'qa/oracle.json').write_text(json.dumps({'library': pn.__version__, 'comparisons': comparisons, 'passed': True}) + '\n')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeWorkflowTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'testMethods': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'numberScenarios': len(CASES),
              'passedNumberScenarios': sum(c['passed'] for c in CASES), 'cases': CASES,
              'scope': 'Serialized plist interpreter with simulated camera/photos/files/phone; host ICU regex. Not an iPhone runtime or OCR test.'}
    (ROOT / 'qa/test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
