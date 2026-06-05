"""
Phase 2: the Kafka PRODUCER.

Simulates a live street-sensor feed: it interleaves real Melbourne traffic
(MELAUDIS, all non-horns) with occasional real car_horn clips (UrbanSound8K),
runs each through the HornDetector, and PUBLISHES a horn event to the Kafka
`horn-events` topic whenever a horn is detected.

Prereq: Kafka running -> (cd docker && docker compose up -d)
Run:    uv run python src/producer.py            (streams ~40 clips)
        uv run python src/producer.py 100         (streams 100 clips)
"""

import glob
import io
import json
import random
import sys
import time
from datetime import datetime, timezone

import librosa
import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
from kafka import KafkaProducer

from predict import get_detector

KAFKA_BROKER = "localhost:9092"
TOPIC = "horn-events"

# Well-known high-traffic spots in Delhi (lat, lon).
SITES = {
    "Connaught Place": (28.6315, 77.2167),
    "ITO": (28.6289, 77.2410),
    "Karol Bagh": (28.6517, 77.1907),
    "Chandni Chowk": (28.6562, 77.2301),
    "AIIMS": (28.5672, 77.2100),
    "Dhaula Kuan": (28.5916, 77.1610),
    "Nehru Place": (28.5494, 77.2509),
}


def site_from_name(name: str) -> str:
    for site in SITES:
        if site.lower() in name.lower():
            return site
    return random.choice(list(SITES))


def load_horn_clips(limit=40):
    """Pull a handful of real car_horn waveforms out of UrbanSound8K parquet."""
    horns = []
    for f in glob.glob("data/urbansound8k/data/*.parquet"):
        t = pq.read_table(f, columns=["audio", "class"])
        for au, cls in zip(t.column("audio").to_pylist(),
                           t.column("class").to_pylist()):
            if cls == "car_horn":
                y, sr = sf.read(io.BytesIO(au["bytes"]), dtype="float32")
                horns.append((y, sr, "urbansound8k_car_horn"))
                if len(horns) >= limit:
                    return horns
    return horns


def build_stream(n_clips):
    """A realistic mix: mostly Melbourne traffic, ~20% real horns, shuffled."""
    n_horns = max(1, n_clips // 5)
    horn_clips = load_horn_clips(n_horns)

    bg = sorted(glob.glob("data/melaudis/27115870/_BG_Final/*.wav"))
    veh = sorted(glob.glob("data/melaudis/27115870/Final_Veh/*/*.wav"))
    traffic_paths = random.sample(bg + veh, n_clips - len(horn_clips))

    stream = [("file", p) for p in traffic_paths] + [("horn", h) for h in horn_clips]
    random.shuffle(stream)
    return stream


def main():
    n_clips = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    detector = get_detector()

    # value_serializer: how to turn our dict into bytes for Kafka. JSON here.
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print(f"Connected to Kafka at {KAFKA_BROKER}, topic '{TOPIC}'.")

    stream = build_stream(n_clips)
    horns_found = 0
    for i, (kind, item) in enumerate(stream, 1):
        if kind == "horn":
            y, sr, source = item
            result = detector.predict_audio(y, sr)
        else:
            source = item.split("/")[-1]
            result = detector.predict_file(item)

        if result["is_horn"]:
            horns_found += 1
            # pick the site ONCE so the label and coordinates always agree.
            site = site_from_name(source)
            lat, lon = SITES[site]
            jitter = lambda x: round(x + random.uniform(-0.002, 0.002), 6)
            event = {
                "event_id": f"horn-{int(time.time()*1000)}-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": site,
                "lat": jitter(lat),
                "lon": jitter(lon),
                "confidence": result["confidence"],
                "source": source,
            }
            # send() is async + buffered — exactly the decoupling from Lesson 7.
            producer.send(TOPIC, event)
            print(f"[{i:3d}/{len(stream)}] 🔊 HORN  conf={event['confidence']:.2f} "
                  f"@ {event['location']}  -> published")
        else:
            print(f"[{i:3d}/{len(stream)}] ·     not-horn (conf {result['confidence']:.2f})")

        time.sleep(0.15)  # pace it so it feels like a live feed

    producer.flush()  # make sure everything buffered is actually sent
    producer.close()
    print(f"\nDone. Published {horns_found} horn events to '{TOPIC}'.")


if __name__ == "__main__":
    main()
