"""Execute the actual generated plist with simulated iOS I/O; never makes a call."""
from dataclasses import dataclass
import hashlib
import json

from icu import matches, replace


@dataclass
class File:
    name: str
    body: str = ''
    kind: str = 'json'
    ocr: str = ''


@dataclass
class Folder:
    name: str


class Halt(Exception):
    pass


def stringify(value):
    if value is None:
        return ''
    if isinstance(value, File):
        return value.body
    if isinstance(value, Folder):
        return value.name
    if isinstance(value, list):
        return '\n'.join(map(stringify, value))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return str(value)


def run(workflow, menus=(), photos=(), camera=(), incoming=None, answers=(), disk=None, fail_save=False,
        rewrite_json=False, corrupt_save=None, detected_phone_numbers=None, native_phone_conversion=None):
    actions = workflow['WFWorkflowActions']
    blocks, stack = {}, []
    for i, action in enumerate(actions):
        ident, p = action['WFWorkflowActionIdentifier'], action['WFWorkflowActionParameters']
        if ident not in ('is.workflow.actions.conditional', 'is.workflow.actions.repeat.each', 'is.workflow.actions.repeat.count'):
            continue
        mode = p['WFControlFlowMode']
        if mode == 0:
            blocks[i] = {'kind': ident, 'group': p['GroupingIdentifier'], 'else': None}
            stack.append(i)
        elif mode == 1:
            assert blocks[stack[-1]]['group'] == p['GroupingIdentifier']
            blocks[stack[-1]]['else'] = i
        else:
            first = stack.pop()
            assert blocks[first]['group'] == p['GroupingIdentifier']
            blocks[first]['end'] = i
    assert not stack
    menus, answers, photos, camera = iter(menus), iter(answers), iter(photos), iter(camera)
    result = {'menus': [], 'alerts': [], 'notifications': [], 'destinations': [], 'previews': [],
              'ocrCalls': 0, 'writes': [], 'executedActions': 0, 'status': 'done',
              'disk': dict(disk or {}), 'variables': {}}
    variables, outputs = result['variables'], {}
    each_depth, repeat_depth = 0, 0

    def evaluate(value):
        if not isinstance(value, dict):
            return value
        serial = value.get('WFSerializationType')
        if serial in ('WFTextTokenAttachment', 'WFDictionaryFieldValue'):
            return evaluate(value['Value'])
        if serial == 'WFTextTokenString':
            s = value['Value']['string'].encode('utf-16-le')
            edits = []
            for span, attachment in value['Value']['attachmentsByRange'].items():
                lo, count = map(int, span.strip('{}').split(','))
                edits.append((lo, count, stringify(evaluate(attachment))))
            for lo, count, replacement in sorted(edits, reverse=True):
                assert s[lo * 2:(lo + count) * 2].decode('utf-16-le') == '\ufffc'
                s = s[:lo * 2] + replacement.encode('utf-16-le') + s[(lo + count) * 2:]
            return s.decode('utf-16-le')
        if 'WFDictionaryFieldValueItems' in value:
            return {stringify(evaluate(i['WFKey'])): evaluate(i['WFValue']) for i in value['WFDictionaryFieldValueItems']}
        if value.get('Type') == 'Variable' and 'Variable' in value:
            return evaluate(value['Variable'])
        kind = value.get('Type')
        if kind == 'Variable':
            name = value['VariableName']
            assert name in variables, ('unassigned variable', name)
            answer = variables[name]
        elif kind == 'ActionOutput':
            identifier = value['OutputUUID']
            assert identifier in outputs, ('unexecuted action referenced', value)
            answer = outputs[identifier]
        elif kind == 'ExtensionInput':
            answer = incoming
        else:
            return value
        for transform in value.get('Aggrandizements', []):
            if transform['Type'] == 'WFDictionaryValueVariableAggrandizement':
                answer = answer.get(transform['DictionaryKey'])
            elif transform['Type'] == 'WFCoercionVariableAggrandizement':
                if transform['CoercionItemClass'] == 'WFStringContentItem':
                    answer = stringify(answer)
                elif transform['CoercionItemClass'] == 'WFNumberContentItem':
                    answer = float(stringify(answer))
                elif transform['CoercionItemClass'] == 'WFPhoneNumberContentItem':
                    answer = stringify(answer)
                    assert matches(r'\A\+[1-9][0-9]{6,14}\z', answer), 'Only a validated E.164 value can reach Call'
                    if native_phone_conversion is not None:
                        answer = native_phone_conversion
                else:
                    raise AssertionError(transform)
        return answer

    def sequence(value):
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def execute(first, last):
        nonlocal each_depth, repeat_depth
        i = first
        while i < last:
            result['executedActions'] += 1
            assert result['executedActions'] < 250000, 'Unexpected runaway workflow'
            action = actions[i]
            ident = action['WFWorkflowActionIdentifier'].removeprefix('is.workflow.actions.')
            p = action['WFWorkflowActionParameters']
            if i in blocks:
                block = blocks[i]
                if ident == 'conditional':
                    condition = p['WFCondition']
                    if condition == 4:
                        rhs = p['WFConditionalActionString']
                        if isinstance(rhs, dict):
                            assert rhs.get('Value', {}).get('attachmentsByRange'), 'Literal string conditions must use scalar storage'
                        yes = stringify(evaluate(p['WFInput'])) == stringify(evaluate(p['WFConditionalActionString']))
                    elif condition == 2:
                        rhs = p['WFNumberValue']
                        assert isinstance(rhs, (int, float)) or rhs.get('WFSerializationType') == 'WFTextTokenAttachment', 'Numeric condition must use number or variable attachment'
                        yes = float(stringify(evaluate(p['WFInput']))) > float(stringify(evaluate(p['WFNumberValue'])))
                    else:
                        raise AssertionError(condition)
                    middle = block['else'] if block['else'] is not None else block['end']
                    if yes:
                        execute(i + 1, middle)
                    elif block['else'] is not None:
                        execute(middle + 1, block['end'])
                else:
                    repeat_depth += 1
                    index_name = 'Repeat Index' + (' ' + str(repeat_depth) if repeat_depth > 1 else '')
                    if ident == 'repeat.each':
                        each_depth += 1
                        item_name = 'Repeat Item' + (' ' + str(each_depth) if each_depth > 1 else '')
                        values = sequence(evaluate(p['WFInput']))
                    else:
                        values = list(range(int(float(stringify(evaluate(p['WFRepeatCount']))))))
                    for index, item in enumerate(values, 1):
                        variables[index_name] = index
                        if ident == 'repeat.each':
                            variables[item_name] = item
                        execute(i + 1, block['end'])
                    if ident == 'repeat.each':
                        each_depth -= 1
                    repeat_depth -= 1
                i = block['end'] + 1
                continue
            answer = None
            if ident == 'comment':
                pass
            elif ident == 'gettext':
                answer = stringify(evaluate(p['WFTextActionText']))
            elif ident == 'setvariable':
                variables[p['WFVariableName']] = evaluate(p['WFInput'])
            elif ident == 'appendvariable':
                name = p['WFVariableName']
                variables[name] = sequence(variables.get(name)) + [evaluate(p['WFInput'])]
            elif ident == 'dictionary':
                answer = evaluate(p['WFItems'])
            elif ident == 'list':
                answer = [evaluate(x) for x in p['WFItems']]
            elif ident == 'getvalueforkey':
                value = evaluate(p['WFInput'])
                if p['WFGetDictionaryValueType'] == 'All Keys':
                    answer = list(value)
                else:
                    key = stringify(evaluate(p['WFDictionaryKey']))
                    assert '.' not in key, 'Shipping graph must walk nested dictionaries explicitly'
                    value = value.get(key) if isinstance(value, dict) else None
                    answer = value
            elif ident == 'setvalueforkey':
                answer = dict(evaluate(p['WFDictionary']))
                key = stringify(evaluate(p['WFDictionaryKey']))
                assert '.' not in key, 'Ambiguous dotted dictionary key'
                answer[key] = evaluate(p['WFDictionaryValue'])
            elif ident == 'count':
                value = evaluate(p['Input'])
                answer = len(stringify(value)) if p['WFCountType'] == 'Characters' else len(sequence(value))
            elif ident == 'text.match':
                answer = matches(stringify(evaluate(p['WFMatchTextPattern'])), stringify(evaluate(p['text'])))
            elif ident == 'text.replace':
                source = stringify(evaluate(p['WFInput']))
                pattern = stringify(evaluate(p['WFReplaceTextFind']))
                replacement = stringify(evaluate(p['WFReplaceTextReplace']))
                answer = replace(pattern, source, replacement) if p['WFReplaceTextRegularExpression'] else source.replace(pattern, replacement)
            elif ident == 'text.split':
                assert p['WFTextSeparator'] == 'New Lines'
                answer = stringify(evaluate(p['text'])).split('\n')
            elif ident == 'hash':
                assert p['WFHashType'] == 'SHA256'
                answer = hashlib.sha256(stringify(evaluate(p['WFInput'])).encode('utf-8')).hexdigest()
            elif ident == 'detect.dictionary':
                answer = json.loads(stringify(evaluate(p['WFInput'])))
            elif ident == 'detect.images':
                answer = [f for f in sequence(evaluate(p['WFInput'])) if isinstance(f, File) and f.kind == 'image']
            elif ident == 'file':
                assert p['WFFile']['fileLocation']['WFFileLocationType'] == 'Shortcuts'
                answer = Folder('Shortcuts')
            elif ident == 'file.createfolder':
                assert isinstance(evaluate(p['WFFolder']), Folder)
                answer = Folder(p['WFFilePath'])
            elif ident == 'documentpicker.open':
                assert p['WFFileErrorIfNotFound'] is False
                answer = result['disk'].get(p['WFGetFilePath'])
            elif ident == 'setitemname':
                answer = File(p['WFName'], stringify(evaluate(p['WFInput'])))
            elif ident == 'documentpicker.save':
                if fail_save:
                    result['status'] = 'io-error'
                    raise Halt()
                file = evaluate(p['WFInput'])
                assert isinstance(file, File) and p['WFAskWhereToSave'] is False
                path = p['WFFileDestinationPath']
                assert path.startswith('QuickCall/') and '..' not in path
                if rewrite_json:
                    file = File(file.name, json.dumps(json.loads(file.body), ensure_ascii=False, sort_keys=True, indent=2))
                if corrupt_save and path.endswith(corrupt_save):
                    data = json.loads(file.body)
                    if corrupt_save == 'settings.json':
                        data['region'] = 'ZZ'
                    else:
                        data['meta']['configVersion'] = 'damaged'
                    file = File(file.name, json.dumps(data))
                result['disk'][path] = file
                result['writes'].append(path)
                answer = file
            elif ident == 'choosefromlist':
                options = sequence(evaluate(p['WFInput']))
                prompt = stringify(evaluate(p['WFChooseFromListActionPrompt']))
                choice = next(menus)
                if choice is None:
                    result['status'] = 'cancelled'
                    raise Halt()
                if isinstance(choice, int):
                    answer = options[choice]
                else:
                    ids = variables.get('RowMap', {})
                    hits = [o for o in options if ids.get(hashlib.sha256(stringify(o).encode()).hexdigest()) == choice]
                    assert len(hits) == 1, (choice, [stringify(o) for o in options])
                    answer = hits[0]
                result['menus'].append({'prompt': prompt, 'options': [stringify(o) for o in options], 'choice': choice})
            elif ident == 'getitemfromlist':
                items = sequence(evaluate(p['WFInput']))
                if p['WFItemSpecifier'] == 'First Item':
                    answer = items[0]
                else:
                    assert p['WFItemSpecifier'] == 'Item At Index'
                    index = int(stringify(evaluate(p['WFItemIndex'])))
                    assert 1 <= index <= len(items), ('Invalid one-based loop index', index, len(items))
                    answer = items[index - 1]
            elif ident == 'takephoto':
                answer = next(camera)
            elif ident == 'selectphoto':
                answer = next(photos)
            elif ident == 'extracttextfromimage':
                answer = evaluate(p['WFImage']).ocr
                result['ocrCalls'] += 1
            elif ident == 'ask':
                answer = next(answers)
                if answer is None:
                    result['status'] = 'cancelled'
                    raise Halt()
            elif ident == 'detect.phonenumber':
                raw = stringify(evaluate(p['WFInput']))
                assert matches(r'\A\+[1-9][0-9]{6,14}\z', raw)
                answer = [raw] if detected_phone_numbers is None else detected_phone_numbers
            elif ident == 'com.apple.mobilephone.call':
                target = stringify(evaluate(p['WFCallContact']))
                assert matches(r'\A\+[1-9][0-9]{6,14}\z', target)
                result['destinations'].append(target)
            elif ident == 'showresult':
                result['previews'].append(stringify(evaluate(p['Text'])))
            elif ident == 'alert':
                message = stringify(evaluate(p['WFAlertActionMessage']))
                if p.get('CustomOutputName') == 'Test destination; no call':
                    result['previews'].append(message)
                else:
                    result['alerts'].append(message)
            elif ident == 'notification':
                result['notifications'].append(stringify(evaluate(p['WFNotificationActionBody'])))
            elif ident == 'exit':
                raise Halt()
            else:
                raise AssertionError('Unsupported action ' + ident)
            outputs[p['UUID']] = answer
            i += 1

    try:
        execute(0, len(actions))
    except Halt:
        pass
    return result
