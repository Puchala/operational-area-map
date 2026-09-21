from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: fix_popup_overlap_wording.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# The geometry-overlap UI generates component-level overlap rows. Make the
# selected-component relationship explicit and unambiguous in the popup.
old = '''<div class="popup-row"><strong>Overlapping with:</strong> ${selectedOverlaps.map(item => `${escapeHtml(item.other_operator_id)} · ${escapeHtml(item.other_site_id)} (${escapeHtml(item.other_component_type)} ${item.other_component_index})`).join(', ')}</div>'''
new = '''<div class="popup-row"><strong>Actual overlap:</strong> ${selectedOverlaps.map(item => `${escapeHtml(selected.type === 'Circle' ? `Circle ${selected.index + 1}` : `Polygon part ${selected.index + 1}`)} ↔ ${escapeHtml(item.other_operator_id)}/${escapeHtml(item.other_site_id)} ${escapeHtml(item.other_component_type)} ${item.other_component_index}`).join(', ')}</div>'''

if old not in text:
    raise SystemExit("Could not locate the component overlap wording")

text = text.replace(old, new, 1)
text = text.replace("<!-- popup-overlap-wording-fix: 2026-09-21 -->", "")
text = text.replace("</head>", "  <!-- popup-overlap-wording-fix: 2026-09-21 -->\n</head>", 1)
path.write_text(text, encoding="utf-8")
print(f"Patched {path}")
