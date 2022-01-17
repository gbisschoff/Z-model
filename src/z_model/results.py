from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from pandas import DataFrame
from numpy import sum
from .file_reader import guess_extension

class Results:
    '''
    Z-Model Results class

    The :class:`Executor` resturns a :class:`Results` object that contains the detailed ECL results and itermediate
    parameters at an account level. The :class:`Results` object also has the ability to summarise the results and
    parameters. Finally, it is possible to save all three reports into a compressed Zip archive for storage and use
    in other programs.

    '''
    def __init__(self, data: DataFrame):
        self.data = data

    def summarise(self, by=['segment_id', 'forecast_reporting_date', 'scenario']):
        '''
        Summarise the ECL results.

        :param by: a list of columns to summarise by. (Default: ``['segment_id', 'scenario', 'forecast_reporting_date']``)

        '''
        df = self.data[[*by, 'outstanding_balance', 'EAD(t)', 'P(S=1)', 'P(S=2)', 'P(S=3)', 'P(S=WO)', 'STAGE1(t)', 'STAGE2(t)', 'STAGE3(t)']].copy()

        df['Exposure(t)_1'] = df['outstanding_balance'] * df['EAD(t)'] * df['P(S=1)']
        df['Exposure(t)_2'] = df['outstanding_balance'] * df['EAD(t)'] * df['P(S=2)']
        df['Exposure(t)_3'] = df['outstanding_balance'] * df['EAD(t)'] * df['P(S=3)']
        df['Exposure(t)_wo'] = df['outstanding_balance'] * df['EAD(t)'] * df['P(S=WO)']

        df['ECL(t)_1'] = df['Exposure(t)_1'] * df['STAGE1(t)']
        df['ECL(t)_2'] = df['Exposure(t)_2'] * df['STAGE2(t)']
        df['ECL(t)_3'] = df['Exposure(t)_3'] * df['STAGE3(t)']
        df['ECL(t)_wo'] = df['Exposure(t)_wo']

        rs = (
            df
            .groupby(by=by)
            .aggregate(
                n_1=('P(S=1)', sum),
                n_2=('P(S=2)', sum),
                n_3=('P(S=3)', sum),
                n_wo=('P(S=WO)', sum),
                exposure_1=('Exposure(t)_1', sum),
                exposure_2=('Exposure(t)_2', sum),
                exposure_3=('Exposure(t)_3', sum),
                exposure_wo=('Exposure(t)_wo', sum),
                ecl_1=('ECL(t)_1', sum),
                ecl_2=('ECL(t)_2', sum),
                ecl_3=('ECL(t)_3', sum),
                ecl_wo=('ECL(t)_wo', sum),
            )
            .reset_index()
            .melt(id_vars=by)
        )

        var_split = rs['variable'].str.split('_', n=1, expand=True)
        rs['variable'] = var_split[0]
        rs['stage'] = var_split[1]

        rs = rs.pivot(index=[*by, 'stage'], columns='variable', values='value').reset_index()
        rs['cr'] = rs['ecl'] / rs['exposure']

        rs.rename(columns={'n': '#', 'exposure': 'Exposure(t)', 'ecl': 'ECL(t)', 'cr': 'CR(t)'}, inplace=True)
        return rs[[*by, 'stage', '#', 'Exposure(t)', 'ECL(t)', 'CR(t)']]

    def parameters(self, by=['segment_id', 'forecast_reporting_date', 'scenario']):
        '''
        Summarise the parameters.

        :param by: a list of columns to summarise by. (Default: ``['segment_id', 'scenario', 'forecast_reporting_date']``)

        '''
        df = self.data[[*by, 'P(S=1)', 'P(S=2)', 'P(S=3)', 'Exposure(t)', '12mPD(t)', 'LGD(t)']].copy()
        df['N'] = (df['P(S=1)'] + df['P(S=2)'] + df['P(S=3)'])
        df['EPD'] = df['Exposure(t)'] * df['12mPD(t)']
        df['ELGD'] = df['Exposure(t)'] * df['LGD(t)']

        rs = (
            df
            .groupby(by=by)
            .aggregate(
                n=('N', sum),
                exposure=('Exposure(t)', sum),
                epd=('EPD', sum),
                elgd=('ELGD', sum)
            )
            .reset_index()
        )
        rs['epd'] = rs['epd'] / rs['exposure']
        rs['elgd'] = rs['elgd'] / rs['exposure']

        rs.rename(columns={'n': '#', 'exposure': 'Exposure(t)', 'epd': '12mPD(t)', 'elgd': 'LGD(t)'}, inplace=True)
        return rs[[*by, '#', 'Exposure(t)', '12mPD(t)', 'LGD(t)']]

    def save(self, url: Path):
        '''
        Save the results and reports to a zip archive.

        :param url: the path to a Zip archive.

        '''
        if guess_extension(url) != '.zip':
            raise ValueError(f'The file path {url} is not a .zip file.')

        with ZipFile(url, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
            zf.writestr("detailed-result.csv", self.data.to_csv(index=False))
            zf.writestr("summary.csv", self.summarise().to_csv(index=False))
            zf.writestr("parameters.csv", self.parameters().to_csv(index=False))
