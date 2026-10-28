import os
import json
import logging
from flask import Flask, request, Response
import requests

# Configurar logging básico
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Cargar variables de entorno
# En un entorno de producción como Cloud Run, estas variables se configuran en el servicio.
VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN')
GOOGLE_CHAT_WEBHOOK_URL = os.environ.get('GOOGLE_CHAT_WEBHOOK_URL')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Endpoint principal que maneja tanto la verificación del webhook (GET)
    como la recepción de mensajes (POST).
    """
    if request.method == 'GET':
        # --- Verificación del Webhook de WhatsApp ---
        # La API de WhatsApp envía un reto para verificar la URL.
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
            if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
                logging.warning("Verification token mismatch")
                return "Verification token mismatch", 403
            logging.info("Webhook verified successfully!")
            return request.args["hub.challenge"], 200
        logging.error("Failed to verify webhook")
        return "Failed to verify webhook", 400

    elif request.method == 'POST':
        # --- Recepción de Mensajes de WhatsApp ---
        data = request.get_json()
        logging.info("Received WhatsApp notification: %s", json.dumps(data, indent=2))

        # Asegurarnos de que el payload tiene el formato esperado
        if 'entry' in data and data['entry']:
            entry = data['entry'][0]
            if 'changes' in entry and entry['changes']:
                change = entry['changes'][0]
                if 'value' in change and 'messages' in change['value']:
                    message_data = change['value']['messages'][0]
                    
                    # Extraer información relevante del mensaje
                    customer_name = change['value']['contacts'][0]['profile']['name']
                    customer_phone = message_data['from']
                    message_text = ""

                    if message_data['type'] == 'text':
                        message_text = message_data['text']['body']
                    elif message_data['type'] == 'interactive':
                        # Para respuestas de botones o listas
                        interactive_response = message_data['interactive']
                        if interactive_response['type'] == 'button_reply':
                            message_text = interactive_response['button_reply']['title']
                        elif interactive_response['type'] == 'list_reply':
                             message_text = interactive_response['list_reply']['title']
                        else:
                            message_text = "Respuesta interactiva no reconocida."
                    elif message_data['type'] == 'button':
                        message_text = message_data['button']['text']
                    else:
                        message_text = f"(_Mensaje de tipo '{message_data['type']}' no soportado_)"
                    
                    # Enviar la información a Google Chat
                    send_to_google_chat(customer_name, customer_phone, message_text)

        return Response(status=200)

    else:
        # Método no permitido
        return Response(status=405)

def send_to_google_chat(name, phone, message):
    """
    Formatea y envía un mensaje a un webhook de Google Chat.
    """
    if not GOOGLE_CHAT_WEBHOOK_URL:
        logging.error("Google Chat Webhook URL is not set.")
        return

    # Formatear el mensaje para Google Chat usando "CardsV2" para un mejor aspecto
    card = {
        "cardsV2": [
            {
                "cardId": "whatsapp-message",
                "card": {
                    "header": {
                        "title": "Nuevo Mensaje de WhatsApp",
                        "subtitle": f"De: {name} ({phone})",
                        "imageUrl": "https://www.idesk.mx/assets/img/whatsapp.png",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "decoratedText": {
                                    "startIcon": {
                                        "knownIcon": "PERSON"
                                    },
                                    "text": f"{name}"
                                    }
                                },
                                {
                                    "decoratedText": {
                                    "startIcon": {
                                        "knownIcon": "PHONE"
                                    },
                                    "text": f"{phone}"
                                    }
                                },
                                {
                                    "textParagraph": {
                                        "text": f"<b>Mensaje:</b><br>{message}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    
    try:
        response = requests.post(GOOGLE_CHAT_WEBHOOK_URL, json=card, headers=headers)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        logging.info("Message sent to Google Chat successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message to Google Chat: {e}")

if __name__ == '__main__':
    # El puerto es definido por Cloud Run a través de la variable de entorno PORT
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
