from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: fix_address_lookup.py <html>")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Replace the entire geocoding block using stable structural anchors. This is
# intentionally independent of whether the source function is async or not,
# because earlier UI patches may change that implementation detail.
start_marker = "    const geocodeCache = new Map();"
end_marker = "    fetch('operational-areas.geojson'"
start = text.find(start_marker)
end = text.find(end_marker, start + len(start_marker)) if start >= 0 else -1
if start < 0 or end < 0:
    raise SystemExit("Could not locate reverse-geocoding block")

replacement = '''    const geocodeCache = new Map();
    const geocodeStorageKey = 'oam-reverse-geocode-v1';
    let lastGeocodeAt = 0;

    function loadStoredGeocodes() {
      try {
        const stored = JSON.parse(localStorage.getItem(geocodeStorageKey) || '{}');
        Object.entries(stored).forEach(([key, value]) => {
          if (typeof value === 'string' && value) geocodeCache.set(key, Promise.resolve(value));
        });
      } catch (error) {
        console.warn('Unable to read address cache:', error);
      }
    }

    function storeGeocode(key, value) {
      try {
        const stored = JSON.parse(localStorage.getItem(geocodeStorageKey) || '{}');
        stored[key] = value;
        const keys = Object.keys(stored);
        if (keys.length > 250) delete stored[keys[0]];
        localStorage.setItem(geocodeStorageKey, JSON.stringify(stored));
      } catch (error) {
        console.warn('Unable to persist address cache:', error);
      }
    }

    loadStoredGeocodes();

    function formatAddress(address, displayName) {
      if (!address) return displayName || 'Address not available';
      const parts = [
        address.house_number && address.road ? `${address.house_number} ${address.road}` : address.road,
        address.neighbourhood || address.suburb,
        address.city || address.town || address.village || address.municipality,
        address.state,
        address.postcode
      ].filter(Boolean);
      return parts.join(', ') || displayName || 'Address not available';
    }

    function reverseGeocode(lat, lng) {
      const key = `${Number(lat).toFixed(6)},${Number(lng).toFixed(6)}`;
      if (geocodeCache.has(key)) return geocodeCache.get(key);

      const promise = (async () => {
        const waitMs = Math.max(0, 1100 - (Date.now() - lastGeocodeAt));
        if (waitMs) await new Promise(resolve => setTimeout(resolve, waitMs));
        lastGeocodeAt = Date.now();

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 7000);
        try {
          const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&zoom=18&addressdetails=1`;
          const response = await fetch(url, {
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
          });
          if (!response.ok) throw new Error(`Reverse geocoding returned HTTP ${response.status}`);
          const result = await response.json();
          const address = formatAddress(result.address, result.display_name);
          storeGeocode(key, address);
          return address;
        } finally {
          clearTimeout(timeout);
        }
      })();

      geocodeCache.set(key, promise);
      promise.catch(() => {
        if (geocodeCache.get(key) === promise) geocodeCache.delete(key);
      });
      return promise;
    }

'''
text = text[:start] + replacement + text[end:]

marker = '<!-- address-lookup-hardening: 2026-09-21 -->'
text = re.sub(r'\n\s*<!-- address-lookup-hardening: 2026-09-21 -->', '', text)
text = text.replace('</head>', f'  {marker}\n</head>', 1)
path.write_text(text, encoding="utf-8")
print(f"Patched {path}")
