# QAgent — AI-Powered Frontend QA Automation

QAgent adalah project demo **automation testing platform** untuk aplikasi web frontend. QAgent menggunakan **Playwright** untuk menjalankan browser automation, **Groq AI** sebagai agent yang membuat dan mengevaluasi test case, serta **Tavily** untuk kebutuhan web search berbasis AI.

Project ini mendemonstrasikan bagaimana proses QA dapat dijalankan otomatis melalui GitHub Actions setiap kali Pull Request dibuat atau diperbarui.

## Fitur utama

- Menjalankan browser automation menggunakan Playwright Chromium.
- Melakukan discovery terhadap halaman dan elemen frontend sebelum test dibuat.
- Membuat beberapa test case berdasarkan konteks Pull Request, terutama commit message, judul, dan deskripsi PR.
- Menggunakan Groq AI untuk:
  - menghasilkan test scenario dari user story dan elemen halaman yang ditemukan;
  - mengevaluasi hasil eksekusi test;
  - menentukan status `pass` atau `fail` serta alasan kegagalan.
- Mengumpulkan console error dari browser selama test berjalan.
- Menghasilkan laporan bug dalam format JSON.
- Menjalankan automation secara otomatis melalui GitHub Workflow dengan trigger Pull Request.
- Mendukung konfigurasi target aplikasi dan secret melalui environment variable.

## Alur kerja

```text
Pull Request dibuat atau diperbarui
                │
                ▼
        GitHub Actions workflow
                │
                ▼
       Install Python dependencies
                │
                ▼
         Install Playwright Chromium
                │
                ▼
      Jalankan frontend_qa/agent.py
                │
                ▼
  Scan halaman login, products, dan cart
                │
                ▼
 Groq AI membuat test case dari konteks PR
                │
                ▼
      Playwright mengeksekusi test case
                │
                ▼
 Groq AI mengevaluasi hasil dan memberi verdict
                │
                ▼
      Simpan bug report dan test report
```

## Struktur project

```text
.
├── .github/
│   └── workflows/
│       └── qa_agent.yml          # GitHub Actions workflow
├── frontend_qa/
│   ├── agent.py                  # Orkestrasi discovery, generate, execute, dan verdict
│   ├── browser_tools.py          # Wrapper Playwright untuk interaksi browser
│   └── reporter.py               # Pembuatan report hasil QA
├── reports/                      # Output report dan screenshot saat runtime
├── requirements.txt              # Dependencies Python
└── README.md
```

## Persyaratan

- Python 3.11 atau lebih baru
- Google Chrome atau Chromium
- API key Groq
- URL aplikasi frontend yang dapat diakses oleh runner GitHub Actions
- Tavily API key apabila fitur web search Tavily digunakan oleh komponen agent

## Instalasi lokal

Clone repository dan buat virtual environment:

```bash
git clone https://github.com/omdika/qagent.git
cd qagent
python -m venv .venv
source .venv/bin/activate
```

Pada Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependency dan browser Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Konfigurasi environment variable

Buat file `.env` di root project:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
APP_URL=https://your-frontend-app.example.com
```

`APP_URL` digunakan sebagai base URL aplikasi yang akan diuji. Jika tidak diatur, agent menggunakan default berikut:

```text
http://localhost:3000
```

Jangan commit file `.env` atau API key ke repository.

## Menjalankan QA agent secara lokal

```bash
python frontend_qa/agent.py
```

Saat dijalankan, agent akan:

1. Membaca konteks PR dari `PR_TITLE` dan `PR_BODY` jika tersedia.
2. Mengakses halaman utama aplikasi:
   - `/index.html`
   - `/products.html`
   - `/cart.html`
3. Menemukan input, button, link, label, dan teks yang tersedia.
4. Mengirim user story dan hasil discovery ke Groq AI.
5. Menghasilkan 4–6 test scenario berdasarkan selector yang benar-benar ditemukan.
6. Menjalankan setiap langkah test menggunakan Playwright.
7. Meminta Groq AI menentukan verdict setiap scenario.
8. Menyimpan bug report dan report hasil eksekusi.

Untuk simulasi konteks Pull Request secara lokal:

```bash
export PR_TITLE="Add checkout flow"
export PR_BODY="User dapat menambahkan produk ke cart dan menyelesaikan checkout."
python frontend_qa/agent.py
```

## GitHub Actions

Workflow berada di `.github/workflows/qa_agent.yml` dan berjalan pada event:

```yaml
on:
  pull_request:
    types: [opened, synchronize]
```

Artinya, QA agent berjalan ketika Pull Request baru dibuat atau ketika ada update baru pada Pull Request.

Tambahkan secrets berikut pada repository melalui **Settings → Secrets and variables → Actions**:

| Secret | Kegunaan |
|---|---|
| `GROQ_API_KEY` | API key untuk Groq AI |
| `TAVILY_API_KEY` | API key untuk Tavily web search, jika digunakan |
| `APP_URL` | URL deployed frontend yang akan diuji |
| `TOKEN_GITHUB` | GitHub token jika diperlukan oleh proses reporting |

Workflow melakukan langkah berikut:

1. Checkout source code.
2. Setup Python 3.11.
3. Install dependency dari `requirements.txt`.
4. Install Chromium untuk Playwright.
5. Membuat `.env` dari GitHub Secrets.
6. Menjalankan `python frontend_qa/agent.py`.

## Output report

Output dibuat ketika agent selesai berjalan:

```text
reports/
├── bug_report.json
└── screenshots/
    ├── discovery.png
    └── *.png
```

### `bug_report.json`

File ini berisi daftar test case yang gagal dan informasi bug, termasuk:

- bug ID;
- judul bug;
- severity;
- test case terkait;
- langkah reproduksi;
- expected result;
- actual result atau alasan kegagalan;
- path screenshot.

File report tambahan dibuat oleh `frontend_qa/reporter.py` sesuai implementasi reporter yang digunakan project.

## Contoh konteks test case

Konteks yang dapat digunakan agent antara lain:

- login dengan credential valid;
- login dengan credential tidak valid;
- validasi locked user;
- browse dan filter produk;
- menambahkan produk ke cart;
- memeriksa total cart;
- menyelesaikan checkout;
- memastikan order confirmation ditampilkan.

Agent menggunakan selector dari hasil page discovery sehingga test scenario tidak perlu bergantung pada selector yang dibuat secara manual oleh AI.

## Catatan desain

- Browser dijalankan dalam mode headless pada GitHub Actions.
- Screenshot discovery disimpan untuk membantu investigasi jika struktur halaman tidak sesuai ekspektasi.
- Console error browser dikumpulkan dan ikut dipertimbangkan saat menentukan verdict.
- Selector yang digunakan oleh test case harus berasal dari elemen nyata yang ditemukan saat discovery.
- Commit message, judul PR, dan deskripsi PR dapat dipakai sebagai konteks perubahan fitur dan acuan pembuatan test case.
- Pastikan `APP_URL` dapat diakses dari GitHub-hosted runner; `localhost` hanya cocok untuk pengujian lokal atau workflow yang juga menjalankan aplikasi target.

## Troubleshooting

### Browser tidak dapat dijalankan

Pastikan dependency browser sudah di-install:

```bash
playwright install chromium
```

Pada environment Linux tertentu, gunakan opsi dependency Playwright bila diperlukan:

```bash
playwright install --with-deps chromium
```

### Test tidak menemukan halaman

Periksa nilai `APP_URL` dan pastikan aplikasi menyediakan route berikut:

```text
/index.html
/products.html
/cart.html
```

### Groq API error

Periksa bahwa `GROQ_API_KEY` tersedia dan valid. Jangan menuliskan key secara langsung di source code atau log.

### Report tidak muncul

Pastikan agent memiliki permission untuk membuat folder `reports/` dan proses berjalan sampai tahap reporter. Periksa log GitHub Actions untuk menemukan step yang gagal.

## Status project

Project ini ditujukan sebagai **demo dan proof of concept** untuk AI-assisted frontend QA automation. Untuk penggunaan production, pertimbangkan penambahan schema validation untuk response LLM, retry dan timeout policy, artifact upload pada GitHub Actions, masking data sensitif, serta test isolation antar-scenario.

## Lisensi

Belum ditentukan. Tambahkan file lisensi apabila project akan dipublikasikan atau digunakan oleh pihak lain.
