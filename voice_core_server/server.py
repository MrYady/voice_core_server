import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from faster_whisper import WhisperModel
import numpy as np
from typing import Set
import os

# Importamos tu analizador semántico modificado
from semantic_analyzer import SemanticAnalyzer

class MessageBroker:
    """Gestiona las suscripciones de los agentes en tiempo real (Pub/Sub nativo)"""
    def __init__(self):
        self._listeners: Set[WebSocket] = set()

    async def subscribe(self, websocket: WebSocket):
        await websocket.accept()
        self._listeners.add(websocket)
        print(f"🤖 Agente conectado. Total suscritos: {len(self._listeners)}")

    def unsubscribe(self, websocket: WebSocket):
        if websocket in self._listeners:
            self._listeners.remove(websocket)
            print(f"🛑 Agente desconectado. Total suscritos: {len(self._listeners)}")

    async def publish(self, message: str):
        if not self._listeners:
            return
        
        # Enviamos el texto a todos los agentes conectados en paralelo
        print(f"📢 Publicando a {len(self._listeners)} agentes: '{message}'")
        await asyncio.gather(
            *[listener.send_text(message) for listener in self._listeners],
            return_exceptions=True
        )

# Inicializamos la app y el broker
app = FastAPI()
broker = MessageBroker()

# Instanciamos el clasificador semántico directamente apuntando al Repositorio de Hugging Face
semantic_evaluator = SemanticAnalyzer(model_repo="MrYady/clasificador-semantico-es")

# Inicialización unificada de Whisper en tu RTX 3060 (Carga limpia y directa)
print("Cargando modelo Faster-Whisper (Medium)...")
model = WhisperModel("medium", device="cuda", compute_type="float32")
print("🚀 Ecosistema de IA en CUDA listo para operar.")


@app.websocket("/stream-audio")
async def audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🎙️ Micrófono conectado. Esperando habla...")
    
    # Buffer de audio crudo y acumulador de texto retenido
    audio_buffer = bytearray()
    frase_acumulada_texto = ""
    silence_counter = 0 
    
    global model

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            # Convertimos fragmento actual para medir energía acústica
            chunk_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            energia = np.sqrt(np.mean(chunk_np**2)) if len(chunk_np) > 0 else 0
            
            if energia < 0.025: 
                silence_counter += 1
            else:
                silence_counter = 0 # Si hablas, se resetea el contador de silencio

            # =========================================================================
            # CASO A: TIMEOUT DE ESCAPE (Silencio absoluto prolongado ~2.5 a 3 segundos)
            # =========================================================================
            if len(audio_buffer) > 0 and silence_counter > 15:
                if frase_acumulada_texto:
                    print(f"⏱️ [Timeout de silencio] Forzando envío de ideas inconclusas: '{frase_acumulada_texto}'")
                    await broker.publish(frase_acumulada_texto)
                    frase_acumulada_texto = ""
                audio_buffer.clear()
                silence_counter = 0

            # =========================================================================
            # CASO B: PAUSA CASUAL DE RESPIRACIÓN (Silencio corto ~0.8 segundos)
            # =========================================================================
            elif len(audio_buffer) > 0 and silence_counter > 4:
                # Extraemos el audio acumulado para procesar este bloque
                audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Reseteamos buffers acústicos de inmediato para no perder el hilo de lo que sigue
                audio_buffer.clear()
                silence_counter = 0
                
                # Transcribimos el bloque de audio actual
                segments, info = model.transcribe(
                    audio_np,
                    language="es",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_speech_duration_ms=300),
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                
                texto_bloque = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
                
                # Filtro rápido de alucinaciones
                alucinaciones = ["gracias por ver", "subscríbete", "youtube", "reproducción", "adiós", "chao"]
                if texto_bloque and not any(aluc in texto_bloque.lower() for aluc in alucinaciones):
                    
                    # Concatenamos de forma limpia al buffer de texto global
                    frase_acumulada_texto = f"{frase_acumulada_texto} {texto_bloque}".strip()
                    
                    # EVALUACIÓN SEMÁNTICA POO (Consume la instancia del modelo en Hugging Face)
                    es_completa = await semantic_evaluator.is_idea_complete(frase_acumulada_texto)
                    
                    if es_completa:
                        print(f"✨ [Idea Concluida Despachada]: {frase_acumulada_texto}")
                        await broker.publish(frase_acumulada_texto)
                        frase_acumulada_texto = "" # Liberamos el acumulador
                    else:
                        print(f"⏳ [Idea Retenida Semánticamente]: '{frase_acumulada_texto}'... esperando continuación.")

    except WebSocketDisconnect:
        print("🎙️ Micrófono desconectado.")
    except Exception as e:
        print(f"Error en flujo de audio: {e}")


@app.websocket("/agentes/suscripcion")
async def agentes_endpoint(websocket: WebSocket):
    """Endpoint donde los agentes se conectan para escuchar las transcripciones"""
    await broker.subscribe(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broker.unsubscribe(websocket)

@app.websocket("/status")
async def servidorOpen(websocket: WebSocket):
    print("Servidor de texto abierto y listo para recibir conexiones de agentes.")
    await websocket.accept()
    return websocket

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    ruta_html = os.path.join("templates", "index.html")
    with open(ruta_html, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)