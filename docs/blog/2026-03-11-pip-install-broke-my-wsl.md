# How a pip install Nuked My Entire WSL Installation (and How I Fixed It)

*March 11, 2026 -- Dr34d*

---

I was just trying to set up a dev environment. That's it. A `pip install`. Something I've done a thousand times. But this time, it didn't just fail -- it took my entire Windows Subsystem for Linux down with it. Not "oh restart WSL and you're fine" down. I mean **WSL is gone, every command returns an error, and nothing Microsoft suggests will fix it** down.

This is the story of how I broke WSL2 so badly that even reinstalling it didn't help, and the rabbit hole I went down to bring it back.

## The Setup

I was working in Kali Linux on WSL2, getting ProwlrBot's dev environment ready. Standard stuff:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Tested it, didn't like the venv name. Deleted it.

```bash
rm -rf venv
python3 -m venv prowlr-venv
source prowlr-venv/bin/activate
pip install -e ".[dev]"
```

ProwlrBot pulls around 240 transitive dependencies -- transformers, onnxruntime, playwright, agentscope, the works. Pip was chugging along, downloading, building wheels, the usual progress bar. Package 230... 235... 238...

And then my terminal just... stopped.

No error message. No traceback. The WSL instance went dark. The window was still open, but nothing was responding. I figured it froze, so I closed the terminal and opened a new one.

```
Error code: Wsl/0x80070422
```

Okay. Weird. Let me try again.

```
wsl --status
```

Same error. Every WSL command. Dead.

## The Error

The full error was:

> "The service cannot be started, either because it is disabled or because it has no enabled devices associated with it."

`0x80070422` -- a Windows service error. Not a Linux problem. Not a pip problem. Something in Windows itself broke.

I checked the WSL service:

```powershell
sc.exe query WslService
# STATE: STOPPED
# WIN32_EXIT_CODE: 1077

sc.exe start WslService
# FAILED 1058
```

The service existed, but it refused to start. Error 1058 means "this service is disabled or has no associated devices." But it was set to manual start. So what gives?

## The Rabbit Hole

Here's everything I tried:

**The obvious stuff:**
- `wsl --shutdown` and try again -- nope
- Restart the computer -- nope
- Uninstall WSL via winget, reinstall -- nope
- `wsl --update` -- says it's already up to date

**The "okay let me get serious" stuff:**
- Verified every Windows feature was enabled: `Microsoft-Windows-Subsystem-Linux`, `VirtualMachinePlatform`, `Hyper-V`, all of it
- Confirmed the hypervisor was running via `systeminfo`
- Checked that every dependency service was running: `vmcompute`, `vmms`, `hns`, `RpcSs`, `DcomLaunch` -- all green
- Set `bcdedit /set hypervisorlaunchtype auto` -- already was

**The "I'm getting desperate" stuff:**
- Deleted the WslService registry entry and recreated it with `sc.exe create`
- Re-registered the WSL Appx package manifest
- Ran `wsl --install --no-distribution` -- said "operation completed successfully" (it lied)
- Registered the COM proxy stub DLL manually

Nothing worked. The service simply would not start.

## The Actual Problem

After hours of digging, I finally figured it out.

When the pip install crashed WSL, it didn't just kill the Linux VM. The crash corrupted or destroyed the **WslService registry entry** in Windows. The service key under `HKLM\SYSTEM\CurrentControlSet\Services\WslService` was just... gone.

And here's the part that made this so painful to diagnose: **nothing in Microsoft's tooling can recreate it.**

- The WSL Store package's `AppxManifest.xml` does NOT define WslService. The service is not registered through the Appx deployment pipeline.
- `wsl --install --no-distribution` reports success but silently fails to register the service.
- `winget` reinstalls the files but doesn't touch the service registry.
- Re-registering the Appx package with `Add-AppxPackage -Register` does nothing because the manifest doesn't contain a service definition.

I also discovered that Windows has TWO `wsl.exe` binaries:

1. `C:\Windows\System32\wsl.exe` (inbox, v10.0.26100) -- takes PATH priority
2. `C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\wsl.exe` (Store app alias)

The inbox one was intercepting every command, trying to talk to a service that didn't exist, and failing. The Store one never got a chance to run.

## The Fix

In the end, the fix was embarrassingly simple -- once I knew what was actually wrong:

```powershell
# Run in an elevated PowerShell

# Create the service with the correct binary path
New-Service -Name 'WslService' `
    -BinaryPathName '"C:\Program Files\WSL\wslservice.exe"' `
    -DisplayName 'WSL Service' `
    -StartupType Manual `
    -Description 'Windows Subsystem for Linux Service'

# Add the vmcompute dependency
sc.exe config WslService depend= vmcompute

# Start it
sc.exe start WslService
```

That's it. The service came up, WSL listed all my distros, and Kali was right where I left it (well, minus the half-installed venv).

The key details that matter:
- **BinaryPathName** must be quoted because of the space in "Program Files" -- get this wrong and you get error 1058 again
- **StartupType** must be Manual (demand-start), not Automatic
- **vmcompute dependency** ensures the Hyper-V compute service is running before WSL tries to start

## The Aftermath (It Wasn't Over)

Even after the service was back, the first boot wasn't clean. The kernel started but the virtual disk was hammering SCSI errors:

```
hv_storvsc: tag#673 cmd 0x2a status: scsi 0x2 srb 0x4 hv 0xc0000001
```

Thousands of these per second. Over 43,000 suppressed callbacks in a single 5-second window. The `0x2a` is a SCSI WRITE command, and `0x2` is CHECK CONDITION -- the virtual disk was rejecting every single write. The VM would boot, start initializing, then choke and timeout:

```
HCS_E_CONNECTION_TIMEOUT
The operation timed out because a response was not received from the virtual machine or container.
```

I tried `wsl --shutdown`, waited, restarted. Same thing. The SCSI errors started flooding the moment the Kali VHDX was attached, before the distro even finished booting.

## The Second Root Cause: NTFS Compression

Turns out there was a deeper problem hiding underneath the service issue. I checked the VHDX file properties:

```powershell
Get-Item "C:\Users\Dr34d\AppData\Local\wsl\{...}\ext4.vhdx" | Select-Object Attributes
# Archive, Compressed
```

**The entire WSL storage folder had NTFS compression enabled.** My 248GB Kali VHDX was being stored with NTFS filesystem-level compression. And the parent folder was compressed too, meaning every new file written there would automatically inherit compression.

This is the actual smoking gun. NTFS compression on a VHDX that's being hammered with random I/O from a Linux filesystem is a disaster waiting to happen. Here's why:

- NTFS compression works on 64KB clusters. Every write to the VHDX requires Windows to decompress the cluster, modify it, recompress it, and write it back.
- pip installing 240 packages generates thousands of small file writes per second inside the Linux filesystem, each translating to random write I/O on the VHDX.
- The Hyper-V storage driver (storvsc) has timeouts. When compressed writes can't keep up, it returns CHECK CONDITION errors.
- Enough of these errors and the entire VM crashes, which is exactly what happened during my pip install.

The fix for this was also annoyingly simple in hindsight, but had a catch. `compact /u` on the VHDX failed:

```
ext4.vhdx [ERR]
The requested operation could not be completed due to a file system limitation
```

NTFS can't decompress a 248GB file in-place. It's too large. So you have to copy it:

```powershell
# Remove compression from the folder first
compact /u /s "C:\Users\Dr34d\AppData\Local\wsl\{...}"

# Copy creates an uncompressed version (takes a while at 248GB)
copy "...\ext4.vhdx" "...\ext4_uncompressed.vhdx"

# Stop WSL and the service to release the file lock
wsl --shutdown
sc.exe stop WslService

# Swap
Remove-Item "...\ext4.vhdx"
Rename-Item "...\ext4_uncompressed.vhdx" "ext4.vhdx"
```

After the swap, Kali booted clean. No SCSI errors. No timeouts. The kernel log was quiet and normal.

## So What Actually Happened?

Putting it all together, the chain of events was:

1. **NTFS compression was silently enabled** on the WSL storage directory (possibly by a disk cleanup tool, a storage sense policy, or manual compression of the AppData folder at some point)
2. **pip install started hammering the VHDX** with hundreds of writes per second across 240 package installations
3. **NTFS compression couldn't keep up** — the decompression-write-recompression cycle fell behind, and storvsc started returning SCSI errors
4. **The WSL VM crashed** when write errors exceeded the timeout threshold
5. **The crash corrupted or destroyed the WslService registry entry** — this is the part I still can't fully explain, but the service key was completely gone after the crash
6. **Nothing could recreate the service** because the WSL Store package doesn't define it in its manifest, and `wsl --install` silently fails to register it

Two separate problems, one crash. The compression caused the crash, and the crash destroyed the service registry. You had to fix both to get WSL running again.

## Lessons Learned

**For ProwlrBot users specifically:**

1. **Create your venv inside the project directory** as `.venv/`, not in a random location
2. **Work on the Linux filesystem** (`/home/user/`), not on Windows mounts (`/mnt/c/`)
3. **Install in stages** to reduce I/O pressure on the virtual filesystem:
   ```bash
   pip install --upgrade pip
   pip install -e .          # core first
   pip install -e ".[dev]"   # dev deps second
   ```
4. **Don't delete and recreate venvs rapidly** -- `rm -rf` on a large venv generates massive I/O that WSL's virtual filesystem has to sync back to the VHDX

**For anyone running WSL2:**

5. **Check for NTFS compression right now.** This is the single most dangerous hidden setting for WSL:
   ```powershell
   compact /s "$env:LOCALAPPDATA\wsl"
   compact /s "$env:LOCALAPPDATA\Packages"
   ```
   If any VHDX files show as compressed, decompress them before they ruin your week. Disable compression permanently:
   ```powershell
   compact /u /s /a /i "$env:LOCALAPPDATA\wsl"
   ```
6. **The WslService registry key is a single point of failure.** If it gets deleted or corrupted, no amount of reinstalling through normal channels will fix it. You need to manually recreate it.
7. **Export your registry key now** while things work:
   ```powershell
   reg export "HKLM\SYSTEM\CurrentControlSet\Services\WslService" WslService-backup.reg
   ```
8. **Keep your distros exported** as backups:
   ```bash
   wsl --export kali-linux kali-backup.tar
   ```
9. The gap between "WSL silently reports success" and "WSL actually works" is wider than you'd expect. Always verify with `wsl -l -v` after any repair.

## The Irony

I was setting up a dev environment for a project that coordinates multiple AI agents. The pip install that broke everything was installing the dependencies that would have let those agents help me debug this problem.

So I built a skill for it. ProwlrBot now ships with a `wsl_doctor` skill -- a diagnostic ladder that checks everything from service state to VHDX compression to registry integrity. It runs the same checks in the same order I wish I had when my terminal went dark at package 238.

Sometimes the tools you're building are exactly the ones you need. Now they exist so nobody else has to spend hours figuring this out.

---

*If you hit this same issue, the [ProwlrBot troubleshooting guide](../troubleshooting.md) has the condensed fix. If you've found a different way WSL can spectacularly break itself, [open an issue](https://github.com/ProwlrBot/prowlrbot/issues) -- we collect these stories now.*
