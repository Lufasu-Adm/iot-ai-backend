import os
import json
import time
import logging
import redis
import numpy as np

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] AI_WORKER: %(message)s")
logger = logging.getLogger(__name__)

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_QUEUE = os.getenv("REDIS_QUEUE_NAME", "sensor_queue")

def start_worker():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    logger.info(f"Worker AI aktif. Menunggu data di antrean '{REDIS_QUEUE}'...")

    while True:
        try:
            # Mengambil semua data yang tersedia di antrean Redis
            raw_data = r.lrange(REDIS_QUEUE, 0, -1)
            
            if len(raw_data) >= 5:
                # Parsing JSON
                dataset = [json.loads(d) for d in raw_data]
                temperatures = [d['temperature'] for d in dataset]
                
                # Logika AI Sederhana: Deteksi Lonjakan (Anomaly)
                current_temp = temperatures[0]
                average_temp = np.mean(temperatures[1:]) 
                
                # Jika suhu naik lebih dari 2 derajat dibanding rata-rata
                if current_temp > (average_temp + 2.0):
                    logger.warning(f"ANOMALI TERDETEKSI! Suhu melonjak ke {current_temp}°C (Rata-rata normal: {average_temp:.2f}°C)")
                else:
                    logger.info(f"Status Stabil: {current_temp}°C")
            
            time.sleep(2) 
            
        except Exception as e:
            logger.error(f"Worker Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()