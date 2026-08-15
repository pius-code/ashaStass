import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

# Same broker ashaBackend's ESP32 devices actually publish to (a private LAN
# broker, not the public HiveMQ one) — the events won't reach us otherwise.
# Only reachable while this process runs on the same network as the broker;
# revisit if/when this gets deployed somewhere that can't reach a private IP.
BROKER = os.getenv("MQTT_IP", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = "asha-iris/events/#"


mqtt_client = mqtt.Client()
mqtt_client.connect(BROKER, PORT, 60)


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    topic = msg.topic  # e.g. "asha-iris/events/a1b2c3"
    task_id = topic.split("/")[-1] # noqa


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
