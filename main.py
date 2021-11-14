import re
import ast
from random import randint


class Card:
    COLOR_CODES = ['r', 'd', 'o', 'e', 's', 'x']
    COLOR_SHORT_NAMES = ["ruby ", "diamd", "onyx ", "emrld", "saphi", "artcr"]
    COLOR_IDS = {
        key: [value, cid] for key, value, cid in zip(COLOR_CODES, COLOR_SHORT_NAMES, range(len(COLOR_CODES)))
    }

    def __init__(self, format_list: list = None, gem: int = None, level: int = None,
                 value: int = None, cost: list = None, printing_rules='e'):
        if format_list and len(format_list) == 9:
            if not isinstance(format_list[0], str):
                raise ValueError("improper color code type in first format argument")
            if len(format_list[0]) != 1:
                raise ValueError("code has exactly one character")
            if any([(not isinstance(i, int)) for i in format_list[1:]]):
                raise ValueError("improper type of format list argument; should be int")
            self.gem = format_list[0]
            self.value = format_list[2]
            self.level = format_list[3]
            self.cost = tuple(format_list[4:])
        else:
            if any([gem is None, level is None, value is None, cost is None]):
                if len(format_list) != 9:
                    raise ValueError("format list has to be exactly 9 elements long")
                raise ValueError("Values can't be empty unless you provide formating list with 9 elements")
            if gem not in self.COLOR_CODES:
                raise ValueError(f"{gem} isn't valid color code")
            if any([not isinstance(level, int), not isinstance(value, int)]):
                raise ValueError("card value and level has to be of type int")
            if len(cost) != 5:
                raise ValueError("cost variable has to have exactly 5 values")
            if any([(not isinstance(val, int)) for val in cost]):
                raise ValueError("values in cost has to be of type int")
            self.gem = gem
            self.value = value
            self.level = level
            self.cost = tuple(cost)
        self.printing_rules = printing_rules

    def __str__(self):
        # guard case
        if not self.printing_rules:
            return str([self.gem, self.level, self.value, self.cost])
        p = f' {self.value if self.value > 0 else " "} '
        rank = ' R' + ''.join(['I' if i <= self.level - 1 else ' ' for i in range(3)]) + ' '
        gem = self.COLOR_SHORT_NAMES[self.color_id]
        return ''.join([
            f"╔═════════════════╗\n",
            f"║ {gem}       {p} ║\n",
            f"║    +    {rank}  ║\n",
            f"║   /_\           ║\n",
            f"║  :<_>:   %s rub ║\n" % (f' {self.cost[0]}',),
            f"║ /=====\  %s dia ║\n" % (f' {self.cost[1]}',),
            f"║ :_[I]_:  %s onx ║\n" % (f' {self.cost[2]}',),
            f"║::::::::: %s emd ║\n" % (f' {self.cost[3]}',),
            f"║          %s sap ║\n" % (f' {self.cost[4]}',),
            f"╚═════════════════╝"])

    def can_be_bought(self, other):
        """
        for simplicity, invoking counterpart method from 'player' class
        :param other:
        :return:
        """
        # guard condition
        if isinstance(other, Card):
            raise NotImplementedError("comparison between cards isn't implemented yet")
        if isinstance(other, Player):
            return other.can_buy(self)
        raise ValueError(f"can't compare object {other.__class__} to Card meaningfully")

    @property
    def color_id(self):
        return self.COLOR_IDS[self.gem][1]

    def print_short(self):
        p_r = self.printing_rules
        self.printing_rules = None
        s = str(self)
        self.printing_rules = p_r
        return s


class Player:

    def __init__(self, p_id: int):
        if not isinstance(p_id, int):
            raise ValueError(f'id of the player should be of class int, not {p_id.__class__}')
        self.id = p_id
        self.tokens = [0] * 6
        self.cards = []

    def can_buy(self, other: Card):
        """
        this is used to calculate if a player can afford to buy a specific card most of the time
        first we calculate if player has enough combined regular tokens + card equivalents
        then if he has not enough, 'wild-card' tokens come to calculation, and only if this is not enough
        it returns false
        :param other: Card that one wish to buy
        :return: True if greateor equal, or not if there's not enough resources
        """
        # guard statement
        if not isinstance(other, Card):
            if isinstance(other, Player):
                raise NotImplementedError("comparison between players isn't implemented yet")
            raise ValueError(f"can't compare object {other.__class__} to Player meaningfully")
        # compute the difference of the player 'buy-power' against card cost, leave
        # values only for tokens that matter, using 'gtz' lambda for that
        cids = Card.COLOR_IDS
        difference = [
            self.buying_power[cids[c_code][1]] - other.cost[cids[c_code][1]]
            for c_code in Card.COLOR_CODES[:5]
        ]
        lacking = -sum([0 if d >= 0 else d for d in difference])
        if lacking > self.tokens[5]:
            return False, lacking
        return True, lacking

    @property
    def buying_power(self):
        power = [_ for _ in self.tokens]
        for card in self.cards:
            power[card.color_id] += 1
        return power

    @property
    def card_power(self):
        power = [0] * 5
        for card in self.cards:
            if card.color_id != 5:
                power[card.color_id] += 1
        return power

    def get_token(self, color: int):
        self.tokens[color] += 1

    def pay_tokens(self, debt, card: Card):
        to_pay = [
                     min(tokens, max(cost - cs, 0)) if cost > 0 else 0
                     for tokens, cs, cost in zip(self.tokens, self.card_power, card.cost)
                  ] + [debt[1]]
        self.tokens = [tokens - pay_amount for tokens, pay_amount in zip(self.tokens, to_pay)]
        return to_pay

    def pay_token(self, color: int):
        if self.tokens[color] == 0:
            raise ValueError("can't pay more, we have 0 tokens")
        self.tokens[color] -= 1

    def buy_card(self, card):
        """
        Note: change the __ge__ to a meaningfully named function call
        :param card:
        :return:
        """
        if (cmp := self.can_buy(card))[0]:
            self.cards.append(card)
            paid = self.pay_tokens(cmp, card)
            return True, paid
        return False, [0] * 6


class Game:
    def __init__(self, player_count: int):
        if not (1 < player_count < 5):
            raise ValueError("cant start game with improper number of players")
        self.player_count = player_count
        self.l1_deck = []
        self.l2_deck = []
        self.l3_deck = []
        self.nobles = []
        self.players = []
        self.tokens = []
        self.open_cards = []

    @staticmethod
    def load_cards(file: str = "cards.txt"):
        all_cards = []
        with open(file, "r") as card_db:
            for line in card_db:
                if not re.match(r"#", line):
                    card_entry = ast.literal_eval(line)
                    all_cards.append(card_entry)
        return all_cards

    @staticmethod
    def dek_tiers(_cards):
        return [_cards[:40], _cards[40:70], _cards[70:90], _cards[90:]]

    @staticmethod
    def shuffle_dek(_dek):
        _d = _dek
        for i in range(len(_d) * 7):
            j = randint(0, len(_d) - 1)
            k = randint(0, len(_d) - 1)
            if k != j:
                _d[j], _d[k] = _d[k], _d[j]
        return _d

    @staticmethod
    def shuffle(_decks):
        return [Game.shuffle_dek(_d) for _d in _decks]

    def setup_tokens(self):
        if self.player_count > 2:
            if self.player_count == 4:
                self.tokens = [7] * 5 + [5]
                return
            self.tokens = [5] * 5 + [5]
            return
        self.tokens = [4] * 5 + [5]

    def setup_cards(self):
        kards = Game.dek_tiers(Game.load_cards())
        self.l1_deck = [Card(c) for c in kards[0]]
        self.l2_deck = [Card(c) for c in kards[1]]
        self.l3_deck = [Card(c) for c in kards[2]]
        self.nobles = [Card(c) for c in kards[3]]
        self.open_cards = [
            [self.l1_deck.pop() for _ in range(4)],
            [self.l2_deck.pop() for _ in range(4)],
            [self.l3_deck.pop() for _ in range(4)],
            [self.nobles.pop() for _ in range(self.player_count + 1)],
        ]

    def setup_players(self):
        self.players = [Player(p_id=i) for i in range(self.player_count)]

    def full_setup(self):
        self.setup_tokens()
        self.setup_cards()
        self.setup_players()

    def give_token(self, color: int, p_id: int):
        if not 0 <= color <= 5:
            raise ValueError('color does not exist')
        if self.tokens[color] > 0:
            self.tokens[color] -= 1
            self.players[p_id].get_token(color)
            return
        raise ValueError("can't give tokens of a color when there's none")

    def take_token(self, color: int, p_id: int):
        if not 0 <= color <= 5:
            raise ValueError('color does not exist')
        if self.players[p_id].tokens[color] > 0:
            self.tokens[color] += 1
            self.players[p_id].pay_token(color)
            return
        raise ValueError("can't take tokens when player has none")

    def player_draw_3(self, colors: list, p_id: int):
        for color in colors:
            self.give_token(color, p_id=p_id)

    def player_draw_2_same(self, color: int, p_id: int):
        if self.tokens[color] > 2:
            self.give_token(color, p_id)
            self.give_token(color, p_id)
            return
        raise ValueError("given color isn't available to be chosen in that option")

    def player_buys(self, desired_card: Card, p_id: int):
        for row in self.open_cards:
            for card in row:
                if desired_card is card:
                    bought, paid = self.players[p_id].buy_card(desired_card)
                    for color, tokens in paid:
                        self.tokens[color] += tokens
        raise ValueError("desired card couldn't be found in the cards present in open")


if __name__ == '__main__':
    cards = Game.load_cards()
    # pprint(cards)
    # print(cards[3], len(cards))
    for dek_t in (decks := Game.dek_tiers(cards)):
        # pprint(dek_t)
        print(len(dek_t))
    decks = Game.shuffle(decks)
    # pprint(decks)
    print(cards[0])
    new_card = Card(format_list=cards[0])
    print(new_card)
    new_card.print_short()
    print(cards[57])
    new_card2 = Card(format_list=cards[57])
    print(new_card2)
    new_card2.print_short()

    player1 = Player(0)
    player1.tokens[1] = 2
    player1.tokens[0] = 1
    player1.tokens[3] = 3
    player1.cards = [new_card, new_card2]
    print(player1.card_power)
    print(player1.card_power)
    print(player1.buying_power)
    print(player1.buying_power)
    print(player1.buying_power)
    print(player1.card_power)
    print(player1.cards)
