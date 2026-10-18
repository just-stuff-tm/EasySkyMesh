#!/usr/bin/env python3
"""Build list = envs in build-iotthinks.sh + envs that appear in the upstream
release's asset names, limited to envs that exist in the source tree.
Usage: matrix.py <meshcore-dir> <upstream-assets.txt>  -> JSON array on stdout"""
import glob, json, os, re, subprocess, sys
root, assets = sys.argv[1], sys.argv[2]
defined = set()
for ini in [os.path.join(root, "platformio.ini")] + glob.glob(os.path.join(root, "variants", "*", "*.ini")):
    defined |= set(re.findall(r"^\[env:([^\]]+)\]", open(ini, encoding="utf-8", errors="ignore").read(), re.M))
listed = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "list-envs.py"), root], capture_output=True, text=True).stdout.split()
from_assets = []
for n in open(assets).read().split():
    m = re.match(r"(.+?)-(?:PowerSaving|v\d)", n)
    if m: from_assets.append(m.group(1))
envs, seen = [], set()
for e in listed + from_assets:
    if e in defined and e not in seen:
        seen.add(e); envs.append(e)
missing = sorted(set(listed + from_assets) - defined)
if missing:
    print("skipping envs not defined in this source: " + ", ".join(missing), file=sys.stderr)
if not envs:
    sys.exit("no envs to build")
print(json.dumps(envs))
