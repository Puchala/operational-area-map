#!/usr/bin/env python3
"""Patch the published submission page to prevent duplicate circles."""

from pathlib import Path
import re
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_circle_input_state.py <html-file>")
    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8")

    pattern = r"  function createCircleFromValues\(\) \{.*?\n  \}\n  function renderCircleList\(\)"
    replacement = '''  function createCircleFromValues() {
    setCircleBuilderStatus('');
    const lat = Number(circleLatitude.value), lng = Number(circleLongitude.value), radiusValue = Number(circleRadius.value);
    if (!Number.isFinite(lat) || lat < -90 || lat > 90) { setCircleBuilderStatus('Enter a valid latitude between -90 and 90.'); circleLatitude.focus(); return; }
    if (!Number.isFinite(lng) || lng < -180 || lng > 180) { setCircleBuilderStatus('Enter a valid longitude between -180 and 180.'); circleLongitude.focus(); return; }
    if (!Number.isFinite(radiusValue) || radiusValue <= 0) { setCircleBuilderStatus('Enter a radius greater than 0.'); circleRadius.focus(); return; }
    let radiusMeters = radiusValue; if (circleRadiusUnit.value === 'km') radiusMeters *= 1000; if (circleRadiusUnit.value === 'mi') radiusMeters *= 1609.344;
    if (!Number.isFinite(radiusMeters) || radiusMeters <= 0 || radiusMeters > 20000000) { setCircleBuilderStatus('Radius must be greater than 0 and no more than 20,000 km.'); circleRadius.focus(); return; }
    const duplicate = getCircleLayers().some(layer => {
      const c = layer.getLatLng();
      return Math.abs(c.lat - lat) < 1e-7 && Math.abs(c.lng - lng) < 1e-7 && Math.abs(layer.getRadius() - radiusMeters) < 0.01;
    });
    if (duplicate) { setCircleBuilderStatus('This circle is already added. Enter a different center point or radius.'); return; }
    const circle = L.circle([lat, lng], { radius: radiusMeters }); drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();
  }
  function renderCircleList()'''

    patched, count = re.subn(pattern, replacement, html, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Expected createCircleFromValues function was not found; refusing to modify the page.")
    path.write_text(patched, encoding="utf-8")


if __name__ == "__main__":
    main()
