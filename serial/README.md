# Serial builds (serial-in-PowerSaving)

This branch builds the EasySkyMesh PowerSaving firmware with one extra feature: **the serial console keeps working while power saving is on**, so a controller wired to the board's UART (here a LilyGO T-SIM on the Heltec V3's RX/TX pins, GPIO44/43) can always send CLI commands.

## What it changes
- On ESP32 boards whose `Serial` is a UART, a byte on UART0 RX wakes the board from PowerSaving light sleep. The board then stays awake 15 s after the last byte, so whole commands and replies get through. The byte that does the waking is lost, so send a CR or LF, wait about 100 ms, then send the command. The T-SIM firmware already does this.
- `set serial.ondemand on|off` (default **on**) and `get serial.ondemand`, over serial and remote admin. **off** gives stock PowerSaving behaviour. The setting is stored in NVS (`serialwake` namespace), so it survives reboots and firmware updates without touching upstream's prefs layout.
- nRF52 and native-USB ESP32 boards are unchanged, because their serial already works during power saving.
- The code is in `serial/src/helpers/SerialWake.*` (new files) plus three one-line hooks that `serial/apply-serial.py` adds by finding anchors in the code, not line numbers. If upstream moves that code so an anchor is missing, the script fails, the run fails and an issue is opened. No build ships without the serial change.

## How the branches work
- **main** is a pure mirror of IoTThinks/EasySkyMesh. Never commit to it, so **Sync fork** on main can only fast-forward and never asks you to "discard commits". The scheduled workflow also syncs main automatically.
- **serial** (this branch) holds only `serial/` and `.github/workflows/serial-build.yml`. Upstream never touches these paths. Don't press Sync fork while viewing **serial**: it isn't meant to track upstream main. A ruleset blocks force-pushes and deletion, so even "Discard commits" can't remove it.
- The firmware source isn't in EasySkyMesh. It's in IoTThinks/MeshCore, on the branch named in the upstream release notes ("Source code: …/tree/PowerSaving-vNN"). The workflow reads that link from the latest upstream release.

## When a build runs
- Every 6 hours (needs **serial** as the default branch: Settings → General → Default branch). The run syncs main, checks the latest upstream release and its source commit, and builds if `<tag>-serial` doesn't exist yet or the source or patch changed.
- On any push to **serial** that touches `serial/` or the workflow.
- Manually: Actions → Serial builds → Run workflow. Options: an older upstream tag, a preview of a source branch (e.g. `PowerSaving-v18`), or force.

Each run builds every env upstream releases (the list in `build-iotthinks.sh` plus every board in the upstream release assets). It then publishes release `<upstream tag>-serial` with the same file types as upstream: `-upgrade.bin` and `-freshInstall-merged.bin` for ESP32, `.uf2`/`.zip` for nRF52, plus `SHA256SUMS.txt`.
