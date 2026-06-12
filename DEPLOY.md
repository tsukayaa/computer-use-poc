# Deploy POC ke GKE — Panduan Laptop Kantor

Tujuan: jalanin AI agent di dalam pod GKE, agent login ke web target,
screenshot tiap step ke-save sebagai bukti buat SPV.

---

## 0. Prasyarat
```bash
kubectl config current-context     # harus cluster Prudential
kubectl get nodes                  # harus jalan tanpa error
```

---

## 1. Ambil kode terbaru
```bash
git pull
```
> `computer-use-preview` sekarang folder biasa (bukan submodule).
> Jangan jalanin `git submodule update` — udah ga relevan.

---

## 2. Jalanin pod
```bash
kubectl run computer-use-poc \
  --image=python:3.13 \
  --restart=Never \
  -it \
  -- /bin/bash
```
Masuk langsung ke dalam pod.

---

## 3. Install dari dalam pod
```bash
git clone https://github.com/tsukayaa/computer-use-poc.git
cd computer-use-poc/computer-use-preview
pip install -r requirements.txt
playwright install --with-deps chromium
```

---

## 4. Set API key
```bash
export GEMINI_API_KEY='ISI_KEY_DISINI'
```

---

## 5. Jalanin agent
```bash
cd ../poc
python orchestrator.py --user 1
```
Bakal kelihatan `[QUERY]`, reasoning agent, dan `[RESULT]` di terminal.
Screenshot tiap step ke-save di `shots/user_1_standard_user/`.

---

## 6. Ambil screenshot (bukti buat SPV)
Buka terminal baru di laptop kantor (jangan keluar dari pod):
```bash
kubectl cp computer-use-poc:/root/computer-use-poc/poc/shots ./shots
```
Buka `./shots/user_1_standard_user/` — file `step_XXXX.png` terakhir =
isi halaman setelah login = bukti agent berhasil masuk.

---

## 7. Beres-beres
```bash
kubectl delete pod computer-use-poc
```

---

## Target web & kredensial
- URL target: ubah `TARGET_URL` di `poc/orchestrator.py`
- Kredensial login: isi `poc/users.csv` (kolom: `username,password`)

---

## Troubleshooting

**Browser crash: `No usable sandbox`**
Edit `computer-use-preview/computers/playwright/playwright.py` baris ~104,
tambah `--no-sandbox` ke list args:
```python
args=[
    "--no-sandbox",
    "--disable-extensions",
    ...
]
```

**Agent timeout / ga bisa konek**
Test dari dalam pod:
```bash
curl -I https://generativelanguage.googleapis.com
curl -I https://URL_PRUHUB
```
Kalau gagal → minta tim infra buka egress dari pod ke dua host itu.

**`401` / `API key not valid`**
```bash
export GEMINI_API_KEY='KEY_BARU'
python orchestrator.py --user 1
```
