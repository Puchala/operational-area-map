from pathlib import Path
import re
import sys


if len(sys.argv) != 2:
    raise SystemExit("Usage: fix_multicircle_popup_behavior.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "<!-- multicircle-popup-fix: 2026-09-21 -->"
if marker in text:
    # Allow the patch script itself to evolve while preserving idempotency on a built page.
    if "layer.eachLayer(childLayer =>" not in text:
        print("MultiCircle popup behavior already patched.")
        raise SystemExit(0)

pattern = re.compile(
    r'''            const centerRow = center && typeof center\.latitude === 'number'.*?\n            const markerCenters = definition\?\.type === 'MultiCircle' ''',
    re.S,
)
match = pattern.search(text)
if not match:
    raise SystemExit("Could not locate the existing popup/center-marker block in index.html")

replacement = '''            const validCenters = definition?.type === 'MultiCircle' && Array.isArray(definition.circles)
              ? definition.circles.map((circle, index) => ({
                  index,
                  center: circle?.center_point,
                  radiusMeters: circle?.radius_meters
                })).filter(item => item.center && typeof item.center.latitude === 'number' && typeof item.center.longitude === 'number' && typeof item.radiusMeters === 'number')
              : [];
            const primaryCenter = center && typeof center.latitude === 'number' && typeof center.longitude === 'number' ? center : null;
            const distanceSquared = (centerPoint, latlng) => {
              const latScale = 111320;
              const lngScale = Math.cos((centerPoint.latitude * Math.PI) / 180) * latScale;
              const dy = (centerPoint.latitude - latlng.lat) * latScale;
              const dx = (centerPoint.longitude - latlng.lng) * lngScale;
              return (dx * dx) + (dy * dy);
            };
            const selectedCircleIndex = latlng => {
              if (!validCenters.length || !latlng) return null;
              let best = validCenters[0];
              let bestDistance = distanceSquared(best.center, latlng);
              validCenters.slice(1).forEach(candidate => {
                const distance = distanceSquared(candidate.center, latlng);
                if (distance < bestDistance) {
                  best = candidate;
                  bestDistance = distance;
                }
              });
              return best.index;
            };
            const buildPopup = selectedIndex => {
              const selected = selectedIndex == null ? null : validCenters.find(item => item.index === selectedIndex);
              const popupCenter = selected?.center || primaryCenter;
              const centerRow = popupCenter
                ? `<div class="popup-row"><strong>Center:</strong> ${escapeHtml(Number(popupCenter.latitude).toFixed(6))}, ${escapeHtml(Number(popupCenter.longitude).toFixed(6))}</div>`
                : '';
              const addressLabel = selected ? `Approx. address (Circle ${selected.index + 1} center)` : (definition?.type === 'MultiCircle' ? 'Approx. address (first center)' : 'Address');
              let definitionRow = '';
              if (definition?.type === 'Circle' && typeof definition.radius_meters === 'number') {
                definitionRow = `<div class="popup-row"><strong>Definition:</strong> Circle — radius ${escapeHtml(formatRadius(definition.radius_meters))}</div>`;
              } else if (definition?.type === 'MultiCircle' && Array.isArray(definition.circles)) {
                definitionRow = `<div class="popup-row"><strong>Definition:</strong> MultiCircle — ${definition.circles.length} circle${definition.circles.length === 1 ? '' : 's'}</div>`;
                if (selected) {
                  definitionRow += `<div class="popup-row"><strong>Selected circle:</strong> Circle ${selected.index + 1} — radius ${escapeHtml(formatRadius(selected.radiusMeters))}</div>`;
                }
                definition.circles.forEach((circle, index) => {
                  if (!circle?.center_point || typeof circle.radius_meters !== 'number') return;
                  const c = circle.center_point;
                  const selectedStyle = selected && selected.index === index ? ' style="font-weight:700"' : '';
                  definitionRow += `<div class="popup-row"${selectedStyle}><strong>Circle ${index + 1}:</strong> ${escapeHtml(Number(c.latitude).toFixed(6))}, ${escapeHtml(Number(c.longitude).toFixed(6))} — ${escapeHtml(formatRadius(circle.radius_meters))}</div>`;
                });
              }
              const effectiveFrom = p.effective_from || null;
              const effectiveTo = p.effective_to || null;
              const effectiveText = effectiveFrom
                ? `${escapeHtml(effectiveFrom)}${effectiveTo ? ` to ${escapeHtml(effectiveTo)}` : ''}`
                : (effectiveTo ? `Until ${escapeHtml(effectiveTo)}` : 'Not specified');
              const addressId = `address-${L.Util.stamp(layer)}-${selected ? selected.index : 'primary'}`;
              return {
                addressId,
                center: popupCenter,
                html: `<div class="popup-title">${escapeHtml(p.operator_id)} · ${escapeHtml(p.site_id)}</div><div class="popup-row"><strong>Locality:</strong> ${escapeHtml(p.metro_locality || 'Not specified')}</div>${selected ? `<div class="popup-row"><strong>Selected circle:</strong> Circle ${selected.index + 1}</div>` : ''}${centerRow}<div class="popup-row"><strong>${addressLabel}:</strong> <span id="${addressId}">${popupCenter ? 'Loading…' : 'Not available'}</span></div>${definitionRow}<div class="popup-row"><strong>Effective:</strong> ${effectiveText}</div><div class="popup-row"><strong>Status:</strong> ${p.potential_overlap ? 'Potential geographic overlap' : 'No detected overlap'}</div>${overlapWith.length ? `<div class="popup-row"><strong>Overlap with:</strong> ${overlapWith.map(escapeHtml).join(', ')}</div>` : ''}${p.coordination_contact ? `<div class="popup-contact"><strong>Coordination contact:</strong><br>${escapeHtml(p.coordination_contact)}</div>` : ''}<div class="popup-note">Informational awareness only — not an authorization or coordination determination. Address is an approximate reverse-geocoded location from the ${selected ? `selected Circle ${selected.index + 1} center` : 'center point'}.</div>`
              };
            };
            const reverseGeocodeForPopup = popupInfo => {
              const element = document.getElementById(popupInfo.addressId);
              if (!element || !popupInfo.center || typeof popupInfo.center.latitude !== 'number' || typeof popupInfo.center.longitude !== 'number') return;
              reverseGeocode(popupInfo.center.latitude, popupInfo.center.longitude)
                .then(address => { element.textContent = address; })
                .catch(error => {
                  console.error('Reverse geocoding failed:', error);
                  element.textContent = 'Address not available';
                });
            };
            const primaryPopup = buildPopup(null);
            layer.bindPopup(primaryPopup.html);

            if (definition?.type === 'MultiCircle' && validCenters.length) {
              layer.on('click', event => {
                const selectedIndex = selectedCircleIndex(event.latlng);
                const popupInfo = buildPopup(selectedIndex);
                layer.bindPopup(popupInfo.html, { autoPan: true });
                layer.openPopup(event.latlng);
                setTimeout(() => reverseGeocodeForPopup(popupInfo), 0);
              });
            } else {
              layer.on('popupopen', () => reverseGeocodeForPopup(primaryPopup));
            }

            const markerCenters = definition?.type === 'MultiCircle' '''

text = text[:match.start()] + replacement + text[match.end():]
text = text.replace('</head>', f'  {marker}\n</head>', 1)
path.write_text(text, encoding='utf-8')
print(f'Patched {path}')