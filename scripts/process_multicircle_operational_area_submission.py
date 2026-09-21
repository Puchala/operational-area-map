#!/usr/bin/env python3
"""Process a MultiCircle operational-area GitHub Issue into a PR."""

import base64
import json
import os
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(__file__))

from process_operational_area_submission import (  # noqa: E402
    api,
    circle_to_polygon,
    clean,
    close_issue,
    comment,
    fail,
    get_file,
    safe_filename,
    same_json,
    strip_code_fence,
)


REPOSITORY = os.environ["GITHUB_REPOSITORY"]
EVENT_PATH = os.environ["GITHUB_EVENT_PATH"]


def extract_submission(body):
    text = strip_code_fence(body)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        marker = "```json"
        start = body.find(marker)
        if start >= 0:
            end = body.find("```", start + len(marker))
            if end >= 0:
                try:
                    return json.loads(body[start + len(marker):end].strip())
                except json.JSONDecodeError:
                    pass
    fail("The issue body does not contain valid JSON submission data.")


def validate_submission(payload):
    if payload.get("submission_type") != "operational_area":
        fail("Unsupported submission type.")
    if payload.get("confirmations", {}).get("minimum_information") is not True:
        fail("Submission confirmation requirements were not satisfied.")
    if payload.get("confirmations", {}).get("authorized") is not True:
        fail("Submission authorization confirmation was not satisfied.")

    operator_id = clean(payload.get("operator_id"))
    site_id = clean(payload.get("site_area_id"))
    metro = clean(payload.get("metro_locality"))
    definition = payload.get("operational_area_definition")
    if not operator_id or not site_id or not metro:
        fail("Operator ID, Site / Area ID, and Metro / Locality are required.")
    if not isinstance(definition, dict) or definition.get("type") != "MultiCircle":
        fail("Operational area definition type must be MultiCircle.")

    circles = definition.get("circles")
    if not isinstance(circles, list) or not circles:
        fail("MultiCircle definition must include at least one circle.")

    normalized = []
    polygons = []
    centers = []
    for index, circle in enumerate(circles, start=1):
        if not isinstance(circle, dict) or circle.get("type") != "Circle":
            fail(f"Circle {index} in MultiCircle must have type Circle.")
        center = circle.get("center_point")
        radius = circle.get("radius_meters")
        if (
            not isinstance(center, dict)
            or isinstance(center.get("latitude"), bool)
            or not isinstance(center.get("latitude"), (int, float))
            or isinstance(center.get("longitude"), bool)
            or not isinstance(center.get("longitude"), (int, float))
        ):
            fail(f"Circle {index} must include a valid center_point.")
        latitude = float(center["latitude"])
        longitude = float(center["longitude"])
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            fail(f"Circle {index} center_point is outside valid latitude/longitude ranges.")
        if (
            isinstance(radius, bool)
            or not isinstance(radius, (int, float))
            or radius <= 0
            or radius > 20000000
        ):
            fail(f"Circle {index} radius_meters must be greater than 0 and no more than 20000000.")

        normalized_center = {"latitude": latitude, "longitude": longitude}
        normalized_circle = {
            "type": "Circle",
            "center_point": normalized_center,
            "radius_meters": round(float(radius), 2),
        }
        normalized.append(normalized_circle)
        centers.append(normalized_center)
        polygons.append(circle_to_polygon(latitude, longitude, float(radius))["coordinates"])

    normalized_definition = {"type": "MultiCircle", "circles": normalized}
    polygon_geometries = [shape({"type": "Polygon", "coordinates": polygon}) for polygon in polygons]
    unioned = unary_union(polygon_geometries)
    geometry = mapping(unioned)
    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        fail("MultiCircle geometry union did not produce a Polygon or MultiPolygon.")
    return operator_id, site_id, metro, normalized_definition, geometry, centers


def main():
    with open(EVENT_PATH, "r", encoding="utf-8") as handle:
        event = json.load(handle)

    issue = event.get("issue") or {}
    issue_number = int(issue["number"])
    issue_url = issue.get("html_url", "")
    body = issue.get("body") or ""
    payload = extract_submission(body)
    operator_id, site_id, metro, definition, geometry, centers = validate_submission(payload)

    safe_operator = safe_filename(operator_id)
    safe_site = safe_filename(site_id)
    if not safe_operator or not safe_site:
        fail("Operator ID and Site / Area ID must contain usable filename characters.")

    bounds = payload.get("geographic_bounds")
    properties = {
        "operator_id": operator_id,
        "site_id": site_id,
        "metro_locality": metro,
        "operational_area_definition": definition,
    }
    if centers:
        properties["center_points"] = centers
    if bounds:
        properties["geographic_bounds"] = bounds

    contact = payload.get("coordination_contact") or {}
    if any(clean(contact.get(key)) for key in ("name", "email", "phone")):
        properties["coordination_contact"] = " | ".join(
            clean(contact.get(key)) for key in ("name", "email", "phone") if clean(contact.get(key))
        )
    if clean(payload.get("effective_from")):
        properties["effective_from"] = clean(payload.get("effective_from"))
    if clean(payload.get("effective_to")):
        properties["effective_to"] = clean(payload.get("effective_to"))

    feature = {"type": "Feature", "properties": properties, "geometry": geometry}
    path = f"operational-areas/{safe_operator}/{safe_site}.geojson"
    branch = f"submission/issue-{issue_number}"

    existing_main = get_file(path, "main")
    if existing_main:
        try:
            existing_text = base64.b64decode(existing_main["content"]).decode("utf-8")
            existing_feature = json.loads(existing_text)
        except (KeyError, ValueError, UnicodeDecodeError) as exc:
            fail(f"Existing operational-area file {path} is not valid JSON: {exc}")
        if same_json(feature, existing_feature):
            comment(issue_number, f"This operational area is already published at {path}. No new Pull Request was created.\n\nPublished source: https://github.com/{REPOSITORY}/blob/main/{path}")
            close_issue(issue_number)
            return

    status, open_prs = api("GET", f"/repos/{REPOSITORY}/pulls?state=open&base=main&per_page=100")
    if status != 200:
        fail(f"Unable to list open pull requests: {open_prs}")
    for pull in open_prs:
        status, files = api("GET", f"/repos/{REPOSITORY}/pulls/{pull['number']}/files?per_page=100")
        if status != 200:
            fail(f"Unable to inspect PR #{pull['number']}: {files}")
        if any(item.get("filename") == path for item in files):
            comment(issue_number, f"An open Pull Request already exists for this operational area: PR #{pull['number']}. No second Pull Request was created.\n\nExisting PR: {pull['html_url']}")
            close_issue(issue_number)
            return

    status, main_ref = api("GET", f"/repos/{REPOSITORY}/git/ref/heads/main")
    if status != 200:
        fail(f"Unable to resolve main branch: {main_ref}")
    main_sha = main_ref["object"]["sha"]
    status, response = api("POST", f"/repos/{REPOSITORY}/git/refs", {"ref": f"refs/heads/{branch}", "sha": main_sha})
    if status not in (201, 422):
        fail(f"Unable to create submission branch {branch}: {response}")

    content = json.dumps(feature, indent=2) + "\n"
    existing_branch = get_file(path, branch)
    write_payload = {
        "message": f"{'Update' if existing_main else 'Add'} operational area from submission #{issue_number}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if existing_branch:
        write_payload["sha"] = existing_branch["sha"]
    status, response = api("PUT", f"/repos/{REPOSITORY}/contents/{path}", write_payload)
    if status not in (200, 201):
        fail(f"Unable to write {path} on {branch}: {response}")

    action_word = "Update" if existing_main else "Publish"
    pr_payload = {
        "title": f"{action_word} operational area: {operator_id} / {site_id}",
        "head": branch,
        "base": "main",
        "draft": False,
        "body": (
            "## Automated MultiCircle operational-area submission\n\n"
            f"This PR was generated from Issue #{issue_number}: {issue_url}.\n\n"
            f"- Operator: {operator_id}\n- Site / Area: {site_id}\n- Metro / Locality: {metro}\n"
            f"- Circle count: {len(definition['circles'])}\n\n"
            "### Review checklist\n"
            "- [ ] Every circle center and radius represents only the intended operational area.\n"
            "- [ ] Minimum-necessary information principle is satisfied.\n"
            "- [ ] No routes, trajectories, customer data, volumes, or sensitive strategy are included.\n"
            "- [ ] Automated validation passes.\n"
            "- [ ] Potential overlap has been reviewed as an awareness signal only.\n\n"
            "The GeoJSON Polygon/MultiPolygon is an interoperability representation; the exact MultiCircle definition is preserved in feature properties."
        ),
    }
    status, pr = api("POST", f"/repos/{REPOSITORY}/pulls", pr_payload)
    if status not in (200, 201):
        fail(f"Unable to create pull request: {pr}")

    dispatch_payload = {
        "event_type": "operational-area-submission",
        "client_payload": {
            "pr_number": pr["number"],
            "head_sha": pr["head"]["sha"],
            "head_ref": pr["head"]["ref"],
            "issue_number": issue_number,
        },
    }
    status, response = api("POST", f"/repos/{REPOSITORY}/dispatches", dispatch_payload)
    if status != 204:
        fail(f"Unable to trigger validation workflow for PR #{pr['number']}: {response}")

    comment(issue_number, f"Submission processed. Pull Request #{pr['number']} was created.\n\nPR: {pr['html_url']}")
    close_issue(issue_number)
    print(f"Created PR #{pr['number']}: {pr['html_url']}")


if __name__ == "__main__":
    main()
