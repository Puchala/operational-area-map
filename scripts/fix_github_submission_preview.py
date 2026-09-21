#!/usr/bin/env python3
"""Patch the generated submission page used by GitHub Pages.

The script must modify the file supplied on the command line.  The Pages
workflow passes _site/submit.html; modifying the repository source here would
not affect the artifact that is actually deployed.
"""

from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_github_submission_preview.py <html-file>")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    old = """  function buildGitHubIssueBody() {\n    const payload = getSubmissionPayload();\n    if (!payload) return '';\n    const bytes = new TextEncoder().encode(JSON.stringify(payload));\n    let binary = ''; bytes.forEach(byte => binary += String.fromCharCode(byte));\n    const encoded = btoa(binary).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/g, '');\n    return '<!-- OPERATIONAL-AREA-SUBMISSION -->\\n\\n<!-- Submission details are populated automatically by the Operational Area Submission Tool. -->\\n\\n<!-- OAM2:' + encoded + ' -->';\n  }"""
    new = """  function buildGitHubIssueBody() {\n    const payload = getSubmissionPayload();\n    if (!payload) return '';\n    const bytes = new TextEncoder().encode(JSON.stringify(payload));\n    let binary = ''; bytes.forEach(byte => binary += String.fromCharCode(byte));\n    const encoded = btoa(binary).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/g, '');\n    const definition = payload.operational_area_definition;\n    let definitionText = '';\n    if (definition && definition.type === 'MultiCircle') {\n      definitionText = '**Geometry Type:** MultiCircle\\n\\n' + definition.circles.map((c, i) => {\n        const p = c.center_point;\n        return '**Circle ' + (i + 1) + ':** ' + p.latitude + ', ' + p.longitude + ' — ' + (Number(c.radius_meters) / 1609.344).toFixed(2) + ' mi (' + (Number(c.radius_meters) / 1000).toFixed(2) + ' km)';\n      }).join('\\n');\n    } else {\n      const geometryType = payload.geometry && payload.geometry.type ? payload.geometry.type : (definition && definition.type ? definition.type : 'Unknown');\n      definitionText = '**Geometry Type:** ' + geometryType;\n      if (definition && definition.type === 'Circle') {\n        definitionText += '\\n\\n**Center:** ' + definition.center_point.latitude + ', ' + definition.center_point.longitude + '\\n**Radius:** ' + (Number(definition.radius_meters) / 1609.344).toFixed(2) + ' mi (' + (Number(definition.radius_meters) / 1000).toFixed(2) + ' km)';\n      }\n      if (payload.geometry && payload.geometry.type === 'Polygon') {\n        const ring = payload.geometry.coordinates && payload.geometry.coordinates[0];\n        if (Array.isArray(ring)) definitionText += '\\n\\n**Boundary vertices:** ' + Math.max(0, ring.length - 1);\n      }\n      if (payload.geometry && payload.geometry.type === 'MultiPolygon') {\n        const polygons = Array.isArray(payload.geometry.coordinates) ? payload.geometry.coordinates : [];\n        definitionText += '\\n\\n**Component polygons:** ' + polygons.length;\n      }\n    }\n    return '<!-- OPERATIONAL-AREA-SUBMISSION -->\\n\\n## Operational Area Submission\\n\\n' +\n      '**Operator ID:** ' + payload.operator_id + '\\n\\n' +\n      '**Site / Area ID:** ' + payload.site_id + '\\n\\n' +\n      '**Metro / Locality:** ' + payload.metro_locality + '\\n\\n' +\n      '**Effective From:** ' + (payload.effective_from || 'Not specified') + '\\n\\n' +\n      '**Effective To:** ' + (payload.effective_to || 'Not specified') + '\\n\\n' +\n      '### Operational Area Definition\\n\\n' + definitionText + '\\n\\n' +\n      '<!-- OAM2:' + encoded + ' -->';\n  }"""
    if old not in text:
        raise SystemExit("target buildGitHubIssueBody function not found")
    text = text.replace(old, new, 1)

    old_url = "window.open(repoUrl + '/issues/new?template=' + template + '&title=' + title + '&body=' + body, '_blank', 'noopener');"
    new_url = "window.open(repoUrl + '/issues/new?title=' + title + '&body=' + body, '_blank', 'noopener');"
    if old_url in text:
        text = text.replace(old_url, new_url, 1)
    elif "/issues/new?template=" in text:
        # Defense-in-depth: the generated artifact must never retain a
        # template-selected issue URL because it can suppress the URL body.
        raise SystemExit("unexpected GitHub template URL remains in generated page")

    path.write_text(text, encoding="utf-8")
    print(f"patched {path}")


if __name__ == "__main__":
    main()
