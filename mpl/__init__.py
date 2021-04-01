from otree.api import *
# from .config import *
from ._builtin import Page, WaitPage
import random
from random import randrange
from otree.models import subsession, session
# from .models import parse_config

doc = """
Multiple price list task as proposed by Holt/Laury (2002), American Economic Review 92(5).
"""


class Constants(BaseConstants):
    # lottery_a = 50
    # lottery_b_hi = 100
    # lottery_b_lo = 10
    num_choices = 10
    num_rounds = 1
    name_in_url = 'mpl'
    players_per_group = None

# def parse_config(config_file):
#     with open("mpl/configs/" + config_file) as f:
#         rows = list(csv.DictReader(f))
#     rounds = []
#     for row in rows:
#         rounds.append({
#             'lottery_a': int(row['lottery_a']),
#             'lottery_b_hi': int(row['lottery_b_hi']),
#             'lottery_b_lo': int(row['lottery_b_lo']),
#         })
#     return rounds


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
     # if self.round_number == 1:
    n = Constants.num_choices
    for p in subsession.get_players():
        indices = [j for j in range(1, n + 1)]
        probabilities = [
            str(k) + "/" + str(n)
            for k in indices
        ]
        q = [
            str(n - k) + "/" + str(n)
            for k in indices
        ]
        form_fields = ['choice_' + str(k) for k in indices]
        p.participant.vars['mpl_choices'] = list(
            zip(indices, form_fields, probabilities, q))
        # print(p.participant.vars['mpl_choices'])
        p.participant.vars['mpl_index_to_pay'] = random.choice(indices)
        p.participant.vars['mpl_choice_to_pay'] = 'choice_' + \
            str(p.participant.vars['mpl_index_to_pay'])
        p.participant.vars['mpl_choices_made'] = [
            None for j in range(1, n + 1)]


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # add model fields to class player
    for j in range(1, Constants.num_choices + 1):
        locals()['choice_' + str(j)] = models.StringField()
    del j
    random_draw = models.IntegerField()
    choice_to_pay = models.StringField()
    option_to_pay = models.StringField()

    def set_payoffs(self):
        self.random_draw = randrange(
            1, len(self.participant.vars['mpl_choices']))
        self.choice_to_pay = self.participant.vars['mpl_choice_to_pay']

        # elicit whether lottery "A" or "B" was chosen for the respective choice
        self.option_to_pay = getattr(self, self.choice_to_pay)

        if self.option_to_pay == 'A':
            self.payoff = self.session.config['lottery_a']
        else:
            if self.random_draw <= self.participant.vars['mpl_index_to_pay']:
                self.payoff = self.session.config['lottery_b_hi']
            else:
                self.payoff = self.session.config['lottery_b_lo']

        # set payoff as global variable
        self.participant.vars['mpl_payoff'] = self.payoff


class Instructions(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1


class Decision(Page):
    form_model = 'player'
    
    @staticmethod
    def get_form_fields(player: Player):
        form_fields = [list(t) for t in zip(
            *player.participant.vars['mpl_choices'])][1]
        return form_fields

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'lottery_a': c(player.session.config['lottery_a']),
            'lottery_b_lo': c(player.session.config['lottery_b_lo']),
            'lottery_b_hi': c(player.session.config['lottery_b_hi']),
            'choices': player.participant.vars['mpl_choices']
        }

    # set player's payoff
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # unzip indices and form fields from <mpl_choices> list
        form_fields = [list(t) for t in zip(
            *player.participant.vars['mpl_choices'])][1]
        # print("here")
        # print(player.participant.vars['mpl_choices'])
        # print(*player.participant.vars['mpl_choices'])
        indices = [list(t)
                   for t in zip(*player.participant.vars['mpl_choices'])][0]
        # if choices are displayed in tabular format
        for j, choice in zip(indices, form_fields):
            # print(j, choice)
            # print(player.choice_1)
            choice_i = getattr(player, choice)
            player.participant.vars['mpl_choices_made'][j - 1] = choice_i
        player.set_payoffs()


class Results(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        choices = [list(t) for t in zip(*player.participant.vars['mpl_choices'])]
        indices = choices[0]
        # get index, round, and choice to pay
        index_to_pay = player.participant.vars['mpl_index_to_pay']
        round_to_pay = indices.index(index_to_pay) + 1
        choice_to_pay = player.participant.vars['mpl_choices'][round_to_pay - 1]

        return {
            'lottery_a': c(player.session.config['lottery_a']),
            'lottery_b_lo': c(player.session.config['lottery_b_lo']),
            'lottery_b_hi': c(player.session.config['lottery_b_hi']),
            'choice_to_pay':  [choice_to_pay],
            'option_to_pay':  player.option_to_pay,
            'payoff':         player.payoff
        }


class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds


page_sequence = [Instructions, Decision, Results, FinalResults]