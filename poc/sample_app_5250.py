"""Sample app gaya IBM 5250 green-screen (Tkinter) — tiru app underwriting Pru.

FULL KEYBOARD, NO MOUSE (kayak 5250 asli):
- klik mouse TIDAK memindah fokus field (di-disable)
- navigasi: Tab / Shift-Tab / panah Atas-Bawah
- pilih menu: ketik nomor opsi + Enter
- F3=Exit, F5=Refresh, F12=Back

Tujuan: tes apakah CUA sanggup EKSPLOR + isi app keyboard-driven TANPA mouse.
Pakai DUMMY data, ga ada PII.

Alur: Sign On -> Main Menu -> (opsi 1) Financial Underwriting -> isi -> Enter.
Kredensial demo: admin / admin123

Jalankan: python sample_app_5250.py
"""
import tkinter as tk

USERNAME = "admin"
PASSWORD = "admin123"

GREEN = "#33ff33"
BLACK = "#000000"
FIELD_BG = "#001a00"
FONT = ("Consolas", 15)
FONT_BOLD = ("Consolas", 15, "bold")


class App5250(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("B - 5250 Display")
        self.geometry("960x680")
        self.configure(bg=BLACK)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._body = tk.Frame(self, bg=BLACK)
        self._body.pack(fill="both", expand=True, padx=24, pady=20)

        self.bind("<F3>", lambda e: self.destroy())
        self.show_signon()

    # --- helpers --------------------------------------------------------
    def _clear(self):
        for seq in ("<Return>", "<F5>", "<F12>"):
            self.unbind(seq)
        for w in self._body.winfo_children():
            w.destroy()

    def _make_entry(self, parent, row, label, width, show=None):
        """Field + label dot-leader. Mouse TIDAK bisa fokus (keyboard only)."""
        tk.Label(parent, text=label, font=FONT, fg=GREEN, bg=BLACK,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=4)
        e = tk.Entry(parent, font=FONT, fg=GREEN, bg=FIELD_BG,
                     insertbackground=GREEN, width=width, relief="flat",
                     show=show)
        e.grid(row=row, column=1, sticky="w", padx=(8, 0), pady=4)
        # Disable mouse: klik & drag ga mindah fokus.
        e.bind("<Button-1>", lambda ev: "break")
        e.bind("<B1-Motion>", lambda ev: "break")
        return e

    def _arrow_nav(self, entries):
        """Panah Atas/Bawah pindah antar field."""
        for i, e in enumerate(entries):
            e.bind("<Down>", lambda ev, n=entries[(i + 1) % len(entries)]:
                   (n.focus_set(), "break")[1])
            e.bind("<Up>", lambda ev, p=entries[(i - 1) % len(entries)]:
                   (p.focus_set(), "break")[1])

    def _status(self, text):
        self._status_lbl.config(text=text)

    # --- Sign On --------------------------------------------------------
    def show_signon(self):
        self._clear()
        tk.Label(self._body, text="Sign On", font=FONT_BOLD, fg=GREEN,
                 bg=BLACK).pack(anchor="w", pady=(8, 24))
        grid = tk.Frame(self._body, bg=BLACK)
        grid.pack(anchor="w", padx=40)

        self._user = self._make_entry(grid, 0, "User  . . . . . .", 20)
        self._pass = self._make_entry(grid, 1, "Password  . . . .", 20, show="*")
        self._arrow_nav([self._user, self._pass])

        self._status_lbl = tk.Label(self._body, text="", font=FONT, fg=GREEN,
                                    bg=BLACK)
        self._status_lbl.pack(anchor="w", padx=40, pady=(16, 0))
        tk.Label(self._body, text="F3=Exit    Enter=Sign On", font=FONT,
                 fg=GREEN, bg=BLACK).pack(side="bottom", anchor="w")

        self.bind("<Return>", lambda e: self._do_signon())
        self._user.focus_set()

    def _do_signon(self):
        if self._user.get() == USERNAME and self._pass.get() == PASSWORD:
            self.show_menu()
        else:
            self._status("Sign on failed. Try again.")

    # --- Main Menu ------------------------------------------------------
    def show_menu(self):
        self._clear()
        tk.Label(self._body, text="Main Menu", font=FONT_BOLD, fg=GREEN,
                 bg=BLACK).pack(anchor="w", pady=(8, 20))

        opts = tk.Frame(self._body, bg=BLACK)
        opts.pack(anchor="w", padx=40)
        for line in ("1. Financial Underwriting by Contract",
                     "2. Client Inquiry",
                     "3. Reports"):
            tk.Label(opts, text=line, font=FONT, fg=GREEN, bg=BLACK,
                     anchor="w").pack(anchor="w", pady=2)

        sel = tk.Frame(self._body, bg=BLACK)
        sel.pack(anchor="w", padx=40, pady=(20, 0))
        self._sel = self._make_entry(sel, 0, "Selection . . . .", 4)

        self._status_lbl = tk.Label(self._body, text="", font=FONT, fg=GREEN,
                                    bg=BLACK)
        self._status_lbl.pack(anchor="w", padx=40, pady=(16, 0))
        tk.Label(self._body,
                 text="Type option number, press Enter.    F3=Exit",
                 font=FONT, fg=GREEN, bg=BLACK).pack(side="bottom", anchor="w")

        self.bind("<Return>", lambda e: self._do_menu())
        self._sel.focus_set()

    def _do_menu(self):
        choice = self._sel.get().strip()
        if choice == "1":
            self.show_underwriting()
        elif choice in ("2", "3"):
            self._status(f"Option {choice} not available in this demo.")
        else:
            self._status("Invalid option. Type 1, 2, or 3.")

    # --- Underwriting screen --------------------------------------------
    def show_underwriting(self):
        self._clear()
        tk.Label(self._body,
                 text="Financial Underwriting by Contract (Sharia)",
                 font=FONT_BOLD, fg=GREEN, bg=BLACK).pack(anchor="w",
                                                          pady=(4, 20))
        grid = tk.Frame(self._body, bg=BLACK)
        grid.pack(anchor="w", padx=20)

        self._f_clientno = self._make_entry(grid, 0, "Client Number . .", 16)
        self._f_clientnm = self._make_entry(grid, 1, "Client Name . . .", 30)
        self._f_currency = self._make_entry(grid, 2, "Currency  . . . .", 6)
        self._f_covcode  = self._make_entry(grid, 3, "Coverage Code . .", 8)
        self._f_sumrisk  = self._make_entry(grid, 4, "Sum At Risk . . .", 20)
        self._fields = [self._f_clientno, self._f_clientnm, self._f_currency,
                        self._f_covcode, self._f_sumrisk]
        self._arrow_nav(self._fields)

        self._status_lbl = tk.Label(self._body, text="", font=FONT, fg=GREEN,
                                    bg=BLACK)
        self._status_lbl.pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(self._body,
                 text="F3=Exit   F5=Refresh   F12=Back   Enter=Submit",
                 font=FONT, fg=GREEN, bg=BLACK).pack(side="bottom", anchor="w")

        self.bind("<Return>", lambda e: self._submit())
        self.bind("<F5>", lambda e: self._refresh())
        self.bind("<F12>", lambda e: self.show_menu())
        self._f_clientno.focus_set()

    def _refresh(self):
        for f in self._fields:
            f.delete(0, tk.END)
        self._status("Screen refreshed.")
        self._f_clientno.focus_set()

    def _submit(self):
        data = {
            "Client Number": self._f_clientno.get(),
            "Client Name": self._f_clientnm.get(),
            "Currency": self._f_currency.get(),
            "Coverage Code": self._f_covcode.get(),
            "Sum At Risk": self._f_sumrisk.get(),
        }
        filled = sum(1 for v in data.values() if v.strip())
        self._status(f"Record saved. {filled}/5 fields entered.")
        print("[5250 SUBMIT]")
        for k, v in data.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    App5250().mainloop()
