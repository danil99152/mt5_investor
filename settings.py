import os

TIMEOUT_INIT = 60_000  # время ожидания при инициализации терминала (рекомендуемое 60_000 millisecond)
MAGIC = 876543210  # идентификатор эксперта
DEVIATION = 20  # допустимое отклонение цены в пунктах при совершении сделки
leader_existed_position_tickets = []  # default var
SERVER_TIME_OFFSET_HOURS = 3  # timedelta(hours=4)
old_investors_balance = {}

EURUSD = USDRUB = EURRUB = -1
sleep_leader_update = 1  # пауза для обновления лидера

terminal_path = os.path.abspath('MetaTrader5/terminal64.exe')
host = 'http://37.230.114.244:8000/'
exchange_id = int(os.getenv("EXCHANGE_ID"))


source = {
    # 'lieder': {},
    # 'investors': [{}, {}],
    # 'settings': {}
}
