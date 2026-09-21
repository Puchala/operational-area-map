#!/usr/bin/env python3
"""Keep operational-area popups intentionally minimal: locality, center, address, and contact."""

from pathlib import Path
import sys

MARKER = "<!-- simplified-operational-area-popup: 2026-09-21 -->"
START = "            const buildPopup = selected => {"
END = "            let activePopupInfo = buildPopup(null);"

REPLACEMENT = r'''            const buildPopup = selected => {
              let popupCenter = selected?.center || null;
              if (!popupCenter && selected?.type === 'Circle' && definition?.center_point) {
                popupCenter = definition.center_point;
              }
              if (!popupCenter && selected?.type === 'Polygon' && polygonChildLayers[selected.index]) {
                const center = polygonChildLayers[selected.index].getBounds().getCenter();
                popupCenter = { latitude: center.lat, longitude: center.lng };
              }
              if (!popupCenter && definition?.type === 'MultiCircle' && validCenters.length) {
                popupCenter = validCenters[0].center;
              }
              // Some published demo polygons do not carry an explicit center_point.
              // Use the rendered feature bounds as the deterministic fallback so
              // Center and address are still available for every operational area.
              if (!popupCenter && layer?.getBounds) {
                const bounds = layer.getBounds();
                if (bounds && bounds.isValid()) {
                  const center = bounds.getCenter();
                  popupCenter = { latitude: center.lat, longitude: center.lng };
                }
              }

              const centerRow = popupCenter
                ? `<div class="popup-row"><strong>Center:</strong> ${escapeHtml(Number(popupCenter.latitude).toFixed(6))}, ${escapeHtml(Number(popupCenter.longitude).toFixed(6))}</div>`
                : '';
              const addressId = `address-${L.Util.stamp(layer)}-${selected ? `${selected.type}-${selected.index}` : 'primary'}`;
              const addressLabel = selected?.type === 'Circle'
                ? `Address (Circle ${selected.index + 1} center)`
                : 'Address';

              return {
                addressId,
                center: popupCenter,
                html: `<div class="popup-title">${escapeHtml(p.operator_id)} · ${escapeHtml(p.site_id)}</div><div class="popup-row"><strong>Locality:</strong> ${escapeHtml(p.metro_locality || 'Not specified')}</div>${centerRow}<div class="popup-row"><strong>${addressLabel}:</strong> <span id="${addressId}">Looking up…</span></div>${p.coordination_contact ? `<div class="popup-contact"><strong>Coordination contact:</strong><br>${escapeHtml(p.coordination_contact)}</div>` : ''}`
              };
            };
'''


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: simplify_operational_area_popup.py <index.html>")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print("Minimal operational-area popup already present; nothing to do.")
        return

    start = text.find(START)
    end = text.find(END, start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate generated popup builder")

    text = text[:start] + REPLACEMENT + text[end:]
    text = text.replace("</head>", f"  {MARKER}\n</head>", 1)
    path.write_text(text, encoding="utf-8")
    print("Applied minimal operational-area popup.")


if __name__ == "__main__":
    main()
