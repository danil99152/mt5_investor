import json
import math

import requests

import settings
from http_commands import patch, get, post
from terminal import Terminal


class DBInterface:
    init_data: dict
    options: dict
    account_id: int
    host: str
    leader_id: int
    leader_balance: float
    leader_equity: float
    investment_size: float
    leader_currency: str

    __slots__ = ['init_data', 'options', 'account_id', 'host', 'leader_id', 'leader_balance',
                 'leader_equity', 'leader_currency', 'investment_size']

    def initialize(self, init_data, account_id, leader_id, host, leader_currency):
        self.init_data = init_data
        self.leader_id = leader_id
        self.account_id = account_id
        self.host = host
        self.leader_currency = leader_currency

    async def update_data(self):
        opt = await self.get_investor_options()
        if opt:
            self.options = opt[-1]
        await self.get_account_data()

    def send_currency(self):
        url = self.host + f'account/patch/{self.account_id}'
        data = {"currency": Terminal.get_account_currency()}
        requests.patch(url=url, data=json.dumps(data))

    async def send_history_position(self, position_ticket, max_balance):
        url = self.host + f'position/get/{self.account_id}/{position_ticket}'
        response = await get(url)
        investment = response[0]['investment_size']
        slippage_percent = self.options['deal_in_plus'] if self.options['deal_in_plus'] \
            else self.options['deal_in_minus']
        drawdown = (max_balance - (Terminal.get_account_balance() - investment)) / max_balance
        history_orders = Terminal.get_history_orders_for_ticket(int(position_ticket))
        deals_time = [deal.time_done for deal in history_orders]
        date_open = deals_time[0]
        date_close = deals_time[-1]
        # datetime.fromtimestamp(deal.time).strftime('%m/%d/%Y %H:%M:%S')
        deals_price = [deal.price_current for deal in history_orders]
        price_open = deals_price[0]
        price_close = deals_price[-1]
        change_percent = round(math.fabs(price_close - price_open) / price_open, 2)

        volumes = [deal.volume_initial for deal in history_orders]
        result_volume = 0
        for vol in volumes[1:]:
            result_volume = volumes[0] - vol
        volume_percent = (1 - result_volume / volumes[0]) * 100
        # print(volumes, volumes[1:])

        position = history_orders[0]
        if not position:
            return
        volume = history_orders[-1].volume_initial

        rates = Terminal.copy_rates_range(position.symbol, date_open - 1, date_close)
        if len(rates):
            price_max = max([_[2] for _ in rates])
            price_min = min([_[3] for _ in rates])
        else:
            price_min = price_max = 0
        history_deals = Terminal.get_history_deals_for_ticket(int(position_ticket))
        if history_deals:
            fee = history_deals[-1].fee
            swap = history_deals[-1].swap
        else:
            fee = swap = 0
        costs = fee + swap
        profits = [deal.profit for deal in history_deals]
        gross_pl = sum(profits)
        net_pl = gross_pl + costs
        balance = investment + net_pl

        current_positions = Terminal.get_positions()
        current_profit = 0
        for pos in current_positions:
            current_profit += pos.profit
        float_pl = Terminal.get_account_balance() - current_profit
        equity = Terminal.get_account_balance() + current_profit
        size = volume * Terminal.get_contract_size(position.symbol) * price_open
        bal_net = balance - net_pl
        lever = size / bal_net if bal_net else 0
        balance_percent = lever * 100
        if position.type == 0:  # BUY
            minimum = (price_min / price_open) * lever * 100 * -1
            maximum = (price_max / price_open) * lever * 100 * -1
        else:  # SELL
            minimum = (price_max / price_open) * lever * 100 * -1
            maximum = (price_min / price_open) * lever * 100 * -1

        data = {
            'ticket': position.ticket,  # Ticket
            'exchange': 'MT5',  # Exchange
            'user_id': '',  #
            'api_key': self.init_data['login'],  # API Key
            'secret_key': self.init_data['password'],  # Secret Key
            'account': self.account_id,  # Account
            'strategy': '',  #
            'investment': 0,  #
            'multiplicator': self.options['multiplier_value'],  # Multiplicator
            'stop_out': self.options['stop_value'],  # Stop out
            'symbol': position.symbol,  # Symbol
            'type': '',  #
            'position': '',  #
            'side': 'buy' if position.type == 0 else 'sell' if position.type == 1 else 'not buy or sell',  # Side
            'currency': '',  #
            'slippage_percent': slippage_percent,  # Slippage %
            'slippage_time': self.options['waiting_time'],  # Slippage time
            'size': size,  # Size
            'lots': volume,  # Lots
            'lever': lever,  # Lever
            'balance_percent': balance_percent,  # Balance %
            'volume_percent': volume_percent,  # Volume %
            'open_time': date_open,  # Open Time
            'open_price': price_open,  # Open Price
            'stop_loss': response[0]['sl'],  # history_orders[-1].sl,  # Stop loss
            'take_profit': response[0]['tp'],  # history_orders[-1].tp,  # Take profit
            'close_time': date_close,  # Close time
            'close_price': price_close,  # Close Price
            'change_percent': change_percent,  # Change_%
            'gross_p_l': gross_pl,  # Gross P&L
            'commision': fee,  # Fee
            'swap': swap,  # Swap
            'costs': costs,  # Costs
            'net_p_l': net_pl,  # Net P&L
            'roi': 0,  #
            'balance': balance,  # Balance
            'equity': equity,  # Equity
            'float_p_l': float_pl,  # Float P&L
            'duration': 0,  #
            'drawdown': drawdown,  # Drawdown
            'minimum': minimum,  # Minimum
            'maximum': maximum,  # Maximum
            'risk_reward': 0,  # `
            'roi_missed': 0,  # `
            'slip_percent': 0,  # `
            'slip_time': 0,  # `
            'magic': position.magic,  # Magic
            'comment': position.comment,  # Comment
        }
        print('history_position:\n', data)
        url = self.host + 'position-history/post'
        await post(url, data=json.dumps(data))

    @staticmethod
    def get_init_data(host, account_idx, terminal_path):
        url = host + f'account/get/{account_idx}'
        init_data = requests.get(url=url).json()[-1]
        init_data['path'] = terminal_path
        return init_data

    @staticmethod
    def get_leader_id(host, account_idx):
        url = host + f'leader_id_by_investor/get/{account_idx}'
        result = requests.get(url=url)
        # print(result.text)
        if result:
            return int(result.text)
        else:
            return -1

    async def get_investor_options(self):
        url = self.host + f'option/list/'
        return await get(url=url)
        # return requests.get(url=url).json()[-1]

    async def disable_dcs(self):
        url = self.host + f'account/patch/{self.account_id}/'
        data = {'access': False}
        await patch(url=url, data=json.dumps(data))

    async def get_db_positions(self, id_):
        url = self.host + f'position/list/active/{id_}'
        result = await get(url=url)
        # print(id_, url, result)
        return result

    async def get_account_data(self):
        url = self.host + f'account/get/{self.leader_id}'
        response = await get(url=url)
        if response:
            self.leader_balance = response[0]['balance']
            self.leader_equity = response[0]['equity']
            self.leader_currency = response[0]['currency']
            self.investment_size = response[0]['investment_size']
        else:
            print('\tEMPTY LEADER DATA')

    async def send_position(self, position, investment_size):
        url = self.host + 'position/post'
        data = {
            "account_pk": self.account_id,
            "ticket": position.ticket,
            "time": position.time,
            "time_update": position.time_update,
            "type": position.type,
            "magic": settings.MAGIC,
            "volume": position.volume,
            "price_open": position.price_open,
            "tp": position.tp,
            "sl": position.sl,
            "price_current": position.price_current,
            "symbol": position.symbol,
            "comment": position.comment,
            "profit": position.profit,
            "price_close": 0,
            "time_close": 0,
            'investment_size': investment_size,
            "active": True
        }
        print(f'\t-- add position {data["ticket"]}')
        await post(url=url, data=json.dumps(data))

    async def update_position(self, position):
        url = self.host + f'position/patch/{self.account_id}/{position.ticket}'
        data = {
            "time_update": position.time_update,
            "volume": position.volume,
            "tp": position.tp,
            "sl": position.sl,
            "profit": position.profit,
            "price_current": position.price_current,
            "comment": position.comment,
        }
        # print(url, data)
        await patch(url=url, data=json.dumps(data))

    async def disable_position(self, position_ticket):
        url = self.host + f'position/patch/{self.account_id}/{position_ticket}'
        data = {
            # "price_close": 0,
            # "time_close": 0,
            "active": False
        }
        # print(self.account_id, url, data)
        print(f'\t-- disable position {position_ticket}')
        await patch(url=url, data=json.dumps(data))
