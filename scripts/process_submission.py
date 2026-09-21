#!/usr/bin/env python3
"""Dispatch a templated operational-area issue to the appropriate processor."""

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
    if not match:
        return None

    version = match.group(1)
    token = match.group(2)
    try:
        padded = token + ('=' * (-len(token) % 4))
        encoded = base64.urlsafe_b64decode(padded.encode('ascii'))
        decoded = gzip.decompress(encoded).decode('utf-8') if version == '1' else encoded.decode('utf-8')
        payload = json.loads(decoded)
    except (ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"Embedded submission payload is invalid: {exc}")

    if payload.get('version') != 1:
        fail('Unsupported embedded submission payload version.')
    return payload


def main():
    event_path = os.environ['GITHUB_EVENT_PATH']
    with open(event_path, 'r', encoding='utf-8') as handle:
        event = json.load(handle)

    issue = event.get('issue') or {}
    body = issue.get('body') or ''
    payload = decode_payload(body)
    definition = payload.get('operational_area_definition') if payload else None
    is_multicircle = isinstance(definition, dict) and definition.get('type') == 'MultiCircle'

    if is_multicircle:
        processor = os.path.join(os.path.dirname(__file__), 'process_multicircle_operational_area_submission.py')
        print('Detected MultiCircle submission; using MultiCircle processor.')
        # The MultiCircle processor expects JSON in the issue body. Preserve the
        # original GitHub event and provide a temporary event containing the
        # decoded template payload only for this subprocess.
        event_copy = dict(event)
        event_copy['issue'] = dict(issue)
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

    processor = os.path.join(os.path.dirname(__file__), 'process_operational_area_submission.py')
    print('Using existing Polygon/Circle operational-area processor.')
    result = subprocess.run([sys.executable, processor], env=os.environ.copy(), check=False)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
