from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: fix_geometry_overlap_ui.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "<!-- geometry-overlap-ui-fix: 2026-09-21 -->"

pattern = re.compile(
    r'''            const validCenters = definition\?\.type === 'MultiCircle'.*?\n            const markerCenters = definition\?\.type === 'MultiCircle' ''',
    re.S,
)
match = pattern.search(text)
if not match:
    raise SystemExit("Could not locate the generated popup block")

replacement = '''            const validCenters = definition?.type === 'MultiCircle' && Array.isArray(definition.circles)
              ? definition.circles.map((circle, index) => ({
                  type: 'Circle', index,
                  center: circle?.center_point,
                  radiusMeters: circle?.radius_meters
                })).filter(item => item.center && Number.isFinite(Number(item.center.latitude)) && Number.isFinite(Number(item.center.longitude)) && Number.isFinite(Number(item.radiusMeters)))
              : [];
            const polygonChildLayers = definition?.type !== 'Circle' && definition?.type !== 'MultiCircle' && typeof layer.getLayers === 'function'
              ? layer.getLayers().filter(child => typeof child.getBounds === 'function')
              : [];
            const distanceSquared = (centerPoint, latlng) => {
              const latScale = 111320;
              const lngScale = Math.cos((Number(centerPoint.latitude) * Math.PI) / 180) * latScale;
              const dy = (Number(centerPoint.latitude) - latlng.lat) * latScale;
              const dx = (Number(centerPoint.longitude) - latlng.lng) * lngScale;
              return (dx * dx) + (dy * dy);
            };
            const selectedCircleIndex = latlng => {
              if (!validCenters.length || !latlng) return null;
              let best = validCenters[0];
              let bestDistance = distanceSquared(best.center, latlng);
              validCenters.slice(1).forEach(candidate => {
                const distance = distanceSquared(candidate.center, latlng);
                if (distance < bestDistance) { best = candidate; bestDistance = distance; }
              });
              return best.index;
            };
            const selectedPolygonIndex = (latlng, targetLayer) => {
              if (!polygonChildLayers.length) return 0;
              const directIndex = polygonChildLayers.indexOf(targetLayer);
              if (directIndex >= 0) return directIndex;
              let bestIndex = 0;
              let bestDistance = Infinity;
              polygonChildLayers.forEach((child, index) => {
                const bounds = child.getBounds();
                if (bounds.contains(latlng)) { bestIndex = index; bestDistance = -1; return; }
                if (bestDistance < 0) return;
                const distance = map.distance(bounds.getCenter(), latlng);
                if (distance < bestDistance) { bestIndex = index; bestDistance = distance; }
              });
              return bestIndex;
            };
            const getComponentOverlaps = selected => {
              if (!selected) return [];
              const details = Array.isArray(p.potential_overlap_components) ? p.potential_overlap_components : [];
              return details.filter(item => item.component_type === selected.type && Number(item.component_index) === selected.index + 1);
            };
            const buildPopup = selected => {
              const selectedOverlaps = getComponentOverlaps(selected);
              let popupCenter = selected?.center || null;
              if (!popupCenter && selected?.type === 'Polygon' && polygonChildLayers[selected.index]) {
                const center = polygonChildLayers[selected.index].getBounds().getCenter();
                popupCenter = { latitude: center.lat, longitude: center.lng };
              }
              const centerRow = popupCenter
                ? `<div class="popup-row"><strong>Center:</strong> ${escapeHtml(Number(popupCenter.latitude).toFixed(6))}, ${escapeHtml(Number(popupCenter.longitude).toFixed(6))}</div>`
                : '';
              let definitionRow = '';
              if (definition?.type === 'Circle' && typeof definition.radius_meters === 'number') {
                definitionRow = `<div class="popup-row"><strong>Definition:</strong> Circle — radius ${escapeHtml(formatRadius(definition.radius_meters))}</div>`;
              } else if (definition?.type === 'MultiCircle' && Array.isArray(definition.circles)) {
                definitionRow = `<div class="popup-row"><strong>Definition:</strong> MultiCircle — ${definition.circles.length} circle${definition.circles.length === 1 ? '' : 's'}</div>`;
                if (selected) {
                  definitionRow += `<div class="popup-row"><strong>Selected circle:</strong> Circle ${selected.index + 1} — radius ${escapeHtml(formatRadius(selected.radiusMeters))}</div>`;
                  definitionRow += selectedOverlaps.length
                    ? `<div class="popup-row"><strong>Circle status:</strong> Potential geographic overlap</div><div class="popup-row"><strong>Overlapping with:</strong> ${selectedOverlaps.map(item => `${escapeHtml(item.other_operator_id)} · ${escapeHtml(item.other_site_id)} (${escapeHtml(item.other_component_type)} ${item.other_component_index})`).join(', ')}</div>`
                    : `<div class="popup-row"><strong>Circle status:</strong> No detected overlap</div>`;
                }
                definition.circles.forEach((circle, index) => {
                  if (!circle?.center_point || typeof circle.radius_meters !== 'number') return;
                  const c = circle.center_point;
                  const selectedStyle = selected && selected.type === 'Circle' && selected.index === index ? ' style="font-weight:700"' : '';
                  definitionRow += `<div class="popup-row"${selectedStyle}><strong>Circle ${index + 1}:</strong> ${escapeHtml(Number(c.latitude).toFixed(6))}, ${escapeHtml(Number(c.longitude).toFixed(6))} — ${escapeHtml(formatRadius(circle.radius_meters))}</div>`;
                });
              } else if (selected?.type === 'Polygon' && polygonChildLayers.length > 1) {
                definitionRow = `<div class="popup-row"><strong>Selected geometry:</strong> Polygon part ${selected.index + 1} of ${polygonChildLayers.length}</div>`;
                definitionRow += selectedOverlaps.length
                  ? `<div class="popup-row"><strong>Part status:</strong> Potential geographic overlap</div><div class="popup-row"><strong>Overlapping with:</strong> ${selectedOverlaps.map(item => `${escapeHtml(item.other_operator_id)} · ${escapeHtml(item.other_site_id)} (${escapeHtml(item.other_component_type)} ${item.other_component_index})`).join(', ')}</div>`
                  : `<div class="popup-row"><strong>Part status:</strong> No detected overlap</div>`;
              }
              const effectiveFrom = p.effective_from || null;
              const effectiveTo = p.effective_to || null;
              const effectiveText = effectiveFrom
                ? `${escapeHtml(effectiveFrom)}${effectiveTo ? ` to ${escapeHtml(effectiveTo)}` : ''}`
                : (effectiveTo ? `Until ${escapeHtml(effectiveTo)}` : 'Not specified');
              const areaStatus = p.potential_overlap ? 'Potential geographic overlap' : 'No detected overlap';
              const addressId = `address-${L.Util.stamp(layer)}-${selected ? `${selected.type}-${selected.index}` : 'primary'}`;
              const addressLabel = selected
                ? (selected.type === 'Circle' ? `Approx. address (Circle ${selected.index + 1} center)` : 'Approx. address (selected part)')
                : (definition?.type === 'MultiCircle' ? 'Approx. address (first center)' : 'Address');
              return {
                addressId,
                center: popupCenter,
                html: `<div class="popup-title">${escapeHtml(p.operator_id)} · ${escapeHtml(p.site_id)}</div><div class="popup-row"><strong>Locality:</strong> ${escapeHtml(p.metro_locality || 'Not specified')}</div>${selected ? `<div class="popup-row"><strong>Selected:</strong> ${selected.type === 'Circle' ? `Circle ${selected.index + 1}` : `Polygon part ${selected.index + 1}`}</div>` : ''}${centerRow}<div class="popup-row"><strong>${addressLabel}:</strong> <span id="${addressId}">Looking up…</span></div>${definitionRow}<div class="popup-row"><strong>Operational-area status:</strong> ${areaStatus}</div>${overlapWith.length ? `<div class="popup-row"><strong>Area-level overlap with:</strong> ${overlapWith.map(escapeHtml).join(', ')}</div>` : ''}${p.coordination_contact ? `<div class="popup-contact"><strong>Coordination contact:</strong><br>${escapeHtml(p.coordination_contact)}</div>` : ''}<div class="popup-note">Informational awareness only — not an authorization or coordination determination. Address is an approximate reverse-geocoded location from the ${selected ? (selected.type === 'Circle' ? `selected Circle ${selected.index + 1} center` : 'selected polygon part') : 'center point'}.</div>`
              };
            };
            let activePopupInfo = buildPopup(null);
            layer.bindPopup(activePopupInfo.html);
            const openSelectedPopup = (selected, event) => {
              activePopupInfo = buildPopup(selected);
              layer.bindPopup(activePopupInfo.html, { autoPan: true });
              layer.openPopup(event?.latlng);
            };
            if (definition?.type === 'MultiCircle' && validCenters.length) {
              layer.on('click', event => {
                const index = selectedCircleIndex(event.latlng);
                openSelectedPopup(validCenters.find(item => item.index === index) || null, event);
              });
            } else if (polygonChildLayers.length > 1) {
              polygonChildLayers.forEach((child, index) => {
                child.on('click', event => {
                  openSelectedPopup({ type: 'Polygon', index }, event);
                  if (event.originalEvent) L.DomEvent.stopPropagation(event.originalEvent);
                });
              });
            } else if (definition?.type === 'Circle') {
              layer.on('click', event => {
                openSelectedPopup({ type: 'Circle', index: 0, center: definition.center_point, radiusMeters: definition.radius_meters }, event);
              });
            }
            layer.on('popupopen', () => {
              requestAnimationFrame(() => reverseGeocodeForPopup(activePopupInfo));
            });

            const markerCenters = definition?.type === 'MultiCircle' '''

text = text[:match.start()] + replacement + text[match.end():]
text = text.replace('</head>', f'  {marker}\n</head>', 1)
path.write_text(text, encoding='utf-8')
print(f'Patched {path}')
