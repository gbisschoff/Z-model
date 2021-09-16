from pandas import read_excel
from numpy import array,  where
from pathlib import Path

class StageMap:
    def __init__(self, x):
        self.x = x

    def __getitem__(self, item):
        return self.x[item]

    def keys(self):
        return self.x.keys()

    def items(self):
        return self.x.items()

    def values(self):
        return self.x.values()

    @classmethod
    def from_dataframe(cls, df):
        return cls({
            r: tuple(
                [i for i, c in enumerate(df.loc[r] == s) if c]
                for s in (1, 2, 3, 4)
            )
            for r in df.index.values
        })

    @classmethod
    def from_file(cls, url: Path, sheet_name = 'STAGE_MAP'):
        stage_map = read_excel(
            io=url,
            sheet_name=sheet_name,
            dtype={'origination/current': str},
            index_col='origination/current',
            engine='openpyxl'
        )
        return cls.from_dataframe(stage_map)
