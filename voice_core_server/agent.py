import asyncio
import websockets
import json
import ollama

# Configuración del agente
SERVER_URL = "ws://127.0.0.1:8000/agentes/suscripcion"
MODELO_LLAMA = "llama3:8b" # Asegúrate de que este sea el nombre exacto en tu 'ollama list'

class LlamaAgent:
    def __init__(self):
        self.contexto_conversacion = [
            {"role": "system", "content": "Eres Luna, una asistente IA local, inteligente, concisa y directa. Responde siempre en español de forma natural."}
        ]

    async def escuchar_servidor(self):
        print(f"🤖 Agente Llama 3 intentando conectar a {SERVER_URL}...")
        
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                print("✅ Agente Llama 3 conectado y listo para procesar tus frases.")
                
                while True:
                    # El agente se queda esperando a que el servidor publique texto limpio
                    texto_recibido = await websocket.recv()
                    
                    print(f"\n📥 Texto recibido del micrófono: '{texto_recibido}'")
                    print("🧠 Pensando respuesta con Llama 3...")
                    
                    # Añadimos lo que dijiste al historial del agente
                    self.contexto_conversacion.append({"role": "user", "content": texto_recibido})
                    
                    # Llamamos a Ollama de forma asíncrona para no bloquear el script
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None, 
                        lambda: ollama.chat(model=MODELO_LLAMA, messages=self.contexto_conversacion)
                    )
                    
                    respuesta_ia = response['message']['content']
                    print(f"🤖 Luna dice: {respuesta_ia}")
                    
                    # Guardamos la respuesta de la IA en el contexto para mantener el hilo de la conversación
                    self.contexto_conversacion.append({"role": "assistant", "content": respuesta_ia})
                    
                    # Limpieza opcional del historial si se vuelve demasiado largo (ej. más de 20 mensajes)
                    if len(self.contexto_conversacion) > 20:
                        self.contexto_conversacion = [self.contexto_conversacion[0]] + self.contexto_conversacion[-10:]

        except websockets.exceptions.ConnectionClosed:
            print("🛑 Se perdió la conexión con el servidor central.")
        except Exception as e:
            print(f"❌ Error en el agente: {e}")

if __name__ == "__main__":
    agente = LlamaAgent()
    try:
        asyncio.run(agente.escuchar_servidor())
    except KeyboardInterrupt:
        print("\n👋 Agente apagado.")