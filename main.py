import re
import ast
from contextlib import suppress
from random import randint
from typing import Union, List, Tuple, Optional


class GameError(Exception):
    pass


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
        # simplifying case
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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if other is not self:
                return [self.gem, self.level, self.value, self.cost] == \
                       [other.gem, other.level, other.value, other.cost]
            else:
                return True
        if other is None:
            return False
        raise NotImplementedError(f"comparison between {other.__class__} and {self.__class__} not implemented")

    @property
    def color_id(self):
        return self.COLOR_IDS[self.gem][1]

    def can_be_bought(self, other):
        """
        for simplicity, invoking counterpart method from 'Player' class
        """
        # guard condition
        if isinstance(other, Card):
            raise NotImplementedError("comparison between cards isn't implemented yet")
        if isinstance(other, Player):
            return other.can_buy(self)
        raise ValueError(f"can't compare object {other.__class__} to Card meaningfully")

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
        self.reserved = (None, None, None,)

    @staticmethod
    def provide_position():
        chosen = False
        while not chosen:
            try:
                row = input("choose row of cards")
                card = input("choose card in given row")
                r = int(row)
                c = int(card)
                chosen = True
                return r, c
            except ValueError as e:
                print("couldn't convert inputs into integer numbers, "
                      "try again and make sure you typed correct data")

    @property
    def buying_power(self):
        # this avoids deepcopy
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

    def check_selection(self, open_cards: List[List[Card]], deck_sizes: List[int], desired_card: tuple):
        if not (desired_card[0] in [0, 1, 2]) or not(desired_card[1] in [0, 1, 2, 3, 4, 5]):
            raise GameError("selection doesn't match any of the available positions")
        if desired_card[1] < 4:
            if open_cards[desired_card[0]][desired_card[1]] is None:
                raise GameError("there is no card at given position")
        if desired_card[1] == 4:
            # check tops of the given row's deck
            if desired_card[0] == 0:
                if deck_sizes[0] == 0:
                    raise GameError("no card in the L1 deck")
            if desired_card[0] == 1:
                if deck_sizes[1] == 0:
                    raise GameError("no card in the L2 deck")
            if desired_card[0] == 2:
                if deck_sizes[2] == 0:
                    raise GameError("no card in the L3 deck")
        if desired_card[1] == 5:
            # check 'slot' in self.reserved
            try:
                if self.reserved[desired_card[0]] is None:
                    raise GameError("no card to choose in this position")
            except IndexError:
                raise GameError("you haven't yet reserved a card")

    def can_buy(self, other: Card) -> Tuple[bool, int]:
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

    def get_token(self, color: int):
        self.tokens[color] += 1

    def pay_tokens(self, debt: Tuple[bool, int], card: Card):
        to_pay = [
                     min(tokens, max(cost - cs, 0)) if cost > 0 else 0
                     for tokens, cs, cost in zip(self.tokens, self.card_power, card.cost)
                  ] + [debt[1]]
        self.tokens = [tokens - pay_amount for tokens, pay_amount in zip(self.tokens, to_pay)]
        return to_pay

    def pay_token(self, color: int):
        if self.tokens[color] == 0:
            raise GameError("can't pay more, we have 0 tokens")
        self.tokens[color] -= 1

    def buy_card(self, card: Card):
        if (cmp := self.can_buy(card))[0]:
            self.cards.append(card)
            paid = self.pay_tokens(cmp, card)
            return True, paid
        return False, [0] * 6

    def buy_reserve(self, desired_card: int):
        try:
            if (cmp := self.can_buy(card := self.reserved[desired_card]))[0]:
                self.cards.append(self.reserved[desired_card])
                r = [c for index, c in enumerate(self.reserved) if index != desired_card] + [None]
                self.reserved = tuple(r)
                paid = self.pay_tokens(cmp, card)
                return True, paid
        except IndexError:
            raise GameError("No card in this reserve slot! Choose another card")
        return False, [0] * 6

    def reserve(self, card: Card):
        if None in self.reserved:
            r = [card] + list(self.reserved[:2])
            self.reserved = tuple(r)
        else:
            raise GameError("Can't reserve more than 3 cards, buy the reserved card out to free space")
        # self.reserved += [card]

    def select_card(self, open_cards: List[List[Card]], deck_sizes):
        desired_card = self.provide_position()
        # function call serving as guard statement
        self.check_selection(open_cards, deck_sizes, desired_card)
        return desired_card


class Game:
    def __init__(self, player_count: int):
        if not (1 < player_count < 5):
            raise GameError("cant start game with improper number of players")
        self.player_count = player_count
        self.l1_deck: List[Card] = []
        self.l2_deck: List[Card] = []
        self.l3_deck: List[Card] = []
        self.nobles: List[Card] = []
        self.players: List[Player] = []
        self.tokens: List[int] = []
        self.open_cards: List[List[Optional[Card]]] = []

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

    @property
    def deck_sizes(self):
        return [len(self.l1_deck), len(self.l2_deck), len(self.l3_deck)]

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
            raise GameError('color does not exist')
        if self.tokens[color] > 0:
            self.tokens[color] -= 1
            self.players[p_id].get_token(color)
            return
        raise GameError("can't give tokens of a color when there's none")

    def take_token(self, color: int, p_id: int):
        if not 0 <= color <= 5:
            raise GameError('color does not exist')
        if self.players[p_id].tokens[color] > 0:
            self.tokens[color] += 1
            self.players[p_id].pay_token(color)
            return
        raise GameError("can't take tokens when player has none")

    def replace_empty(self):
        for deck, row in enumerate(self.open_cards):
            for index, slot in enumerate(row):
                if not slot:
                    with suppress(IndexError):
                        # it is ok for multiple/one of the decks to run out,
                        # in 4-player game l1 runs out quite often
                        if deck == 0:
                            self.open_cards[deck][index] = self.l1_deck.pop()
                        elif deck == 1:
                            self.open_cards[deck][index] = self.l2_deck.pop()
                        elif deck == 2:
                            self.open_cards[deck][index] = self.l3_deck.pop()

    def player_draw_3(self, colors: Union[list, tuple], p_id: int):
        if 0 < len(colors) < 4:
            for color in colors:
                self.give_token(color, p_id=p_id)
            return
        raise GameError("too many or too little colors chosen")

    def player_draw_2_same(self, color: int, p_id: int):
        if self.tokens[color] > 2:
            self.give_token(color, p_id)
            self.give_token(color, p_id)
            return
        raise GameError("given color isn't available to be chosen in that option")

    def player_select(self, p_id: int):
        self.players[p_id]: Player
        desired_card = self.players[p_id].select_card(self.open_cards, self.deck_sizes)
        # the necessary check were already performed in 'Player' by this point
        if desired_card[1] == 4:
            # reserve-only - selecting top of the corresponding deck
            # since i am using pop to push new cards onto open field, the last element of the
            # card list in a deck is considered it's top
            if desired_card[0] == 0:
                card = self.l1_deck[-1]
            if desired_card[0] == 1:
                card = self.l2_deck[-1]
            if desired_card[0] == 2:
                card = self.l3_deck[-1]
        elif desired_card[1] == 5:
            # buying from reserved cards only
            card = self.players[p_id].reserved[desired_card[0]]
        else:
            card = self.open_cards[desired_card[0]][desired_card[1]]
        return card, desired_card

    def player_buys(self, card: Card, desired_card: tuple, p_id: int):
        # traditional buy
        if desired_card[1] in [0, 1, 2, 3]:
            bought, paid = self.players[p_id].buy_card(card)
            if bought:
                self.open_cards[desired_card[0]][desired_card[1]] = None
        elif desired_card[1] == 4:
            raise GameError("can't buy card from the top of the library directly!")
        # buy from reserve
        elif desired_card[1] == 5:
            bought, paid = self.players[p_id].buy_reserve(desired_card[0])
        try:
            for color, tokens in enumerate(paid):
                self.tokens[color] += tokens
        except UnboundLocalError:
            raise GameError("something went wrong with buying card")

    def player_reserve(self, card: Card, desired_card: tuple, p_id: int):
        if desired_card[1] == 4:
            self.players[p_id].reserve(card)
            if desired_card[0] == 0:
                c = self.l1_deck.pop()
            if desired_card[0] == 1:
                c = self.l2_deck.pop()
            if desired_card[0] == 2:
                c = self.l3_deck.pop()
        else:
            self.players[p_id].reserve(card)
            self.open_cards[desired_card[0]][desired_card[1]] = None
            c = card
        self.give_token(Card.COLOR_IDS['x'][1], p_id)
        return c


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
