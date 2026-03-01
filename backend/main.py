import os
import json
import logging
import redis
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Any, Dict

# ==========================================
# 1. KONFIGURASI LOGGING (Standar Industri)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. MANAJEMEN ENVIRONMENT VARIABLES
# ==========================================
# MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensor/data")

# InfluxDB
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-admin-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "iot_org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "sensor_data")

# Redis (Message Broker untuk AI Worker)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "sensor_queue")

# ==========================================
# 3. INISIALISASI KONEKSI
# ==========================================
# InfluxDB Setup
try:
    influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    logger.info("Koneksi InfluxDB berhasil diinisialisasi.")
except Exception as e:
    logger.critical(f"Gagal menginisialisasi InfluxDB: {e}")
    exit(1)

# Redis Setup
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()  # Tes koneksi awal
    logger.info("Koneksi Redis berhasil diinisialisasi.")
except redis.ConnectionError as e:
    logger.warning(f"Tidak dapat menghubungi Redis (mungkin belum siap): {e}")

# ==========================================
# 4. LOGIKA BISNIS (DATA PROCESSING)
# ==========================================
def process_sensor_data(payload: Dict[str, Any]) -> None:
    """
    Fungsi untuk memproses data sensor:
    1. Menyimpan data historis ke InfluxDB.
    2. Melempar data terbaru ke Redis untuk AI Worker.
    """
    device_id = payload.get('device_id', 'UNKNOWN_DEVICE')
    temp = payload.get('temperature', 0.0)
    humidity = payload.get('humidity', 0.0)

    # A. Tulis ke InfluxDB
    try:
        point = Point("environment") \
            .tag("device_id", device_id) \
            .field("temperature", float(temp)) \
            .field("humidity", float(humidity))
        
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        logger.info(f"[{device_id}] InfluxDB Write OK | Suhu: {temp}°C")
    except Exception as e:
        logger.error(f"Kesalahan penulisan InfluxDB: {e}")

    # B. Dorong ke Redis Queue
    try:
        redis_client.lpush(REDIS_QUEUE_NAME, json.dumps(payload))
        redis_client.ltrim(REDIS_QUEUE_NAME, 0, 9)  # Hanya simpan 10 data terbaru di antrean
    except Exception as e:
        logger.error(f"Kesalahan penulisan Redis: {e}")

# ==========================================
# 5. KONTROLER MQTT
# ==========================================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info(f"Terhubung ke MQTT Broker di {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Berlangganan pada topik: '{MQTT_TOPIC}'")
    else:
        logger.error(f"Koneksi MQTT ditolak dengan kode: {reason_code}")

def on_message(client, userdata, msg):
    try:
        # Decode payload dan parsing sebagai JSON
        raw_payload = msg.payload.decode('utf-8')
        payload = json.loads(raw_payload)
        
        # Lemparkan ke fungsi pemrosesan terpisah
        process_sensor_data(payload)
        
    except json.JSONDecodeError:
        logger.warning(f"Menerima payload non-JSON yang diabaikan: {msg.payload}")
    except Exception as e:
        logger.error(f"Kesalahan tidak terduga di on_message: {e}", exc_info=True)

# ==========================================
# 6. MAIN EXECUTION ENTRY POINT
# ==========================================
def main():
    logger.info("Memulai servis Backend Collector...")
    
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Menerima sinyal interupsi. Mematikan servis...")
    except Exception as e:
        logger.critical(f"Kegagalan sistem fatal: {e}")
    finally:
        mqtt_client.disconnect()
        influx_client.close()
        logger.info("Servis dimatikan dengan aman.")

if __name__ == "__main__":
    main()