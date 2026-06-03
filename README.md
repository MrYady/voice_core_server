# Voice Core Server 🎙️🧠🤖
Ecosistema de agentes de IA locales con procesamiento de voz en tiempo real. Utiliza Faster-Whisper, un clasificador semántico local basado en BETO entrenado a medida para la consolidación inteligente de ideas, y un broker Pub/Sub nativo sobre WebSockets para conectar agentes autónomos

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado bajo una arquitectura orientada a objetos basada en el patrón **Publisher/Subscriber (Pub/Sub)** sobre WebSockets, dividiendo las responsabilidades en componentes totalmente aislados:

1. **Cliente de Captura (`microphone_client.py`)**: Captura el audio del micrófono físico de forma continua y envía los buffers binarios crudos al servidor central.
2. **Servidor Central (`server.py`)**: 
   * **Faster-Whisper (Medium)**: Transcribe las ráfagas de audio recibidas.
   * **MessageBroker**: Administra las suscripciones de los múltiples agentes en tiempo real.
   * **Doble Filtro de Consolidación**: Evita enviar texto incoherente a los agentes evaluando silencios acústicos prolongados (Timeout de escape a los 2.5s) y pausas cortas de respiración (~0.8s).
3. **Analizador Semántico (`semantic_analyzer.py`)**: Carga un modelo binario de clasificación de texto basado en **BETO (BERT en Español)** ajustado a medida (*fine-tuned*). Determina de forma instantánea si una frase está `COMPLETA` o `INCOMPLETA` para retener o despachar el texto.
4. **Agente Autónomo (`agent.py`)**: Consume las frases completas publicadas por el servidor e interactúa de forma local con **Ollama (Llama 3:8B)** manteniendo el hilo contextual de la conversación.

---

## 📂 Estructura del Proyecto

```text
├── mi_modelo_semantico/      # Binarios del modelo BETO entrenado en Google Colab
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   ├── tokenizer.json
│   ├── training_args.bin
│   └── vocab.txt
├── templates/
│   └── index.html            # Dashboard visual del servidor
├── agent.py            # Suscriptor / Agente inteligente (llama3:8b)
├── microphone_client.py      # Cliente emisor de audio por micrófono
├── semantic_analyzer.py      # Módulo POO del clasificador sintáctico local
└── server.py                 # Servidor central FastAPI & WebSockets (Cerebro)
