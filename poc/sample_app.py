"""Sample desktop app (Tkinter) buat tes CUA — mirroring alur Prudential.

Alur: login (username+password) -> home + menu (Home / Form / About) ->
Form 6 field (Nama, Tempat Tinggal, Tanggal Lahir, Email, No Telepon, Pekerjaan)
-> Submit.

Native Windows window, BUKAN browser. Dipakai sbg target tes desktop CUA.
Kredensial demo: admin / admin123

Jalankan: python sample_app.py
"""
import tkinter as tk
from tkinter import ttk, messagebox

USERNAME = "admin"
PASSWORD = "admin123"

FORM_FIELDS = [
    "Nama Lengkap",
    "Tempat Tinggal",
    "Tanggal Lahir",
    "Email",
    "Nomor Telepon",
    "Pekerjaan",
]

BG = "#f0f2f5"
ACCENT = "#0a5"
FONT = ("Segoe UI", 12)
FONT_BIG = ("Segoe UI", 18, "bold")


class SampleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sample Form App")
        self.geometry("900x600")
        self.configure(bg=BG)
        self.resizable(False, False)
        # Selalu di atas window lain -> ga ke-hide di belakang VSCode pas CUA jalan.
        self.attributes("-topmost", True)

        self._entries = {}
        self._container = tk.Frame(self, bg=BG)
        self._container.pack(fill="both", expand=True)

        self.show_login()

    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    # --- Login ----------------------------------------------------------
    def show_login(self):
        self._clear()
        f = tk.Frame(self._container, bg=BG)
        f.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(f, text="Login", font=FONT_BIG, bg=BG).grid(
            row=0, column=0, columnspan=2, pady=(0, 24))

        tk.Label(f, text="Username", font=FONT, bg=BG).grid(
            row=1, column=0, sticky="e", padx=8, pady=8)
        self._login_user = tk.Entry(f, font=FONT, width=24)
        self._login_user.grid(row=1, column=1, pady=8)

        tk.Label(f, text="Password", font=FONT, bg=BG).grid(
            row=2, column=0, sticky="e", padx=8, pady=8)
        self._login_pass = tk.Entry(f, font=FONT, width=24, show="*")
        self._login_pass.grid(row=2, column=1, pady=8)

        tk.Button(f, text="Login", font=FONT, bg=ACCENT, fg="white",
                  width=20, command=self._do_login).grid(
            row=3, column=0, columnspan=2, pady=(20, 0))

    def _do_login(self):
        if (self._login_user.get() == USERNAME
                and self._login_pass.get() == PASSWORD):
            self.show_home()
        else:
            messagebox.showerror("Login gagal", "Username atau password salah.")

    # --- Home (menu + content) ------------------------------------------
    def show_home(self):
        self._clear()
        # Sidebar menu
        sidebar = tk.Frame(self._container, bg="#222", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="MENU", font=("Segoe UI", 13, "bold"),
                 bg="#222", fg="white").pack(pady=(24, 16))

        for label, cmd in [("Home", self._page_home),
                           ("Form", self._page_form),
                           ("About", self._page_about)]:
            tk.Button(sidebar, text=label, font=FONT, bg="#333", fg="white",
                      bd=0, width=18, anchor="w", padx=16,
                      command=cmd).pack(pady=2)

        self._content = tk.Frame(self._container, bg="white")
        self._content.pack(side="right", fill="both", expand=True)
        self._page_home()

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _page_home(self):
        self._clear_content()
        tk.Label(self._content, text="Home", font=FONT_BIG, bg="white").pack(
            anchor="w", padx=32, pady=(32, 8))
        tk.Label(self._content,
                 text="Selamat datang. Pilih menu 'Form' untuk mengisi data.",
                 font=FONT, bg="white").pack(anchor="w", padx=32)

    def _page_about(self):
        self._clear_content()
        tk.Label(self._content, text="About", font=FONT_BIG, bg="white").pack(
            anchor="w", padx=32, pady=(32, 8))
        tk.Label(self._content, text="Sample app buat tes desktop CUA.",
                 font=FONT, bg="white").pack(anchor="w", padx=32)

    # --- Form (6 field) -------------------------------------------------
    def _page_form(self):
        self._clear_content()
        self._entries = {}
        tk.Label(self._content, text="Form Data Diri", font=FONT_BIG,
                 bg="white").pack(anchor="w", padx=32, pady=(24, 16))

        grid = tk.Frame(self._content, bg="white")
        grid.pack(anchor="w", padx=32)

        for i, field in enumerate(FORM_FIELDS):
            tk.Label(grid, text=field, font=FONT, bg="white", width=16,
                     anchor="w").grid(row=i, column=0, sticky="w", pady=8)
            e = tk.Entry(grid, font=FONT, width=36)
            e.grid(row=i, column=1, pady=8, padx=(8, 0))
            self._entries[field] = e

        self._form_status = tk.Label(self._content, text="", font=FONT,
                                     bg="white", fg=ACCENT)
        self._form_status.pack(anchor="w", padx=32, pady=(8, 0))

        tk.Button(self._content, text="Submit", font=FONT, bg=ACCENT,
                  fg="white", width=20, command=self._submit_form).pack(
            anchor="w", padx=32, pady=(16, 0))

    def _submit_form(self):
        values = {k: e.get() for k, e in self._entries.items()}
        filled = sum(1 for v in values.values() if v.strip())
        self._form_status.config(
            text=f"Submitted. {filled}/{len(FORM_FIELDS)} field terisi.")
        print("[FORM SUBMITTED]")
        for k, v in values.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    SampleApp().mainloop()
