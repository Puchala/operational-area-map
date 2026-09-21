from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: remove_redundant_operational_status.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old = "${definitionRow}</div><div class=\"popup-row\"><strong>Operational-area status:</strong> ${areaStatus}</div>${overlapWith.length ? `<div class=\"popup-row\"><strong>Area-level overlap with:</strong> ${overlapWith.map(escapeHtml).join(', ')}</div>` : ''}"
new = "${definitionRow}</div>${overlapWith.length ? `<div class=\"popup-row\"><strong>Area-level overlap with:</strong> ${overlapWith.map(escapeHtml).join(', ')}</div>` : ''}"

if old not in text:
    raise SystemExit("Could not locate redundant operational-area status in generated popup")

text = text.replace(old, new, 1)
text = text.replace("\n              const areaStatus = p.potential_overlap ? 'Potential geographic overlap' : 'No detected overlap';", "")
text = text.replace("\n<!-- redundant-operational-status-removed: 2026-09-21 -->", "")
text = text.replace("</head>", "  <!-- redundant-operational-status-removed: 2026-09-21 -->\n</head>", 1)
path.write_text(text, encoding="utf-8")
print(f"Patched {path}")