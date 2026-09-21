#!/usr/bin/env python3
"""Fix circle-builder input state during the GitHub Pages build.

After a circle is added, refresh() repopulates the input fields from the last
existing circle. That makes a second click on Add Circle duplicate the previous
circle when the user has not intentionally changed the fields. Clear the
builder inputs after refresh so every additional circle requires explicit input.
"""

from pathlib import Path
import sys

OLD = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"
NEW = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_circle_input_state.py <html-file>")
    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8")
    if OLD not in html:
        raise SystemExit("Expected circle creation statement was not found; refusing to modify the page.")
    # The source currently clears before refresh. Move the clear after refresh.
    old = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"
    new = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"
    # Apply a precise semantic replacement of the function statement if needed.
    source = html
    target = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"
    replacement = "drawn.addLayer(circle); map.fitBounds(circle.getBounds(), { padding: [24, 24] }); refresh(); clearCircleInputs();"
    if target != replacement:
        source = source.replace(target, replacement, 1)
    # The intended behavior is already represented by the ordering above in
    # this published source; keep this script as a guard for future builds.
    path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
