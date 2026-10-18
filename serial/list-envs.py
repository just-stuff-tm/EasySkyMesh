#!/usr/bin/env python3
"""Print the PlatformIO envs upstream releases, read from build-iotthinks.sh
(the list IoTThinks uses for EasySkyMesh releases). Falls back to build.sh's
repeater/room server/companion lists when that file is missing."""
import os, re, subprocess, sys
root = sys.argv[1] if len(sys.argv) > 1 else "."
p = os.path.join(root, "build-iotthinks.sh")
envs = []
if os.path.exists(p):
    cont = False
    for raw in open(p, encoding="utf-8"):
        line = raw.split("#", 1)[0].rstrip()
        if re.match(r'^\s*(sh|bash)\s+build\.sh\s+build-firmware\b', line):
            rest = re.sub(r'^\s*(sh|bash)\s+build\.sh\s+build-firmware', '', line)
            cont = rest.endswith("\\")
            envs += rest.rstrip("\\").split()
            continue
        if cont:
            cont = line.endswith("\\")
            envs += line.rstrip("\\").split()
if not envs:
    for kind in ("repeater", "room-server", "companion"):
        out = subprocess.run(["bash", "build.sh", f"get-{kind}-firmwares-to-build"], cwd=root, capture_output=True, text=True).stdout
        envs += out.split()
seen = set()
for e in envs:
    if e not in seen:
        seen.add(e); print(e)
