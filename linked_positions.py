"""Class that create table of investor positions that opened for each one lieder position"""

import settings
from deal_comment import DealComment
from terminal import Terminal


class LinkedPositions:
    lieder_ticket: int
    positions: list
    volume: float
    symbol: str
    type: int

    __slots__ = ['lieder_ticket', 'positions', 'volume', 'symbol', 'type']

    def __init__(self, lieder_ticket, investor_positions=None):
        self.lieder_ticket = lieder_ticket
        self.positions = []
        self.symbol = ''
        self.type = -1
        if not investor_positions:
            investor_positions = Terminal.get_positions()
        for pos in investor_positions:
            comment = DealComment().set_from_string(pos.comment)
            if comment.lieder_ticket == self.lieder_ticket:
                self.positions.append(pos)
                if self.symbol == '':
                    self.symbol = pos.symbol
                if self.type < 0:
                    self.type = pos.type
        volume = 0.0
        for _ in self.positions:
            volume += _.volume
        decimals = Terminal.get_volume_decimals(self.symbol)
        self.volume = round(volume, decimals)

    @staticmethod
    def get_lieder_position_ticket(position):
        """Get lieder position ticket from investors position"""
        if DealComment.is_valid_string(position.comment):
            comment = DealComment().set_from_string(position.comment)
            return comment.lieder_ticket
        return -1

    @staticmethod
    def get_linked_positions_table():
        """Get table of investors positions, grouped for each lieder position ticket"""
        stored_ticket = []
        positions_table = []
        investor_positions = Terminal.get_positions()
        for pos in investor_positions:
            lid_ticket = LinkedPositions.get_lieder_position_ticket(pos)
            if lid_ticket not in stored_ticket:
                stored_ticket.append(lid_ticket)
                linked_positions = LinkedPositions(lieder_ticket=lid_ticket, investor_positions=investor_positions)
                positions_table.append(linked_positions)
        return positions_table

    def string(self):
        """For print table"""
        result = "\t"
        result += self.symbol + ' ' + str(self.lieder_ticket) + ' ' + str(self.volume) + " " + str(len(self.positions))
        for _ in self.positions:
            result += '\n\t\t' + str(_)
        return result

    def modify_volume(self, new_volume):
        """Change summary volume of linked positions"""
        print('  Текущий объем:', self.volume, ' Новый:', new_volume)
        decimals = Terminal.get_volume_decimals(self.symbol)
        new_comment = DealComment()
        new_comment.lieder_ticket = self.lieder_ticket
        new_comment.reason = '08'
        new_comment_str = new_comment.string()
        if new_volume > self.volume:  # Увеличение объема
            vol = round(new_volume - self.volume, decimals)
            print('\t Увеличение объема на', vol)
            request = {
                "action": Terminal.trade_action_deal(),
                "symbol": self.symbol,
                "volume": vol,
                "type": self.type,
                "price": Terminal.get_price_bid(self.symbol) if self.type == Terminal.position_type_sell()
                else Terminal.get_price_ask(self.symbol),
                "deviation": settings.DEVIATION,
                "magic": settings.MAGIC,
                "comment": new_comment_str,
                "type_time": Terminal.order_tyme_gtc(),
                "type_filling": Terminal.order_filling_fok(),
            }
            result = Terminal.send_order(request)
            return result
        elif new_volume < self.volume:  # Уменьшение объема
            target_volume = round(self.volume - new_volume, decimals)
            for pos in reversed(self.positions):
                if pos.volume <= target_volume:  # Если объем позиции меньше либо равен целевому, то закрыть позицию
                    print('\t Уменьшение объема. Закрытие позиции', pos.ticket, ' объем:', pos.volume)
                    request = {
                        'action': Terminal.trade_action_deal(),
                        'position': pos.ticket,
                        'symbol': pos.symbol,
                        'volume': pos.volume,
                        "type": Terminal.order_type_sell() if pos.type == Terminal.position_type_buy()
                        else Terminal.order_type_buy(),
                        'price': Terminal.get_price_bid(self.symbol) if self.type == Terminal.position_type_sell()
                        else Terminal.get_price_ask(self.symbol),
                        'deviation': Terminal.DEVIATION,
                        'magic:': Terminal.MAGIC,
                        'comment': new_comment_str,
                        'type_tim': Terminal.order_tyme_gtc(),
                        'type_filing': Terminal.order_filling_ioc()
                    }
                    result = Terminal.send_order(request)
                    print('\t', Terminal.send_retcodes[result.retcode], ':', result.retcode)
                    target_volume = round(target_volume - pos.volume,
                                          decimals)  # Уменьшить целевой объем на объем закрытой позиции
                elif pos.volume > target_volume:  # Если объем позиции больше целевого, то закрыть часть позиции
                    print('\t Уменьшение объема. Частичное закрытие позиции', pos.ticket, 'объем:', pos.volume,
                          'на', target_volume)
                    request = {
                        "action": Terminal.trade_action_deal(),
                        "symbol": pos.symbol,
                        "volume": target_volume,
                        "type": Terminal.order_type_sell() if pos.type == Terminal.position_type_buy()
                        else Terminal.order_type_buy(),
                        "position": pos.ticket,
                        'price': Terminal.get_price_bid(self.symbol) if self.type == Terminal.position_type_sell()
                        else Terminal.get_price_ask(self.symbol),
                        "deviation": Terminal.DEVIATION,
                        "magic": Terminal.MAGIC,
                        "comment": new_comment_str,
                        'type_tim': Terminal.order_tyme_gtc(),
                        "type_filling": Terminal.order_filling_fok(),
                    }
                    if target_volume > 0:
                        result = Terminal.send_order(request)
                        print('\t', Terminal.send_retcodes[result.retcode], ':', result.retcode)
                    else:
                        print('\t Частичное закрытие объема = 0.0')
                    break
