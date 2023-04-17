"""Class for connection and execute deals with terminal MetaTrader5"""
from datetime import datetime, timedelta
from math import fabs, floor

import MetaTrader5 as Mt

from deal_comment import DealComment
import settings
from http_commands import send_comment


class Terminal:
    send_retcodes = {
        -800: ('CUSTOM_RETCODE_NOT_ENOUGH_MARGIN', 'Уменьшите множитель или увеличьте сумму инвестиции'),
        -700: ('CUSTOM_RETCODE_LIMITS_NOT_CHANGED', 'Уровни не изменены'),
        -600: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
        -500: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
        -400: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
        -300: ('CUSTOM_RETCODE_EQUAL_VOLUME', 'Новый объем сделки равен существующему'),
        -200: ('CUSTOM_RETCODE_WRONG_SYMBOL', 'Нет такого торгового символа'),
        -100: ('CUSTOM_RETCODE_NOT_ENOUGH_MARGIN', 'Нехватка маржи. Выбран режим - Не открывать сделку или Не выбрано'),
        10004: ('TRADE_RETCODE_REQUOTE', 'Реквота'),
        10006: ('TRADE_RETCODE_REJECT', 'Запрос отклонен'),
        10007: ('TRADE_RETCODE_CANCEL', 'Запрос отменен трейдером'),
        10008: ('TRADE_RETCODE_PLACED', 'Ордер размещен'),
        10009: ('TRADE_RETCODE_DONE', 'Заявка выполнена'),
        10010: ('TRADE_RETCODE_DONE_PARTIAL', 'Заявка выполнена частично'),
        10011: ('TRADE_RETCODE_ERROR', 'Ошибка обработки запроса'),
        10012: ('TRADE_RETCODE_TIMEOUT', 'Запрос отменен по истечению времени'),
        10013: ('TRADE_RETCODE_INVALID', 'Неправильный запрос'),
        10014: ('TRADE_RETCODE_INVALID_VOLUME', 'Неправильный объем в запросе'),
        10015: ('TRADE_RETCODE_INVALID_PRICE', 'Неправильная цена в запросе'),
        10016: ('TRADE_RETCODE_INVALID_STOPS', 'Неправильные стопы в запросе'),
        10017: ('TRADE_RETCODE_TRADE_DISABLED', 'Торговля запрещена'),
        10018: ('TRADE_RETCODE_MARKET_CLOSED', 'Рынок закрыт'),
        10019: ('TRADE_RETCODE_NO_MONEY', 'Нет достаточных денежных средств для выполнения запроса'),
        10020: ('TRADE_RETCODE_PRICE_CHANGED', 'Цены изменились'),
        10021: ('TRADE_RETCODE_PRICE_OFF', 'Отсутствуют котировки для обработки запроса'),
        10022: ('TRADE_RETCODE_INVALID_EXPIRATION', 'Неверная дата истечения ордера в запросе'),
        10023: ('TRADE_RETCODE_ORDER_CHANGED', 'Состояние ордера изменилось'),
        10024: ('TRADE_RETCODE_TOO_MANY_REQUESTS', 'Слишком частые запросы'),
        10025: ('TRADE_RETCODE_NO_CHANGES', 'В запросе нет изменений'),
        10026: ('TRADE_RETCODE_SERVER_DISABLES_AT', 'Автотрейдинг запрещен сервером'),
        10027: ('TRADE_RETCODE_CLIENT_DISABLES_AT', 'Автотрейдинг запрещен клиентским терминалом'),
        10028: ('TRADE_RETCODE_LOCKED', 'Запрос заблокирован для обработки'),
        10029: ('TRADE_RETCODE_FROZEN', 'Ордер или позиция заморожены'),
        10030: ('TRADE_RETCODE_INVALID_FILL', 'Указан неподдерживаемый тип исполнения ордера по остатку'),
        10031: ('TRADE_RETCODE_CONNECTION', 'Нет соединения с торговым сервером'),
        10032: ('TRADE_RETCODE_ONLY_REAL', 'Операция разрешена только для реальных счетов'),
        10033: ('TRADE_RETCODE_LIMIT_ORDERS', 'Достигнут лимит на количество отложенных ордеров'),
        10034: (
            'TRADE_RETCODE_LIMIT_VOLUME', 'Достигнут лимит на объем ордеров и позиций для данного символа'),
        10035: ('TRADE_RETCODE_INVALID_ORDER', 'Неверный или запрещённый тип ордера'),
        10036: ('TRADE_RETCODE_POSITION_CLOSED', 'Позиция с указанным POSITION_IDENTIFIER уже закрыта'),
        10038: ('TRADE_RETCODE_INVALID_CLOSE_VOLUME', 'Закрываемый объем превышает текущий объем позиции'),
        10039: ('TRADE_RETCODE_CLOSE_ORDER_EXIST', 'Для указанной позиции уже есть ордер на закрытие'),
        10040: ('TRADE_RETCODE_LIMIT_POSITIONS',
                'Количество открытых позиций, которое можно одновременно иметь на счете, '
                'может быть ограничено настройками сервера'),
        10041: (
            'TRADE_RETCODE_REJECT_CANCEL',
            'Запрос на активацию отложенного ордера отклонен, а сам ордер отменен'),
        10042: (
            'TRADE_RETCODE_LONG_ONLY',
            'Запрос отклонен, так как на символе установлено правило "Разрешены только '
            'длинные позиции"  (POSITION_TYPE_BUY)'),
        10043: ('TRADE_RETCODE_SHORT_ONLY',
                'Запрос отклонен, так как на символе установлено правило "Разрешены только '
                'короткие позиции" (POSITION_TYPE_SELL)'),
        10044: ('TRADE_RETCODE_CLOSE_ONLY',
                'Запрос отклонен, так как на символе установлено правило "Разрешено только '
                'закрывать существующие позиции"'),
        10045: ('TRADE_RETCODE_FIFO_CLOSE',
                'Запрос отклонен, так как для торгового счета установлено правило "Разрешено '
                'закрывать существующие позиции только по правилу FIFO" ('
                'ACCOUNT_FIFO_CLOSE=true)'),
        10046: (
            'TRADE_RETCODE_HEDGE_PROHIBITED',
            'Запрос отклонен, так как для торгового счета установлено правило '
            '"Запрещено открывать встречные позиции по одному символу"')}

    login: int
    password: str
    server: str
    path: str
    account_balance: float
    account_equity: float
    start_date: datetime

    SERVER_DELTA_TIME = timedelta(hours=settings.SERVER_TIME_OFFSET_HOURS)
    TIMEOUT = settings.TIMEOUT_INIT
    DEVIATION = settings.DEVIATION
    MAGIC = settings.MAGIC

    __slots__ = ['login', 'password', 'server', 'path', 'account_balance', 'account_equity', 'start_date']

    def __init__(self, login, password, server, path, start_date):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.start_date = start_date

    def init_mt(self):
        """Initialize connection"""
        return Mt.initialize(login=self.login, server=self.server, password=self.password, path=self.path,
                             timeout=self.TIMEOUT)

    @staticmethod
    def get_account_balance():
        return Mt.account_info().balance

    def get_balance(self):
        self.account_balance = self.get_account_balance()
        return self.account_balance

    # @property
    def get_equity(self):
        self.account_equity = Mt.account_info().equity
        return self.account_equity

    @staticmethod
    def is_init_data_valid(data):
        try:
            valid = int(data['login']) and data['password'] and data['server'] and data['path']
            if not valid:
                print('Неверные данные инициализации', data)
            return valid
        except Exception as e:
            print('Неверные данные инициализации', e)
            return False

    @staticmethod
    def get_account_currency():
        return Mt.account_info().currency

    @staticmethod
    def symbol_info_tick(symbol):
        return Mt.symbol_info_tick(symbol)

    @staticmethod
    def get_contract_size(symbol):
        return Mt.symbol_info(symbol).trade_contract_size

    @staticmethod
    def get_history_deals_for_ticket(ticket):
        return Mt.history_deals_get(position=ticket)

    @staticmethod
    def get_history_orders_for_ticket(ticket):
        return Mt.history_orders_get(ticket=ticket)

    @staticmethod
    def copy_rates_range(symbol, time_from, time_to):
        return Mt.copy_rates_range(symbol, Mt.TIMEFRAME_M1, time_from, time_to)

    @staticmethod
    def copy_ticks_range(symbol, time_from, time_to):
        ticks = Mt.copy_ticks_range(symbol, time_from, time_to, Mt.COPY_TICKS_INFO)
        return ticks

    @staticmethod
    def send_order(request):
        return Mt.order_send(request)

    @staticmethod
    def trade_action_deal():
        return Mt.TRADE_ACTION_DEAL

    @staticmethod
    def trade_action_sltp():
        return Mt.TRADE_ACTION_SLTP

    @staticmethod
    def order_type_buy():
        return Mt.ORDER_TYPE_BUY

    @staticmethod
    def order_type_sell():
        return Mt.ORDER_TYPE_SELL

    @staticmethod
    def position_type_buy():
        return Mt.POSITION_TYPE_BUY

    @staticmethod
    def position_type_sell():
        return Mt.POSITION_TYPE_SELL

    @staticmethod
    def order_tyme_gtc():
        return Mt.ORDER_TIME_GTC

    @staticmethod
    def order_filling_ioc():
        return Mt.ORDER_FILLING_IOC

    @staticmethod
    def order_filling_fok():
        return Mt.ORDER_FILLING_FOK

    @staticmethod
    def get_price_bid(symbol):
        return Mt.symbol_info_tick(symbol).bid

    @staticmethod
    def get_price_ask(symbol):
        return Mt.symbol_info_tick(symbol).ask

    @staticmethod
    def get_volume_decimals(symbol):
        """Return decimal after point for symbol lot volume"""
        min_lot = Mt.symbol_info(symbol).volume_min
        return str(min_lot)[::-1].find('.')

    @staticmethod
    def get_symbol_decimals(symbol):
        points = Mt.symbol_info(symbol).point
        str_point = str(points)
        if 'e' in str_point:
            tmp = int(str_point.split('-')[-1])
        else:
            tmp = str_point[::-1].find('.')
        # print('=======', tmp)
        return tmp

    @staticmethod
    def get_pos_pips_tp(position, price=None):
        """calc position TP in pips"""
        if price is None:
            price = position.price_open
        result = 0.0
        try:
            if position.tp > 0:
                result = round(fabs(price - position.tp) / Mt.symbol_info(position.symbol).point)
        except AttributeError:
            if position['tp'] > 0:
                result = round(fabs(price - position['tp']) / Mt.symbol_info(position['symbol']).point)
        return result

    @staticmethod
    def get_pos_pips_sl(position, price=None):
        """calc position SL in pips"""
        if price is None:
            price = position.price_open
        result = 0.0
        try:
            if position.sl > 0:
                result = round(fabs(price - position.sl) / Mt.symbol_info(position.symbol).point)
        except AttributeError:
            if position['sl'] > 0:
                result = round(fabs(price - position['sl']) / Mt.symbol_info(position['symbol']).point)
        return result

    @staticmethod
    def get_positions(only_own=True):
        """Return own positions that was investor opened. [call for Lieder only with 'only_own=False']"""
        result = []
        positions = Mt.positions_get()
        if not positions:
            positions = []
        if only_own and len(positions):
            for _ in positions:
                if positions[positions.index(_)].magic == Terminal.MAGIC and \
                        DealComment.is_valid_string(_.comment):
                    result.append(_)
        else:
            result = positions

        return result

    @staticmethod
    def get_investors_positions_count(only_own=True):
        """Opened positions count"""
        return len(Terminal.get_positions()) if only_own else len(Terminal.get_positions(False))

    @staticmethod
    def is_lieder_position_in_investor(leader_position):
        """Return True if lieder position already exist in investor positions list"""
        invest_positions = Terminal.get_positions(only_own=False)
        if len(invest_positions) > 0:
            for pos in invest_positions:
                if DealComment.is_valid_string(pos.comment):
                    comment = DealComment().set_from_string(pos.comment)
                    if leader_position['ticket'] == comment.lieder_ticket:
                        return True
        return False

    # @staticmethod
    def is_lieder_position_in_investor_history(self, leader_position):
        """Return True if lieder position was opened by investor"""
        date_from = self.start_date + Terminal.SERVER_DELTA_TIME
        date_to = datetime.today().replace(microsecond=0) + timedelta(days=1)
        deals = Mt.history_deals_get(date_from, date_to)
        if not deals:
            deals = []
        result = None
        result_sl = None
        if len(deals) > 0:
            for pos in deals:
                if DealComment.is_valid_string(pos.comment):
                    comment = DealComment().set_from_string(pos.comment)
                    if leader_position['ticket'] == comment.lieder_ticket:
                        result = pos
                        if comment.reason == '07':
                            result_sl = pos
                if result and result_sl:
                    break
        return result, result_sl

    # @staticmethod
    def is_position_opened(self, leader_position, options_data):
        """Check position for exist in history and current positions of investor"""
        if Terminal.is_lieder_position_in_investor(leader_position=leader_position):
            return True

        exist_position, closed_by_sl = self.is_lieder_position_in_investor_history(leader_position=leader_position)
        if exist_position:
            if not closed_by_sl:
                if options_data['closed_deals_myself'] == 'Переоткрывать':
                    return False
            return True
        return False

    @staticmethod
    def is_symbol_allow(symbol):
        all_symbols = Mt.symbols_get()
        symbol_names = []
        for symbol_ in all_symbols:
            symbol_names.append(symbol_.name)

        if symbol in symbol_names:
            if Mt.symbol_select(symbol, True):
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def get_positions_profit():
        """Return profit of current open positions"""
        positions = Terminal.get_positions(only_own=True)
        result = 0
        if len(positions) > 0:
            for pos in positions:
                if pos.type < 2:
                    result += pos.profit  # + pos.commission
        return result

    # @staticmethod
    def get_history_profit(self):
        """Return profit of history deals"""
        date_from = self.start_date + Terminal.SERVER_DELTA_TIME
        date_to = datetime.now().replace(microsecond=0) + timedelta(days=1)
        deals = Mt.history_deals_get(date_from, date_to)

        if not deals:
            deals = []
        result = 0
        own_deals = []
        try:
            pos_tickets = []
            if len(deals) > 0:
                for pos in deals:
                    if DealComment.is_valid_string(pos.comment):
                        linked_pos = Mt.history_deals_get(position=pos.position_id)
                        for lp in linked_pos:
                            if lp.ticket not in pos_tickets:
                                pos_tickets.append(lp.ticket)
                                own_deals.append(lp)
            if len(own_deals) > 0:
                for pos in own_deals:
                    if pos.type < 2:
                        result += pos.profit  # + pos.commission
        except Exception as ex:
            print('ERROR get_history_profit():', ex)
            result = None
        return result

    @staticmethod
    def get_lots_for_investment(symbol, investment):
        print(
            f'\nsymbol: {symbol}')  # currency_base: {Mt.symbol_info(smb).currency_base}  currency_profit: {Mt.symbol_info(smb).currency_profit}  currency_margin: {Mt.symbol_info(smb).currency_margin}')
        price = Mt.symbol_info_tick(symbol).bid
        leverage = Mt.account_info().leverage
        contract = Mt.symbol_info(symbol).trade_contract_size

        min_lot = Mt.symbol_info(symbol).volume_min
        lot_step = Mt.symbol_info(symbol).volume_step
        decimals = str(lot_step)[::-1].find('.')

        volume_none_round = (investment * leverage) / (contract * price)
        if volume_none_round < min_lot:
            volume = 0.0
        else:
            volume = round(floor(volume_none_round / lot_step) * lot_step, decimals)

        print(
            f'Размер инвестиции: {investment}  Курс: {price}  Контракт: {contract}  Плечо: {leverage}  >>  ОБЪЕМ: {volume}')
        return volume

    # @staticmethod
    async def edit_volume_for_margin(self, options, request):
        """Calc for margin deficit and check for max deal volume"""
        response = Mt.order_check(request)
        if not response or len(response) <= 0:
            return 'EMPTY_REQUEST'
        if response.retcode == 10019 or response.retcode == 10014:  # Неправильный объем # Нет достаточных денежных средств для выполнения запроса
            info = Mt.symbol_info(request['symbol'])
            max_vol = info.volume_max
            if request['volume'] > max_vol:
                print(options['login'], f'Объем сделки [{request["volume"]}] больше максимального [{max_vol}]. ')
                await send_comment('Объем сделки больше максимального')
                return 'MORE_THAN_MAX_VOLUME'
            if options['not_enough_margin'] == 'Минимальный объем':
                request['volume'] = Mt.symbol_info(request['symbol']).volume_min
            elif options['not_enough_margin'] == 'Достаточный объем':
                hst_profit = self.get_history_profit()
                cur_profit = Terminal.get_positions_profit()
                balance = options['investment_size'] + hst_profit + cur_profit
                volume = Terminal.get_lots_for_investment(symbol=request['symbol'], investment=balance)
                request['volume'] = volume
            elif options['not_enough_margin'] == 'Не открывать' \
                    or options['not_enough_margin'] == 'Не выбрано':
                request = None
        return request

    # @staticmethod
    async def open_position(self, options_data, symbol, deal_type, lot, sender_ticket: int, tp=0.0, sl=0.0):
        """Open position in terminal"""
        try:
            point = Mt.symbol_info(symbol).point
            price = tp_in = sl_in = 0.0
            if deal_type == 0:  # BUY
                deal_type = Mt.ORDER_TYPE_BUY
                price = Mt.symbol_info_tick(symbol).ask
            if tp != 0:
                tp_in = price + tp * point
            if sl != 0:
                sl_in = price - sl * point
            elif deal_type == 1:  # SELL
                deal_type = Mt.ORDER_TYPE_SELL
                price = Mt.symbol_info_tick(symbol).bid
                if tp != 0:
                    tp_in = price - tp * point
                if sl != 0:
                    sl_in = price + sl * point
        except AttributeError:
            return {'retcode': -200}
        comment = DealComment()
        comment.lieder_ticket = sender_ticket
        comment.reason = '01'
        request = {
            "action": Mt.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": deal_type,
            "price": price,
            "sl": sl_in,
            "tp": tp_in,
            "deviation": Terminal.DEVIATION,
            "magic": Terminal.MAGIC,
            "comment": comment.string(),
            "type_time": Mt.ORDER_TIME_GTC,
            "type_filling": Mt.ORDER_FILLING_FOK,
        }
        checked_request = await self.edit_volume_for_margin(options=options_data,
                                                            request=request)  # Проверка и расчет объема при недостатке маржи
        if not checked_request:
            return {'retcode': -100}
        elif checked_request == -1:
            return {'retcode': -800}
        elif checked_request != 'EMPTY_REQUEST' and checked_request != 'MORE_THAN_MAX_VOLUME':
            result = Mt.order_send(checked_request)
            return result

    @staticmethod
    def close_position(position, reason):
        """Close position"""
        tick = Mt.symbol_info_tick(position.symbol)
        if not tick:
            return
        new_comment_str = position.comment
        if DealComment.is_valid_string(position.comment):
            comment = DealComment().set_from_string(position.comment)
            comment.reason = reason
            new_comment_str = comment.string()
        request = {
            'action': Mt.TRADE_ACTION_DEAL,
            'position': position.ticket,
            'symbol': position.symbol,
            'volume': position.volume,
            'type': Mt.ORDER_TYPE_BUY if position.type == 1 else Mt.ORDER_TYPE_SELL,
            'price': tick.ask if position.type == 1 else tick.bid,
            'deviation': Terminal.DEVIATION,
            'magic:': Terminal.MAGIC,
            'comment': new_comment_str,
            'type_tim': Mt.ORDER_TIME_GTC,
            'type_filing': Mt.ORDER_FILLING_IOC
        }
        result = Mt.order_send(request)
        print('\t\t - close position:', new_comment_str)
        return result

    @staticmethod
    def force_close_all_positions(reason):
        """Forced close positions"""
        positions = Terminal.get_positions(only_own=False)
        if len(positions) > 0:
            for position in positions:
                if position.magic == Terminal.MAGIC and DealComment.is_valid_string(position.comment):
                    Terminal.close_position(position=position, reason=reason)
        return positions

    @staticmethod
    def close_positions_by_lieder(leader_positions):
        """Close investor positions that was closed in lieder"""
        positions_investor = Terminal.get_positions()
        non_existed_positions = []
        if positions_investor:
            for ip in positions_investor:
                position_exist = False
                for lp in leader_positions:
                    comment = DealComment().set_from_string(ip.comment)
                    if comment.lieder_ticket == lp['ticket']:
                        position_exist = True
                        break
                if not position_exist:
                    non_existed_positions.append(ip)
        for pos in non_existed_positions:
            Terminal.close_position(position=pos, reason='06')
        return non_existed_positions
