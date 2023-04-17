
TIMEOUT_INIT = 60_000  # время ожидания при инициализации терминала (рекомендуемое 60_000 millisecond)
MAGIC = 876543210  # идентификатор эксперта
DEVIATION = 20  # допустимое отклонение цены в пунктах при совершении сделки
leader_existed_position_tickets = []  # default var
SERVER_TIME_OFFSET_HOURS = 3  # timedelta(hours=4)
old_investors_balance = {}

EURUSD = USDRUB = EURRUB = -1
sleep_leader_update = 1  # пауза для обновления лидера

host = 'https://my.atimex.io:8000/api/demo_mt5/'

source = {
    # 'lieder': {},
    # 'investors': [{}, {}],
    # 'settings': {}
}
