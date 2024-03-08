import websocket
import json
import time
import threading
from datetime import datetime
from binance.client import Client
import AbrirOrden
from time import sleep

# Configura tu clave API y secreto de Binance
api_key = 'TU_API_KEY'
api_secret = 'TU_API_SECRET'

# Crea una instancia del cliente de Binance
client = Client(api_key, api_secret)

# Obtiene la lista de pares de futuros
exchange_info = client.futures_exchange_info()

# Crea una lista para almacenar los pares de interés
pares_interes = []

# Filtra y almacena los pares en USDT del mercado PERPETUAL, excluyendo BTCUSDT y ETHUSDT
for symbol_info in exchange_info['symbols']:
    if symbol_info['quoteAsset'] == 'USDT' and symbol_info['contractType'] == 'PERPETUAL' and symbol_info['symbol'] not in ['USDCUSDT','BTCUSDT','ETHUSDT', 'SRMUSDT', 'HNTUSDT', 'TOMOUSDT', 'CVCUSDT', 'BTSUSDT', 'BTCSTUSDT', 'SCUSDT', 'RAYUSDT', 'FTTUSDT', 'COCOSUSDT']:
        pares_interes.append(symbol_info['symbol'])

# Definir los parámetros generales
umbral_porcentaje = 5
espera_segundos = 1800

# Un diccionario para realizar un seguimiento de las últimas alertas por símbolo
ultima_alerta = {}

# Función para manejar los mensajes entrantes del WebSocket
def on_message(ws, message):
    data = json.loads(message)
    if 'k' in data:
        candle = data['k']
        close_price = float(candle['c'])
        open_price = float(candle['o'])

        # Calcular el cambio porcentual
        cambio_porcentual = ((close_price - open_price) / open_price) * 100

        if abs(cambio_porcentual) >= umbral_porcentaje:
            symbol = data['s']  # Obtener el símbolo de la moneda
            current_price = float(data['k']['c'])
            local_time = datetime.now().strftime('%H:%M:%S')

            # Comprobar si ya ha pasado el tiempo de espera desde la última alerta
            if symbol not in ultima_alerta or (time.time() - ultima_alerta[symbol]) >= espera_segundos:
                if cambio_porcentual > 0:
                    sleep(1)
                    print(f"ALERTA ({local_time}): {symbol} SUBIO UN: +{cambio_porcentual:.2f}% EN 5 MINUTO, PRECIO: {current_price}")
                    sleep(2)
                    abrirOrden.abrir_orden(symbol, direction='SELL')
                else:
                    sleep(1)
                    print(f"ALERTA ({local_time}): {symbol} BAJO UN: {cambio_porcentual:.2f}% EN 5 MINUTO, PRECIO: {current_price}")
                    sleep(2)
                    AbrirOrden.abrir_orden(symbol, direction='BUY')
                    
                #send_telegram_message(TELEGRAM_CHAT_ID, mensaje)
                
                # Actualizar el tiempo de la última alerta
                ultima_alerta[symbol] = time.time()    
                
# Función principal para la conexión WebSocket
def start_websocket(symbol):
    url = f"wss://fstream.binance.com/ws/{symbol.lower()}@kline_5m"
    ws = websocket.WebSocketApp(url, on_message=on_message)
    ws.run_forever()

# Iniciar conexiones WebSocket para todas las monedas de futuros en USDT
symbols = pares_interes
for symbol in symbols:
    websocket_thread = threading.Thread(target=start_websocket, args=(symbol,))
    websocket_thread.start()

# Esperar a que todos los hilos WebSocket terminen
for symbol in symbols:
    websocket_thread.join()