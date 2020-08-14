import ssl
import sys

import paho.mqtt.client as paho

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def main():
    client = paho.Client()
    client.username_pw_set("sammy", "sammy")
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.connect("localhost", 1883)
    client.subscribe("test", qos=1)
    client.loop_forever()


if __name__ == '__main__':
    main()
