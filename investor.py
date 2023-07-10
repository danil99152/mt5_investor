# TODO: rewrite all cyrillic text to latin in print or send it via http because of encoding problem

import asyncio
import threading
from datetime import datetime
from math import fabs

from db_interface import DBInterface
from deal_comment import DealComment
import settings
from linked_positions import LinkedPositions
from terminal import Terminal

terminal: Terminal
old_investors_balance = 0
leader_positions = []
max_balance = 0
dcs_access = True
EURUSD = EURRUB = USDRUB = 0
db = DBInterface()
start_date = datetime.now().replace(microsecond=0)

leader_account_id = -1
exchange_id = settings.exchange_id

host = settings.host
terminal_path = settings.terminal_path


async def check_connection_exchange():
    close_reason = None
    try:
        if db.options['api_key_expired']:
            close_reason = '04'
            # force_close_all_positions(investor=investor, reason=close_reason)
        elif db.options['no_exchange_connection']:
            close_reason = '05'
            # force_close_all_positions(investor=investor, reason=close_reason)
        # if close_reason:
        #     await send_comment(comment=deal_comment.reasons_code[close_reason])
    except Exception as e:
        print("Exception in patching_connection_exchange:", e)
    return True if close_reason else False


async def check_notification():
    if db.options['notification']:
        # await send_comment('Вы должны оплатить вознаграждение')
        return True
    return False


async def execute_conditions():
    if db.options['disconnect']:
        # await send_comment('Инициатор отключения: ' + db.options['shutdown_initiator'])

        if Terminal.get_investors_positions_count(only_own=True) == 0:  # если нет открытых сделок
            await db.disable_dcs()

        if db.options['open_trades_disconnect'] == 'Закрыть':  # если сделки закрыть
            closed_positions = Terminal.force_close_all_positions('03')
            for _ in closed_positions:
                await db.send_history_position(_.ticket, max_balance)
            await db.disable_dcs()

        elif db.options['accompany_transactions']:  # если сделки оставить и не сопровождать
            await db.disable_dcs()


async def check_stop_limits():
    """Проверка стоп-лимита по проценту либо абсолютному показателю"""
    start_balance = float(db.options['investment'])
    if start_balance <= 0:
        start_balance = 1
    limit_size = float(db.options['stop_value'])
    calc_limit_in_percent = True if db.options['stop_loss'] == 'Процент' else False
    history_profit = terminal.get_history_profit()
    current_profit = Terminal.get_positions_profit()
    # SUMM TOTAL PROFIT
    if history_profit is None or current_profit is None:
        return
    close_positions = False
    total_profit = history_profit + current_profit
    print(f' - {init_data["login"]} [{db.leader_currency}] - {len(Terminal.get_positions())} positions. Access:',
          dcs_access, ' ', datetime.now(), end='')
    print('\t', 'Прибыль'.encode('utf-8') if total_profit >= 0
    else 'Убыток'.encode('utf-8'), 'торговли c'.encode('utf-8'), start_date,
          ':', round(total_profit, 2), db.leader_currency,
          '{curr.', round(current_profit, 2), ': hst. ' + str(round(history_profit, 2)) + '}')
    # CHECK LOST SIZE FOR CLOSE ALL
    if total_profit < 0:
        if calc_limit_in_percent:
            current_percent = fabs(total_profit / start_balance) * 100
            if current_percent >= limit_size:
                close_positions = True
        elif fabs(total_profit) >= limit_size:
            close_positions = True
        # CLOSE ALL POSITIONS
        active_positions = Terminal.get_positions()
        if close_positions and len(active_positions) > 0:
            print('     Закрытие всех позиций по условию стоп-лосс'.encode('utf-8'))
            # await send_comment('Закрытие всех позиций по условию стоп-лосс. Убыток торговли c' + str(
            #     start_date.replace(microsecond=0)) + ':' + str(round(total_profit, 2)))
            for act_pos in active_positions:
                if act_pos.magic == terminal.MAGIC:
                    Terminal.close_position(position=act_pos, reason='07')
                    await db.send_history_position(act_pos.ticket, max_balance)
            if db.options['open_trades'] == 'Закрыть и отключить':
                await db.disable_dcs()


def synchronize_positions_volume():
    try:
        investors_balance = db.options['investment']
        global old_investors_balance
        if "Корректировать объем" in (db.options["recovery_model"], db.options["buy_hold_model"]):
            if investors_balance != old_investors_balance:
                volume_change_coefficient = investors_balance / old_investors_balance
                if volume_change_coefficient != 1.0:
                    investors_positions_table = LinkedPositions.get_linked_positions_table()
                    for _ in investors_positions_table:
                        decimals = Terminal.get_volume_decimals(_.symbol)
                        volume = _.volume
                        new_volume = round(volume_change_coefficient * volume, decimals)
                        if volume != new_volume:
                            _.modify_volume(new_volume)
                old_investors_balance = investors_balance
    except Exception as e:
        print("Exception in synchronize_positions_volume():", e)


def synchronize_positions_limits(lieder_positions):
    """Изменение уровней ТП и СЛ указанной позиции"""
    for l_pos in lieder_positions:
        if not Terminal.is_symbol_allow(l_pos['symbol']):
            continue
        l_tp = Terminal.get_pos_pips_tp(l_pos, l_pos['price_open'])
        l_sl = Terminal.get_pos_pips_sl(l_pos, l_pos['price_open'])
        if l_tp > 0 or l_sl > 0:
            for i_pos in Terminal.get_positions():
                request = []
                new_comment_str = comment = ''
                if DealComment.is_valid_string(i_pos.comment):
                    comment = DealComment().set_from_string(i_pos.comment)
                    comment.reason = '09'
                    new_comment_str = comment.string()
                if comment.lieder_ticket == int(l_pos['ticket']):
                    i_tp = Terminal.get_pos_pips_tp(i_pos)
                    i_sl = Terminal.get_pos_pips_sl(i_pos)
                    sl_lvl = tp_lvl = 0.0
                    decimals = 10 ** -Terminal.get_symbol_decimals(i_pos.symbol)
                    if i_pos.type == Terminal.position_type_buy():
                        sl_lvl = i_pos.price_open - l_sl * decimals if l_sl else 0.0
                        tp_lvl = i_pos.price_open + l_tp * decimals if l_tp else 0.0
                    elif i_pos.type == Terminal.position_type_sell():
                        sl_lvl = i_pos.price_open + l_sl * decimals if l_sl else 0.0
                        tp_lvl = i_pos.price_open - l_tp * decimals if l_tp else 0.0

                    if i_tp != l_tp or i_sl != l_sl:
                        request = {
                            "action": Terminal.trade_action_sltp(),
                            "position": i_pos.ticket,
                            "symbol": i_pos.symbol,
                            "sl": sl_lvl,
                            "tp": tp_lvl,
                            "magic": Terminal.MAGIC,
                            "comment": new_comment_str
                        }

                if request:
                    result = Terminal.send_order(request)
                    print('\tЛимит изменен:'.encode('utf-8'), result)


def check_transaction(leader_position):
    """Проверка открытия позиции"""
    price_refund = bool(db.options['price_refund'])
    if not price_refund:  # если не возврат цены
        timeout = db.options['waiting_time']  # * 60

        deal_time = int(leader_position['time_update'])  # - datetime.utcnow().timestamp())
        curr_time = int(datetime.timestamp(datetime.utcnow().replace(microsecond=0)))
        delta_time = curr_time - deal_time
        if delta_time > timeout:  # если время больше заданного
            print('Время истекло'.encode('utf-8'))
            return False

    transaction_type = 0
    if db.options['ask_an_investor'] == 'Плюс':
        transaction_type = 1
    elif db.options['ask_an_investor'] == 'Минус':
        transaction_type = -1
    deal_profit = leader_position['profit']
    if transaction_type > 0 > deal_profit:  # если открывать только + и профит < 0
        return False
    if deal_profit > 0 > transaction_type:  # если открывать только - и профит > 0
        return False

    transaction_plus = float(db.options['deal_in_plus'])
    transaction_minus = float(db.options['deal_in_minus'])
    price_open = float(leader_position['price_open'])
    price_current = float(leader_position['price_current'])

    res = None
    if leader_position['type'] == 0:  # Buy
        res = (price_current - price_open) / price_open * 100  # Расчет сделки покупки по формуле
    elif leader_position['type'] == 1:  # Sell
        res = (price_open - price_current) / price_open * 100  # Расчет сделки продажи по формуле
    return True if res is not None and transaction_plus >= res >= transaction_minus else False  # Проверка на заданные отклонения


def multiply_deal_volume(leader_position):
    """Расчет множителя"""
    lieder_balance_value = db.leader_balance if db.options['multiplier'] == 'Баланс' else db.leader_equity
    symbol = leader_position['symbol']
    lieder_volume = leader_position['volume']
    multiplier = float(db.options['multiplier_value'])
    investment_size = float(db.options['investment'])
    get_for_balance = True if db.options['multiplier'] == 'Баланс' else False
    if get_for_balance:
        ext_k = (investment_size + terminal.get_history_profit()) / lieder_balance_value
    else:
        ext_k = (investment_size + terminal.get_history_profit() + Terminal.get_positions_profit()) / \
                lieder_balance_value
    try:
        decimals = Terminal.get_volume_decimals(symbol)
    except AttributeError:
        decimals = 2
    if not db.options['changing_multiplier']:
        result = round(lieder_volume * ext_k, decimals)
    else:
        result = round(lieder_volume * multiplier * ext_k, decimals)
    return result


def get_currency_coefficient():
    global EURUSD, EURRUB, USDRUB
    lid_currency = db.leader_currency  # source['lieder']['currency']
    inv_currency = Terminal.get_account_currency()  # investor['currency']
    # eurusd = usdrub = eurrub = -1

    usdrub = Terminal.get_price_bid('USDRUB')
    eurusd = Terminal.get_price_bid('EURUSD')
    eurrub = usdrub * eurusd

    if eurusd > 0:
        EURUSD = eurusd
    if usdrub > 0:
        USDRUB = usdrub
    if eurrub > 0:
        EURRUB = eurrub
    currency_coefficient = 1
    try:
        if lid_currency == inv_currency:
            currency_coefficient = 1
        elif lid_currency == 'USD':
            if inv_currency == 'EUR':
                currency_coefficient = 1 / eurusd
            elif inv_currency == 'RUB':
                currency_coefficient = usdrub
        elif lid_currency == 'EUR':
            if inv_currency == 'USD':
                currency_coefficient = eurusd
            elif inv_currency == 'RUB':
                currency_coefficient = eurrub
        elif lid_currency == 'RUB':
            if inv_currency == 'USD':
                currency_coefficient = 1 / usdrub
            elif inv_currency == 'EUR':
                currency_coefficient = 1 / eurrub
    except Exception as e:
        print('Except in get_currency_coefficient()', e)
        currency_coefficient = 1
    return currency_coefficient


async def execute_investor(leader_id, leaders, sleep=settings.sleep_leader_update):
    global leader_positions, db, max_balance
    while True:
        await db.update_data(leader_id)
        leader_positions = await db.get_db_positions(leaders)
        balance = Terminal.get_account_balance()
        if balance > max_balance:
            max_balance = balance

        if db.options['blacklist']:
            print(init_data['login'], 'in blacklist')
            return
        if await check_notification():
            print(init_data['login'], 'not pay - notify')
            return
        # if await check_connection_exchange():
        #     print(init_data['login'], 'API expired or Broker disconnected')
        #     return

        if dcs_access:
            await execute_conditions()  # проверка условий кейса закрытия
        if dcs_access:
            await check_stop_limits()  # проверка условий стоп-лосс

        if dcs_access:

            # synchronize_positions_volume()  # коррекция объемов позиций
            synchronize_positions_limits(leader_positions)  # коррекция лимитов позиций

            for pos_lid in leader_positions:
                if not Terminal.is_symbol_allow(pos_lid['symbol']):
                    continue
                tick = Terminal.copy_rates_range(pos_lid['symbol'], pos_lid['time'],
                                                 Terminal.symbol_info_tick(pos_lid['symbol']).time)
                # print(tick)
                if terminal.is_position_opened(options_data=db.options, leader_position=pos_lid):
                    continue

                inv_tp = Terminal.get_pos_pips_tp(pos_lid, pos_lid['price_open'])
                inv_sl = Terminal.get_pos_pips_sl(pos_lid, pos_lid['price_open'])

                ret_code = None
                if check_transaction(leader_position=pos_lid):

                    volume = multiply_deal_volume(leader_position=pos_lid)
                    decimals = Terminal.get_volume_decimals(pos_lid['symbol'])
                    volume = round(volume / get_currency_coefficient(), decimals)
                    response = await terminal.open_position(options_data=db.options, symbol=pos_lid['symbol'],
                                                            deal_type=pos_lid['type'],
                                                            lot=volume, sender_ticket=int(pos_lid['ticket']),
                                                            tp=inv_tp, sl=inv_sl)
                    if response:
                        try:
                            ret_code = response.retcode
                        except AttributeError:
                            ret_code = response['retcode']
                if ret_code:
                    msg = (str(init_data['login']) + ' ' + str(Terminal.send_retcodes[ret_code][1].decode('utf-8'))) \
                        .encode('utf-8')  # + ' : ' + str(ret_code)
                    # if ret_code != 10009:  # Заявка выполнена
                    #     await send_comment('\t' + msg)
                    print(msg)
            # else:
            #     set_comment('Не выполнено условие +/-')

        # закрытие позиций от лидера
        if (dcs_access or  # если сопровождать сделки или доступ есть
                (not dcs_access and db.options['accompany_transactions'])):
            closed_positions_by_leader = Terminal.close_positions_by_lieder(leader_positions=leader_positions)
            closed_positions_by_investor = await db.get_db_disable_positions(exchange_id=exchange_id)
            positions_investor = Terminal.get_positions()
            db_tickets = [obj['ticket'] for obj in closed_positions_by_investor]
            for _ in closed_positions_by_leader:
                await db.send_history_position(_.ticket, max_balance)
            for pos in positions_investor:
                if pos not in closed_positions_by_leader and pos.ticket in db_tickets:
                    Terminal.close_position(position=pos, reason='06')
                    await db.send_history_position(pos.ticket, max_balance)

        active_db_positions = await db.get_db_positions([exchange_id])
        active_db_tickets = [int(position['ticket']) for position in active_db_positions]
        terminal_positions = Terminal.get_positions()
        terminal_tickets = [position.ticket for position in terminal_positions]

        for position in terminal_positions:
            if position.ticket not in active_db_tickets:
                await db.send_position(position, db.investment_size)
            else:
                await db.update_position(position)

        for position in active_db_positions:
            if int(position['ticket']) not in terminal_tickets:
                await db.disable_position(int(position['ticket']))

        await asyncio.sleep(sleep)


def callback(leader_id, leader_account_ids):
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(execute_investor(leader_id=leader_id, leaders=leader_account_ids))
    event_loop.run_forever()


if __name__ == '__main__':
    init_data = db.get_init_data(host=host, exchange_idx=exchange_id, terminal_path=terminal_path)
    print(init_data)

    if not Terminal.is_init_data_valid(init_data):
        exit()
    terminal = Terminal(login=int(init_data['login']),
                        password=init_data['password'],
                        server=init_data['server'],
                        path=init_data['path'],
                        start_date=datetime.now(),
                        portable=True)
    if not terminal.init_mt():
        print('Ошибка инициализации инвестора'.encode('utf-8'), init_data)
        exit()
    leader_account_ids = db.get_leader_ids(host, exchange_id)
    for leader_account_id in leader_account_ids:
        db.initialize(init_data=init_data, leader_id=leader_account_id, exchange_id=exchange_id, host=host,
                      leader_currency=Terminal.get_account_currency())

        db.send_currency()
        threading.Thread(target=callback, args=(leader_account_id, leader_account_ids,)).start()
