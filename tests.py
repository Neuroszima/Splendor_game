import unittest
from random import choice, randint, shuffle
from re import match, findall, search
from ast import literal_eval
from copy import deepcopy
from os import remove
from pprint import pprint

from main import Card, Player, Game


class CardTest(unittest.TestCase):
    def setUp(self):
        self.all_cards = []
        with open("cards.txt", "r") as card_db:
            for line in card_db:
                if not match(r"#", line):
                    card_entry = literal_eval(line)
                    self.all_cards.append(card_entry)

    def test_init(self):
        color_codes = ['r', 'd', 'o', 'e', 's', 'x']
        wrong_color = chr(randint(35, 98))
        rand_card = choice(self.all_cards)
        rand_cost = [randint(0, 2)] * 5
        improper_cost = [randint(0, 2)] * randint(1, 3)
        rand_value = randint(0, 5)
        rand_level = randint(1, 3)
        try:
            card = Card(format_list=rand_card)
            card2 = Card(
                gem=rand_card[0],
                cost=rand_card[4:],
                level=rand_card[3],
                value=rand_card[2]
            )
        except ValueError:
            raise AssertionError("card couldn't be instantiated successfully, "
                                 "while it should with %s" % str(rand_card))
        self.assertRaises(ValueError, Card, format_list=None, gem='b',
                          cost=rand_cost, value=rand_value, level=rand_level)
        self.assertRaises(ValueError, Card, format_list=None, gem=choice(color_codes),
                          cost=improper_cost, value=rand_value, level=rand_level)
        self.assertRaises(ValueError, Card, format_list=[randint(0, 2)]*3)
        self.assertRaises(ValueError, Card, format_list=[randint(0, 2)]*9)
        rand_card2 = deepcopy(rand_card)
        rand_card3 = deepcopy(rand_card)
        rand_card2[randint(1, 4)] = chr(randint(35, 98))
        rand_card3[-randint(1, 4)] = chr(randint(35, 98))
        self.assertRaises(ValueError, Card, format_list=rand_card2)
        self.assertRaises(ValueError, Card, format_list=rand_card3)

    def test_can_be_bought(self):
        card = Card(choice(self.all_cards))
        card2 = Card(choice(self.all_cards))
        # cls_list = [int, tuple, list]
        class_list = [randint(0, 182893), tuple([randint(0, 124)]*randint(0, 7)), [2]*randint(0, 5)]
        player = Player(1)
        try:
            card.can_be_bought(player)
        except Exception as e:
            raise AssertionError(
                "method 'can_be_bought' should have been implemented, instead it fails with error: %s" % str(e))
        try:
            card.can_be_bought(card2)
        except Exception as e:
            self.assertIs(e.__class__, NotImplementedError)
        try:
            card.can_be_bought(choice(class_list))
        except Exception as e:
            self.assertIs(e.__class__, ValueError)

    def test_id_property(self):
        chois = choice(self.all_cards)
        card = Card(chois)
        c_id = Card.COLOR_IDS[chois[0]][1]
        self.assertIs(card.color_id.__class__, int)
        self.assertEqual(card.color_id, c_id)

    def test_print(self):
        # language=regexp
        rank_match = r' R([I ]{3}) '
        # language=regexp
        color_match = r'(?:([a-z]{4} )|([a-z]{5}))'
        # language=regexp
        cost_match = r'[0-9] [a-z]{3} ║'
        # language=regexp
        value_match = r'╔[═]{17}╗\n║ (?:([a-z]{4} )|([a-z]{5})) {8}(?P<value>[0-9 ]) {2}║'
        card = Card(choice(self.all_cards))
        s = str(card)
        self.assertEqual(len(s.split('\n')), 10)
        self.assertIsNotNone(search(rank_match, s))
        self.assertIsNotNone(search(color_match, s))
        self.assertIsNotNone(search(value_match, s)['value'])
        self.assertIsNotNone(costs := findall(cost_match, s))
        if card.value > 0:
            self.assertGreater(int(search(value_match, s)['value']), 0)
        else:
            self.assertIs(search(value_match, s)['value'], " ")
        self.assertEqual(len(costs), 5)


class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.all_cards = []
        with open("cards.txt", "r") as card_db:
            for line in card_db:
                if not match(r"#", line):
                    card_entry = literal_eval(line)
                    self.all_cards.append(card_entry)
        self.chosen_cards = [Card(choice(self.all_cards[:90])) for _ in range(randint(1, 20))]
        self.pid = randint(0, 3627)
        self.player_instance = Player(p_id=self.pid)
        self.player_instance.cards = self.chosen_cards

    def card_power_function(self, cards):
        rubies, diamonds, onyxes, emeralds, saphires, wildcards = [0] * 6
        for card in cards:
            if card.gem == "o":
                onyxes += 1
            elif card.gem == "r":
                rubies += 1
            elif card.gem == "e":
                emeralds += 1
            elif card.gem == "d":
                diamonds += 1
            elif card.gem == "s":
                saphires += 1
        return [rubies, diamonds, onyxes, emeralds, saphires, wildcards]

    def power_to_cost_difference(self, test_card, power):
        IDS = test_card.COLOR_IDS
        rubies_missing = power[IDS['r'][1]] - test_card.cost[IDS['r'][1]]
        diamonds_missing = power[IDS['d'][1]] - test_card.cost[IDS['d'][1]]
        onyxes_missing = power[IDS['o'][1]] - test_card.cost[IDS['o'][1]]
        emeralds_missing = power[IDS['e'][1]] - test_card.cost[IDS['e'][1]]
        sapphires_missing = power[IDS['s'][1]] - test_card.cost[IDS['s'][1]]
        return [rubies_missing, diamonds_missing, onyxes_missing, emeralds_missing, sapphires_missing]

    def test_init(self):
        rando_argument = [
            chr(randint(32, 97)),
            [randint(0, 2)]*randint(0, 5),
            tuple([randint(0, 2)]*randint(0, 5))
        ]
        player = Player(self.pid)
        self.assertEqual(player.tokens, [0]*6)
        self.assertEqual(player.id, self.pid)
        self.assertEqual(player.cards, [])
        self.assertRaises(ValueError, Player, p_id=choice(rando_argument))

    def test_card_power(self):
        total_card_power = self.card_power_function(self.chosen_cards)
        for player_p, card_p in zip(self.player_instance.card_power, total_card_power):
            self.assertEqual(player_p, card_p)

    def test_buying_power(self):
        total_card_power = self.card_power_function(self.chosen_cards)
        self.player_instance.tokens = [randint(0, 4) for _ in range(6)]
        total_buying_power = [c_p + tokens for c_p, tokens in zip(
            total_card_power, self.player_instance.tokens
        )]
        for player_p, tot_p in zip(self.player_instance.buying_power, total_buying_power):
            self.assertEqual(player_p, tot_p)
        # following is the result of me passing original reference to the calculations resulting in
        # overwriting original values
        self.assertIsNot(self.player_instance.tokens, self.player_instance.buying_power)

    def test_greater_than(self):
        cp = self.card_power_function(self.chosen_cards)
        self.player_instance.tokens = [randint(0, 4) for _ in range(6)]
        bp = [c_p + t for c_p, t in zip(cp, self.player_instance.tokens)]
        test_card = Card(choice(self.all_cards))
        # calculating value of the missing tokens for each of the token's colors individually
        difference = self.power_to_cost_difference(test_card=test_card, power=bp)
        # getting the idea if we still can buy the card when wildcards are in possession
        debt = 0
        for diff in difference:
            debt -= diff if diff < 0 else 0
        buying = True if bp[5] >= debt else False
        # real test
        comp = self.player_instance.can_buy(test_card)
        self.assertEqual(buying, comp[0])
        self.assertEqual(debt, comp[1])

    def test_get_token(self):
        c_codes = Card.COLOR_CODES
        IDS = Card.COLOR_IDS
        ch_c = choice(c_codes)
        self.player_instance.get_token(IDS[ch_c][1])
        self.assertEqual(1, self.player_instance.tokens[IDS[ch_c][1]])

    def test_pay_token(self):
        c_codes = Card.COLOR_CODES
        IDS = Card.COLOR_IDS
        ch_c = choice(c_codes)
        self.assertRaises(ValueError, self.player_instance.pay_token, color=IDS[ch_c][1])
        self.assertEqual(0, self.player_instance.tokens[IDS[ch_c][1]])
        self.player_instance.get_token(IDS[ch_c][1])
        self.player_instance.get_token(IDS[ch_c][1])
        self.assertEqual(2, self.player_instance.tokens[IDS[ch_c][1]])
        self.player_instance.pay_token(IDS[ch_c][1])
        self.assertEqual(1, self.player_instance.tokens[IDS[ch_c][1]])

    def test_pay_tokens(self):
        # we have to first generate a card that we can always buy
        original_tokens = [randint(1, 3) for _ in range(6)]
        self.player_instance.tokens = original_tokens
        card = Card(choice(self.all_cards))
        while not (cmp := self.player_instance.can_buy(card))[0]:
            card = Card(choice(self.all_cards))

        # calculating what needs to be paid with actual tokens, subtracting values of cards
        # that generate value
        card_difference = self.power_to_cost_difference(card, self.player_instance.card_power)
        # highlighting all the terms that MATTER with respect to actual costs of the card,
        # else they become nullified, meaning we don't have to spend tokens for the cost that doesn't exist
        to_pay = [-d if d < 0 and cc != 0 else 0 for d, cc in zip(card_difference, card.cost)]
        # calculating negative terms - if we miss some tokens from excessive costs that we can't pay normally,
        # we still can use wildcards/gold to pay them
        missing_tokens = [player_t - pay_color if pay_color > player_t else 0
                          for player_t, pay_color in zip(original_tokens, to_pay)]
        debt = 0
        for token_debt in missing_tokens:
            if token_debt < 0:
                debt -= token_debt
        # # nullifying negative terms that were used in previous step, and adding the 'wildcards' to the list
        to_pay = [cost if cost<tokens else tokens for cost, tokens in zip(to_pay, original_tokens)] + [debt]
        original_tokens = [o - tp for o, tp in zip(original_tokens, to_pay)]
        tokens_paid = self.player_instance.pay_tokens(cmp, card)
        self.assertEqual(to_pay, tokens_paid)
        self.assertEqual(original_tokens, self.player_instance.tokens)

    def test_buy_card(self):
        """
        this test checks entire buy procedure
        we dynamically add 'marker' to check whether the card was added, since there could be the same card
        already present in players 'library' due to test suite setUp procedure
        :return:
        """
        card = Card(choice(self.all_cards))
        card.marker = 1
        original_tokens = [randint(0, 2) for _ in range(6)]
        self.player_instance.tokens = original_tokens
        cmp = self.player_instance.can_buy(card)
        self.player_instance.buy_card(card)
        # search the card in players library
        for index, c in enumerate(self.player_instance.cards):
            if hasattr(c, 'marker'):
                if cmp[0]:
                    print('BUY - OK')
                    break
                else:
                    raise AssertionError("found bought card when player should have had no funds "
                                         "to buy it in the first place")
            if index == len(self.player_instance.cards)-1:
                if cmp[0]:
                    self.assertFalse(self.player_instance.tokens == original_tokens,
                                     "tokens were not subtracted correctly")
                    raise AssertionError("couldn't find marked card even though it should be bought")
                else:
                    print("DID NOT BUY - OK")


class GameTest(unittest.TestCase):
    def setUp(self):
        players = [2, 3, 4]
        self.num_of_players = choice(players)
        self.game_instance = Game(self.num_of_players)
        self.game_instance.setup_tokens()
        self.game_instance.setup_cards()
        self.game_instance.setup_players()
        # language=regexp
        self.l1_regexp = r'\[\"[rdoes]\", 1, [0-1], (?P<level>[1])(?:, [0-4]){5}]'
        # language=regexp
        self.l2_regexp = r'\[\"[rdoes]\", 1, [1-3], (?P<level>[2])(?:, [0-6]){5}]'
        # language=regexp
        self.l3_regexp = r'\[\"[rdoes]\", 1, [3-5], (?P<level>[3])(?:, [0-7]){5}]'
        # language=regexp
        self.aristocrates_regexp = r'\[\"x\", 0, 3, (?P<level>[0])(?:, [0-4]){5}]'

    def test_init(self):
        improper_players = randint(-10707, 1)
        improper_players2 = randint(5, 123097)
        self.assertRaises(ValueError, Game, player_count=improper_players)
        self.assertRaises(ValueError, Game, player_count=improper_players2)
        try:
            Game(player_count=randint(2, 4))
        except ValueError as e:
            raise AssertionError(f"initializing game raised {e} when passed proper values to constructor")

    def test_setup_tokens(self):
        # there can only be 5 gold tokens, no matter the number of players
        wildcard_tokens = 5
        # other number of tokens depend on the number of players
        other_tokens = 0
        if self.num_of_players == 2:
            other_tokens = 4
        elif self.num_of_players == 3:
            other_tokens = 5
        elif self.num_of_players == 4:
            other_tokens = 7
        tokens_total = [other_tokens, other_tokens, other_tokens, other_tokens, other_tokens, wildcard_tokens]
        # print(self.game_instance.tokens)
        # print(self.num_of_players)
        # print(tokens_total)
        self.assertEqual(tokens_total, self.game_instance.tokens)

    def test_setup_players(self):
        player_ids = [_ for _ in range(self.num_of_players)]
        self.assertEqual(player_ids, [player.id for player in self.game_instance.players])

    def test_give_token(self):
        player_copy: Player
        color = choice(Card.COLOR_CODES)
        color_id = Card.COLOR_IDS[color][1]
        player_id = choice([i for i in range(self.num_of_players)])
        player_copy = deepcopy(self.game_instance.players[player_id])
        tokens_state = deepcopy(self.game_instance.tokens)
        self.assertEqual(player_id, player_copy.id)
        player_copy.tokens[color_id] += 1
        tokens_state[color_id] -= 1
        self.game_instance.give_token(color_id, player_id)
        self.assertEqual(player_copy.tokens, self.game_instance.players[player_id].tokens)
        self.assertEqual(tokens_state, self.game_instance.tokens)
        test_game = Game(randint(2, 4))
        # can't generate tokens out of thin air
        test_game.tokens = [0 for _ in range(6)]
        self.assertRaises(ValueError, test_game.give_token, color=color_id, p_id=player_id)

    def test_card_reading(self):
        testgame = Game(randint(2, 4))
        file = open('cards.txt', 'r')
        lines = [file.readline() for _ in range(randint(1, 70))]
        # comment lines in the file start with "#"
        card_lines = [l for l in lines if "#" not in l]
        file.close()
        test_file = 'test.txt'
        with open(test_file, 'x') as tf:
            tf.writelines(lines)
        cards = testgame.load_cards(test_file)
        remove(test_file)
        self.assertEqual(len(card_lines), len(cards))

    def test_deck_separation(self):
        # now we load all of the cards, but we split accordingly by types
        from ast import literal_eval
        file = open('cards.txt', 'r')
        lines = []
        for li in file:
            lines.append(li)
        file.close()
        dek_1 = [literal_eval(lin) for lin in lines if match(self.l1_regexp, lin)]
        dek_2 = [literal_eval(lin) for lin in lines if match(self.l2_regexp, lin)]
        dek_3 = [literal_eval(lin) for lin in lines if match(self.l3_regexp, lin)]
        dek_aristocrates = [literal_eval(lin) for lin in lines if match(self.aristocrates_regexp, lin)]
        # comment lines in the file start with "#"
        cards = self.game_instance.load_cards()
        d1, d2, d3, da = self.game_instance.dek_tiers(cards)
        self.assertEqual(dek_1, d1)
        self.assertEqual(dek_2, d2)
        self.assertEqual(dek_3, d3)
        self.assertEqual(dek_aristocrates, da)

    def test_cards_out(self):
        cards = self.game_instance.load_cards()
        d1, d2, d3, da = self.game_instance.dek_tiers(cards)
        for x in [d1, d2, d3, da]:
            shuffle(x)
        d1_reveal = [Card(d1.pop()) for _ in range(4)]
        d2_reveal = [Card(d2.pop()) for _ in range(4)]
        d3_reveal = [Card(d3.pop()) for _ in range(4)]
        da_reveal = [Card(da.pop()) for _ in range(self.num_of_players+1)]
        self.game_instance.setup_cards()
        for index, out in enumerate([d1_reveal, d2_reveal, d3_reveal, da_reveal]):
            self.assertEqual(len(out), len(self.game_instance.open_cards[index]))
            self.assertEqual([c.level for c in out],
                             [ci.level for ci in self.game_instance.open_cards[index]])

    def test_full_setup(self):
        test_game = Game(player_num:=randint(2, 4))
        test_game.full_setup()
        self.assertEqual(player_num, len(test_game.players))
        self.assertEqual(6, len(test_game.tokens))
        for i in range(3):
            self.assertEqual(4, len(test_game.open_cards[i]))
        self.assertEqual(player_num+1, len(test_game.open_cards[-1]))

    def test_player_draw_2(self):
        pass


class CrossClassTests(unittest.TestCase):


    def test_give_take_token(self):
        """
        making sure number of tokens stay the same no matter what we attempt to do with giving/taking
        tokens from the players, raising ValueErrors when needed
        :return:
        """
        for playernum, tokens in zip([2, 3, 4], [4, 5, 7]):
            test_game = Game(playernum)
            test_game.setup_players()
            test_game.tokens = [tokens] * 5 + [5]
            test_game.players[0]: Player
            for c_co in Card.COLOR_CODES[:5]:
                c_id = Card.COLOR_IDS[c_co][1]
                for _ in range(tokens+3):
                    try:
                        test_game.give_token(c_id, 0)
                    except ValueError:
                        pass
                    self.assertEqual(tokens,
                                     test_game.tokens[c_id]+test_game.players[0].tokens[c_id])
                    self.assertGreaterEqual(test_game.tokens[c_id], 0)
                    self.assertGreaterEqual(test_game.players[0].tokens[c_id], 0)
                for _ in range(tokens+3):
                    try:
                        test_game.take_token(c_id, 0)
                    except ValueError:
                        pass
                    self.assertEqual(tokens,
                                     test_game.tokens[c_id]+test_game.players[0].tokens[c_id])
                    self.assertGreaterEqual(test_game.tokens[c_id], 0)
                    self.assertGreaterEqual(test_game.players[0].tokens[c_id], 0)


if __name__ == '__main__':
    unittest.main()
