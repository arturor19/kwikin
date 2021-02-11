#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define GPIO2_LED 2
const char* ssid = "RAMLOZ2";
const char* password =  "Queonda_123";
const char* mqttServer = "kwikin.mx";
const int mqttPort = 1883;
const char* mqttUser = "kwikin";
const char* mqttPassword = "GuiArtMig123!";
const char* sub = "0000000/Entrada 1/accion";
const char* pub = "puertas";

// Constantes estatus dispositivo 
const char* encendido = "{'coto': 'Bambu', 'puerta': 'Entrada 1', 'accion': 3}";
const char* vivo = "{'coto': 'Bambu', 'puerta': 'Entrada 1', 'accion': 4}";
const char* activando = "{'coto': 'Bambu', 'puerta': 'Entrada 1', 'accion': 5}";

 
WiFiClient espClient;
PubSubClient client(espClient);
 
void setup() {
 
  Serial.begin(115200);
  pinMode(GPIO2_LED, OUTPUT);
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to the WiFi network");
 
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
 
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
 
    if (client.connect("ESP8266Client", mqttUser, mqttPassword )) {
 
      Serial.println("connected");  
 
    } else {
 
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
 
    }
  }
 
  client.publish(pub, "Hello from ESP8266");
  client.subscribe(sub);
 
}
 
void callback(char* topic, byte* payload, unsigned int length) {
  String strPayload = ""; 
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
 
  Serial.print("Message:");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
    strPayload += (char)payload[i];
  }
  if (strPayload == "ON"){
    digitalWrite(GPIO2_LED, HIGH); 
    client.publish("puertas", activando);
    Serial.println("\nActivando...");
    delay(3000);
    digitalWrite(GPIO2_LED, LOW); 
  } else if (strPayload == "VIVO"){
    client.publish("puertas", vivo);
    Serial.println("Vivo...");
  }
  Serial.println();
  Serial.println("-----------------------");
 
}
 
void loop() {
  client.loop();
}
