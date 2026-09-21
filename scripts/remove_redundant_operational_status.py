from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: remove_redundant_operational_status.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Remove the redundant operational-area status row regardless of which
# preceding popup-row implementation produced it. This must be idempotent:
# a generated page that is already clean is a successful result, not a CI error.
text = re.sub(
    r'<div class="popup-row"><strong>Operational-area status:</strong>.*?</div>',
    '',
    text,
    count=1,
    flags=re.DOTALL,
)

# Remove the now-unused template variable declaration when present.
text = re.sub(
    r'\n\s*const areaStatus = p\.potential_overlap \? [^;]+;',
    '',
    text,
    count=1,
)

# Remove any previous marker before adding the canonical marker.
text = text.replace("\n<!-- redundant-operational-status-removed: 2026-09-21 -->", "")
text = text.replace("\n  <!-- redundant-operational-status-removed: 2026-09-21 -->", "")
text = text.replace("</head>", "  <!-- redundant-operational-status-removed: 2026-09-21 -->\n</head>", 1)

if '<strong>Operational-area status:</strong>' in text:
    raise SystemExit("Redundant operational-area status remains in generated popup")

path.write_text(text, encoding="utf-8")
print(f"Popup status cleanup verified: {path}")
