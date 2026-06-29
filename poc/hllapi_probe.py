"""Probe HLLAPI read-only buat PC5250 (IBM i Access / Client Access for Windows).

TUJUAN: buktiin kita bisa BACA layar green-screen 5250 lewat EHLLAPI,
deterministik (teks, bukan pixel/screenshot). Ini plan-B kalau computer-use
Gemini ga bisa (butuh :generateContent yang mungkin ga ada di gateway kantor).

AMAN: cuma Connect + Copy Presentation Space + Query Cursor. TIDAK ngetik,
TIDAK kirim key, TIDAK ubah apa-apa di host.

PRASYARAT:
  - Emulator PC5250 lagi KEBUKA + udah login, ada sesi "B" (judul "B - 5250 Display").
  - DLL: ehlapi32.dll (32-bit, dari ...\IBM\Client Access\Emulator).
  - Python WAJIB 32-bit (DLL 32-bit). Kalau pakai 64-bit -> WinError 193.

JALANIN (di laptop kantor, PowerShell):
  python hllapi_probe.py
  # atau kasih path DLL + sesi eksplisit:
  python hllapi_probe.py "C:\\Program Files (x86)\\IBM\\Client Access\\Emulator\\ehlapi32.dll" B
"""
import ctypes
import struct
import sys
from ctypes import byref, c_int, create_string_buffer

# --- CONFIG ----------------------------------------------------------------
# Default coba nama doang (ngandelin PATH). Kalau "not found", kasih full path
# via argv atau ganti di sini ke FullName hasil search kamu.
DLL_PATH = sys.argv[1] if len(sys.argv) > 1 else "ehlapi32.dll"
SESSION = sys.argv[2] if len(sys.argv) > 2 else "B"

# Nomor fungsi EHLLAPI (standar).
FN_CONNECT = 1
FN_DISCONNECT = 2
FN_COPY_PS = 5
FN_QUERY_CURSOR = 7
FN_QUERY_SESSION_STATUS = 22

RC_MEANING = {
    0: "OK",
    1: "PS tidak valid / sesi salah (cek huruf sesi)",
    2: "parameter error",
    4: "PS error (host sibuk?)",
    5: "data inhibited / panjang salah",
    9: "system error",
    11: "resource tidak tersedia",
}


def load_dll() -> ctypes.CDLL:
    bits = struct.calcsize("P") * 8
    if bits != 32:
        print(f"[!] Python ini {bits}-bit. ehlapi32.dll = 32-bit.")
        print("    Load kemungkinan gagal (WinError 193). Pakai Python 32-bit.")
    try:
        # EHLLAPI 'hllapi' = __stdcall -> WinDLL.
        return ctypes.WinDLL(DLL_PATH)
    except OSError as e:
        print(f"[X] Gagal load DLL: {e}")
        print("    - WinError 193  -> bitness mismatch, pakai Python 32-bit.")
        print("    - not found     -> kasih full path: python hllapi_probe.py <path> B")
        sys.exit(1)


def make_caller(dll: ctypes.CDLL):
    try:
        fn = dll.hllapi
    except AttributeError:
        print("[X] Entry 'hllapi' ga ada di DLL. Cek dumpbin/exports.")
        sys.exit(1)

    def call(func: int, buf, length: int):
        f = c_int(func)
        ln = c_int(length)
        rc = c_int(0)
        fn(byref(f), buf, byref(ln), byref(rc))
        return ln.value, rc.value

    return call


def rc_text(rc: int) -> str:
    return f"rc={rc} ({RC_MEANING.get(rc, 'unknown')})"


def main():
    print(f"DLL     : {DLL_PATH}")
    print(f"Sesi    : {SESSION}")
    dll = load_dll()
    call = make_caller(dll)

    # 1) Connect Presentation Space.
    buf = create_string_buffer(SESSION.encode("ascii"), 256)
    _, rc = call(FN_CONNECT, buf, len(SESSION))
    print(f"\n[Connect]            {rc_text(rc)}")
    if rc != 0:
        print("    Gagal connect. Pastikan emulator kebuka + sesi bener.")
        sys.exit(1)

    # 2) Query Session Status -> ambil rows x cols PS.
    rows, cols = 24, 80
    buf = create_string_buffer(20)
    buf[0:1] = SESSION.encode("ascii")
    _, rc = call(FN_QUERY_SESSION_STATUS, buf, 18)
    if rc == 0:
        raw = buf.raw
        r = int.from_bytes(raw[12:14], "little")
        c = int.from_bytes(raw[14:16], "little")
        if 1 <= r <= 100 and 1 <= c <= 200:
            rows, cols = r, c
    print(f"[Session Status]     {rc_text(rc)} -> {rows} x {cols}")

    # 3) Copy Presentation Space (BACA seluruh layar).
    size = rows * cols
    buf = create_string_buffer(size + 1)
    ln, rc = call(FN_COPY_PS, buf, size)
    print(f"[Copy PS]            {rc_text(rc)}, {ln} char\n")
    if rc not in (0,):
        print("    Copy PS gagal. Layar mungkin kosong/locked.")
        sys.exit(1)

    text = buf.raw[:size].decode("latin-1")
    print("=" * cols)
    for i in range(rows):
        line = text[i * cols:(i + 1) * cols]
        clean = "".join(ch if 32 <= ord(ch) < 127 else " " for ch in line)
        print(f"{i + 1:2} |{clean.rstrip()}")
    print("=" * cols)

    # 4) Query Cursor Location.
    buf = create_string_buffer(4)
    pos, rc = call(FN_QUERY_CURSOR, buf, 0)
    if rc == 0 and cols:
        print(f"\n[Cursor]             {rc_text(rc)} offset={pos} "
              f"(row {pos // cols + 1}, col {pos % cols + 1})")
    else:
        print(f"\n[Cursor]             {rc_text(rc)}")

    # 5) Disconnect (cleanup, ga ubah host).
    buf = create_string_buffer(SESSION.encode("ascii"), 4)
    call(FN_DISCONNECT, buf, 1)
    print("\n[Disconnect]         done. Read-only, host tidak diubah.")


if __name__ == "__main__":
    main()
