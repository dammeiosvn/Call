"""Compile native iOS workflows. No network is used by the generated shortcuts."""
from pathlib import Path
import hashlib
import json
import plistlib

from workflow import Workflow, dictionary_value, variable as v, ref, token

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'config/catalog.json').read_text(encoding='utf-8'))
CATALOG_JSON = json.dumps(CATALOG, ensure_ascii=False, separators=(',', ':'))
# A symbolic Shortcuts container, without an author's device ID or bookmark.
SHORTCUTS_FOLDER = {'fileLocation': {'WFFileLocationType': 'Shortcuts',
    'relativeSubpath': '', 'appContainerBundleIdentifier': 'com.apple.shortcuts',
    'fileProviderDomainID': 'com.apple.CloudDocs.MobileDocumentsFileProvider'},
    'filename': 'Documents', 'displayName': 'Shortcuts'}
JSON_STRING = r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"'
PAIR = JSON_STRING + r'\s*:\s*' + JSON_STRING
SETTINGS_PATTERN = r'\A\s*\{\s*' + PAIR + r'(?:\s*,\s*' + PAIR + r')*\s*\}\s*\z'


def build(dry_run=False):
    w = Workflow('Quick Call Image Test' if dry_run else 'Quick Call Image')
    a, get, text, put, label = w.action, w.get, w.text, w.put, w.label

    def require_eq(value, expected, message='invalidConfig'):
        g = w.if_eq(value, expected)
        w.otherwise(g)
        w.alert(label(message), stop=True)
        w.end_if(g)

    def load_strings():
        w.set('Strings', get(v('Catalog'), 'languages.', v('Language')))
        present = w.if_gt(w.count(get(v('Strings'), 'name'), 'Characters'))
        w.otherwise(present)
        w.assign('Language', 'en')
        w.set('Strings', get(v('Catalog'), 'languages.en'))
        w.end_if(present)

    def read_file(name):
        return a('documentpicker.open', {'WFFile': ref(v('StorageRoot')),
            'WFGetFilePath': 'QuickCall/' + name, 'WFFileErrorIfNotFound': False,
            'WFGetFolderContents': False}, name)

    def save_file(body, name):
        named = w.named_json(body, name)
        return a('documentpicker.save', {'WFInput': ref(named), 'WFFolder': ref(v('StorageRoot')),
            'WFAskWhereToSave': False, 'WFFileDestinationPath': 'QuickCall/' + name,
            'WFSaveFileOverwrite': True}, 'Save ' + name)

    def create_folder():
        a('file.createfolder', {'WFFolder': ref(v('StorageRoot')), 'WFFilePath': 'QuickCall'}, 'QuickCall folder')

    def persist_catalog():
        save_file(text(v('EmbeddedCatalogJSON')), 'catalog.json')
        check = text(read_file('catalog.json'), name='Saved catalog contents')
        require_eq(w.hash(check), w.hash(v('EmbeddedCatalogJSON')), 'saveFailed')

    def save_settings():
        create_folder()
        settings = text('{"schemaVersion":"1","region":"', v('Region'),
            '","language":"', v('Language'), '","singleResult":"', v('SingleResult'), '"}',
            name='Settings JSON')
        previous = read_file('settings.json')
        exists = w.if_gt(w.count(previous))
        save_file(text(previous), 'settings.previous.json')
        w.end_if(exists)
        save_file(settings, 'settings.json')
        reread = text(read_file('settings.json'), name='Saved settings contents')
        require_eq(w.hash(reread), w.hash(settings), 'saveFailed')
        w.notify('saved')

    def menu_start():
        w.empty_list('Rows')
        w.empty_dict('RowMap')

    def row(display, identifier):
        w.append('Rows', display)
        w.set('RowMap', put(v('RowMap'), w.hash(display), identifier))

    def menu_finish(prompt):
        selected = text(w.choose(v('Rows'), prompt), name='Selected label')
        return text(get(v('RowMap'), w.hash(selected)), name='Selected ID')

    def append_menu(group):
        entries = get(v('Catalog'), 'menus.' + group)
        g, item = w.each(entries)
        w.set('MenuItem', item)
        enabled = w.if_eq(get(v('MenuItem'), 'enabled'), '1')
        icon = get(v('Catalog'), 'icons.', get(v('MenuItem'), 'iconKey'))
        title = get(v('Strings'), get(v('MenuItem'), 'labelKey'))
        display = text(icon, ' ', title, name='Menu row')
        row(display, get(v('MenuItem'), 'handler'))
        w.end_if(enabled)
        w.end_loop(g)

    def menu(group, prompt_key):
        menu_start()
        append_menu(group)
        return menu_finish(label(prompt_key))

    def choose_country(bootstrap=False):
        menu_start()
        loop, item = w.each(get(v('Catalog'), 'countryOrder'))
        w.set('CountryID', item)
        profile = get(v('Catalog'), 'countries.', v('CountryID'))
        display = text(get(profile, 'icon'), ' ', v('CountryID'), ' ', get(profile, 'callingCode'),
            ' · ', get(profile, 'name'), name='Country row')
        row(display, v('CountryID'))
        w.end_loop(loop)
        prompt = get(v('Catalog'), 'behavior.bootstrapCountryPrompt') if bootstrap else label('countryPrompt')
        w.set('Region', menu_finish(prompt))
        selected = get(v('Catalog'), 'countries.', v('Region'))
        require_eq(get(selected, 'regionCode'), v('Region'))
        w.set('Language', get(selected, 'defaultLanguage'))
        load_strings()

    def choose_language():
        menu_start()
        loop, item = w.each(get(v('Catalog'), 'languageOrder'))
        w.set('LanguageID', item)
        display = text('🌐 ', get(v('Catalog'), 'languages.', v('LanguageID'), '.name'), name='Language row')
        row(display, v('LanguageID'))
        w.end_loop(loop)
        w.set('Language', menu_finish(label('languagePrompt')))
        load_strings()

    def finish_call(target):
        w.set('DialTarget', target)
        eligible = w.if_match(v('DialTarget'), get(v('Catalog'), 'behavior.e164Pattern'))
        if dry_run:
            a('showresult', {'Text': token(label('testResult'), '\n\n', v('DialTarget'))}, 'Test destination; no call')
        else:
            phone = a('detect.phonenumber', {'WFInput': ref(v('DialTarget'))}, 'Dialable phone number')
            one = w.if_eq(w.count(phone), '1')
            # Phone intent gets the validated international number, never a menu label/contact name.
            a('com.apple.mobilephone.call', {'WFCallContact': ref(w.first(phone)),
                'IntentAppDefinition': {'BundleIdentifier': 'com.apple.TelephonyUtilities.PhoneIntentHandler'}}, 'Call selected number')
            w.otherwise(one)
            w.alert(label('invalidConfig'), stop=True)
            w.end_if(one)
        a('exit')
        w.otherwise(eligible)
        w.alert(label('invalidConfig'), stop=True)
        w.end_if(eligible)

    def validate_nsn(profile, nsn):
        valid = w.if_match(nsn, get(profile, 'nationalPattern'))
        canonical = text(get(profile, 'callingCode'), nsn, name='Canonical E164 number')
        safe = w.if_match(canonical, get(v('Catalog'), 'behavior.e164Pattern'))
        # E164 keys contain no dots, so Dictionary's dotted-key lookup is unambiguous.
        prior = get(v('Numbers'), canonical)
        new_number = w.if_eq(w.count(prior, 'Characters'), '0')
        context = w.replace(v('Line'), r'\s+', ' ')
        context = w.replace(context, r'\A(.{0,72})[\s\S]*\z', '$1')
        w.set('Numbers', put(v('Numbers'), canonical, context))
        w.end_if(new_number)
        w.assign('CandidateValid', '1')
        w.end_if(safe)
        w.end_if(valid)

    def extract_numbers():
        w.empty_dict('Numbers')
        w.assign('Unresolved', '0')
        w.set('WorkingText', w.replace(v('RawText'), '＋', '+', regex=False))
        w.set('WorkingText', w.replace(v('WorkingText'), r'\r', '\n'))
        digits = w.match(v('WorkingText'), get(v('Catalog'), 'behavior.unicodeDigitPattern'))
        digits_loop, digit = w.each(digits)
        w.set('Digit', text(digit))
        replacement = get(v('Catalog'), 'digitMap.', v('Digit'))
        w.set('WorkingText', w.replace(v('WorkingText'), v('Digit'), replacement, regex=False))
        w.end_loop(digits_loop)
        lines = a('text.split', {'text': ref(v('WorkingText')), 'WFTextSeparator': 'New Lines'}, 'OCR lines')
        lines_loop, line = w.each(lines)
        w.set('Line', text(line))
        candidates = w.match(v('Line'), get(v('Catalog'), 'behavior.candidatePattern'))
        candidate_loop, candidate = w.each(candidates)
        w.set('CandidateRaw', text(candidate))
        # Numeric matches cannot contain backslashes; quoting the exact match is safe for ICU.
        before_pattern = text(r'\Q', v('CandidateRaw'), r'\E[\s\S]*\z')
        before = w.replace(v('Line'), before_pattern, '')
        after_pattern = text(r'\A[\s\S]*?\Q', v('CandidateRaw'), r'\E')
        after = w.replace(v('Line'), after_pattern, '')
        w.assign('IgnoreCandidate', '0')
        ignored = w.if_match(before, get(v('Catalog'), 'behavior.ignorePrefixPattern'))
        w.assign('IgnoreCandidate', '1')
        w.end_if(ignored)
        currency = w.if_match(after, get(v('Catalog'), 'behavior.currencySuffixPattern'))
        w.assign('IgnoreCandidate', '1')
        w.end_if(currency)
        accepted = w.if_eq(v('IgnoreCandidate'), '0')
        w.set('Candidate', w.replace(v('CandidateRaw'), '[^0-9+]', ''))
        w.assign('CandidateValid', '0')
        explicit = w.if_match(v('Candidate'), r'\A\+')
        w.otherwise(explicit)
        idd = get(v('DefaultProfile'), 'internationalPrefixPattern')
        has_idd = w.if_match(v('Candidate'), idd)
        w.set('Candidate', w.replace(v('Candidate'), idd, '+'))
        w.end_if(has_idd)
        w.end_if(explicit)
        international = w.if_match(v('Candidate'), r'\A\+')
        country_loop, country_id = w.each(get(v('Catalog'), 'countryOrder'))
        w.set('ValidationRegion', country_id)
        w.set('ValidationProfile', get(v('Catalog'), 'countries.', v('ValidationRegion')))
        cc = get(v('ValidationProfile'), 'callingCode')
        cc_pattern = text('\\A\\', cc, r'[0-9]+\z')
        right_code = w.if_match(v('Candidate'), cc_pattern)
        w.set('NSN', w.replace(v('Candidate'), cc, '', regex=False))
        # Only an explicit parenthesized optional trunk marker may be removed in an international number.
        trunk = get(v('ValidationProfile'), 'nationalPrefix')
        trunk_present = w.if_gt(w.count(trunk, 'Characters'))
        optional_trunk = text('\\A\\', cc, r'[ \u00A0\u202F]*\(', trunk, r'\)')
        marked = w.if_match(v('CandidateRaw'), optional_trunk)
        w.set('NSN', w.replace(v('NSN'), text(r'\A', trunk), ''))
        w.end_if(marked)
        w.end_if(trunk_present)
        validate_nsn(v('ValidationProfile'), v('NSN'))
        w.end_if(right_code)
        w.end_loop(country_loop)
        missing = w.if_eq(v('CandidateValid'), '0')
        w.assign('Unresolved', '1')
        w.end_if(missing)
        w.otherwise(international)
        w.set('NSN', v('Candidate'))
        w.assign('DomesticAllowed', '0')
        bare_allowed = w.if_eq(get(v('DefaultProfile'), 'acceptBareNSN'), '1')
        w.assign('DomesticAllowed', '1')
        w.end_if(bare_allowed)
        trunk = get(v('DefaultProfile'), 'nationalPrefix')
        nonempty = w.if_gt(w.count(trunk, 'Characters'))
        prefixed = w.if_match(v('NSN'), text(r'\A', trunk, r'[0-9]+\z'))
        w.set('NSN', w.replace(v('NSN'), text(r'\A', trunk), ''))
        w.assign('DomesticAllowed', '1')
        w.end_if(prefixed)
        w.end_if(nonempty)
        domestic_allowed = w.if_eq(v('DomesticAllowed'), '1')
        validate_nsn(v('DefaultProfile'), v('NSN'))
        w.end_if(domestic_allowed)
        w.end_if(international)
        w.end_if(accepted)
        w.end_loop(candidate_loop)
        w.end_loop(lines_loop)

    a('comment', {'WFCommentActionText': 'Quick Call Image · 1.0.0-beta.1\nCommunity testing build. Configuration, languages and icons are bundled below. On-device settings live in QuickCall. The Test variant never contains a Call action.'})
    resources = a('dictionary', {'WFItems': dictionary_value({'CatalogJSON': CATALOG_JSON,
        'AppVersion': CATALOG['meta']['configVersion']})}, 'QuickCall · Editable Resources')
    w.set('EmbeddedCatalogJSON', get(resources, 'CatalogJSON'))
    w.set('Catalog', a('detect.dictionary', {'WFInput': ref(v('EmbeddedCatalogJSON'))}, 'Bundled catalog'))
    w.set('Strings', get(v('Catalog'), 'languages.en'))
    w.set('SharedImages', a('detect.images', {'WFInput': ref({'Type': 'ExtensionInput'})}, 'Shared images'))
    w.set('StorageRoot', a('file', {'WFFile': SHORTCUTS_FOLDER}, 'Portable Shortcuts folder'))
    catalog_file = read_file('catalog.json')
    catalog_exists = w.if_gt(w.count(catalog_file))
    w.set('Catalog', a('detect.dictionary', {'WFInput': ref(catalog_file)}, 'Local catalog'))
    w.otherwise(catalog_exists)
    create_folder()
    persist_catalog()
    w.end_if(catalog_exists)
    require_eq(get(v('Catalog'), 'meta.schemaVersion'), '1')
    require_eq(get(v('Catalog'), 'meta.engineRevision'), '1')
    w.assign('SettingsValid', '0')
    w.assign('Region', 'VN')
    w.assign('Language', 'en')
    w.assign('SingleResult', 'call')
    settings_file = read_file('settings.json')
    settings_text = text(settings_file, name='Settings file text')
    settings_format = w.if_match(settings_text, SETTINGS_PATTERN)
    settings = a('detect.dictionary', {'WFInput': ref(settings_text)}, 'Saved settings')
    version_ok = w.if_eq(get(settings, 'schemaVersion'), '1')
    w.set('Region', get(settings, 'region'))
    w.set('Language', get(settings, 'language'))
    w.set('SingleResult', get(settings, 'singleResult'))
    region_shape = w.if_match(v('Region'), r'\A[A-Z]{2}\z')
    region_ok = w.if_eq(get(v('Catalog'), 'countries.', v('Region'), '.regionCode'), v('Region'))
    language_shape = w.if_match(v('Language'), r'\A[A-Za-z-]+\z')
    language_ok = w.if_gt(w.count(get(v('Catalog'), 'languages.', v('Language'), '.name'), 'Characters'))
    mode_ok = w.if_match(v('SingleResult'), r'\A(?:call|choose)\z')
    w.assign('SettingsValid', '1')
    w.end_if(mode_ok)
    w.end_if(language_ok)
    w.end_if(language_shape)
    w.end_if(region_ok)
    w.end_if(region_shape)
    w.end_if(version_ok)
    w.end_if(settings_format)
    needs_setup = w.if_eq(v('SettingsValid'), '0')
    w.assign('Language', 'en')
    w.assign('SingleResult', 'call')
    load_strings()
    choose_country(bootstrap=True)
    choose_language()
    save_settings()
    w.end_if(needs_setup)
    load_strings()
    if dry_run:
        w.notify('testBanner')
    w.assign('Route', 'menu')
    shared = w.if_gt(w.count(v('SharedImages')))
    w.assign('Route', 'shared')
    w.end_if(shared)

    interactions = w.times(get(v('Catalog'), 'behavior.maxInteractions'))
    w.set('DefaultProfile', get(v('Catalog'), 'countries.', v('Region')))
    is_menu = w.if_eq(v('Route'), 'menu')
    w.set('Route', menu('main', 'sourcePrompt'))
    w.end_if(is_menu)
    settings_route = w.if_eq(v('Route'), 'settings')
    setting_id = menu('settings', 'settingsPrompt')
    w.set('SettingID', setting_id)
    country_setting = w.if_eq(v('SettingID'), 'country')
    choose_country()
    choose_language()
    save_settings()
    w.end_if(country_setting)
    language_setting = w.if_eq(v('SettingID'), 'language')
    choose_language()
    save_settings()
    w.end_if(language_setting)
    restore_setting = w.if_eq(v('SettingID'), 'restore')
    create_folder()
    persist_catalog()
    w.set('Catalog', a('detect.dictionary', {'WFInput': ref(v('EmbeddedCatalogJSON'))}, 'Restored catalog'))
    load_strings()
    w.notify('restored')
    w.end_if(restore_setting)
    w.assign('Route', 'menu')
    w.end_if(settings_route)
    about_route = w.if_eq(v('Route'), 'about')
    w.alert(text('Quick Call Image ', CATALOG['meta']['configVersion'], '\n\n', label('aboutBody')))
    w.assign('Route', 'menu')
    w.end_if(about_route)
    cancelled = w.if_eq(v('Route'), 'cancel')
    a('exit')
    w.end_if(cancelled)
    camera = w.if_eq(v('Route'), 'camera')
    w.set('Images', a('takephoto', {'WFCameraCaptureShowPreview': True,
        'WFCameraCaptureDevice': 'Back', 'WFPhotoCount': 1}, 'Photo'))
    w.assign('Route', 'ocr')
    w.end_if(camera)
    photos = w.if_eq(v('Route'), 'photos')
    w.set('Images', a('selectphoto', {'WFSelectMultiplePhotos': False}, 'Selected photo'))
    w.assign('Route', 'ocr')
    w.end_if(photos)
    shared = w.if_eq(v('Route'), 'shared')
    w.set('Images', v('SharedImages'))
    w.assign('Route', 'ocr')
    w.end_if(shared)
    manual = w.if_eq(v('Route'), 'manual')
    w.set('RawText', a('ask', {'WFInputType': 'Text', 'WFAskActionPrompt': token(label('enterNumber')),
        'WFAllowsMultilineText': False}, 'Entered number'))
    w.assign('Route', 'parse')
    w.end_if(manual)
    ocr = w.if_eq(v('Route'), 'ocr')
    images_exist = w.if_gt(w.count(v('Images')))
    several = w.if_gt(w.count(v('Images')), 1)
    w.set('Image', w.choose(v('Images'), label('selectImage')))
    w.otherwise(several)
    w.set('Image', w.first(v('Images')))
    w.end_if(several)
    w.set('RawText', a('extracttextfromimage', {'WFImage': ref(v('Image'))}, 'OCR text'))
    w.assign('Route', 'parse')
    w.otherwise(images_exist)
    a('exit')
    w.end_if(images_exist)
    w.end_if(ocr)
    parse = w.if_eq(v('Route'), 'parse')
    too_large = w.if_gt(w.count(v('RawText'), 'Characters'), get(v('Catalog'), 'behavior.maxTextCharacters'))
    w.alert(label('largeText'), stop=True)
    w.end_if(too_large)
    extract_numbers()
    w.set('NumberKeys', w.keys(v('Numbers')))
    w.set('ResultCount', w.count(v('NumberKeys')))
    one = w.if_eq(v('ResultCount'), '1')
    no_unknown = w.if_eq(v('Unresolved'), '0')
    immediate = w.if_eq(v('SingleResult'), 'call')
    finish_call(w.first(v('NumberKeys')))
    w.end_if(immediate)
    w.end_if(no_unknown)
    w.end_if(one)
    has_numbers = w.if_gt(v('ResultCount'))
    menu_start()
    numbers_loop, number = w.each(v('NumberKeys'))
    w.set('MenuNumber', text(number))
    display = text(get(v('Catalog'), 'icons.call'), ' ', v('MenuNumber'), ' · ',
        get(v('Numbers'), v('MenuNumber')), name='Phone row')
    row(display, v('MenuNumber'))
    w.end_loop(numbers_loop)
    append_menu('results')
    w.set('ResultPrompt', text(label('chooseNumber')))
    unknown = w.if_eq(v('Unresolved'), '1')
    w.set('ResultPrompt', text(label('unsupported')))
    w.end_if(unknown)
    w.set('ResultChoice', menu_finish(v('ResultPrompt')))
    selected_phone = w.if_match(v('ResultChoice'), get(v('Catalog'), 'behavior.e164Pattern'))
    finish_call(v('ResultChoice'))
    w.end_if(selected_phone)
    w.set('Route', v('ResultChoice'))
    w.otherwise(has_numbers)
    w.set('Route', menu('recovery', 'noResults'))
    w.end_if(has_numbers)
    retry = w.if_eq(v('Route'), 'retry')
    w.assign('Route', 'menu')
    w.end_if(retry)
    cancel = w.if_eq(v('Route'), 'cancel')
    a('exit')
    w.end_if(cancel)
    w.end_if(parse)
    w.end_loop(interactions)
    w.alert(label('limit'), stop=True)
    return w.header()


def main():
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    info = {}
    for test, stem in [(False, 'Quick-Call-Image'), (True, 'Quick-Call-Image-Test')]:
        workflow = build(test)
        raw = plistlib.dumps(workflow, fmt=plistlib.FMT_XML, sort_keys=False)
        assert plistlib.loads(raw) == workflow
        destination = out / (stem + '.unsigned.shortcut')
        destination.write_bytes(raw)
        # Compact binary plist is also supplied as signing input; XML stays
        # reproducible for inspection but need not be committed twice.
        (out / (stem + '.unsigned.bplist')).write_bytes(plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY, sort_keys=False))
        info[stem] = {'actions': len(workflow['WFWorkflowActions']), 'bytes': len(raw),
                      'unsignedSHA256': hashlib.sha256(raw).hexdigest(), 'dryRun': test}
    (ROOT / 'qa/build.json').write_text(json.dumps(info, indent=2) + '\n')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
