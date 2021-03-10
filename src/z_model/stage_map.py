from pandas import read_excel
from numpy import array,  where


class StageMap:
    def __init__(self, x):
        self.x = x

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
    def from_file(cls, url, sheet_name = 'STAGE_MAP'):
        stage_map = read_excel(
            io=url,
            sheet_name=sheet_name,
            dtype={'origination/current': str},
            index_col='origination/current'
        )
        return cls.from_dataframe(stage_map)
