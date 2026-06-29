<#
  Probe HLLAPI read-only buat PC5250 (IBM i Access / Client Access for Windows)
  -- versi PowerShell, TANPA install Python.

  Kenapa: python.org keblok di kantor + butuh 32-bit. PowerShell 32-bit udah ada
  bawaan Windows dan bisa P/Invoke ehlapi32.dll (32-bit) langsung.

  AMAN: cuma Connect + Query Status + Copy Presentation Space + Query Cursor.
  TIDAK ngetik, TIDAK kirim key, TIDAK ubah host.

  PRASYARAT: emulator PC5250 kebuka + udah login, sesi "B" (judul "B - 5250 Display").

  JALANIN -- WAJIB PowerShell 32-bit:
    C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File .\hllapi_probe.ps1
  Opsional kasih sesi lain:  ... -File .\hllapi_probe.ps1 -Session B
#>
param(
  [string]$Session = "B",
  [string]$EmulatorDir = "C:\Program Files (x86)\IBM\Client Access\Emulator",
  [ValidateSet("StdCall", "Cdecl")][string]$Conv = "StdCall"
)

if ([Environment]::Is64BitProcess) {
  Write-Host "[!] Ini PowerShell 64-bit. ehlapi32.dll = 32-bit -> bakal gagal load." -ForegroundColor Yellow
  Write-Host "    Jalanin pakai PowerShell 32-bit:" -ForegroundColor Yellow
  Write-Host "    C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File .\hllapi_probe.ps1"
  return
}

# Biar ehlapi32.dll ketemu (resolve dari folder Emulator).
if (Test-Path $EmulatorDir) { $env:PATH = "$EmulatorDir;$env:PATH" }

# P/Invoke. Dua varian calling-convention; default StdCall (EHLLAPI = PASCAL).
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
try {
  Add-Type -TypeDefinition $src -ErrorAction Stop
} catch {
  Write-Host "[X] Add-Type gagal (compile/.NET keblok?): $_" -ForegroundColor Red
  return
}

function Invoke-Hll([int]$func, [byte[]]$data, [int]$length) {
  $f = $func; $l = $length; $rc = 0
  if ($Conv -eq "Cdecl") { [Hll]::C([ref]$f, $data, [ref]$l, [ref]$rc) }
  else { [Hll]::S([ref]$f, $data, [ref]$l, [ref]$rc) }
  return [pscustomobject]@{ Length = $l; Rc = $rc }
}

$RC = @{
  0 = "OK"; 1 = "PS invalid / sesi salah"; 2 = "param error"; 4 = "PS error (host sibuk?)";
  5 = "data inhibited / panjang salah"; 9 = "system error"; 11 = "resource ga tersedia"
}
function RcText([int]$rc) { $m = $RC[$rc]; if (-not $m) { $m = "unknown" }; "rc=$rc ($m)" }

Write-Host "DLL dir : $EmulatorDir"
Write-Host "Sesi    : $Session"
Write-Host "Conv    : $Conv`n"

# 1) Connect Presentation Space.
$buf = [System.Text.Encoding]::ASCII.GetBytes($Session)
try {
  $r = Invoke-Hll 1 $buf $Session.Length
} catch {
  Write-Host "[X] Call gagal: $_" -ForegroundColor Red
  Write-Host "    Coba calling-convention lain: tambah  -Conv Cdecl" -ForegroundColor Yellow
  return
}
Write-Host ("[Connect]        " + (RcText $r.Rc))
if ($r.Rc -ne 0) {
  Write-Host "    Gagal connect. Cek emulator kebuka + huruf sesi bener." -ForegroundColor Yellow
  Write-Host "    Kalau rc aneh, coba  -Conv Cdecl" -ForegroundColor Yellow
  return
}

# 2) Query Session Status -> rows x cols.
$rows = 24; $cols = 80
$buf = New-Object byte[] 20
$buf[0] = [byte][char]$Session
$r = Invoke-Hll 22 $buf 18
if ($r.Rc -eq 0) {
  $qr = [BitConverter]::ToUInt16($buf, 12)
  $qc = [BitConverter]::ToUInt16($buf, 14)
  if ($qr -ge 1 -and $qr -le 100 -and $qc -ge 1 -and $qc -le 200) { $rows = $qr; $cols = $qc }
}
Write-Host ("[Session Status] " + (RcText $r.Rc) + " -> $rows x $cols")

# 3) Copy Presentation Space (BACA seluruh layar).
$size = $rows * $cols
$buf = New-Object byte[] ($size + 1)
$r = Invoke-Hll 5 $buf $size
Write-Host ("[Copy PS]        " + (RcText $r.Rc) + ", $($r.Length) char`n")
if ($r.Rc -ne 0) { Write-Host "    Copy PS gagal." -ForegroundColor Yellow; return }

$latin1 = [System.Text.Encoding]::GetEncoding("ISO-8859-1")
$text = $latin1.GetString($buf, 0, $size)
$bar = "=" * $cols
Write-Host $bar
for ($i = 0; $i -lt $rows; $i++) {
  $line = $text.Substring($i * $cols, $cols)
  $clean = -join ($line.ToCharArray() | ForEach-Object {
    $c = [int]$_; if ($c -ge 32 -and $c -lt 127) { [char]$c } else { " " } })
  "{0,2} |{1}" -f ($i + 1), $clean.TrimEnd()
}
Write-Host $bar

# 4) Query Cursor Location (offset balik di Length).
$buf = New-Object byte[] 4
$r = Invoke-Hll 7 $buf 0
if ($r.Rc -eq 0) {
  $pos = $r.Length
  $rw = [math]::Floor($pos / $cols) + 1; $cl = ($pos % $cols) + 1
  Write-Host ("`n[Cursor]         " + (RcText $r.Rc) + " offset=$pos (row $rw, col $cl)")
} else {
  Write-Host ("`n[Cursor]         " + (RcText $r.Rc))
}

# 5) Disconnect (cleanup, ga ubah host).
$buf = [System.Text.Encoding]::ASCII.GetBytes($Session)
Invoke-Hll 2 $buf 1 | Out-Null
Write-Host "`n[Disconnect]     done. Read-only, host ga diubah."
