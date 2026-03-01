import paho.mqtt.client as mqtt
import json
import time
import random

# Konfigurasi Broker (Docker Mosquitto)
BROKER = "localhost"
PORT = 1883
TOPIC = "sensor/data"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

try:
    print(f"Menghubungkan ke Broker di {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Gagal konek: {e}. Pastikan kontainer iot_mosquitto nyala!")
    exit()

print("Mulai mengirim data... (Tekan Ctrl+C untuk berhenti)")

try:
    while True:
        # Simulasi data sensor
        payload = {
            "device_id": "SENSOR_RUANGAN_01",
            "temperature": round(random.uniform(24.0, 32.0), 2),
            "humidity": round(random.uniform(50.0, 80.0), 2),
            "timestamp": time.time()
        }
        
        # Kirim data ke topik MQTT
        client.publish(TOPIC, json.dumps(payload))
        print(f"Data Terkirim ke '{TOPIC}': {payload}")
        
        time.sleep(2) 
except KeyboardInterrupt:
    print("\nSimulasi dihentikan.")
    client.disconnect()