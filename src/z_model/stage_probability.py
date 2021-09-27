from numpy import array, zeros, sum, stack, insert
from pandas import notna, Series, Index, DataFrame
from dateutil.relativedelta import relativedelta
from .account import Account
from .transition_matrix import TransitionMatrix
from .stage_map import StageMap

class StageProbability:
    def __init__(self, transition_matrix: TransitionMatrix, stage_map: StageMap, time_in_watchlist: int = 1):
        self.transition_matrix = transition_matrix
        self.stage_map = stage_map
        self.time_in_watchlist = time_in_watchlist

    def get_stage_probabilities(self, idx:Index ,origination_rating: int, current_rating:int):
        n_periods, (n_ratings, _) = self.transition_matrix.shape
        template = zeros(shape=(len(idx), 4))
        origination_stage_map = self.stage_map[origination_rating]
        cumulative_probabilities = stack(self.transition_matrix.get_cumulative(idx, return_list=True))[:, current_rating, :]
        for stage in range(4):
            template[:, stage] = sum(cumulative_probabilities[:, origination_stage_map[stage]], axis=1)

        stage_probabilities = DataFrame(template, columns=[1, 2, 3, 'wo'])[:len(idx)]
        stage_probabilities.set_index(idx, inplace=True)
        return stage_probabilities

    def __getitem__(self, account: Account):
        sp = self.get_stage_probabilities(
            account.remaining_life_index,
            account.origination_rating,
            account.current_rating,
        )
        if notna(account.watchlist):
            sp.iloc[:self.time_in_watchlist] = 0
            sp.iloc[:self.time_in_watchlist, account.watchlist-1] = 1
        return sp
