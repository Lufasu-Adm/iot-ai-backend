# Dockerized Predictive Monitoring System for IoT and AI-Driven Anomaly Detection

## Ringkasan Proyek

Sebuah purwarupa arsitektur *backend* berbasis *microservices* yang dirancang untuk menerima, memproses, menyimpan, dan memvisualisasikan data sensor IoT secara *real-time*. Sistem ini menerapkan *event-driven architecture* dan modul AI statistik sederhana (Moving Average + rolling std / z-score) untuk mendeteksi anomali suhu.

Dokumen ini disusun agar bisa langsung dicopy–paste ke README.md pada repositori GitHub dan dipakai sebagai referensi pengembangan, pengujian, dan demonstrasi.

---

## Tujuan (Why)

1. Mendemonstrasikan integrasi layanan containerized (MQTT broker, TSDB, message queue, worker AI, visualisasi) dalam satu ekosistem Docker.
2. Menyediakan pipeline data end-to-end dari perangkat IoT (atau simulator) hingga dashboard monitoring.
3. Menyisipkan modul deteksi anomali sederhana yang dapat dievaluasi dan dikembangkan lebih lanjut untuk skripsi/proyek penelitian.

---

## Komponen Arsitektur (What & How)

Sistem terdiri dari layanan-layanan terisolasi yang saling berkomunikasi melalui jaringan internal Docker:

1. **Eclipse Mosquitto (MQTT broker)**

   * Fungsi: menerima publikasi data sensor dari perangkat/simulator.
   * Peran: gateway komunikasi ringan (pub/sub).

2. **Backend Collector (Python)**

   * Fungsi: subscribe ke topik MQTT, melakukan validasi payload JSON, menulis data ke InfluxDB, dan menempatkan entri ke antrean Redis untuk pemrosesan asinkron.

3. **InfluxDB 2 (Time-Series Database)**

   * Fungsi: penyimpanan metrik waktu-berurutan dengan schema yang dioptimalkan untuk query agregasi/time-range.

4. **Redis (in-memory queue)**

   * Fungsi: buffer / queue untuk data yang akan dianalisis oleh AI Worker; memungkinkan *backpressure* dan retry sederhana.

5. **AI Worker (Python)**

   * Fungsi: dequeue data dari Redis, menerapkan algoritma Moving Average / rolling std, menentukan apakah sebuah titik adalah anomali, dan menulis status ke InfluxDB / log.
   * Catatan: didesain stateless terhadap antrean (state rolling disimpan lokal per sensor, atau bisa disimpan di Redis untuk replikasi).

6. **Grafana**

   * Fungsi: visualisasi real-time dari data InfluxDB, konfigurasi alert, dan pembuatan dasbor untuk demonstrasi.

---

## Technology Stack

* **Containerization:** Docker, Docker Compose
* **Bahasa:** Python 3.10+
* **Library utama (Python):** `paho-mqtt`, `redis`, `influxdb-client`, `numpy`
* **Service images:** `eclipse-mosquitto`, `redis:alpine`, `influxdb:2.x`, `grafana/grafana`

---

## Alur Data (Data Flow) — langkah demi langkah

1. Perangkat/simulator mem-publish JSON payload ke broker MQTT pada topik `sensors/temperature/<sensor_id>`.
2. Backend Collector melakukan subscribe pada topik tersebut, melakukan parsing dan validasi, lalu:

   * Menulis titik metrik ke InfluxDB (measurement: `temperature`, tags: `sensor_id`, fields: `value`, `status`).
   * Push JSON serial ke Redis list (mis. `rpush queue:temperature`).
3. AI Worker men-*poll* Redis (`blpop`), melakukan update rolling-statistics untuk sensor terkait, menilai apakah titik termasuk anomali.
4. Jika terdeteksi anomali: worker menulis event peringatan ke InfluxDB (measurement: `anomalies`) dan/atau mengirim notifikasi/log.
5. Grafana membaca InfluxDB dan menampilkan metrik + peringatan pada dashboard.

Analogi singkat: Backend Collector berperan seperti resepsionis di rumah sakit—mencatat kedatangan pasien (data) dan meneruskan file pasien (queue) ke analis medis (AI Worker) yang bertugas menilai kondisi kritis (anomali).

---

## Algoritma Deteksi Anomali — Penjelasan Teknis (Why & How)

**Pendekatan dasar:** Rolling Moving Average (MA) dan Rolling Standard Deviation (SD). Metode ini populer untuk deteksi lonjakan singkat pada sinyal sensor.

* Notasi:

  * `x_t` : pembacaan suhu saat waktu t
  * `N` : jendela (window) untuk rolling mean
  * `MA_t = (1/N) * sum_{i=0}^{N-1} x_{t-i}`
  * `SD_t = sqrt((1/(N-1)) * sum_{i=0}^{N-1} (x_{t-i} - MA_t)^2)`

* Aturan deteksi sederhana (z-score threshold):

  * `z_t = (x_t - MA_t) / SD_t`
  * Jika `|z_t| >= k` (contoh: `k = 3`), tandai sebagai anomali.

**Parameter & trade-offs**

* `N` kecil → deteksi cepat, tetapi rentan false positives (bising).
* `N` besar → lebih stabil, tetapi lambat merespons perubahan cepat.
* `k` rendah → lebih sensitif (lebih banyak false positives).
* Pilih kombinasi `N` dan `k` berdasarkan karakteristik sensor dan kebutuhan SLA deteksi.

**Variasi yang direkomendasikan:**

* EWMA (Exponentially Weighted Moving Average) untuk memberi bobot lebih ke observasi terbaru.
* Kombinasi MA + persentil (mis. 99th percentile) untuk sinyal dengan distribusi non-gaussian.

**Pseudocode singkat (AI Worker):**

```python
# rolling window per sensor (menggunakan deque) untuk mean & std
for message in redis.blpop('queue:temperature'):
    sensor_id = message['sensor_id']
    value = message['value']
    window = windows[sensor_id]  # deque maxlen=N
    window.append(value)
    if len(window) == N:
        ma = mean(window)
        sd = std(window)
        z = (value - ma) / (sd if sd>0 else 1e-6)
        if abs(z) >= k:
            write_anomaly_to_influx(sensor_id, value, z)
        write_point_to_influx(sensor_id, value, status='ok' or 'anomaly')
```

---

## Prasyarat (Prerequisites)

Pastikan mesin Anda memiliki:

* Docker Engine
* Docker Compose
* Git
* Python 3.10+ (hanya diperlukan bila menjalankan simulator lokal di luar kontainer)

---

## Instalasi & Menjalankan (Copy–paste ready)

1. Clone repository:

```bash
git clone https://github.com/Lufasu-Adm/iot-ai-backend.git
cd iot-ai-backend
```

2. Build & jalankan semua service dengan Docker Compose:

```bash
docker compose up -d --build
```

3. (Opsional) Jalankan simulator sensor lokal (di mesin host):

```bash
pip install -r requirements.txt   # jika ada
python sensor_simulator.py
```

4. Contoh mengirim satu pesan MQTT (menggunakan `mosquitto_pub`):

```bash
mosquitto_pub -h localhost -t 'sensors/temperature/sensor-001' -m '{"sensor_id": "sensor-001", "value": 36.7, "ts": 1672531200}'
```

---

## Variabel Konfigurasi Penting

* `INFLUXDB_TOKEN` — ganti default token dengan token aman Anda.
* `GRAFANA_ADMIN_PASSWORD` — selalu ubah password default pada instalasi awal.
* `REDIS_QUEUE_NAME` — nama list Redis (`queue:temperature`).
* `ROLLING_WINDOW_N` — ukuran jendela default untuk MA.
* `ANOMALY_THRESHOLD_K` — threshold z-score.

Simpan variabel sensitif di `.env` dan jangan commit ke VCS.

---

## Monitoring & Debugging

* Cek status container:

```bash
docker compose ps
```

* Lihat log AI Worker realtime:

```bash
docker logs -f iot_worker
```

* Akses Grafana: `http://localhost:3000` (ubah kredensial default segera).
* Akses InfluxDB UI: `http://localhost:8086`.

---

## Pengujian & Evaluasi

**Strategi pengujian:**

1. Unit test untuk fungsi statistik (mean, std, z-score).
2. Integration test: jalankan simulator dengan skenario normal + skenario anomali.
3. Evaluasi metrik deteksi: Precision, Recall, F1. Gunakan label ground truth dari skenario sintetis.

**Contoh perhitungan sederhana (pseudocode):**

* `precision = TP / (TP + FP)`
* `recall = TP / (TP + FN)`
* `f1 = 2 * (precision * recall) / (precision + recall)`

---

## File & Struktur Direktori (contoh)

```
/ (repo root)
├─ docker-compose.yml
├─ backend_collector/
│  ├─ app.py
│  ├─ requirements.txt
├─ ai_worker/
│  ├─ worker.py
│  ├─ requirements.txt
├─ sensor_simulator.py
├─ grafana/
│  ├─ provisioning/
└─ README.md
```

---

## Best Practices & Catatan Akademis

* Jangan gunakan kredensial default pada lingkungan production.
* Pisahkan state (InfluxDB) dan ephemeral queue (Redis). Untuk ketahanan state, pertimbangkan menyimpan snapshot rolling-state ke Redis.
* Untuk skala, pertimbangkan partitioning berdasarkan `sensor_id` dan men-deploy worker multiple instances.
* Pertimbangkan metode deteksi yang lebih canggih (isolation forest, LSTM autoencoder) jika anomali bersifat kontekstual dan non-stationary.

---

## Contributing

1. Fork repo
2. Buat branch fitur: `git checkout -b feat/my-feature`
3. Commit dan push

```bash
git add .
git commit -m "menambahkan deskripsi fitur X"
git push origin feat/my-feature
```

4. Buat Pull Request dan sertakan deskripsi eksperimen/dataset untuk reproduksibilitas.

---

## Lisensi

Lisensi sesuai file `LICENSE` pada repositori. Untuk contoh akademis gunakan lisensi MIT.

---

## Referensi singkat

* InfluxDB Documentation
* Grafana Documentation
* Paho-MQTT Python Client
