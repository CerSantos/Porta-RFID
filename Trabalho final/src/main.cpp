#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>

void enviarDados(String uid);

// Pinos conforme sua solicitação
#define SS_PIN    5
#define RST_PIN   22
#define LED_PIN   2

// Configurações de rede
const char* ssid = "RIBEIRO";
const char* password = "Trt111930#";

// IP do seu computador onde o app Python está rodando
// Exemplo: "http://192.168.0"
const char* serverUrl = "http://192.168.0.209:5000/log";  //Lembrar de mudar para o IP do seu computador

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  SPI.begin(); 
  rfid.PCD_Init();
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado!");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  rfid.PCD_Init(); //Reinicia o sensor para garantir que ele está ativo
 static unsigned long ultimaVerificacao = 0;
  if (millis() - ultimaVerificacao > 2000) {
    Serial.println("Aguardando cartão...");
    ultimaVerificacao = millis();
  }
  // Procura por novos cartões
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Pega a UID do cartão
   String uidString = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    uidString += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    uidString += String(rfid.uid.uidByte[i], HEX);
  }
  uidString.toUpperCase();

  Serial.println("Cartão Detectado: " + uidString);
  digitalWrite(LED_PIN, LOW);
  enviarDados(uidString); // Agora o compilador já conhece a função

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

void enviarDados(String uid) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Envia a UID para o Python decidir
    String httpRequestData = "{\"uid\":\"" + uid + "\"}";
    int httpResponseCode = http.POST(httpRequestData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Resposta do Servidor: " + response);

      // Se o Python responder "autorizado", pisca o LED
      if (response.indexOf("autorizado") != -1) {
        for(int i=0; i<3; i++){
          digitalWrite(LED_PIN, HIGH); delay(100);
          digitalWrite(LED_PIN, LOW); delay(100);
        }
      }else{
        // Se negado, o LED fica apagado por 2 segundos como sinal de erro
        digitalWrite(LED_PIN, LOW);
        delay(2000);
      }
    } else {
      Serial.print("Erro no envio: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
}
