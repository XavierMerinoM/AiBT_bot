import openai
import requests
import time
import os
from dotenv import load_dotenv

# obtenemos la información de las interacciones del usuario en Telegram con el bot
def get_updates(offset, token):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()["result"]

# enviamos la respuesta (text) del usuario (chat_id) hacia bot
def send_messages(chat_id, text, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    response = requests.post(url, params=params)
    return response

# maneja la interaccion hacia OpenAI
def get_openai_response(prompt):
    try:
        # nombre (unico) del modelo despues de proceso de fine-tuning
        # podemos obtener el nombre del playground
        model_engine = os.environ["FINE_TUNED_MODEL_NAME"]
        # los hiperparametros deben ser los mismos obtenidos en el Playground
        response = openai.Completion.create(
            engine = model_engine,
            prompt = prompt,
            max_tokens = 1000,
            # cantidad de respuestas
            n = 1,
            stop = " END",
            temperature = 0.5
        )
    except openai.error.APIError as e:
        #Manejar error de API aquí, p. reintentar o iniciar sesión
        print(f"La API de OpenAI devolvió un error de API: {e}")
        pass #Aprobar
    except openai.error.APIConnectionError as e:
        #Manejar error de conexión aquí
        print(f"Error al conectarse a la API de OpenAI: {e}")
        pass
    except openai.error.RateLimitError as e:
        #Manejar error de límite de tasa (recomendamos usar retroceso exponencial)
        print(f"La solicitud de API de OpenAI excedió el límite de frecuencia: {e}")
        pass
    finally:
        # strip - Remove spaces at the beginning and at the end of the string
        return response.choices[0].text.strip()

def main():
    # Take the variables from the .env file
    load_dotenv() 

    # Load variable that contains the API from OpenAI
    openai.api_key = os.environ["OPENAI_API"]
    TOKEN = os.environ["TELEGRAM_TOKEN"]

    print("Starting bot...")
    offset = 0
    while True:
        # Consultamos información del usuario y el mensaje
        updates = get_updates(offset, TOKEN)
        if updates:
            for update in updates:
                # Obtenemos la información del mensaje 
                offset = update["update_id"] +1
                chat_id = update["message"]["chat"]['id']
                user_message = update["message"]["text"]
                print(f"Received message: {user_message}")
                # genera una respuesta (completion) de una interacción con el modelo. La respuesta contiene el resultado del prompt enviado por el usuario
                GPT = get_openai_response(user_message)
                send_messages(chat_id, GPT, TOKEN)
        else:
            time.sleep(1)

if __name__ == '__main__':
    main()
