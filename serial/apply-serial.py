#!/usr/bin/env python3
"""Apply the serial-in-PowerSaving change to a MeshCore / PowerSaving source tree.

Usage: python3 apply-serial.py <meshcore-source-dir>
Idempotent. Copies two new files and adds three one-line hooks found by anchors
(not line numbers), so it keeps working when upstream edits the surrounding code.
Exits non-zero (and says why) if any anchor is missing, so CI never ships a build
without the serial change.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
root = sys.argv[1] if len(sys.argv) > 1 else "."
errors = []

def edit(rel, fn):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        errors.append(f"{rel}: file not found"); return
    s = open(p, encoding="utf-8").read()
    if "SerialWake" in s:
        print(f"= {rel}: already patched"); return
    out = fn(s)
    if out is None: return
    open(p, "w", encoding="utf-8").write(out)
    print(f"+ {rel}: patched")

def insert_after(s, pattern, text, what, rel):
    m = re.search(pattern, s, re.M)
    if not m:
        errors.append(f"{rel}: anchor not found: {what}"); return None
    e = s.index("\n", m.end()) + 1 if "\n" in s[m.end():] else len(s)
    return s[:e] + text + s[e:]

def insert_before_line(s, pattern, text, what, rel):
    m = re.search(pattern, s, re.M)
    if not m:
        errors.append(f"{rel}: anchor not found: {what}"); return None
    b = s.rfind("\n", 0, m.start()) + 1
    return s[:b] + text + s[b:]

# 1. new files
for f in ("SerialWake.h", "SerialWake.cpp"):
    dst = os.path.join(root, "src", "helpers", f)
    if not os.path.isdir(os.path.dirname(dst)):
        errors.append("src/helpers: directory not found"); break
    shutil.copyfile(os.path.join(HERE, "src", "helpers", f), dst)
    print(f"+ src/helpers/{f}: copied")

# 2. ESP32 light sleep: stay awake while the serial CLI is in use, wake on UART RX
def esp32(s):
    rel = "src/helpers/ESP32Board.h"
    s = insert_after(s, r'^#include\s*<Arduino\.h>', '#include <helpers/SerialWake.h>  // serial-in-PowerSaving\n', "#include <Arduino.h>", rel)
    if s is None: return None
    m = re.search(r'void\s+sleep\s*\(\s*uint32_t\s+secs\s*\)\s*override\s*\{', s)
    if not m:
        errors.append(f"{rel}: anchor not found: void sleep(uint32_t secs) override {{"); return None
    head, body = s[:m.end()], s[m.end():]
    body = insert_before_line(body, r'^\s*gpio_num_t\s+wakeupPin\s*=', '    if (SerialWake::beforeSleep()) { delay(1); return; }  // serial CLI in use (serial-in-PowerSaving)\n', "gpio_num_t wakeupPin = ... in sleep()", rel)
    if body is None: return None
    body = insert_after(body, r'^\s*esp_light_sleep_start\(\);', '    SerialWake::afterSleep();  // serial-in-PowerSaving\n', "esp_light_sleep_start(); in sleep()", rel)
    if body is None: return None
    return head + body
edit("src/helpers/ESP32Board.h", esp32)

# 3. CLI: set/get serial.ondemand
def cli(s):
    rel = "src/helpers/CommonCLI.cpp"
    s = insert_after(s, r'^#include\s*<Arduino\.h>', '#include "SerialWake.h"  // serial-in-PowerSaving\n', "#include <Arduino.h>", rel)
    if s is None: return None
    return insert_after(s, r'^void\s+CommonCLI::handleCommand\s*\(\s*uint32_t\s+sender_timestamp\s*,\s*char\s*\*\s*command\s*,\s*char\s*\*\s*reply\s*\)\s*\{',
                        '    if (SerialWake::handleCommand(command, reply)) return;  // set/get serial.ondemand\n', "CommonCLI::handleCommand(...) {", rel)
edit("src/helpers/CommonCLI.cpp", cli)

if errors:
    print("SERIAL PATCH FAILED:\n  " + "\n  ".join(errors), file=sys.stderr)
    sys.exit(1)
print("serial-in-PowerSaving applied")
