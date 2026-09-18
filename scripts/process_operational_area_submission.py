#!/usr/bin/env python3
"""Process a structured operational-area GitHub Issue into a PR."""

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request


API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
REPOSITORY = os.environ["GITHUB_REPOSITORY"]
EVENT_PATH = os.environ["GITHUB_EVENT_PATH"]


def api(method, path, payload=None):
    url = API + path
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "operational-area-map-submission",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"message": raw}
        return exc.code, detail


def fail(message):
    print(f"::error::{message}")
    raise SystemExit(1)


def clean(value):
    return (value or "").replace("\r", "").strip()


def strip_code_fence(value):
    value = clean(value)
    fence = chr(96) * 3
    if value.startswith(fence):
        value = value[len(fence):].lstrip()
        if value.lower().startswith("json"):
            value = value[4:].lstrip()
        if value.endswith(fence):
            value = value[:-len(fence)].rstrip()
    return value.strip()


def field(body, label, required=False):
    marker = f"### {label}"
    start = body.find(marker)
    if start < 0:
        if required:
            fail(f"Missing required field: {label}")
        return ""

    value_start = start + len(marker)
    next_heading = body.find("\n### ", value_start)
    value = body[value_start:] if next_heading < 0 else body[value_start:next_heading]
    value = value.strip()

    if required and not value:
        fail(f"Missing required field: {label}")
    return value


def stable(value):
    if isinstance(value, list):
        return [stable(item) for item in value]
    if isinstance(value, dict):
        return {key: stable(value[key]) for key in sorted(value)}
    return value


def same_json(left, right):
    return stable(left) == stable(right)


def safe_filename(value):
    value = re.sub(r"[^A-Za-z0-9._-]", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80]


def comment(issue_number, message):
    status, response = api(
        "POST",
        f"/repos/{REPOSITORY}/issues/{issue_number}/comments",
        {"body": message},
    )
    if status not in (200, 201):
        fail(f"Unable to comment on Issue #{issue_number}: {response}")


def close_issue(issue_number):
    status, response = api(
        "PATCH",
        f"/repos/{REPOSITORY}/issues/{issue_number}",
        {"state": "closed", "state_reason": "completed"},
    )
    if status != 200:
        fail(f"Unable to close Issue #{issue_number}: {response}")


def get_file(path, ref):
    encoded_path = urllib.parse.quote(path, safe="/")
    encoded_ref = urllib.parse.quote(ref, safe="")
    status, response = api(
        "GET",
        f"/repos/{REPOSITORY}/contents/{encoded_path}?ref={encoded_ref}",
    )
    if status == 404:
        return None
    if status != 200:
        fail(f"Unable to read {path} from {ref}: {response}")
    if isinstance(response, list):
        fail(f"Expected {path} to be a file, but GitHub returned a directory.")
    return response


def main():
    with open(EVENT_PATH, "r", encoding="utf-8") as handle:
        event = json.load(handle)

    issue = event.get("issue") or {}
    issue_number = int(issue["number"])
    issue_url = issue.get("html_url", "")
    body = issue.get("body") or ""

    operator_id = clean(field(body, "Operator ID", required=True))
    site_id = clean(field(body, "Site / Area ID", required=True))
    metro = clean(field(body, "Metro / Locality", required=True))
    geometry_raw = strip_code_fence(field(body, "Operational Area Geometry", required=True))
    center_raw = clean(field(body, "Center Point (optional)"))
    bounds_raw = strip_code_fence(field(body, "Geographic Bounds (optional)"))
    contact_name = clean(field(body, "Coordination Contact Name (optional)"))
    contact_email = clean(field(body, "Coordination Contact Email (optional)"))
    contact_phone = clean(field(body, "Coordination Contact Phone (optional)"))
    effective_from = clean(field(body, "Effective From (optional)"))
    effective_to = clean(field(body, "Effective To (optional)"))

    try:
        geometry = json.loads(geometry_raw)
    except json.JSONDecodeError:
        fail("Operational Area Geometry is not valid JSON.")

    if (
        not isinstance(geometry, dict)
        or geometry.get("type") not in ("Polygon", "MultiPolygon")
        or not isinstance(geometry.get("coordinates"), list)
    ):
        fail("Geometry must be a GeoJSON Polygon or MultiPolygon.")

    bounds = None
    if bounds_raw:
        try:
            bounds = json.loads(bounds_raw)
        except json.JSONDecodeError:
            fail("Geographic Bounds must be valid JSON.")

    center_point = None
    if center_raw:
        parts = [part.strip() for part in center_raw.split(",")]
        if len(parts) != 2:
            fail("Center Point must be latitude,longitude.")
        try:
            center_point = {
                "latitude": float(parts[0]),
                "longitude": float(parts[1]),
            }
        except ValueError:
            fail("Center Point must be latitude,longitude.")

    safe_operator = safe_filename(operator_id)
    safe_site = safe_filename(site_id)
    if not safe_operator or not safe_site:
        fail("Operator ID and Site / Area ID must contain usable filename characters.")

    properties = {
        "operator_id": operator_id,
        "site_id": site_id,
        "metro_locality": metro,
    }

    if center_point is not None:
        properties["center_point"] = center_point
    if bounds is not None:
        properties["geographic_bounds"] = bounds
    if contact_name or contact_email or contact_phone:
        contact_parts = [part for part in (contact_name, contact_email, contact_phone) if part]
        properties["coordination_contact"] = " | ".join(contact_parts)
    if effective_from:
        properties["effective_from"] = effective_from
    if effective_to:
        properties["effective_to"] = effective_to

    feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry,
    }

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
            comment(
                issue_number,
                (
                    f"This operational area is already published at {path}. "
                    "No new Pull Request was created because the submitted data "
                    "matches the existing published area.\n\n"
                    f"Published source: https://github.com/{REPOSITORY}/blob/main/{path}"
                ),
            )
            close_issue(issue_number)
            print(f"Duplicate submission detected for {path}; no PR created.")
            return

    status, open_prs = api(
        "GET",
        f"/repos/{REPOSITORY}/pulls?state=open&base=main&per_page=100",
    )
    if status != 200:
        fail(f"Unable to list open pull requests: {open_prs}")

    for pull in open_prs:
        pr_number = pull["number"]
        status, files = api(
            "GET",
            f"/repos/{REPOSITORY}/pulls/{pr_number}/files?per_page=100",
        )
        if status != 200:
            fail(f"Unable to inspect PR #{pr_number}: {files}")

        if any(item.get("filename") == path for item in files):
            comment(
                issue_number,
                (
                    f"An open Pull Request already exists for this operational area: "
                    f"PR #{pr_number}. No second Pull Request was created.\n\n"
                    f"Existing PR: {pull['html_url']}"
                ),
            )
            close_issue(issue_number)
            print(f"Open PR #{pr_number} already changes {path}; no PR created.")
            return

    status, main_ref = api("GET", f"/repos/{REPOSITORY}/git/ref/heads/main")
    if status != 200:
        fail(f"Unable to resolve main branch: {main_ref}")
    main_sha = main_ref["object"]["sha"]

    status, response = api(
        "POST",
        f"/repos/{REPOSITORY}/git/refs",
        {"ref": f"refs/heads/{branch}", "sha": main_sha},
    )
    if status not in (201, 422):
        fail(f"Unable to create submission branch {branch}: {response}")

    content = json.dumps(feature, indent=2) + "\n"
    existing_branch = get_file(path, branch)

    payload = {
        "message": (
            f"Update operational area from submission #{issue_number}"
            if existing_main
            else f"Add operational area from submission #{issue_number}"
        ),
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if existing_branch:
        payload["sha"] = existing_branch["sha"]

    status, response = api(
        "PUT",
        f"/repos/{REPOSITORY}/contents/{urllib.parse.quote(path, safe='/')}",
        payload,
    )
    if status not in (200, 201):
        fail(f"Unable to write {path} on {branch}: {response}")

    action_word = "Update" if existing_main else "Publish"
    pr_payload = {
        "title": f"{action_word} operational area: {operator_id} / {site_id}",
        "head": branch,
        "base": "main",
        "draft": False,
        "body": (
            "## Automated operational-area submission\n\n"
            f"This PR was generated from Issue #{issue_number}: {issue_url}.\n\n"
            "### Proposed area\n"
            f"- Operator: {operator_id}\n"
            f"- Site / Area: {site_id}\n"
            f"- Metro / Locality: {metro}\n"
            "- Source: Operator submission form\n\n"
            "### Review checklist\n"
            "- [ ] Geometry is correct and represents only the intended operational area.\n"
            "- [ ] Minimum-necessary information principle is satisfied.\n"
            "- [ ] No routes, trajectories, customer data, volumes, or sensitive strategy are included.\n"
            "- [ ] Contact information is appropriate for publication.\n"
            "- [ ] Effective dates are correct, if supplied.\n"
            "- [ ] Automated validation passes.\n"
            "- [ ] Potential overlap has been reviewed as an awareness signal only.\n\n"
            "Publication is automatic when the required CI validation passes."
        ),
    }

    status, pr = api("POST", f"/repos/{REPOSITORY}/pulls", pr_payload)
    if status not in (200, 201):
        fail(f"Unable to create pull request: {pr}")

    comment(
        issue_number,
        (
            f"Submission processed. Pull Request #{pr['number']} was created. "
            "The area will be published automatically when the required CI validation passes.\n\n"
            f"PR: {pr['html_url']}"
        ),
    )
    close_issue(issue_number)
    print(f"Created PR #{pr['number']}: {pr['html_url']}")


if __name__ == "__main__":
    main()
