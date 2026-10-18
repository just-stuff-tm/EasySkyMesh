# EasySkyMesh PowerSaving + serial.ondemand

Builds of the [EasySkyMesh](https://github.com/IoTThinks/EasySkyMesh) PowerSaving firmware with one addition, `serial.ondemand`, so the serial console keeps working while power saving is on. (Builds that follow stock MeshCore as soon as it releases are at [just-stuff-tm/MeshCore](https://github.com/just-stuff-tm/MeshCore/releases).)

## serial.ondemand
- With power saving on, ESP32 boards light-sleep between packets. While asleep, the UART is stopped, so a controller on the serial port gets no answer. In this setup that's a LilyGO T-SIM on a Heltec V3's GPIO44 (RX) / GPIO43 (TX).
- With `serial.ondemand` **on** (the default), any byte on UART0 RX wakes the board, and it stays awake 15 s after the last byte.
- The byte that wakes the board is lost. Send CR or LF, wait about 100 ms, then send the command.
- Commands, over serial or remote admin:
  - `set serial.ondemand on` / `set serial.ondemand off` (**off** = the stock PowerSaving behaviour)
  - `get serial.ondemand`
- The setting is stored in NVS, so it survives reboots and updates.
- Applies to ESP32 boards whose serial port is a UART (e.g. Heltec V3). On nRF52 and native-USB ESP32 boards, serial already works during power saving, so nothing changes there.

## Releases
- Release tag: `<upstream tag>-serial`, e.g. `PowerSaving17.1-serial`. It holds every board upstream releases, with the same file types: ESP32 `-upgrade.bin` (keeps identity) and `-freshInstall-merged.bin`; nRF52 `.uf2`/`.zip`; plus `SHA256SUMS.txt`.
- File names carry the version with `-serial`, e.g. `Heltec_v3_repeater-PowerSaving17.1.6-serial-upgrade.bin`.

## When EasySkyMesh releases
Press **Run workflow** (Actions → "Serial builds" → Run workflow). Pushes to `serial` also start a build. There is no schedule.
- The workflow reads the latest upstream release, finds the source branch named in its notes ("Source code: …/tree/PowerSaving-vNN" in IoTThinks/MeshCore), applies `serial/`, builds everything and publishes `<tag>-serial`.
- If that tag is already built from the same commit and patch, the run ends after a few seconds. Options: **upstream_tag** (an older release), **source_ref** (a preview of a source branch, e.g. `PowerSaving-v18`, published as a pre-release), and **force**.
- If the patch no longer fits, the run fails, an issue is opened (when Issues are enabled), and nothing is released.
- GitHub only shows the **Run workflow** button for workflows on the default branch, so set the default branch to **serial** (Settings → General → Default branch). Alternatively, from a terminal: `gh workflow run serial-build.yml -R just-stuff-tm/EasySkyMesh --ref serial`.

## Branches
- **main** is an untouched mirror of IoTThinks/EasySkyMesh, so **Sync fork** there always fast-forwards. Syncing main doesn't start a build, because main has no workflow file. Press Run workflow afterwards.
- **serial** holds only `serial/` and `.github/workflows/serial-build.yml`. A ruleset blocks force-pushes and deletion. Don't press Sync fork while viewing serial.

## How the patch is applied
`serial/src/helpers/SerialWake.{h,cpp}` are copied in. `serial/apply-serial.py` then adds three one-line hooks, found by matching code rather than line numbers: in `ESP32Board.h` (include, and around `esp_light_sleep_start()`) and in `CommonCLI::handleCommand()`.

## Credits and license
- Firmware: [MeshCore](https://github.com/meshcore-dev/MeshCore) by Scott Powell / rippleradios.com and contributors, with the PowerSaving work by [IoTThinks / EasySkyMesh](https://github.com/IoTThinks/EasySkyMesh) ([source](https://github.com/IoTThinks/MeshCore)) and its contributors. Both are MIT licensed; the license text ships with the source as `license.txt`.
- The serial.ondemand addition (`serial/`) is released under the same MIT license.
