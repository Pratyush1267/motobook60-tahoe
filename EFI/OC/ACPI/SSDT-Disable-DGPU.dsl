/*
 * SSDT-Disable-DGPU.dsl
 * Disable NVIDIA dGPU for Motorola 83J7 (Intel Core 7 240H)
 *
 * This SSDT disables the discrete GPU by calling its _OFF method.
 * The typical PCI path for NVIDIA dGPU on laptops is _SB.PCI0.RP05.PXSX
 * or _SB.PCI0.PEG0.PEGP - adjust based on actual hardware.
 */
DefinitionBlock ("", "SSDT", 2, "ZPSS", "DGPUOff", 0x00003000)
{
    External (_SB_.PCI0.RP05.PXSX, DeviceObj)
    External (_SB_.PCI0.RP05.PXSX._OFF, MethodObj)
    External (_SB_.PCI0.PEG0.PEGP, DeviceObj)
    External (_SB_.PCI0.PEG0.PEGP._OFF, MethodObj)
    External (_SB_.PCI0.GFX0, DeviceObj)
    External (_SB_.PCI0.GFX0._OFF, MethodObj)

    Method (_INI, 0, NotSerialized)  // _INI: Initialize
    {
        // Try common NVIDIA dGPU paths and call _OFF if they exist
        If (CondRefOf (\_SB.PCI0.RP05.PXSX._OFF))
        {
            \_SB.PCI0.RP05.PXSX._OFF ()
        }

        If (CondRefOf (\_SB.PCI0.PEG0.PEGP._OFF))
        {
            \_SB.PCI0.PEG0.PEGP._OFF ()
        }

        If (CondRefOf (\_SB.PCI0.GFX0._OFF))
        {
            \_SB.PCI0.GFX0._OFF ()
        }
    }
}