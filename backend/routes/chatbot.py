import os
import requests
from flask import Blueprint, jsonify, request

chatbot_bp = Blueprint("chatbot", __name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Eres el asistente virtual de Herrería "Los Mejía", un taller que
trabaja hierro, aluminio y vidrio (portones, rejas, barandales, ventanas,
cancelería y trabajos a medida). Tu trabajo es:

- Responder dudas sobre materiales, tipos de trabajo y tiempos de entrega en general.
- Guiar al cliente a usar el cotizador de la página (sección "Cotizador") si
  quiere un precio, explicando que solo necesita el material y las medidas en metros.
- Si el cliente quiere hablar con una persona, pedirle que deje su nombre y
  teléfono, y avisar que el equipo de Los Mejía le contactará.
- Ser breve, cálido y profesional. Responder siempre en español de México.
- No inventar precios exactos: los precios reales salen del cotizador de la página.
"""


@chatbot_bp.post("/mensaje")
def enviar_mensaje():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({
            "error": "El chatbot no está configurado todavía. "
                     "Falta la variable de entorno ANTHROPIC_API_KEY en el servidor."
        }), 503

    data = request.get_json(force=True)
    historial = data.get("historial", [])  # [{role: "user"|"assistant", content: "..."}]
    if not historial:
        return jsonify({"error": "Falta 'historial' con al menos un mensaje."}), 400

    try:
        respuesta = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": historial,
            },
            timeout=20,
        )
        respuesta.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"No se pudo contactar al chatbot: {e}"}), 502

    cuerpo = respuesta.json()
    texto = "".join(
        bloque.get("text", "") for bloque in cuerpo.get("content", [])
        if bloque.get("type") == "text"
    )
    return jsonify({"respuesta": texto})
