"""Class translate lieder ticket and deal reason into position comment"""

reasons_code = {
    '01': 'Открыто СКС',
    '02': 'Закрыто по условию Блеклист',
    '03': 'Закрыто по команде пользователя',
    '04': 'Ключ APi истек',
    '05': 'Нет связи с биржей',
    '06': 'Закрыто инвестором',
    '07': 'Закрыто по условию стоп-лосс',
    '08': 'Объем изменен',
    '09': 'Лимиты изменены',
}


class DealComment:
    # comment = {
    #     'lieder_ticket': -1,
    #     'reason': '',  # Закрыто лидером, Закрыто по условию стоп-лосс
    # }

    lieder_ticket: int
    reason: str
    SEPARATOR = '-'
    __slots__ = ['lieder_ticket', 'reason']

    def __init__(self):
        self.lieder_ticket = -1
        self.reason = ''

    @staticmethod
    def is_valid_string(string: str):
        if len(string) > 0:
            sliced = string.split(DealComment.SEPARATOR)
            if len(sliced) == 2:
                if sliced[1] not in reasons_code:
                    return False
                try:
                    ticket = int(sliced[0])
                    if ticket < 0:
                        return False
                except ValueError:
                    return False
            else:
                return False
        return True

    def string(self):
        return f'{self.lieder_ticket}' + DealComment.SEPARATOR + f'{self.reason}'

    def obj(self):
        return {'lieder_ticket': self.lieder_ticket, 'reason': self.reason}

    def set_from_string(self, string: str):
        if DealComment.SEPARATOR in string:
            split_str = string.split(DealComment.SEPARATOR)
            lid_str = split_str[0]
            cause = split_str[1]
        elif len(string) > 0:
            lid_str = string
            cause = ''
        else:
            lid_str = '-1'
            cause = ''
        try:
            self.lieder_ticket = int(lid_str)
            self.reason = cause
        except ValueError:
            self.lieder_ticket = -1
            self.reason = ''
        return self

    def set_from_ticket(self, ticket: int):
        self.lieder_ticket = ticket
        self.reason = ''
