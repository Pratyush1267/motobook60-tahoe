# motobook60-tahoe

macOS 26 **Tahoe** (26.7.1, build **25G241**) with **Metal 2** graphics acceleration on the
**Motorola motobook 60 14IRH10R** (Lenovo `17AA`, Intel **Core 7 240H**, Raptor Lake-H) —
iGPU `8086:A7AB` spoofed as Tiger Lake `9A49` via NootedGreen.

Status: **installer-ready**. EFI prepared and machine-tuned; macOS not yet installed on the target
(this repo documents the working setup path). Derived from the
[ThinkPad E16 Gen 3](https://github.com/keenerdavid18/thinkpad-e16-gen3-hackintosh) and
[JulioNectar/XPS13Plus-IrisXe-Tahoe](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe)
builds — both pinned to 25G241.

## Hardware

| Part | Device | Status |
|---|---|---|
| CPU | Core 7 240H (RPL-H, 10C/16T) | works — `SSDT-PLUG-ALT`, CpuTopologyRebuild |
| iGPU | `8086:A7AB`, 64 EU / **4 L3 banks** | **Metal 2** via NootedGreen spoof (`9A49`), Apple GPUDriversIntel 16.0.32 userspace stack |
| Display | 2880×1800 eDP | backlight via SSDT-PNLF + BrightnessKeys |
| Audio | Senary SN6140 `14F1:1F87` on RPL cAVS `8086:51CA` | custom AppleALC (CX8070-derived layouts 15/21) + SimpleHDA |
| Touchpad | ELAN06FA on I2C0 `8086:51E8` | VoodooI2C + `-vi2c-force-polling` |
| Keyboard | PS/2 | VoodooPS2 |
| NVMe | WD PC SN7100S | NVMeFix |
| USB | PCH xHCI `8086:51ED` | XHCI-unsupported + USBToolBox (UTBDefault) |
| Wi-Fi/BT | Realtek RTL8922AE `10EC:8922` / `0BDA:D922` | **not supported on macOS** — swap to Intel AX210/AX211 and enable the shipped (disabled) itlwm/BT kexts, or tether |
| Card reader | Realtek RTS522A | Sinetek-rtsx (experimental, disabled) |

## Configs (`EFI/OC/`)

| File | Purpose |
|---|---|
| `config.plist` | **Install config** (active): `-igfxvesa`, no GPU spoof, 22 kexts (SMC/input/USB/NVMe/audio), SIP `0xA03` |
| `config-accel.plist` | **Accelerated**: NootedGreen + WhateverGreen on, full `ngreen-*` args with `ngreen-eu=64 ngreen-l3=4`, SIP `0xA13` |
| `config-bisect.plist`, `config-liluonly.plist`, `config-nokext.plist`, `config-v*-vesa*` | debug ladder from bring-up sessions |

**Before booting:** regenerate `PlatformInfo → Generic` (serial/MLB/UUID) with
[macserial](https://github.com/acidanthera/OpenCorePkg/releases) (`macserial -m MacBookPro16,2`)
in **both** configs, and verify the serial at checkcoverage.apple.com shows *invalid*.

## Install sequence

1. **BIOS**: Secure Boot off, UEFI-only, VT-d may stay on.
2. **USB**: FAT32 boot partition with this `EFI/` at its root; the full
   **26.7.1 25G241** `InstallAssistant.pkg` (Apple catalog product `142-28081`) + the
   NootedGreen/XPS13Plus payload on a data partition.
   (`make_config.py` / `docs-usb.md` document the layout this was built with.)
3. Install macOS (install config), several reboots, APFS target.
4. **Never update past 25G241** — the userspace GPU stack is build-pinned. Disable automatic updates.
5. Userspace GPU stack (from the XPS13Plus reference): build HookCase + patched Metal driver,
   install Apple TGL kexts to `/Library/Extensions`, shader compiler to `xe.bundle`.
6. Swap `config-accel.plist` → `config.plist` on the ESP, reboot.
7. Verify: `system_profiler SPDisplaysDataType` → **Metal 2**; `ioreg -rc IntelAccelerator -d1 |
   grep xe-topo` → **20486** (64 EU / 4 L3 — anything else means the topology override didn't apply).

## Known issues

- Sleep/lid-wake broken (GPU hang) — keep sleep off.
- GPU reset storms (~3 s freezes) possible under load.
- macOS updates past 25G241 break graphics.
- FairPlay (Apple Music/TV) breaks with `-ngreengva`; not used here.

## Credits

- [keenerdavid18/thinkpad-e16-gen3-hackintosh](https://github.com/keenerdavid18/thinkpad-e16-gen3-hackintosh) — base EFI, custom AppleALC (SN6140 retag), SimpleHDA integration
- [JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe) — NootedGreen userspace stack (Apple GPUDriversIntel 16.0.32, HookCase, patched Metal)
- [sgiammori/NootedGreen](https://github.com/sgiammori/NootedGreen) — the driver itself
- [laobamac/SimpleHDA](https://github.com/laobamac/SimpleHDA) — AppleHDA restored for Tahoe
- acidanthera — OpenCore, Lilu, WhateverGreen, VirtualSMC, macserial, macrecovery
