# Dockerized Predictive Monitoring System for IoT and AI-Driven Anomaly Detection

## Project Overview

Sistem ini merupakan purwarupa arsitektur *backend* berbasis *microservices* yang dirancang untuk menerima, memproses, menyimpan, dan memvisualisasikan data sensor IoT secara *real-time*. Sistem ini mengimplementasikan konsep *event-driven architecture* dan dilengkapi dengan modul *Artificial Intelligence* (AI) untuk mendeteksi anomali suhu secara otomatis menggunakan model statistik dasar.

Proyek ini dikembangkan sebagai demonstrasi integrasi berbagai teknologi standar industri dalam satu ekosistem *container* (Docker).

## System Architecture

Sistem ini terdiri dari enam layanan utama yang saling terisolasi namun terhubung melalui jaringan internal Docker:

1. **Eclipse Mosquitto (MQTT Broker):** Bertindak sebagai protokol komunikasi ringan untuk menerima aliran data metrik dari perangkat IoT atau simulator sensor.
2. **Backend Collector (Python):** Layanan yang berlangganan (*subscribe*) pada topik MQTT, memproses *payload* JSON, dan mendistribusikan data ke *database* dan *message queue*.
3. **InfluxDB 2:** *Time-Series Database* (TSDB) yang dioptimalkan untuk menyimpan log data sensor dengan performa tulis dan baca yang tinggi.
4. **Redis:** *In-memory data structure store* yang difungsikan sebagai *message queue* untuk menampung data sementara (*buffer*) sebelum diproses oleh modul analitik.
5. **AI Worker (Python):** Modul komputasi asinkron yang mengambil antrean data dari Redis dan menerapkan algoritma *Moving Average* untuk mendeteksi lonjakan suhu (*anomaly detection*) secara *real-time*.
6. **Grafana:** Platform visualisasi data interaktif yang terhubung langsung dengan InfluxDB untuk menampilkan dasbor metrik lingkungan dan peringatan sistem.

## Technology Stack

* **Infrastructure:** Docker, Docker Compose
* **Programming Language:** Python 3.10
* **Libraries:** `paho-mqtt`, `redis`, `influxdb-client`, `numpy`
* **Services:** Mosquitto, Redis Alpine, InfluxDB, Grafana

## Prerequisites

Sebelum menjalankan sistem ini, pastikan lingkungan kerja Anda telah memasang perangkat lunak berikut:

* Docker Engine
* Docker Compose
* Git
* Python 3.10+ (hanya untuk menjalankan simulator eksternal)

## Installation and Execution

1. Kloning repositori ini ke dalam mesin lokal Anda:

   ```bash
   git clone https://github.com/Lufasu-Adm/iot-ai-backend.git
   cd iot-ai-backend
   ```

2. Bangun dan jalankan seluruh kontainer menggunakan Docker Compose:

   ```bash
   docker-compose up -d --build
   ```

3. Jalankan simulator sensor IoT (berjalan di luar kontainer sebagai klien eksternal):

   ```bash
   pip install paho-mqtt
   python sensor_simulator.py
   ```

## System Monitoring and Access

Setelah seluruh layanan berstatus Running, Anda dapat memantau sistem melalui akses berikut:

* **Grafana Dashboard:** Akses [http://localhost:3000](http://localhost:3000) (Kredensial bawaan: admin / adminpassword123).
* **InfluxDB Data Explorer:** Akses [http://localhost:8086](http://localhost:8086).
* **AI Worker Logs (Anomaly Detection):** Pantau hasil analisis real-time melalui terminal dengan perintah:

  ```bash
  docker logs -f iot_worker
  ```

## System Demonstration

Gambar 1: Tampilan split-screen yang menunjukkan visualisasi real-time pada dasbor Grafana (kiri) dan log operasional dari AI Worker yang sedang mendeteksi anomali suhu secara langsung (kanan).

Gaya penulisan di atas sangat cocok untuk repositori GitHub tingkat profesional. Penjelasannya terstruktur, menggunakan istilah teknis yang tepat (seperti *event-driven architecture*, *time-series database*, *in-memory data structure*), dan langsung pada intinya.

Jika kamu sudah menyalinnya, kamu bisa langsung melakukan proses `git add .`, `git commit`
