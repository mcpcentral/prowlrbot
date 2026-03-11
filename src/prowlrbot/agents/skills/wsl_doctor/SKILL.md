---
name: wsl_doctor
description: "Diagnose and repair Windows Subsystem for Linux (WSL2) issues. Runs progressive checks from simple to deep — service state, VHDX health, NTFS compression, Hyper-V stack, networking, DNS, memory, GPU passthrough, and registry integrity. Use when WSL won't start, distros crash, networking fails, or performance is degraded."
metadata:
  {
    "prowlr":
      {
        "emoji": "🩺",
        "requires": { "platform": "win32" }
      }
  }
---

# WSL Doctor — Diagnostic & Repair Skill

Diagnose and fix WSL2 issues using a progressive escalation approach. Start with the quickest, least invasive checks and only escalate to deeper diagnostics if earlier steps don't explain the problem.

## When to Use

- User says: "WSL won't start", "WSL crashed", "WSL is broken", "fix my WSL"
- User gets errors like `0x80070422`, `HCS_E_CONNECTION_TIMEOUT`, `Error 1058`
- WSL commands hang or return errors
- Distros won't boot or show I/O errors
- WSL networking/DNS isn't working
- WSL performance is severely degraded
- GPU passthrough or CUDA isn't working
- WSL is using too much memory or disk
- systemd services aren't starting
- Clock skew or time sync issues

## Diagnostic Ladder

**Always run checks in this order. Stop as soon as you find the problem.**

### Level 1 — Quick Health Check (5 seconds)

Run these via `shell` tool. Report results before moving deeper.

```powershell
# Check if WSL service exists and its state
sc.exe query WslService

# Check if WSL can list distros
wsl -l -v

# Check WSL version
wsl --version
```

**If WslService is RUNNING and distros are listed:** Problem is likely distro-specific, skip to Level 3.
**If WslService is STOPPED or missing:** Go to Level 2.
**If wsl commands hang:** Run `wsl --shutdown` first, then retry.

### Level 2 — Service & Hypervisor Stack (30 seconds)

```powershell
# Check WslService start type and config
sc.exe qc WslService

# Check dependencies are running
sc.exe query vmcompute
sc.exe query vmms

# Check hypervisor is active
systeminfo | findstr /C:"Hyper-V"

# Check if WslService registry exists
reg query "HKLM\SYSTEM\CurrentControlSet\Services\WslService" /v ImagePath
```

**If WslService registry key is MISSING:** This is the critical failure. The service entry was destroyed. Fix:

```powershell
# Recreate the service (elevated PowerShell required)
New-Service -Name 'WslService' -BinaryPathName '"C:\Program Files\WSL\wslservice.exe"' -DisplayName 'WSL Service' -StartupType Manual -Description 'Windows Subsystem for Linux Service'
sc.exe config WslService depend= vmcompute
sc.exe start WslService
```

**If WslService exists but won't start (Error 1058):**
- Check `Start` DWORD: `reg query "HKLM\SYSTEM\CurrentControlSet\Services\WslService" /v Start` — must be `0x3` (Manual)
- Check binary exists: `Test-Path "C:\Program Files\WSL\wslservice.exe"`
- Check binary path quoting — must have quotes around path with spaces

**If vmcompute is STOPPED:**

```powershell
sc.exe start vmcompute
```

**If hypervisor not detected:**

```powershell
# Check if virtualization is enabled in BIOS (AMD-V / Intel VT-x)
systeminfo | findstr /C:"Virtualization Enabled"

# Check hypervisor launch type
bcdedit /enum | findstr hypervisorlaunchtype
# Must be "Auto". If not:
bcdedit /set hypervisorlaunchtype auto
# Reboot required

# Check for conflicting hypervisors (VirtualBox, VMware)
# These can grab the hypervisor exclusively
Get-Service *vmware* *virtualbox* *vbox* 2>$null | Format-Table Name, Status
```

### Level 3 — VHDX & Disk Health (1-2 minutes)

```powershell
# Find all WSL VHDX files
Get-ChildItem "$env:LOCALAPPDATA\wsl" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue | Select-Object FullName, Length, Attributes, LastWriteTime

Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue | Select-Object FullName, Length, Attributes, LastWriteTime

# Check free disk space
Get-PSDrive C | Select-Object Used, Free
```

**Check for these problems:**

1. **NTFS Compression (CRITICAL):** If `Attributes` includes `Compressed`, the VHDX will suffer write failures under heavy I/O. This causes storvsc SCSI errors, HCS_E_CONNECTION_TIMEOUT, and VM crashes. Fix:

```powershell
wsl --shutdown
# Remove compression from folder
compact /u /s "<parent_folder_path>"
# Copy to decompress (compact /u fails on large files)
copy "<path>\ext4.vhdx" "<path>\ext4_uncompressed.vhdx"
# Verify copy is not compressed
Get-Item "<path>\ext4_uncompressed.vhdx" | Select-Object Attributes
# Swap files (stop WslService first if delete fails)
sc.exe stop WslService
Remove-Item "<path>\ext4.vhdx"
Rename-Item "<path>\ext4_uncompressed.vhdx" "ext4.vhdx"
```

2. **Missing VHDX:** If a distro's VHDX doesn't exist, it cannot start. User must unregister and reinstall that distro:

```powershell
wsl --unregister <distro-name>
wsl --install <distro-name>
```

3. **File size 0 or very small:** VHDX is corrupted. Restore from backup or unregister.

4. **Sharing violation:** Another process has the VHDX locked.

```powershell
wsl --shutdown
sc.exe stop WslService
# Wait 10 seconds, retry
```

5. **Disk full on host:** WSL VHDX grows dynamically. If the Windows drive is full, WSL will crash with I/O errors.

```powershell
# Check free space
(Get-PSDrive C).Free / 1GB
# If low, compact the VHDX after cleanup:
wsl --shutdown
Optimize-VHD -Path "<path>\ext4.vhdx" -Mode Full
# Or use the WSL built-in:
wsl --manage <distro-name> --resize <size-in-bytes>
```

6. **VHDX too large / needs compaction:** The VHDX only grows, never shrinks automatically.

```powershell
# Inside WSL first, reclaim space:
wsl -d <distro> -e sudo fstrim /
# Then from PowerShell:
wsl --shutdown
Optimize-VHD -Path "<path>\ext4.vhdx" -Mode Full
```

### Level 4 — Networking & DNS

**If WSL starts but has no network or DNS:**

```bash
# Inside WSL — check connectivity
ip addr show eth0
ping -c 1 8.8.8.8          # Raw IP — tests network layer
ping -c 1 google.com        # DNS — tests resolution
cat /etc/resolv.conf         # Check DNS config
```

**Common fixes:**

**DNS resolution fails but ping to IP works:**

```bash
# WSL auto-generates resolv.conf from Windows. If it's wrong:
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf

# Prevent WSL from overwriting it:
# Add to /etc/wsl.conf:
# [network]
# generateResolvConf = false
```

**No network at all (no IP on eth0):**

```powershell
# From PowerShell — restart the WSL network adapter
wsl --shutdown
# Reset the Hyper-V virtual switch
Get-HnsNetwork | Where-Object { $_.Name -eq "WSL" } | Remove-HnsNetwork
# Restart WSL — it will recreate the network
wsl
```

**If HNS (Host Networking Service) is broken:**

```powershell
sc.exe query hns
# If stopped:
sc.exe start hns
# Nuclear option — reset all HNS state:
Stop-Service hns
Remove-Item "C:\ProgramData\Microsoft\Windows\HNS\HNS.data" -ErrorAction SilentlyContinue
Start-Service hns
wsl --shutdown
```

**VPN interferes with WSL networking:**

```bash
# Inside WSL, check if the default route is wrong
ip route show
# If VPN hijacks the route, add manual route:
sudo ip route add default via <wsl-gateway-ip> dev eth0
```

```powershell
# Or configure WSL to use mirrored networking (WSL 2.0+)
# In %USERPROFILE%\.wslconfig:
# [wsl2]
# networkingMode=mirrored
```

**Port forwarding / localhost not working:**

```powershell
# WSL2 runs in a VM — localhost forwarding depends on the WSL service
# Check if localhostForwarding is disabled:
# In %USERPROFILE%\.wslconfig:
# [wsl2]
# localhostForwarding=true   # This is the default

# If still broken, manually forward:
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$(wsl hostname -I | ForEach-Object { $_.Trim() })
```

### Level 5 — Memory & Performance

**WSL using too much memory:**

```powershell
# Check vmmem process memory usage
Get-Process vmmem -ErrorAction SilentlyContinue | Select-Object WorkingSet64, VirtualMemorySize64
```

```ini
# Create or edit %USERPROFILE%\.wslconfig
[wsl2]
memory=8GB          # Limit WSL memory (default: 50% of host RAM or 8GB, whichever is less)
swap=4GB            # Swap size (default: 25% of host RAM)
processors=4        # Limit CPU cores
```

```powershell
# After editing .wslconfig:
wsl --shutdown
# Changes take effect on next WSL start
```

**WSL is slow / high latency:**

```bash
# Inside WSL — check if you're on Windows filesystem (slow)
pwd
# If path starts with /mnt/c/ — move to Linux filesystem: /home/user/

# Check I/O performance
dd if=/dev/zero of=/tmp/testfile bs=1M count=100 oflag=direct
# Expect >200 MB/s on Linux FS, <50 MB/s on /mnt/c/
rm /tmp/testfile
```

**Windows filesystem is very slow from WSL:**

```ini
# In /etc/wsl.conf inside the distro:
[automount]
options = "metadata,umask=22,fmask=11"

# In %USERPROFILE%\.wslconfig:
[wsl2]
# Experimental: may improve /mnt/c performance
crossDistro = true
```

### Level 6 — systemd & Init

**systemd not working:**

```bash
# Check if systemd is enabled
cat /etc/wsl.conf | grep systemd
# Should have:
# [boot]
# systemd=true

# If missing, add it:
sudo bash -c 'echo -e "[boot]\nsystemd=true" >> /etc/wsl.conf'
# Then restart: wsl --shutdown from PowerShell, then re-enter

# Check if systemd is actually PID 1
ps -p 1 -o comm=
# Should say "systemd", not "init"

# Check for failed units
systemctl --failed
```

**systemd services failing:**

```bash
# Common issue: systemd-resolved conflicts with WSL DNS
sudo systemctl disable systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Common issue: snapd fails (not supported in WSL)
sudo systemctl disable snapd snapd.socket snapd.seeded snapd.snap-repair.timer 2>/dev/null
```

### Level 7 — GPU & CUDA Passthrough

**GPU not detected in WSL:**

```bash
# Check if GPU is visible
nvidia-smi
# If "command not found" — the NVIDIA drivers in WSL come from Windows, not apt
ls /usr/lib/wsl/lib/
# Should contain libcuda.so, libnvidia-ml.so, etc.
```

```powershell
# From Windows — verify GPU driver supports WSL
nvidia-smi
# Driver must be 470.76+ for WSL GPU support
# Update via: https://developer.nvidia.com/cuda/wsl

# Check that the lxss GPU libraries exist
Test-Path "C:\Windows\System32\lxss\lib\libcuda.so.1"
```

**nvidia-smi works but CUDA programs fail:**

```bash
# DO NOT install nvidia drivers inside WSL — they conflict
# Remove any accidentally installed drivers:
sudo apt remove --purge nvidia-* 2>/dev/null

# Install CUDA toolkit only (not drivers):
# Use the WSL-specific CUDA installer from NVIDIA
```

### Level 8 — Clock Skew & Time Sync

**WSL clock is wrong (common after sleep/hibernate):**

```bash
# Check time difference
date
# Compare with Windows time
powershell.exe -Command "Get-Date"

# Fix immediately:
sudo hwclock -s

# Or force NTP sync if systemd is running:
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd
```

```powershell
# From Windows — the Hyper-V time sync should handle this
# Check if it's working:
reg query "HKLM\SYSTEM\CurrentControlSet\Services\W32Time\Config" /v MaxAllowedPhaseOffset
```

**Persistent clock skew after sleep:**

```ini
# In %USERPROFILE%\.wslconfig:
[wsl2]
# Experimental flag (WSL 2.4+):
# Automatically resync time when host resumes
kernelCommandLine = hv_utils.timesync_implicit=1
```

### Level 9 — Windows Features & Kernel (2 minutes)

Only check if Levels 1-8 didn't find the issue.

```powershell
# Verify required Windows features
dism /online /Get-FeatureInfo /FeatureName:Microsoft-Windows-Subsystem-Linux
dism /online /Get-FeatureInfo /FeatureName:VirtualMachinePlatform
dism /online /Get-FeatureInfo /FeatureName:Microsoft-Hyper-V

# Check hypervisor launch type
bcdedit /enum | findstr hypervisorlaunchtype

# Verify WSL kernel exists
Test-Path "C:\Program Files\WSL\tools\kernel"

# Check for dual wsl.exe conflict
Get-Command wsl.exe -All | Format-Table Source, Version

# Check WSL Store package integrity
Get-AppxPackage -Name "MicrosoftCorporationII.WindowsSubsystemForLinux" | Select-Object PackageFullName, Status, InstallLocation

# System file integrity
sfc /verifyonly
```

**If features are disabled:** Enable them (requires reboot):

```powershell
dism /online /Enable-Feature /FeatureName:Microsoft-Windows-Subsystem-Linux /NoRestart
dism /online /Enable-Feature /FeatureName:VirtualMachinePlatform /NoRestart
# Reboot required
```

**If hypervisorlaunchtype is not "Auto":**

```powershell
bcdedit /set hypervisorlaunchtype auto
# Reboot required
```

**If WSL Store package status is not "Ok":**

```powershell
Get-AppxPackage -Name "MicrosoftCorporationII.WindowsSubsystemForLinux" | Remove-AppxPackage
winget install --id Microsoft.WSL --source winget
```

### Level 10 — Event Log Deep Dive (last resort)

```powershell
# Check System log for WSL/Hyper-V errors
Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddHours(-6)} | Where-Object { $_.Message -match 'wsl|storvsc|hv_|Hyper-V|vmcompute|HCS' } | Select-Object -First 20 TimeCreated, Id, Message | Format-List

# Check Application log
Get-WinEvent -FilterHashtable @{LogName='Application'; Level=2; StartTime=(Get-Date).AddHours(-6)} | Where-Object { $_.Message -match 'wsl|WSL' } | Select-Object -First 10 TimeCreated, Id, Message | Format-List

# Check for kernel crashes / BSODs related to Hyper-V
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Hyper-V-Worker'; StartTime=(Get-Date).AddDays(-7)} -ErrorAction SilentlyContinue | Select-Object -First 10 TimeCreated, Id, Message | Format-List
```

## Distro-Specific Issues

### Distro won't install / register

```powershell
# List registered distros
wsl -l -v

# If distro shows but won't start — check VHDX (Level 3)
# If distro doesn't show — re-register:
wsl --import <name> <install-path> <backup.tar>
# Or reinstall:
wsl --install <distro-name>
```

### Distro boots to root instead of user

```bash
# Inside WSL — set default user
# In /etc/wsl.conf:
# [user]
# default=yourusername

# Or from Windows:
<distro>.exe config --default-user yourusername
```

### Cannot access Windows files from WSL

```bash
# Check mount
mount | grep drvfs
# Should show /mnt/c type drvfs

# If not mounted:
sudo mount -t drvfs C: /mnt/c

# Check /etc/wsl.conf
cat /etc/wsl.conf
# Should have:
# [automount]
# enabled = true
# root = /mnt/
```

### Cannot access WSL files from Windows

```powershell
# WSL files are accessible via \\wsl$\ or \\wsl.localhost\
Test-Path "\\wsl.localhost\kali-linux\home"

# If not accessible, the WSL 9P file server may be down
# Restart the distro:
wsl --terminate kali-linux
wsl -d kali-linux
```

## Prevention Commands

Give these to the user after any successful repair:

```powershell
# Backup WslService registry key (run now, save yourself later)
reg export "HKLM\SYSTEM\CurrentControlSet\Services\WslService" "$env:USERPROFILE\WslService-backup.reg"

# Backup distros
wsl --export kali-linux "$env:USERPROFILE\kali-backup.tar"

# Check for NTFS compression on WSL storage (should return NO compressed files)
compact /s "$env:LOCALAPPDATA\wsl"

# Disable compression on WSL storage permanently
compact /u /s /a /i "$env:LOCALAPPDATA\wsl"

# Set memory limits to prevent runaway usage
# Create %USERPROFILE%\.wslconfig if it doesn't exist:
# [wsl2]
# memory=8GB
# swap=4GB
```

## Common Error Code Reference

| Error | Meaning | First Check |
|-------|---------|-------------|
| `0x80070422` | Service cannot start | Level 2 — WslService registry |
| `Error 1058` | Service disabled or broken | Level 2 — Start DWORD, binary path |
| `Error 1060` | Service does not exist | Level 2 — Recreate service |
| `Error 1077` | Service never started since boot | Normal if WSL not used yet — just start it |
| `HCS_E_CONNECTION_TIMEOUT` | VM started but can't connect | Level 3 — VHDX compression or corruption |
| `SHARING_VIOLATION` | VHDX locked by process | `wsl --shutdown` + stop WslService |
| `PATH_NOT_FOUND` | VHDX file missing | Level 3 — check distro registration |
| `Errno 5 / I/O error` | Disk write failure | Level 3 — NTFS compression on VHDX |
| `storvsc` SCSI errors in dmesg | Virtual disk write failures | Level 3 — NTFS compression |
| `0x80370102` | VM couldn't start — no hypervisor | Level 2 — enable Hyper-V, check BIOS |
| `0x80370106` | VM couldn't start — nested virt | Level 2 — conflicting hypervisor (VBox/VMware) |
| `0x80004005` | Generic failure | Level 10 — check event logs for detail |
| `0x800701bc` | VHDX format error | Level 3 — VHDX corrupted, restore backup |
| `0x80040326` | WSL2 requires kernel update | `wsl --update` |
| `0xc03a001a` | VHDX is full | Level 3 — expand or compact VHDX |
| `Element not found` | Distro not registered | `wsl --import` or `wsl --install` |
| `No address associated with hostname` | DNS broken | Level 4 — fix resolv.conf |
| `Cannot connect to Docker` | Docker Desktop WSL integration | Restart Docker Desktop or re-enable WSL integration |

## .wslconfig Quick Reference

Location: `%USERPROFILE%\.wslconfig` (applies globally to all distros)

```ini
[wsl2]
memory=8GB                    # RAM limit
swap=4GB                      # Swap file size
swapFile=C:\\temp\\wsl-swap.vhdx  # Custom swap location
processors=4                  # CPU core limit
localhostForwarding=true      # Forward ports to Windows localhost
nestedVirtualization=true     # Allow VMs inside WSL
debugConsole=false            # Kernel debug console
kernelCommandLine=            # Extra kernel params
networkingMode=mirrored       # mirrored (share Windows network) or NAT (default)
firewall=true                 # Apply Windows firewall to WSL
dnsTunneling=true             # Tunnel DNS through Windows
autoProxy=true                # Use Windows proxy settings
```

## wsl.conf Quick Reference

Location: `/etc/wsl.conf` inside each distro (per-distro settings)

```ini
[boot]
systemd=true                  # Enable systemd as PID 1
command=                      # Command to run on boot

[automount]
enabled=true                  # Auto-mount Windows drives
root=/mnt/                    # Mount point root
options="metadata,umask=22,fmask=11"  # Mount options

[network]
generateResolvConf=true       # Auto-generate /etc/resolv.conf
generateHosts=true            # Auto-generate /etc/hosts
hostname=                     # Custom hostname

[interop]
enabled=true                  # Run Windows executables from WSL
appendWindowsPath=true        # Add Windows PATH to WSL PATH

[user]
default=username              # Default login user
```

## Response Style

- Lead with what you found, not what you're checking
- If a fix requires elevation, tell the user explicitly: "Run this in an elevated PowerShell"
- After fixing, always verify with `wsl -l -v` and a test launch
- Suggest the prevention commands after every successful repair
- If you can't determine the issue, collect the output of ALL levels and present a summary
- Group related problems — don't make the user run 10 separate commands when 3 will do
