from otree.api import *
import random

doc = """
Monopoly posted price setting with flat discrete demand.
Are consumers able to maintain cooperation under monopoly pricing?
"""

class C(BaseConstants):
    NAME_IN_URL = 'boycott'
    PLAYERS_PER_GROUP = 6  # 1 Monopolist + 5 Consumers
    NUM_ROUNDS = 10
    base_payment = cu(1)
    chat_round_start = 6  # Communication starts in Round 6


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    price = models.CurrencyField(min=0, max=150, label="Set the price")

    def set_payoffs(self):
        consumers = [p for p in self.get_players() if p.role() == 'Consumer']
        units_sold = 0

        for c in consumers:
            if c.buy_choice == 'buy' and c.endowment >= self.price:
                c.payoff = c.endowment - self.price
                units_sold += 1
            else:
                c.payoff = c.endowment

        monopolist = self.get_player_by_role('Monopolist')
        monopolist.payoff = units_sold * self.price

    def get_consumer_values(self):
        return [(p.id_in_group, p.endowment) for p in self.get_players() if p.role() == 'Consumer']


class Player(BasePlayer):
    endowment = models.CurrencyField()
    buy_choice = models.StringField(
        choices=[('buy', 'Buy'), ('no_buy', 'Do Not Buy')],
        label="Do you want to buy the monopolist's product?",
        widget=widgets.RadioSelect,
        blank=True,
    )
    chat_text = models.LongStringField(blank=True)

    def role(self):
        if self.id_in_group == 1:
            return 'Monopolist'
        else:
            return 'Consumer'

    def set_endowment(self):
        self.endowment = random.choice([142, 144, 146, 148, 150])

    def creating_session(self):
        if self.round_number == 1:
            for p in self.subsession.get_players():
                p.set_endowment()

# PAGES
from ._builtin import Page, WaitPage
from .models import C


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1


class AdditionalInstructions(Page):
    def is_displayed(self):
        return self.round_number == C.chat_round_start

class ShowConsumerValues:
    def vars_for_template(self):
        return {
            'all_values': self.group.get_consumer_values()
        }

class SetPrice(ShowConsumerValues, Page):
    form_model = 'group'
    form_fields = ['price']

    def is_displayed(self):
        return self.player.role() == 'Monopolist'




class WaitForMonopolist(WaitPage):
    pass


class Chat(ShowConsumerValues, Page):
    form_model = 'player'
    form_fields = ['chat_text']

    def is_displayed(self):
        return self.round_number >= C.chat_round_start and self.player.role() == 'Consumer'

    def vars_for_template(self):
        return {
            'all_values': self.group.get_consumer_values()
        }


class ConsumerDecision(ShowConsumerValues, Page):
    form_model = 'player'
    form_fields = ['buy_choice']

    def is_displayed(self):
        return self.player.role() == 'Consumer'




class WaitForConsumers(WaitPage):
    after_all_players_arrive = 'set_payoffs'


class RoundResults(ShowConsumerValues, Page):
    def vars_for_template(self):
        return {
            'all_values': self.group.get_consumer_values(),
            'price': self.group.price,
            'role': self.player.role(),
            'buy_choice': self.player.buy_choice,
            'payoff': self.player.payoff
        }


class SessionResults(ShowConsumerValues, Page):
    def is_displayed(self):
        return self.round_number == C.NUM_ROUNDS


page_sequence = [
    Instructions,
    AdditionalInstructions,
    SetPrice,
    WaitForMonopolist,
    Chat,
    ConsumerDecision,
    WaitForConsumers,
    RoundResults,
    SessionResults
]
