#!/usr/bin/env python3
"""Dispatch operational-area submissions to the appropriate processor."""

import base64
import gzip
import json
import os
import re
import subprocess
import sys
import tempfile


def fail(message):
    print(f"::error::{message}")
    raise SystemExit(1)


def decode_payload(body):
    match = re.search(r'<!--\s*OAM(1|2):([A-Za-z0-9_-]+)\s*-->', body)
    if match:
        version = match.group(1)
        token = match.group(2)
        try:
            padded = token + ('=' * (-len(token) % 4))
            encoded = base64.urlsafe_b64decode(padded.encode('ascii'))
            decoded = gzip.decompress(encoded).decode('utf-8') if version == '1' else encoded.decode('utf-8')
            payload = json.loads(decoded)
        except (ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f'Embedded submission payload is invalid: {exc}')
        if payload.get('version') != 1:
            fail('Unsupported embedded submission payload version.')
        return payload

    text = body.strip()
    try:
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text
            if text.endswith('```'):
                text = text[:-3].rstrip()
        payload = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return None

    if isinstance(payload, dict) and payload.get('submission_type') == 'operational_area':
        return payload
    return None


def canonicalize(payload):
    """Map the current browser payload to the legacy Circle/Polygon processor schema."""
    return {
        'version': 1,
        'submission_type': payload.get('submission_type'),
        'operator_id': payload.get('operator_id'),
        'site_id': payload.get('site_id') or payload.get('site_area_id'),
        'metro_locality': payload.get('metro_locality'),
        'center_point': payload.get('center_point'),
        'geographic_bounds': payload.get('geographic_bounds'),
        'coordination_contact_name': (payload.get('coordination_contact') or {}).get('name') or payload.get('coordination_contact_name'),
        'coordination_contact_email': (payload.get('coordination_contact') or {}).get('email') or payload.get('coordination_contact_email'),
        'coordination_contact_phone': (payload.get('coordination_contact') or {}).get('phone') or payload.get('coordination_contact_phone'),
        'effective_from': payload.get('effective_from'),
        'effective_to': payload.get('effective_to'),
        'operational_area_definition': payload.get('operational_area_definition'),
        'geometry': payload.get('geometry'),
        'confirm_minimum_info': payload.get('confirm_minimum_info') is True or (payload.get('confirmations') or {}).get('minimum_information') is True,
        'authorized': payload.get('authorized') is True or (payload.get('confirmations') or {}).get('authorized') is True,
    }


def run_processor(processor, event, payload):
    event_copy = dict(event)
    event_copy['issue'] = dict(event.get('issue') or {})
    event_copy['issue']['body'] = json.dumps(payload, indent=2)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False) as handle:
        json.dump(event_copy, handle)
        temp_event_path = handle.name
    try:
        env = os.environ.copy()
        env['GITHUB_EVENT_PATH'] = temp_event_path
        result = subprocess.run([sys.executable, processor], env=env, check=False)
        raise SystemExit(result.returncode)
    finally:
        try:
            os.unlink(temp_event_path)
        except FileNotFoundError:
            pass


def main():
    event_path = os.environ['GITHUB_EVENT_PATH']
    with open(event_path, 'r', encoding='utf-8') as handle:
        event = json.load(handle)

    issue = event.get('issue') or {}
    body = issue.get('body') or ''
    payload = decode_payload(body)

    if payload is None:
        # Keep the original Markdown-template workflow completely unchanged.
        processor = os.path.join(os.path.dirname(__file__), 'process_operational_area_submission.py')
        print('No structured payload marker found; using existing Polygon/Circle processor.')
        result = subprocess.run([sys.executable, processor], env=os.environ.copy(), check=False)
        raise SystemExit(result.returncode)

    definition = payload.get('operational_area_definition')
    is_multicircle = isinstance(definition, dict) and definition.get('type') == 'MultiCircle'

    if is_multicircle:
        processor = os.path.join(os.path.dirname(__file__), 'process_multicircle_operational_area_submission.py')
        print('Detected MultiCircle submission; using MultiCircle processor.')
        run_processor(processor, event, payload)

    processor = os.path.join(os.path.dirname(__file__), 'process_operational_area_submission.py')
    print('Detected structured Polygon/Circle submission; using existing processor.')
    run_processor(processor, event, canonicalize(payload))


if __name__ == '__main__':
    main()
