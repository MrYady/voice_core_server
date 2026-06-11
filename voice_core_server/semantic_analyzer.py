import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

class SemanticAnalyzer:
    """Clase optimizada que evalúa la completitud de una frase cargando el modelo desde Hugging Face."""
    
    def __init__(self, model_repo: str = "MrYady/clasificador-semantico-es"):
        self.model_repo = model_repo
        
        print(f"🧠 Descargando/Cargando clasificador semántico desde Hugging Face [{model_repo}]...")
        
        # Transformers se encarga de buscarlo y cachearlo desde la nube automáticamente
        self.tokenizer = AutoTokenizer.from_pretrained(model_repo)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_repo)
        
        # Configuración de hardware (GPU RTX 3060)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval() # Modo evaluación (desactiva dropout/batchnorm)
        
        # Corrección del objeto device a string para evitar errores de atributo
        print(f"✅ Clasificador semántico cargado exitosamente en [{str(self.device).upper()}].")
    
    async def is_idea_complete(self, text: str) -> bool:
        """
        Determina de forma nativa e instantánea si la frase ha concluido.
        Retorna True si está COMPLETA, False si está INCOMPLETA.
        """
        texto_limpio = text.strip()
        if not texto_limpio:
            return False

        # REGLA DE ORO POR CÓDIGO: Filtro rápido para signos de exclamación o interrogación cerrados
        if texto_limpio.endswith('?') or texto_limpio.endswith('!'):
            print(f"✨ [Evaluación Automática] '{texto_limpio}' -> COMPLETA (Signo detectado)")
            return True

        try:
            # Tokenizamos el texto de entrada y lo enviamos al hardware correspondiente (GPU/CPU)
            inputs = self.tokenizer(
                texto_limpio, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=64
            ).to(self.device)
            
            # Desactivamos el cálculo de gradientes para acelerar la inferencia
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # El modelo nos da logits (probabilidades base). Sacamos el índice del valor más alto.
            # 0 = INCOMPLETA, 1 = COMPLETA
            prediccion = torch.argmax(outputs.logits, dim=1).item()
            
            if prediccion == 1:
                print(f"🧠 [HF Model] '{texto_limpio}' -> ✨ COMPLETA")
                return True
            else:
                print(f"🧠 [HF Model] '{texto_limpio}' -> ⏳ INCOMPLETA")
                return False

        except Exception as e:
            print(f"⚠️ Error en inferencia remota del clasificador: {e}")
            # Mecanismo de escape por si algo falla en los tensores, liberamos el texto
            return True

# Bloque de pruebas para validar tu nuevo clasificador desde HF sin levantar el servidor
if __name__ == "__main__":
    import asyncio
    
    async def test_local():
        try:
            analyzer = SemanticAnalyzer()
            print("\n--- Ejecutando Test de Inferencia Desde Hugging Face ---")
            
            frases = [
                "¿Puedes decirme de qué versículo de la Biblia es este texto?",
                "Hola Luna, búscame información sobre el trading de criptomonedas.",
                "El bot de trading de hoy creo que",
                "y si mejor hacemos una fiesta en la playa?",
                "el clima de hoy es muy",
                "No solo por el hecho de que no teníamos el dinero suficiente",
                "En cuanto la luz del semáforo cambie a verde",
                "Para poder entender el desenlace de esta complicada historia",
                "Después de haber pasado más de tres horas esperando en la sala de embarque",
                "Siempre que intentas explicar lo que realmente sucedió aquella noche",
                "Aunque todos sabían perfectamente quién era el verdadero responsable",
                "Con el propósito de mejorar los resultados del próximo trimestre",
                "Si decides aceptar la oferta de trabajo que te hicieron ayer",
                "A menos que ocurra un milagro de última hora en el proyecto",
                "Cada vez que escucho esa melodía tan melancólica en la radio",
                "Por más que intentamos reparar el motor del coche viejo",
                "Desde que se mudaron a esa enorme casa en las afueras de la ciudad",
                "Con el fin de evitar malentendidos entre los miembros del comité",
                "Si las sospechas del detective resultan ser completamente ciertas",
                "A pesar de las advertencias que nos dieron los guías locales",
                "En el preciso instante en que la alarma comenzó a sonar"
            ]
            
            for f in frases:
                res = await analyzer.is_idea_complete(f)
                print(f"Resultado: {res}\n")
                
        except Exception as e:
            print(e)

    asyncio.run(test_local())