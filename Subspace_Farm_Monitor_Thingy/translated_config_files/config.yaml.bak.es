# Complete esto y cópielo en los directorios del monitor y del visor, ya que será el mismo para ambos

LANGUAGE: 'es'
# en = Inglés
# cn = Chino
# uk = Ucraniano
# es = Español
# ja = Japonés
# fr = Francés
# de = Alemán
# ko = Coreano
# vi = Vietnamita
# ru = Ruso

 #################
# Necesario para ambos #
 ################

# OBLIGATORIO:
FRONT_END_IP: "192.168.1.209" # La IP en la que se ejecuta el Visor -- 127.0.0.1, 192.168.1.69, lo que sea
FRONT_END_PORT: "8016" # Puerto que utiliza el frontend del Visor

 #######################
# Configuración del Backend del Agricultor #
 #######################

# OBLIGATORIO: (El análisis de registros será opcional, pero aún no)
FARMER_NAME: "Moya" # Cómo se referirá a este agricultor
FARMER_LOG: '/home/wolf/Subspace/farmlog.txt' # Analizar este archivo de registro del Agricultor - En Windows use dobles \\

# OBLIGATORIO:
# Debe agregar esto a su comando de lanzamiento del Agricultor: --prometheus-listen-on <localIP>:<PORT>
FARMER_IP: '192.168.1.209' # Esta es la IP de arriba
FARMER_PORT: '8181' # Este es el Puerto de arriba

 ########################
# Configuración del Visor Frontend #
 ########################

# Nota: Dejar NODE_IP y/o NODE_PORT vacíos deshabilitará la visualización de datos del nodo Y el monitoreo de la billetera

# Debe agregar esto a su comando de lanzamiento del Nodo: --rpc-listen-on <LocalIP>:<Port>
NODE_IP: "192.168.1.208" # Su IP del nodo de arriba -- 127.0.0.1, 192.168.1.69, lo que sea
NODE_PORT: "9944" # Puerto que utiliza el nodo de arriba. 9944 es el predeterminado.

# Monitoreo de la Billetera - Consulta su nodo para cambios de saldo y puede notificarle #
WALLET: "st9CjiVAh3PYt5P5XFrRgPg47nw39G1Y3kB7FwbMTzAxegUX1" # Vacío deshabilita el monitoreo de la billetera
WAIT_PERIOD: 480 # intervalo de verificación de la billetera en segundos

# % para tener en cuenta el tamaño de su caché al calcular los tamaños. El predeterminado del Agricultor es 1.
# A menos que lo haya cambiado en su comando de lanzamiento, déjelo como está.
# El tamaño de la caché no se contará si se establece en 0. No use un símbolo %, solo un número.
CACHE_SIZE: 1 

 ###############
# Notificaciones #
 ###############
 
SEND_DISCORD: False
SEND_PUSHOVER: False

# Las notificaciones generales van aquí #
DISCORD_WEBHOOK: "https://discord.com/api/webhooks/1199928287774912602/gLIVElpW-eoii3uZh7Dsd6SG3Ee7BIs50pdH7FXeEWEaR5jDW5jhpx0VsaKc3w6XLkHU" 

# Como arriba, pero solo para notificaciones de la billetera. Por defecto es DISCORD_WEBHOOK si está vacío.
DISCORD_WALLET_NOTIFICATIONS: "https://discord.com/api/webhooks/1199199521981345792/LOlCM6nTtmZTyI6Fnk-O8Hso7KVFG4NXmqXIUfsv8V2dy7au9uFB7SkBCYQfJh5Z_noR" 

PUSHOVER_APP_TOKEN: "xxxxxxxxxxxxx" # sí, necesito implementar mejor soporte de Pushover
PUSHOVER_USER_KEY: "xxxxxxxxxxxx"

 #########################
###   FIN DE LA CONFIGURACIÓN DEL USUARIO   ###
 #########################


####Actualmente no se usa####
SEND_REPORT: False # Enviar imagen del Agricultor a través de Discord
REPORT_FREQ: 3600

# Interno #
USE_BANNERS: True # permite obtener el banner del pie de página para información

 ################Experimental################

TOGGLE_ENCODING: False # Si la lista de discos no aparece, o muestra un error de Unicode o UTF-16, cambie esta configuración

# Está Obsoleto, o pronto lo estará - ¡Déjelo como está! #
SHOW_LOGGING: True 
MUTE_HICKORY: True 
HOUR_24: False 
TOGGLE_ENCODING_NODE: True 
