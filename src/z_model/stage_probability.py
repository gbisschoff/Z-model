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

    @staticmethod
    def _add_write_off(transition_matrix: TransitionMatrix, time_to_sale: int, probability_of_cure: float, frequency:int = 1):
        """
        Add write-off state to the matrix
        """
        x = stack(transition_matrix.values)
        n, rows, columns = x.shape

        s = (1 - 1 / time_to_sale) ** frequency
        c = (1 - s) * probability_of_cure
        wo = (1 - s) * (1 - probability_of_cure)

        x_new = zeros((n, rows + 1, columns + 1), dtype=x.dtype)
        x_new[:, :rows, :columns] = x
        x_new[:, -1, -1] = 1
        x_new[:, rows-1, columns - 2] = c
        x_new[:, rows-1, columns - 1] = s
        x_new[:, rows-1, columns] = wo

        return TransitionMatrix(Series(list(x_new), dtype='object', index=transition_matrix.index))

    def get_stage_probabilities(self, idx:Index ,origination_rating: int, current_rating:int):
        n_periods, (n_ratings, _) = self.transition_matrix.shape
        template = zeros(shape=(len(idx) + 1, 4))
        origination_stage_map = self.stage_map[origination_rating]
        cumulative_probabilities = stack(self.transition_matrix.get_cumulative(idx, return_list=True))[:, current_rating, :]
        cumulative_probabilities = insert(cumulative_probabilities, 0, zeros(n_ratings), axis=0)
        cumulative_probabilities[0, current_rating] = 1
        for stage in range(4):
            template[:, stage] = sum(cumulative_probabilities[:, origination_stage_map[stage]], axis=1)

        stage_probabilities = DataFrame(template, columns=[1, 2, 3, 'wo'])[:len(idx)]
        stage_probabilities.set_index(idx, inplace=True)
        return stage_probabilities

    @classmethod
    def from_transition_matrix(cls, transition_matrix: TransitionMatrix, time_to_sale: int, probability_of_cure: float, stage_map: StageMap, frequency: int = 1, time_in_watchlist: int = 1):
        return cls(cls._add_write_off(transition_matrix, time_to_sale, probability_of_cure, frequency), stage_map, time_in_watchlist)

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
