# Tahoe 26.7.1 (25G241) install USB — Motorola motobook 60 14IRH10R (Core 7 240H, 8086:A7AB)

**Contents of this stick:**

| Partition | Contents |
|---|---|
| `EFI` (D:, FAT32, 1 GB) | OpenCore + configs + kexts + `com.apple.recovery.boot/` (26.7 recovery fallback) |
| `DATA` (E:, exFAT, 56 GB) | `InstallAssistant.pkg` (full 26.7.1 **25G241** installer, 17.1 GB), `payload/` (NootedGreen 95f81898 + XPS13Plus reference build) |

**Configs on the EFI partition** (`EFI/OC/`):
- `config.plist` — INSTALL config (active): verbose, `-igfxvesa`, no GPU spoof, only audio kexts load.
- `config-accel.plist` — ACCELERATED config: NootedGreen 9A49 spoof, full ngreen args with
  `ngreen-eu=64 ngreen-l3=4` (this machine's iGPU), Metal 2.
- `config-bisect.plist` / `config-liluonly.plist` / `config-nokext.plist` / `config-v*-vesa*` —
  debugging ladders from earlier boot attempts. Keep for troubleshooting.

---

## Install path (use the FULL installer, not the recovery image)

The recovery image on the EFI partition is a **26.7.x fallback only** — its exact build couldn't be
verified, and the NootedGreen userspace stack is **pinned to 25G241**. The full installer on DATA is
the verified 25G241 build (Apple product 142-28081), which is the build the whole GPU stack expects.

### Phase 1 — getting 25G241 onto the machine

The full installer needs macOS to execute. Since this laptop is not on macOS yet:

**Option A (no second Mac): bootstrap via recovery, then install 25G241 on top.**
1. Boot this stick (F12 → USB). OpenCore menu → the **recovery** entry (macOS Base System).
2. Use Disk Utility inside recovery to erase the target as APFS.
3. Recovery installs the 26.7.x build it carries — fine for reaching a desktop.
4. At the desktop (install config, VESA graphics), open Terminal and install the *full 25G241
   installer package* onto the running system (this only adds the installer app, it does not
   upgrade you):

   ```
   sudo installer -pkg /Volumes/DATA/InstallAssistant.pkg -target /
   ```

5. Run the "Install macOS Tahoe 26.7.1" app from /Applications and point it at the same volume —
   an in-place reinstall puts the system on exactly **25G241**, keeping your files.
6. Continue to Phase 2.

**Option B (second Mac available): classic clean install.**
On the Mac, use `createinstallmedia` — but that ERASES this stick. Only do it after copying
EFI/ and payload/ elsewhere (Windows backup exists at
`C:\Users\praty\New folder\usb-backup-2026-11-13`).

### Phase 2 — install

1. Boot the stick with the install `config.plist` (default). F12 → USB → OpenCore → the macOS
   installer entry.
2. Install to APFS. Reboots several times — keep picking the installer in OpenCore.
3. Desktop reached: audio (AppleALC + SimpleHDA, layout 15), touchpad, keyboard, battery work.
   No graphics acceleration yet.

### Phase 3 — GPU acceleration (Metal 2)

Follow `DATA:/payload/README-POST-INSTALL.txt` steps 2–7: extract the payload on APFS, build
HookCase + the patched Metal driver, install Apple's TGL kexts into /Library/Extensions, then swap
`config-accel.plist` → `config.plist` on the EFI partition and reboot.

Verify:
- `system_profiler SPDisplaysDataType` → **Metal Support: Metal 2**
- `ioreg -rc IntelAccelerator -d1 | grep xe-topo` → **20486** (64 EU / 4 L3 — this machine)
- `kmutil showloaded | grep NootedGreen`

### Known issues (carried from the reference builds)
- Sleep is broken on this class of hardware — keep sleep off, use display-off instead.
- GPU reset storms (~3 s freezes) can occur under heavy load.
- **Never take macOS updates past 25G241** (automatic updates OFF) — updates break graphics.
- FairPlay (Apple Music/TV DRM) breaks if `-ngreengva` is added; don't add it.

## Serials
Install config: `C02GWGZDML7H`, accel config: `C02G2TYRML7H` — both MacBookPro16,2, generated with
macserial during this project. Verify at checkcoverage.apple.com → must say "not valid" before you
sign into an Apple ID.

## Emergency
- Boot fails after swapping to the accel config: boot the stick again; the install config is
  still on it. Or step down the bisect ladder (`config-bisect.plist` = Lilu only).
- Windows is untouched; the OpenCore picker shows both OSes.
- Full backup of the previous stick layout: `C:\Users\praty\New folder\usb-backup-2026-11-13`.
