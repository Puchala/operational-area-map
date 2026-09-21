#!/usr/bin/env python3
"""Add the GitHub issue-template submission bridge to the published page.

The source submission app remains unchanged. This small deployment-time bridge
keeps Polygon/Circle behavior intact while giving MultiCircle submissions a
human-readable GitHub issue body plus a hidden machine-readable payload.
"""

from pathlib import Path
import sys


BRIDGE = r'''<script>
(function () {
  const button = document.getElementById('createGithubSubmission');
  if (!button) return;

  function encodeBase64Url(value) {
    const bytes = new TextEncoder().encode(value);
    let binary = '';
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function parsePayload() {
    if (typeof buildSubmissionText !== 'function') return null;
    const text = buildSubmissionText().trim();
    if (!text) return null;
    const json = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
    return JSON.parse(json);
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function formatRadius(meters) {
    return (Number(meters) / 1609.344).toFixed(2) + ' mi (' +
      (Number(meters) / 1000).toFixed(2) + ' km)';
  }

  button.addEventListener('click', function (event) {
    let payload;
    try {
      payload = parsePayload();
    } catch (_) {
      return; // Let the existing submission handler report the normal error.
    }

    const definition = payload && payload.operational_area_definition;
    if (!definition || definition.type !== 'MultiCircle') return;

    event.preventDefault();
    event.stopImmediatePropagation();

    const circles = Array.isArray(definition.circles) ? definition.circles : [];
    const rows = circles.map((circle, index) => {
      const point = circle.center_point || {};
      return '| ' + (index + 1) + ' | ' + escapeHtml(point.latitude) +
        ' | ' + escapeHtml(point.longitude) + ' | ' +
        escapeHtml(formatRadius(circle.radius_meters)) + ' |';
    }).join('\n');

    const visibleBody = [
      '<!-- OPERATIONAL-AREA-SUBMISSION -->',
      '',
      '## Operational Area Submission',
      '',
      '**Operator ID:** ' + escapeHtml(payload.operator_id || ''),
      '',
      '**Site / Area ID:** ' + escapeHtml(payload.site_id || payload.site_area_id || ''),
      '',
      '**Metro / Locality:** ' + escapeHtml(payload.metro_locality || ''),
      '',
      '**Effective From:** ' + escapeHtml(payload.effective_from || ''),
      '',
      '**Effective To:** ' + escapeHtml(payload.effective_to || ''),
      '',
      '### Operational Area Definition',
      '',
      '**Type:** MultiCircle',
      '',
      '| Circle | Latitude | Longitude | Radius |',
      '| --- | ---: | ---: | ---: |',
      rows,
      '',
      '<!-- OAM2:' + encodeBase64Url(JSON.stringify(payload)) + ' -->'
    ].join('\n');

    const repoUrl = typeof getGitHubRepositoryUrl === 'function'
      ? getGitHubRepositoryUrl()
      : 'https://github.com/Puchala/operational-area-map';
    const siteId = payload.site_id || payload.site_area_id || '';
    const url = repoUrl + '/issues/new?template=' + encodeURIComponent('operational-area.md') +
      '&title=' + encodeURIComponent('Operational Area Submission: ' + siteId) +
      '&body=' + encodeURIComponent(visibleBody);

    window.open(url, '_blank', 'noopener');
  }, true);
})();
</script>'''


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: prepare_submission_page.py <html-file>')

    path = Path(sys.argv[1])
    html = path.read_text(encoding='utf-8')
    if 'submission-preview-bridge: multicircle-v1' in html:
        return

    marker = '<!-- submission-preview-bridge: multicircle-v1 -->'
    html += '\n' + marker + '\n' + BRIDGE + '\n'
    path.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()
