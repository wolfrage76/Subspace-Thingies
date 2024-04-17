# Заполните это и скопируйте в обе директории монитора и просмотра, так как это будет одинаково для обоих

LANGUAGE: 'ru'
# en = Английский
# cn = Китайский
# uk = Украинский
# es = Испанский
# ja = Японский
# fr = Французский
# de = Немецкий
# ko = Корейский
# vi = Вьетнамский
# ru = Русский

 #################
# Необходимо для обоих #
 ################

# ОБЯЗАТЕЛЬНО:
FRONT_END_IP: "192.168.1.209" # IP, на котором работает просмотрщик - 127.0.0.1, 192.168.1.69, любой
FRONT_END_PORT: "8016" # Порт, который использует фронтенд просмотра

 #######################
# Конфигурация бэкенда фермера #
 #######################

# ОБЯЗАТЕЛЬНО: (Разбор логов станет необязательным, но пока нет)
FARMER_NAME: "Moya" # Как этот фермер будет называться
FARMER_LOG: '/home/wolf/Subspace/farmlog.txt' # Разбираем этот файл лога фермера - в Windows используйте двойные \\

# ОБЯЗАТЕЛЬНО:
# Вам нужно добавить это в команду запуска вашего фермера: --prometheus-listen-on <localIP>:<PORT>
FARMER_IP: '192.168.1.209' # Это IP из выше
FARMER_PORT: '8181' # Это порт из выше

 ########################
# Конфигурация фронтенда просмотра #
 ########################

# Примечание: Оставление NODE_IP и/или NODE_PORT пустыми отключит отображение данных узла и мониторинг кошелька

# Вам нужно добавить это в команду запуска вашего узла: --rpc-listen-on <LocalIP>:<Port>
NODE_IP: "192.168.1.208" # IP вашего узла из выше -- 127.0.0.1, 192.168.1.69, любой
NODE_PORT: "9944" # Порт, который использует узел из выше. 9944 - это значение по умолчанию.

# Мониторинг кошелька - Запрашивает ваш узел на предмет изменений баланса и может уведомлять вас #
WALLET: # "stxxxxxxxxxxxxxxxx" # Пусто отключает мониторинг кошелька
WAIT_PERIOD: 480 # интервал проверки кошелька в секундах

# % для учета размера вашего кэша при расчете размеров. Значение по умолчанию для фермера - 1.
# Если вы не меняли это в команде запуска, оставьте как есть.
# Размер кэша не будет учитываться, если установлено значение 0. Не используйте символ %, только число.
CACHE_SIZE: 1 

# By default, the tool now parses the log to pull only the last sector's time for each plot.  This
# appears to be more accurate overall than the metrics method of taking an average of many hundreds
# of sector times, where a single interruption, or replots, can distort the numbers until the next restart.
# Using only last sector time will certainly make the impact of any changes made apparent much more quickly.
# Set to False if you want to go back to the previous method of very long term averaging provided
# by the metrics.
LAST_SECTOR_ONLY: True

 ###############
# Уведомления #
 ###############
 
SEND_DISCORD: False
SEND_PUSHOVER: False

# Общие уведомления указываются здесь #
DISCORD_WEBHOOK: "https://discord.com/api/webhooks/xxxxxxx" 

# Как выше, но только для уведомлений кошелька. По умолчанию используется DISCORD_WEBHOOK, если пусто.
DISCORD_WALLET_NOTIFICATIONS: "https://discord.com/api/webhooks/1dRxxxxxx" 

PUSHOVER_APP_TOKEN: "xxxxxxxxxxxxx" # да, мне нужно реализовать лучшую поддержку Pushover
PUSHOVER_USER_KEY: "xxxxxxxxxxxx"

 #########################
###   КОНЕЦ КОНФИГУРАЦИИ ПОЛЬЗОВАТЕЛЯ   ###
 #########################


####В настоящее время не используется####
SEND_REPORT: False # Отправить изображение фермера через Discord
REPORT_FREQ: 3600

# Внутреннее #
USE_BANNERS: True # позволяет получать баннер нижнего колонтитула для информации

 ################Экспериментально################

TOGGLE_ENCODING: False # Если список дисков не отображается или показывает ошибку Unicode или UTF-16, переключите эту настройку

# Устарело, или скоро устареет - Оставьте как есть! #
SHOW_LOGGING: True 
MUTE_HICKORY: True 
HOUR_24: False 
TOGGLE_ENCODING_NODE: True 
