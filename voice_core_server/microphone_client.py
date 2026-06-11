import asyncio
import websockets
import pyaudio

# Configuración estándar para IA de voz y Biometría
FORMAT = pyaudio.paInt16       # 16 bits por muestra
CHANNELS = 1                  # Mono
RATE = 16000                  # 16kHz
CHUNK = 4000                  # Tamaño del bloque de lectura (~0.25 segundos de audio)

# URL del servidor central
SERVER_URL = "ws://127.0.0.1:8000/stream-audio"

class AudioStreamer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None

    def start_input_stream(self):
        """Inicializa la captura del micrófono físico"""
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        print("🎙️  Micrófono inicializado correctamente.")

    async def send_audio(self):
        """Se conecta al servidor y transmite el audio en tiempo real"""
        print(f"🔗 Conectando al servidor en {SERVER_URL}...")
        
        try:
            async with websockets.connect(SERVER_URL) as websocket:
                print("✅ Conectado al servidor de IA. Empieza a hablar...")
                self.start_input_stream()

                # Bucle infinito de transmisión
                while True:
                    # Explicación: Lee los bytes crudos del micrófono.
                    # exception_on_overflow=False evita que el script se caiga si la CPU se retrasa un milisegundo
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Enviamos los bytes directamente por el WebSocket
                    await websocket.send(data)
                    
                    # Pequeño respiro asíncrono para no bloquear el hilo principal
                    await asyncio.sleep(0.01)

        except websockets.exceptions.ConnectionRefusedError:
            print("❌ No se pudo conectar al servidor. ¿Te aseguraste de ejecutar server.py primero?")
        except Exception as e:
            print(f"🛑 Ocurrió un error en la transmisión: {e}")
        finally:
            self.close()

    def close(self):
        """Cierra los flujos de audio de forma limpia"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        print("🔌 Conexión y micrófono cerrados.")

if __name__ == "__main__":
    streamer = AudioStreamer()
    try:
        # Arrancamos el bucle asíncrono
        asyncio.run(streamer.send_audio())
    except KeyboardInterrupt:
        print("\n👋 Transmisión finalizada por el usuario.")