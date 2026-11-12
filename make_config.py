#!/usr/bin/env python
"""Adapt the ThinkPad E16 Gen 3 Tahoe EFI config for the Lenovo LNVNB161216 (Core 7 240H, 8086:A7AB).

Transformations (vs the reference repo's EFI/OC/config.plist + config-install.plist):
  1. SMBIOS: inject fresh MacBookPro16,2 serials (never boot someone else's serials).
  2. WiFi/BT: user has RTL8922AE (Realtek, no macOS driver) -> disable ALL WiFi kexts and the
     Intel BT chain; keep them on disk for a future AX210/AX211 swap. Drop -itlwm* and itlwm_he args.
  3. Ethernet: user has RTL8152 USB (no Intel I219) -> disable IntelMausiEthernet.
  4. USB: ThinkPad UTBMap is their port map -> disable UTBMap.kext (XHCI-unsupported-600 stays:
     user's xHCI is the same 8086:51ED).
  5. EC: YogaSMC is ThinkPad EC software -> disable (Lenovo consumer EC differs; VPC0/VPC2004 is
     present on this board so it MAY work; leave kext on disk, disabled, as an experiment toggle).
  6. Graphics: identical iGPU (8086:A7AB) and same ACPI path \\_SB.PC00.GFX0 -> keep the
     NootedGreen + WhateverGreen stack, device properties, and all ngreen-* boot-args untouched,
     EXCEPT ngreenblmax which is panel-specific: keep the reference value as a starting point but
     flag it in the README (if max brightness looks ~18%, recalibrate per docs).
  7. config-install.plist: same as accelerated config but installer-safe: NootedGreen/WhateverGreen/
     BTLEAdvFixup/BTIdle/CpuTopologyRebuild disabled, no IGPU device-properties, SIP fully on (csr 0),
     boot-args 'keepsyms=1 debug=0x100 -v', ShowPicker=true.
  8. MinKernel/MaxKernel: SimpleHDA/ForbiddenItlwm/AirportItlwm pinned to 25.x (Tahoe) as upstream.
  9. Keep the _OSI->XOSI patch + SSDT-XOSI (Windows _OSI semantics for the Lenovo DSDT).
"""
import plistlib

REF = r"C:/Users/praty/Downloads/ref-thinkpad-e16/EFI/OC/config.plist"
OUT_ACCEL = r"C:/Users/praty/New folder/EFI-LENOVO/EFI/OC/config.plist"
OUT_INSTALL = r"C:/Users/praty/New folder/EFI-LENOVO/EFI/OC/config-install.plist"

SERIAL = "C02CX7Z9ML7H"
MLB = "C02026306J9P8PGA8"
UUID = "7234A6BB-6CC9-4591-A709-9905233CD695"
# ROM: a local-administered MAC address (locally administered, unicast)
ROM = bytes.fromhex("A8A8A8000001")

INSTALL_ARGS = "keepsyms=1 debug=0x100 -v"

# kexts to switch off in BOTH configs (hardware this machine doesn't have)
DISABLE_BOTH = {
    "itlwm.kext",              # Intel WiFi — no Intel card
    "AirportItlwm.kext",        # Intel WiFi — no Intel card
    "ForbiddenItlwm.kext",      # Intel WiFi (AWDL fork) — no Intel card
    "IntelBluetoothFirmware.kext",  # Intel BT — no Intel BT
    "IntelBTPatcher.kext",      # Intel BT — no Intel BT
    "IntelMausiEthernet.kext",  # I219 — this board has RTL8152 USB ethernet
    "UTBMap.kext",              # ThinkPad port map — remap on this Lenovo
    "YogaSMC.kext",             # ThinkPad EC software — try enabling later as an experiment
}

def set_enabled(entry, val):
    entry["Enabled"] = val

def main():
    with open(REF, "rb") as f:
        cfg = plistlib.load(f)

    # ---- SMBIOS ----
    gen = cfg["PlatformInfo"]["Generic"]
    gen["SystemSerialNumber"] = SERIAL
    gen["MLB"] = MLB
    gen["SystemUUID"] = UUID
    gen["ROM"] = ROM

    # ---- kexts: disable hardware we don't have ----
    for e in cfg["Kernel"]["Add"]:
        bp = e["BundlePath"]
        if bp in DISABLE_BOTH:
            set_enabled(e, False)

    # ---- boot-args: strip itlwm/awdl args, keep everything else (ngreen stack) ----
    nv = cfg["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    args = nv["boot-args"]
    keep = []
    for tok in args.split():
        low = tok.lower()
        if low.startswith("itlwm") or low.startswith("-itlawdl") or low == "itlwm_he=1":
            continue
        if low.startswith("itlawdl") or low.startswith("-itlwm"):
            continue
        keep.append(tok)
    nv["boot-args"] = " ".join(keep)

    # csr-active-config stays b'\x13\n\x00\x00' (0xA13) in the accelerated config.

    # ---- write accelerated config ----
    with open(OUT_ACCEL, "wb") as f:
        plistlib.dump(cfg, f, sort_keys=True)

    # ---- build config-install.plist from the SAME base (keeps kexts consistent) ----
    with open(REF, "rb") as f:
        inst = plistlib.load(f)

    gi = inst["PlatformInfo"]["Generic"]
    gi["SystemSerialNumber"] = SERIAL
    gi["MLB"] = MLB
    gi["SystemUUID"] = UUID
    gi["ROM"] = ROM

    # disable the whole GPU stack while installing
    for e in inst["Kernel"]["Add"]:
        bp = e["BundlePath"]
        if bp in DISABLE_BOTH:
            set_enabled(e, False)
        if bp in {"NootedGreen.kext", "WhateverGreen.kext", "BTLEAdvFixup.kext", "BTIdle.kext",
                  "CpuTopologyRebuild.kext"}:
            set_enabled(e, False)

    # no IGPU device properties during install (NootedGreen absent -> properties can wedge the installer)
    inst["DeviceProperties"]["Add"].pop("PciRoot(0x0)/Pci(0x2,0x0)", None)

    # installer boot-args + SIP fully enabled
    nvi = inst["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
    nvi["boot-args"] = INSTALL_ARGS
    nvi["csr-active-config"] = b"\x00\x00\x00\x00"

    # show the picker while installing (multiple volumes to choose)
    inst["Misc"]["Boot"]["ShowPicker"] = True
    inst["Misc"]["Boot"]["HideAuxiliary"] = False
    inst["Misc"]["Security"]["ScanPolicy"] = 0

    with open(OUT_INSTALL, "wb") as f:
        plistlib.dump(inst, f, sort_keys=True)

    print("accelerated :", OUT_ACCEL)
    print("install     :", OUT_INSTALL)
    print("serial      :", SERIAL)
    print("boot-args   :", nv["boot-args"])

if __name__ == "__main__":
    main()
