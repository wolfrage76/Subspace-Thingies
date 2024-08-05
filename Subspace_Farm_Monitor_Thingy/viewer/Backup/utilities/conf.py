from collections import defaultdict
import time

# Initialize state
proves = {}
audits = {}
last_manual_update_time = time.time()
index_updated_externally = False
farmer_names_filtered = []
force_update = True
allSummedPlotting = {}
allSummedplottingCount = {}
avgtime = defaultdict(lambda: {})
balance = "0.0 tSSC"
banners = 'Visit http://subspace.ifhya.com for community tools!'
best_block = 0
cache_size = 1
current_farmer_index = 0
curr_farm_name = "Default"
curr_farm = None
curr_line = str()
curr_sector_disk = defaultdict(lambda: 0)
deltas = defaultdict(lambda: '00:00')
disk_farms = set()
dl = 0
drive_directory = {}
errors = [str(), str(), str(), str(), str(), str(), str(),]
event_times = defaultdict(int)
farm_deltas = defaultdict(lambda: {})
farmer_data = {}
farmer_name = 'WolfrageRocks'  # str()
farm_metrics = {}
farm_names = []
farm_plot_size = defaultdict(lambda: "0")
farm_recent_rewards = defaultdict(lambda: {})
farm_recent_skips = defaultdict(int)
farm_rewards = defaultdict(lambda: {})
farm_skips = defaultdict(int)
finalized = 0
frame_delays = -1
hour_24 = False
imported = 0
is_syncing = True
lang = {}
last_farm = int()
last_logs = [str(), str(), str(), str(), str(), str(), str(),]
# However many initialized is how many it'll show
last_node_logs = [str(), str(), str(), str(), str(), str(),]
last_sector_time = defaultdict(int)
last_sector_only = True
latest_version = "Unknown"
layout = None
name = str()
node_errors = [str(), str(), str(), str(), str(), str(), str(),]
#node_log_file = str()
node_warnings = [str(), str(), str(), str(), str(), str(), str(),]
no_more_drives = False
paused = False
peers = 0
plot_space = {}
plot_time_seconds = 0.0
prove_method = {}
psdTotal = 0
psTotal = 0
remote_farms = {}
remTotal = 0
replotting = defaultdict(lambda: False)
reward_count = 0
rewards_per_hr = defaultdict(lambda: [])
running = False
secTime = {}
sector_times = defaultdict(lambda: 0)
show_logging = True
startTime = 0
sum_plotted = defaultdict(lambda: {})
sum_size = defaultdict(lambda: {})
system_stats = {}
toggle_encoding = False
toggle_encoding_node = False
total_completed = 0
total_error_count = 0
translation = {}
ui_port = '8016'
ul = 0
unroll = False
ver = ''
view_state = 1
view_xtras = True
wallet = str()
warning_farms = []
warnings = [str(), str(), str(), str(), str(), str(), str(),]
theme_data = None
theme = None

translation['en'] = {
    'farm': 'Farm',
    'farmers': 'Farmers',
    'ram': 'RAM',
    'uptime': 'Up', 
    'day': 'day',
    'load': 'Load',
    'rewards': 'Rewards',
    'global_stats': 'Global Stats',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': 'Avg Sector',
    'lastsector':'Last Sector',
    'eta': 'ETA',
    'hour': 'hr',
    'plots': 'Plots',
    'block': 'Block',
    'peers': 'Peers',
    'synced': 'Synced',
    'unsynced': 'Unsynced',
    'latest': 'Latest',
    'replotting': 'Replotting',
    'report': 'Report',
    'inactivity_removal': 'Removed due to inactivity',
    'spacebar': 'SPACE',
    'tab': 'TAB',
    'pause': 'Pause',
    'toggle_data': 'Toggle Data',
    'change_display': 'Change Display',
    'quit': 'uit', # Done for English as Q is the displayed menu key. Use your full word for Quit
    'hm': 'H/M',
    'defaultbanner': 'Check out the community tools at:', 
    'an_error_occured':'an error occured' , 
    'pausing':'pausing' , 
    'exiting_requested':'Exiting as requested...' , 
    'error_sending':'Error sending to ##' , # wherever '##' is in the text will be replaced automatically    'wallet_error':'Wallet error',
    'decode_error': 'Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file!)',
    'connection_closed': 'Connection Closed',
    'retrying_seconds': 'Retrying in ## seconds', # wherever '##' is in the text will be replaced automatically
    'cycle_theme': 'Cycle Theme',
}

translation['ru'] = {
    'farm': 'Ферма',
    'farmers': 'Фермеры',
    'ram': 'ОЗУ',
    'uptime': 'Время работы',
    'day': 'день',
    'load': 'Нагрузка',
    'rewards': 'Награды',
    'global_stats': 'Глобальная статистика',
    'single_hits': 'H',
    'single_misses': 'М',
    'avgsector': 'Среднее Сектор',
    'eta': 'ОЖ',
    'hour': 'час',
    'plots': 'Плоты',
    'block': 'Блок',
    'peers': 'Пиры',
    'synced': 'Синхронизировано',
    'unsynced': 'Не синхронизировано',
    'latest': 'Последняя версия',
    'replotting': 'Перепланировка',
    'report': 'Отчет',
    'inactivity_removal': 'Удалено из-за неактивности',
    'spacebar': 'ПРОБЕЛ',
    'tab': 'ТАБ',
    'pause': 'Пауза',
    'toggle_data': 'Переключить данные',
    'change_display': 'Изменить отображение',
    'quit': 'Выход',
    'hm': '[green]H[yellow]/[red]М',
    'defaultbanner': 'Ознакомьтесь с инструментами сообщества на:',
    'lastsector':'Last Sector',
    'an_error_occured':'an error occured' , 
    'pausing':'pausing' , 
    'exiting_requested':'Exiting as requested...' , 
    'error_sending':'Error sending to ##' , # wherever '##' is in the text will be replaced automatically 
    'wallet_error':'Wallet error',
    'decode_error': 'Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file!)',
    'connection_closed': 'Connection Closed',
    'retrying_seconds': 'Retrying in ## seconds', # wherever '##' is in the text will be replaced automatically
    'cycle_theme': 'Cycle Theme',
}


translation['cn'] = {
                'farmer': '农场',
                'farmers': '农民',
                'ram': '内存',
                'uptime':'运行时间',
                'day': '天',
                'load': '加载', 
                'rewards': '奖励',
                'global_stats': '全球统计',
                'single_hits': '赢',
                'single_misses': '丢失', 
                'avgsector':'平均扇区时间', 
                'eta':'埃塔',
                'hour': '小时',
                'plots': '地块', 
                'block': '当前区块高度',
                'peers':'Anode同行数量', 
                'synced':'已同步', 
                'unsynced': '不同步',
                'latest': '最新版本', 
                'replotting': '重新绘制', 
                'report': '报告', 
                'inactivity_removal': '因不活跃而被删除',
                'spacebar': '空格键',
                'tab': 'TAB键',
                'pause':'暂停', 
                'toggle_data': '切换数据', 
                'change_display':'改变显示',
                'quit':'退出', 
                'hm': '[green]赢[yellow]/[red]错过', 
                'defaultbanner': '查看社区工具：',
                'cpu': 'CPU',
                'an_error_occured':'发生了错误' , 
                'pausing':'暂停' , 
                'exiting_requested':'根据请求退出...' , 
                'error_sending':'发送到 ## 时出错' ,
                'wallet_error':'钱包错误',
                'decode_error': '遇到解码错误（在config.yaml文件中切换TOGGLE_ENCODING!）',
                'connection_closed': '连接关闭',
                'retrying_seconds': '暂停 ## 秒',
                'lastsector':'最后一个扇区',
                'cycle_theme': '循环主题' 
                }


translation['lol'] = {
    'farm': 'Fam',
    'farmers': 'Fam',
    'ram': 'RAM',
    'uptime': "Chillin'",
    'day': 'day',
    'load': 'Load',
    'rewards': 'Riz',
    'global_stats': 'Spilling Tea',
    'single_hits': ':thumbs_up:',
    'single_misses': ':pile_of_poo:',
    'avgsector': 'Work Shift',
    'eta': "Quittin' Time",
    'hour': 'hr',
    'plots': 'Plots',
    'block': 'Block',
    'peers': 'Peeps',
    'synced': 'In the Know',
    'unsynced': 'Confused',
    'latest': 'Latest',
    'replotting': 'Do Over',
    'report': 'Report',
    'inactivity_removal': 'Removed due to inactivity',
    'spacebar': 'SPACE',
    'tab': 'TAB',
    'pause': 'Pause',
    'toggle_data': 'Toggle Data',
    'change_display': 'Change Display',
    'quit': 'uit',
    'hm': 'H/M',
    'defaultbanner': 'Check out the community tools at:', 
    'an_error_occured':'an error occured' , 
    'pausing':'pausing' , 
    'exiting_requested':'Exiting as requested...' , 
    'error_sending':'Error sending to ' ,     'wallet_error':'Wallet error',
    'decode_error': 'Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file!)',
    'connection_closed': 'Connection Closed',
    'retrying_seconds': 'Retrying in ## seconds'
     
}

translation['ua'] = {
    'farm': 'Ферма',
    'farmers': 'Фермери',
    'ram': 'ОЗП',
    'uptime': 'Час роботи',
    'day': 'день',
    'load': 'Навантаження',
    'rewards': 'Винагороди',
    'global_stats': 'Глобальна статистика',
    'single_hits': 'Х',
    'single_misses': 'В',
    'avgsector': 'Середнє Сектор',
    'eta': 'ETA',
    'hour': 'година',
    'plots': 'Ділянки',
    'block': 'Блок',
    'peers': 'Піри',
    'synced': 'Синхронізовано',
    'unsynced': 'Не синхронізовано',
    'latest': 'Останній',
    'replotting': 'Перезасіювання',
    'report': 'Звіт',
    'inactivity_removal': 'Видалено через неактивність',
    'spacebar': 'Пробіл',
    'tab': 'Таб',
    'pause': 'Пауза',
    'toggle_data': 'Перемикання даних',
    'change_display': 'Змінити відображення',
    'quit': 'Вийти',
    'hm': '[green]H[yellow]/[red]М',
    'defaultbanner': 'Ознайомтеся з інструментами спільноти на:',
	'lastsector':'останній сектор',
    'cycle_theme': 'Тема циклу' ,
    'an_error_occured':'виникла помилка' , 
    'pausing':'пауза' , 
    'exiting_requested':'Вихід за запитом...' , 
    'error_sending':'Помилка надсилання до ##' , # усюди, де '##' в тексті буде замінено автоматично
    'wallet_error':'помилка гаманця',
    'decode_error': 'Сталася помилка декодування (перемкніть TOGGLE_ENCODING у файлі config.yaml!)',
    'connection_closed': 'Підключення закрито',
    'retrying_seconds': 'Повторна спроба через ## секунд", # усюди, де "##" у тексті, буде замінено автоматично',
}

translation['es'] = {
    'farm': 'Granja',
    'farmers': 'Granjeros',
    'ram': 'RAM',
    'uptime': 'Tiempo activo',
    'day': 'día',
    'load': 'Carga',
    'rewards': 'Recompensas',
    'global_stats': 'Estadísticas globales',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': 'Promedio Sector',
    'eta': 'ETA',
    'hour': 'hr',
    'plots': 'Parcelas',
    'block': 'Bloque',
    'peers': 'Pares',
    'synced': 'Sincronizado',
    'unsynced': 'No sincronizado',
    'latest': 'Último',
    'replotting': 'Reparcelación',
    'report': 'Informe',
    'inactivity_removal': 'Eliminado por inactividad',
    'spacebar': 'ESPACIO',
    'tab': 'TAB',
    'pause': 'Pausa',
    'toggle_data': 'Alternar datos',
    'change_display': 'Cambiar pantalla',
    'quit': 'Salir',
    'hm': '[green]H[yellow]/[red]M',
    'defaultbanner': 'Consulta las herramientas de la comunidad en:',
                'lastsector':'Last Sector',
                'cycle_theme': 'Cycle Theme' 
}

translation['jp'] = {
    'farm': 'ファーム',
    'farmers': '農家',
    'ram': 'RAM',
    'uptime': '稼働時間',
    'day': '日',
    'load': '負荷',
    'rewards': '報酬',
    'global_stats': 'グローバル統計',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': '平均セクター',
    'eta': 'ETA',
    'hour': '時',
    'plots': 'プロット',
    'block': 'ブロック',
    'peers': 'ピア',
    'synced': '同期済み',
    'unsynced': '未同期',
    'latest': '最新',
    'replotting': '再配置',
    'report': 'レポート',
    'inactivity_removal': '非活動による削除',
    'spacebar': 'スペース',
    'tab': 'タブ',
    'pause': '一時停止',
    'toggle_data': 'データ切り替え',
    'change_display': '表示変更',
    'quit': '終了',
    'hm': '[green]H[yellow]/[red]M',
    'defaultbanner': 'コミュニティツールをチェック：',
                'lastsector':'Last Sector',
                'cycle_theme': 'Cycle Theme' 
}

translation['fr'] = {
    'farm': 'Ferme',
    'farmers': 'Farmeurs',
    'ram': 'RAM',
    'uptime': 'Temps de fonctionnement',
    'day': 'jour',
    'load': 'Chargement',
    'rewards': 'Récompenses',
    'global_stats': 'Statistiques globales',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': 'Moyenne Secteur',
    'eta': 'ETA',
    'hour': 'heure',
    'plots': 'Parcelles',
    'block': 'Bloc',
    'peers': 'Pairs',
    'synced': 'Synchronisé',
    'unsynced': 'Non synchronisé',
    'latest': 'Dernier version',
    'replotting': 'Replantation',
    'report': 'Rapport',
    'inactivity_removal': 'Retiré pour inactivité',
    'spacebar': 'ESPACE',
    'tab': 'TAB',
    'pause': 'Pause',
    'toggle_data': 'Basculer les données',
    'change_display': 'Changer l\'affichage',
    'quit': 'Quitter',
    'hm': '[green]H[yellow]/[red]M',
    'defaultbanner': 'Découvrez les outils de la communauté sur:', 
    'an_error_occured':'an error occured' , 
    'pausing':'pausing' , 
    'exiting_requested':'Exiting as requested...' , 
    'error_sending':'Error sending to ##' , # wherever '##' is in the text will be replaced automatically
    'wallet_error':'Wallet error',
    'decode_error': 'Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file!)',
    'connection_closed': 'Connection Closed',
    'retrying_seconds': 'Retrying in ## seconds', # wherever '##' is in the text will be replaced automatically
    'cycle_theme': 'Cycle Theme',
    'lastsector':'Last Sector',
}

translation['de'] = {
    'farm': 'Farm',
    'farmers': 'Landwirte',
    'ram': 'RAM',
    'uptime': 'Laufzeit',
    'day': 'Tag',
    'load': 'Last',
    'rewards': 'Belohnungen',
    'global_stats': 'Globale Statistiken',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': 'Durchschnitt Sektor',
    'eta': 'ETA',
    'hour': 'Std',
    'plots': 'Parzellen',
    'block': 'Block',
    'peers': 'Peers',
    'synced': 'Synchronisiert',
    'unsynced': 'Nicht synchronisiert',
    'latest': 'Neueste',
    'replotting': 'Umplanung',
    'report': 'Bericht',
    'inactivity_removal': 'Wegen Inaktivität entfernt',
    'spacebar': 'LEERTASTE',
    'tab': 'TAB',
    'pause': 'Pause',
    'toggle_data': 'Daten umschalten',
    'change_display': 'Anzeige ändern',
    'quit': 'Beenden',
    'hm': '[green]H[yellow]/[red]M',
    'defaultbanner': 'Schauen Sie sich die Community-Tools an unter:',
                'lastsector':'Last Sector',
                'cycle_theme': 'Cycle Theme' 
}

translation['ko'] = {
    'farm': '농장',
    'farmers': '농부들',
    'ram': 'RAM',
    'uptime': '가동 시간',
    'day': '일',
    'load': '부하',
    'rewards': '보상',
    'global_stats': '글로벌 통계',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': '평균섹터',
    'eta': 'ETA',
    'hour': '시간',
    'plots': '플롯',
    'block': '블록',
    'peers': '피어',
    'synced': '동기화됨',
    'unsynced': '동기화되지 않음',
    'latest': '최신',
    'replotting': '재배치',
    'report': '보고서',
    'inactivity_removal': '비활성화로 인한 제거',
    'spacebar': '스페이스바',
    'tab': '탭',
    'pause': '일시 정지',
    'toggle_data': '데이터 전환',
    'change_display': '디스플레이 변경',
    'quit': '종료',
    'hm': '[green]H[yellow]/[red]M',
    'defaultbanner': '커뮤니티 도구를 확인하세요:',
                'lastsector':'Last Sector',
                'cycle_theme': 'Cycle Theme' 
}

translation['vi'] = {
    'farm': 'Nông trại',
    'farmers': 'Nông dân',
    'ram': 'RAM',
    'uptime': 'Thời gian hoạt động',
    'day': 'Ngày',
    'load': 'Tải',
    'rewards': 'Phần thưởng',
    'global_stats': 'Thống kê chung',
    'single_hits': 'H',
    'single_misses': 'M',
    'avgsector': 'Trung bình sector',
    'eta': 'ETA',
    'hour': 'giờ',
    'plots': 'Plots',
    'block': 'block',
    'peers': 'peers',
    'synced': 'Đã đồng bộ',
    'unsynced': 'Chưa đồng bộ',
    'latest': 'Mới nhất',
    'replotting': 'plot lại',
    'report': 'Báo cáo',
    'inactivity_removal': 'Loại bỏ do không hoạt động',
    'spacebar': 'spacebar',
    'tab': 'TAB',
    'pause': 'Tạm dừng',
    'toggle_data': 'Chuyển đổi dữ liệu',
    'change_display': 'Thay đổi hiển thị',
    'quit': 'Thoát',
    'hm': 'H/M',
    'defaultbanner': 'Banner mặc định',
	'lastsector':'Sector cuối',
	'cycle_theme': 'Cycle Theme', 
    'an_error_occured':'một lỗi đã xảy ra' , 
    'pausing':'đang dừng' , 
    'exiting_requested':'Yêu cầu thoát...' , 
    'error_sending':'Có lỗi gửi đến ##' , # wherever '##' is in the text will be replaced automatically
    'wallet_error':'Lỗi ví',
    'decode_error': 'Lỗi đọc mã xảy ra (Toggle TOGGLE_ENCODING in the config.yaml file!)',
    'connection_closed': 'Kết nối đã được đóng',
    'retrying_seconds': 'Thử lại trong ## giây', # wherever '##' is in the text will be replaced automatically
    }
