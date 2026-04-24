#include <Arduino.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>

void enviarDados(String uid);

// Pinos
#define SS_PIN    5
#define RST_PIN   22
#define LED_PIN   2

// Configurações de rede
String ssid;
String password;
String serverUrl;

MFRC522 rfid(SS_PIN, RST_PIN);

// Carrega as configurações do LittleFS
bool carregarConfig() {
  // 1. Tenta montar o sistema de arquivos
  if (!LittleFS.begin(true)) {
    Serial.println("[-] Erro crítico: Falha ao montar LittleFS");
    return false;
  }

  // 2. Verifica se o arquivo existe. Se não, tenta criar o padrão.
  if (!LittleFS.exists("/config.json")) {
    Serial.println("[!] Arquivo config.json não encontrado. Criando padrão...");
    
    File writeFile = LittleFS.open("/config.json", "w");
    if (!writeFile) {
      Serial.println("[-] Erro ao criar arquivo config.json");
      return false;
    };
  }

  // 3. Abre o arquivo para leitura
  File configFile = LittleFS.open("/config.json", "r");
  if (!configFile) {
    Serial.println("[-] Erro ao abrir config.json para leitura");
    return false;
  }

  // 4. Faz o parsing do JSON
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, configFile);
  configFile.close();

  if (error) {
    Serial.print("[-] Erro no processamento do JSON: ");
    Serial.println(error.c_str());
    return false;
  }

  // 5. Atribui às variáveis globais
  ssid = doc["ssid"].as<String>();
  password = doc["password"].as<String>();
  serverUrl = doc["serverUrl"].as<String>();

  Serial.println("[+] Configurações carregadas:");
  Serial.println("    SSID: " + ssid);
  Serial.println("    URL:  " + serverUrl);

  return true;
}

void setup() {
  Serial.begin(115200);
  SPI.begin(); 
  rfid.PCD_Init();
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

   if (!carregarConfig()) {
    Serial.println("Usando configurações padrão ou travando por falta de dados.");
  }

   Serial.println("Conectando ao WiFi...");
  Serial.println("Conectando ao SSID: " + ssid);
  WiFi.begin(ssid.c_str(), password.c_str());

  WiFi.begin(ssid.c_str(), password.c_str());
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
