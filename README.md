# Sistema de Controle de Acesso com RFID e ESP32

## Sobre o Projeto

Este projeto implementa a lógica fundamental de um sistema de controle de acesso automatizado utilizando um microcontrolador ESP32 e um módulo leitor RFID. A proposta inicial é identificar e validar uma tag ou cartão RFID previamente autorizado.

**Aviso de Desenvolvimento:** Este repositório contém um protótipo em fase inicial e de experimentação (o código e a estrutura ainda estão um pouco "bagunçados"). Durante o processo de desenvolvimento, ferramentas de Inteligência Artificial foram utilizadas para auxiliar na correção de bugs e na resolução de problemas lógicos.

## Funcionalidades

* **Leitura de Tags:** Identificação e leitura de cartões ou chaveiros RFID.
* **Validação de Acesso:** Comparação do identificador único (UID) da tag aproximada com os UIDs predefinidos no código.
* **Feedback de Status:** Utilização do Monitor Serial (e possivelmente LEDs) para indicar se o acesso foi liberado ou negado.

## Hardware Utilizado

* 1x Placa de Desenvolvimento ESP32
* 1x Módulo Leitor RFID (ex: RC522)
* Tags e cartões RFID compatíveis (13.56MHz)
* Jumpers variados e Protoboard

## Esquema de Ligação (Pinout)

*Observação: As portas podem ser ajustadas de acordo com a sua montagem, desde que o código seja atualizado.*

| Componente | Pino do Componente | Pino no ESP32 | 
| ----- | ----- | ----- | 
| **RFID RC522** | SDA (SS) | GPIO 5 | 
|  | SCK | GPIO 18 | 
|  | MOSI | GPIO 23 | 
|  | MISO | GPIO 19 | 
|  | IRQ | Não Conectado | 
|  | GND | GND | 
|  | RST | GPIO 22 | 
|  | 3.3V | 3.3V | 

## Software e Bibliotecas

O firmware foi desenvolvido em C/C++ utilizando o ambiente **PlatformIO**. As dependências de bibliotecas podem ser gerenciadas diretamente pelo arquivo `platformio.ini`.

A principal biblioteca utilizada neste projeto é:
* `MFRC522`: Responsável pela comunicação via SPI com o módulo leitor.

## Melhorias Futuras

* [ ] Refatorar e organizar a estrutura do código do protótipo atual.
* [ ] Implementar o acionamento físico de uma fechadura utilizando um relé ou servomotor.
* [ ] Adicionar feedback visual/sonoro com LEDs e Buzzer.
