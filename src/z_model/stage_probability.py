from numpy import array
from .transition_matrix import TransitionMatrix


class StageProbability:
    def __init__(self, x: array):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, t):
        return self.x[t]

    @classmethod
    def from_transition_matrix(cls, transition_matrix: TransitionMatrix, origination_rating: int, current_rating: int, stage_mapping: array):
        cp = transition_matrix.get_cumulative(0, len(transition_matrix), return_list=True)[:, current_rating]
        cp = array([[cp[t, stage_mapping[origination_rating][stage]].sum() for stage in range(4)] for t in range(len(cp))])
        return cls(cp)
