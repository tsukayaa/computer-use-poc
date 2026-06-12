# Deploy POC ke GKE — Panduan Laptop Kantor

Panduan langkah demi langkah: dari `git pull` sampai agent jalan di dalam pod
dan screenshot-nya bisa diambil. Ikuti urut dari atas.

> **Ganti dulu placeholder ini sebelum mulai:**
> - `REGION` — region Artifact Registry, contoh `asia-southeast2`
> - `PROJECT_ID` — GCP project id Prudential
> - `REPO` — nama repo Artifact Registry
> - `GEMINI_API_KEY` — key dari SPV
>
> Cara cepat set sebagai variabel shell (Linux/Mac di laptop kantor):
> ```bash
> export IMAGE="REGION-docker.pkg.dev/PROJECT_ID/REPO/computer-use-poc:latest"
> ```

---

## 0. Prasyarat (cek sekali)
Pastikan tool ini ada di laptop kantor:
```bash
git --version
docker --version
kubectl version --client
gcloud version          # kalau pakai Artifact Registry GCP
```
Dan `kubectl` udah nunjuk ke cluster yang bener:
```bash
kubectl config current-context     # harus cluster Prudential
kubectl get nodes                  # harus jalan tanpa error
```

---

## 1. Ambil kode terbaru
```bash
git pull
```
> `computer-use-preview` sekarang **folder biasa** (bukan submodule lagi).
> Sesudah pull, folder itu langsung keisi penuh. **JANGAN** jalanin
> `git submodule update` — udah ga relevan.

---

## 2. Build image Docker
Dari root repo (tempat `Dockerfile` berada):
```bash
docker build -t "$IMAGE" .
```
Base image: `mcr.microsoft.com/playwright/python:v1.55.0-noble` (Chromium +
library OS udah preinstalled).

> Kalau build gagal narik base image dari `mcr.microsoft.com` (registry
> eksternal keblok), berarti perlu mirror image itu ke registry internal Pru
> dulu. Lihat bagian **Troubleshooting**.

---

## 3. Push image ke registry
Login dulu (sekali):
```bash
gcloud auth configure-docker REGION-docker.pkg.dev
```
Push:
```bash
docker push "$IMAGE"
```

---

## 4. Set image di pod.yaml
Edit `k8s/pod.yaml`, ganti baris `image:` jadi sama persis dengan `$IMAGE`:
```yaml
      image: REGION-docker.pkg.dev/PROJECT_ID/REPO/computer-use-poc:latest
```

---

## 5. Bikin Secret (API key)
Key **tidak** ada di image / repo. Inject lewat Secret cluster:
```bash
kubectl create secret generic gemini-api-key \
  --from-literal=GEMINI_API_KEY='KEY_DARI_SPV'
```
Cek:
```bash
kubectl get secret gemini-api-key
```
> Ganti key nanti: `kubectl delete secret gemini-api-key` lalu buat lagi,
> terus restart pod (step 8).

---

## 6. Jalankan pod
```bash
kubectl apply -f k8s/pod.yaml
kubectl get pod computer-use-poc -w     # tunggu STATUS = Running, Ctrl+C kalau udah
```
Pod ini **idle** (sleep) — belum jalanin agent. Agent dijalanin manual di step 7.

---

## 7. Masuk pod & jalanin agent
```bash
kubectl exec -it computer-use-poc -- /bin/bash
```
Di dalam pod:
```bash
cd /app/poc
python orchestrator.py --user 1
```
Bakal kelihatan `[QUERY]`, reasoning agent, dan `[RESULT]` di terminal.
Screenshot tiap step ke-save ke `/app/poc/shots/user_1_standard_user/`.

Keluar dari pod: `exit`.

---

## 8. Ambil screenshot (bukti buat SPV)
Dari laptop kantor (di luar pod):
```bash
kubectl cp computer-use-poc:/app/poc/shots ./shots
```
Buka `./shots/user_1_standard_user/` — file `step_XXXX.png` **terakhir** =
isi halaman setelah login = bukti agent berhasil masuk.

---

## 9. Beres-beres
```bash
kubectl delete pod computer-use-poc
# secret boleh dibiarkan buat run berikutnya, atau:
# kubectl delete secret gemini-api-key
```

Restart pod (mis. ganti key atau ulang demo):
```bash
kubectl delete pod computer-use-poc
kubectl apply -f k8s/pod.yaml
```

---

## Target web & user
- URL target diatur di `poc/orchestrator.py` baris `TARGET_URL`
  (sekarang `https://www.saucedemo.com` buat test).
- Kredensial login di `poc/users.csv` (kolom: `username,password`).
- Buat PruHub: ganti `TARGET_URL` + isi `users.csv` dengan kredensial PruHub.

---

## Troubleshooting

**Pod `CrashLoopBackOff` / browser error `No usable sandbox`**
Chromium sandbox sering gagal di pod. Edit
`computer-use-preview/computers/playwright/playwright.py` baris ~104,
tambah `--no-sandbox` ke list `args`, lalu **rebuild + push image** (step 2-3):
```python
args=[
    "--no-sandbox",
    "--disable-extensions",
    ...
]
```

**Agent timeout / `Page.screenshot: Timeout` / ga bisa konek**
Egress pod keblok. Pod harus bisa nyampe:
- `generativelanguage.googleapis.com:443` (Gemini API)
- URL target (PruHub):443

Test dari dalam pod:
```bash
kubectl exec -it computer-use-poc -- /bin/bash
curl -I https://generativelanguage.googleapis.com
```
Kalau gagal → minta tim infra buka egress, atau set proxy korporat di
`k8s/pod.yaml`:
```yaml
env:
  - name: HTTPS_PROXY
    value: "http://proxy-pru:port"
  - name: NO_PROXY
    value: "10.0.0.0/8,localhost,127.0.0.1"
```

**`401` / `API key not valid`**
Secret salah/expired. Buat ulang (step 5), restart pod (step 8).

**Build gagal pull base image dari mcr.microsoft.com**
Registry eksternal keblok. Opsi: mirror image
`mcr.microsoft.com/playwright/python:v1.55.0-noble` ke Artifact Registry
internal Pru, lalu ganti baris `FROM` di `Dockerfile` ke path mirror itu.
