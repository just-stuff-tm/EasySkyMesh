#!/usr/bin/env python3
"""Decide what the serial build should build.

Reads the upstream EasySkyMesh release (latest, or the tag given), finds the
MeshCore source branch its notes link to, resolves it to a commit, and checks
whether a matching "<tag>-serial" release already exists here.
Writes key=value lines to $GITHUB_OUTPUT.
"""
import hashlib, json, os, re, sys, urllib.request, urllib.error

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")
REPO = os.environ["GITHUB_REPOSITORY"]
IN_TAG = os.environ.get("IN_TAG", "").strip()
IN_SRC = os.environ.get("IN_SOURCE", "").strip()
FORCE = os.environ.get("IN_FORCE", "false").lower() == "true"
HERE = os.path.dirname(os.path.abspath(__file__))

def api(path, ok404=False):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "serial-build", **({"Authorization": "Bearer " + TOKEN} if TOKEN else {})})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if ok404 and e.code == 404:
            return None
        sys.exit(f"GitHub API {path}: HTTP {e.code} {e.read()[:300]!r}")

def out(**kw):
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as f:
        for k, v in kw.items():
            f.write(f"{k}={v}\n")
    for k, v in kw.items():
        print(f"{k}={v}")

me = api(f"/repos/{REPO}")
upstream = (me.get("parent") or {}).get("full_name") or "IoTThinks/EasySkyMesh"
rel = api(f"/repos/{upstream}/releases/tags/{IN_TAG}") if IN_TAG else api(f"/repos/{upstream}/releases/latest")
tag = rel["tag_name"]
body = rel.get("body") or ""

# MeshCore source: "owner/repo@ref", "ref" (IoTThinks/MeshCore), or from the release notes
src_repo, src_ref = "IoTThinks/MeshCore", None
if IN_SRC:
    if "@" in IN_SRC:
        src_repo, src_ref = IN_SRC.split("@", 1)
    else:
        src_ref = IN_SRC
else:
    m = re.search(r"https://github\.com/([\w.-]+/[\w.-]*MeshCore[\w.-]*)/tree/([\w./-]+?)[)\s\]]", body + " ")
    if not m:
        sys.exit(f"Could not find the MeshCore source branch in the notes of {upstream} release {tag}. "
                 "Run the workflow manually with source_ref (e.g. PowerSaving-v18).")
    src_repo, src_ref = m.group(1), m.group(2)
commit = api(f"/repos/{src_repo}/commits/{src_ref}")
sha = commit["sha"]

h = hashlib.sha256()
for root, _, files in sorted(os.walk(HERE)):
    for f in sorted(files):
        if f.endswith((".py", ".h", ".cpp")):
            h.update(open(os.path.join(root, f), "rb").read())
patch_id = h.hexdigest()[:12]

prerelease = bool(IN_SRC and not IN_TAG)   # a custom source build is a preview, not the upstream release
if prerelease:
    tag = re.sub(r"[^\w.-]+", "-", src_ref)
out_tag = f"{tag}-serial"
mine = api(f"/repos/{REPO}/releases/tags/{out_tag}", ok404=True)
same = bool(mine) and f"source-commit: {sha}" in (mine.get("body") or "") and f"patch-id: {patch_id}" in (mine.get("body") or "")
build = FORCE or not same

asset_names = [a["name"] for a in rel.get("assets", [])]
with open("upstream-assets.txt", "w") as f:
    f.write("\n".join(asset_names) + "\n")

out(build=str(build).lower(), upstream=upstream, upstream_tag=tag, upstream_url=rel["html_url"],
    tag=out_tag, source_repo=src_repo, source_ref=src_ref, source_sha=sha, patch_id=patch_id,
    exists=str(bool(mine)).lower(), prerelease=str(prerelease).lower())
if not build:
    print(f"{out_tag} is already built from {src_repo}@{sha[:7]} with patch {patch_id}; nothing to do.")
