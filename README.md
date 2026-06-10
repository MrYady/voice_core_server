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
```

## ⚙️ Requisitos Previos
Hardware: Tarjeta gráfica NVIDIA (Optimizado para arquitectura Ampere / RTX 3060 o superior con CUDA configurado).

Software:

Python 3.10 o superior.

Ollama instalado y corriendo localmente con el modelo llama3:8b.

## 🚀 Instalación y Configuración

Clonar el repositorio:
```
git clone https://github.com/MrYady/voice_core_server.git
cd voice_core_server
```
Instalar dependencias necesarias:

```
pip install fastapi uvicorn faster-whisper numpy torch transformers websockets ollama
```
## 🛠️ Pasos de Ejecución (Flujo de Trabajo Completo)

Para poner en marcha todo el ecosistema, debes abrir 3 terminales independientes y ejecutar los componentes en el siguiente orden estricto. Esto garantiza que los canales de comunicación por WebSockets se enlacen correctamente:

**Paso 1:**   Levantar el Servidor Central (El Cerebro)Este componente inicializa el pipeline de procesamiento de audio en la GPU, el broker de suscripciones y el clasificador de texto local. ```python server.py```

**¿Qué pasa internamente?** 
1. Se cargan los pesos del clasificador semántico basado en PyTorch en la VRAM de la gráfica.
2. Se instancia el motor de transcripción de alto rendimiento Faster-Whisper.
3. Se abre el puerto 8000 quedando a la espera de clientes de audio y agentes.Espera a ver el mensaje en consola antes de continuar: 🚀 Ecosistema de IA en CUDA listo para operar.

**Paso 2:** Conectar el Agente Inteligente (Luna)En tu segunda terminal, arranca el script del agente que procesará tus peticiones de negocio, tus consultas generales. ```python agent_llama.py```

**¿Qué pasa internamente?** 
El script se conecta al WebSocket del servidor en la ruta /agentes/suscripcion. 
El MessageBroker del servidor registra al agente en su lista de escucha activa.La consola del servidor imprimirá: 🤖 Agente conectado. Total suscritos: 1.

**Paso 3:** Activar la Captura de Audio (El Micrófono)En la tercera terminal, inicia el cliente encargado de digitalizar y transmitir tu voz. ```python microphone_client.py``` 

**¿Qué pasa internamente?** 
El cliente abre el flujo de entrada de tu hardware de audio (micrófono principal).
Comienza a enviar ráfagas de bytes binarios directas al endpoint /stream-audio del servidor.El servidor mostrará: 🎙️ Micrófono conectado. Esperando habla....


## 🧠 Funcionamiento del Doble Filtro (Ejemplo Bíblico y Técnico)

Gracias a la integración de SemanticAnalyzer, el sistema es capaz de entender intenciones conversacionales complejas sin interrumpirte mientras piensas:

**Pausa de respiración:** Si dices "¿Puedes decirme de qué versículo de la Biblia es este texto?" y te callas un segundo para recordar la cita, el modelo BETO local detectará que la idea está INCOMPLETA. El servidor retendrá el texto en el acumulador y no molestará al agente principal.

**Consolidación:** Al continuar hablando con "Y mientras tanto, amó Dios tanto al mundo...", el nuevo bloque se fusiona. El analizador vuelve a evaluar y, al notar que la pregunta ya tiene su objeto, dictamina que la idea está COMPLETA, despachando el bloque entero unificado a Luna por el WebSocket.

**Timeout de duda:** Si dices "Quiero crear una carpeta de nombreee..." y te quedas mudo pensando, el reloj de escape acústico detectará un silencio prolongado (más de 2.5 segundos) y forzará el envío de la frase incompleta para que el agente intervenga y te asista en la toma de decisiones.

