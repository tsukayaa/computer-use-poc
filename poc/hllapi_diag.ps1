<#
  Diagnosa HLLAPI -- kenapa Connect rc=1.
  Cek: (1) EHLLAPI API hidup? (2) sesi apa yang EHLLAPI lihat?

  Scan Connect huruf A..Z. Yang balik rc 0/4/5 = sesi ADA (4=busy,5=locked,
  tetep "connected"). Semua rc=1 = EHLLAPI ga lihat sesi apa pun.

  AMAN: cuma Connect + Disconnect + Query System. Ga ngetik/ubah host.

  JALANIN (dari folder poc, VSCode terminal ok):
    C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File .\hllapi_diag.ps1
  Bandingin calling-convention:
    ... -File .\hllapi_diag.ps1 -Conv Cdecl
#>
param(
  [string]$EmulatorDir = "C:\Program Files (x86)\IBM\Client Access\Emulator",
  [ValidateSet("StdCall", "Cdecl")][string]$Conv = "StdCall"
)

if ([Environment]::Is64BitProcess) {
  Write-Host "[!] PowerShell 64-bit -> ehlapi32.dll 32-bit ga bakal load." -ForegroundColor Yellow
  Write-Host "    Pakai: C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
  return
}
if (Test-Path $EmulatorDir) { $env:PATH = "$EmulatorDir;$env:PATH" }

$src = @"
using System;
using System.Runtime.InteropServices;
public static class Hll {
  [DllImport("ehlapi32.dll", EntryPoint="hllapi", CallingConvention=CallingConvention.StdCall)]
  public static extern void S(ref int func, byte[] data, ref int len, ref int rc);
  [DllImport("ehlapi32.dll", EntryPoint="hllapi", CallingConvention=CallingConvention.Cdecl)]
  public static extern void C(ref int func, byte[] data, ref int len, ref int rc);
}
"@
try { Add-Type -TypeDefinition $src -ErrorAction Stop }
catch { Write-Host "[X] Add-Type gagal: $_" -ForegroundColor Red; return }

function Invoke-Hll([int]$func, [byte[]]$data, [int]$length) {
  $f = $func; $l = $length; $rc = 0
  if ($Conv -eq "Cdecl") { [Hll]::C([ref]$f, $data, [ref]$l, [ref]$rc) }
  else { [Hll]::S([ref]$f, $data, [ref]$l, [ref]$rc) }
  return [pscustomobject]@{ Length = $l; Rc = $rc }
}

Write-Host "Conv : $Conv`n"

# --- Query System (20): API hidup? + versi --------------------------------
$buf = New-Object byte[] 64
$r = Invoke-Hll 20 $buf 64
Write-Host ("[Query System]  rc=" + $r.Rc + "  (0 = EHLLAPI hidup)")
if ($r.Rc -eq 0) {
  $hex = ($buf[0..23] | ForEach-Object { $_.ToString("X2") }) -join " "
  $asc = -join ($buf[0..23] | ForEach-Object { if ($_ -ge 32 -and $_ -lt 127) { [char]$_ } else { "." } })
  Write-Host "    raw[0..23] hex: $hex"
  Write-Host "    raw[0..23] asc: $asc"
}

# --- Scan Connect A..Z ----------------------------------------------------
Write-Host "`n[Scan Connect A..Z]  (cari yang rc 0/4/5)"
$found = @()
foreach ($code in 65..90) {
  $letter = [char]$code
  $b = [System.Text.Encoding]::ASCII.GetBytes([string]$letter)
  $r = Invoke-Hll 1 $b 1
  if ($r.Rc -in 0, 4, 5) {
    Write-Host ("    $letter -> rc=" + $r.Rc + "  <== SESI ADA") -ForegroundColor Green
    $found += $letter
    $bd = [System.Text.Encoding]::ASCII.GetBytes([string]$letter)
    Invoke-Hll 2 $bd 1 | Out-Null   # disconnect
  } elseif ($r.Rc -ne 1) {
    Write-Host ("    $letter -> rc=" + $r.Rc)
  }
}

Write-Host ""
if ($found.Count -gt 0) {
  Write-Host ("HASIL: sesi kebaca -> " + ($found -join ", ")) -ForegroundColor Green
  Write-Host ("Run probe pakai huruf itu, mis:  ...hllapi_probe.ps1 -Session " + $found[0])
} else {
  Write-Host "HASIL: EHLLAPI ga lihat sesi apa pun (semua rc=1)." -ForegroundColor Yellow
  Write-Host "  Kemungkinan: (a) HLLAPI di-disable di config PC5250,"
  Write-Host "               (b) emulator pakai DLL HLLAPI lain (WinHLLAPI/pcshll), atau"
  Write-Host "               (c) butuh -Conv Cdecl (coba run ulang dgn itu)."
}
