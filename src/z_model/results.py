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

    def reporting_rate_results(self):
        '''
        Return only the IFRS9 Reporting date results
        '''
        rs = self.data[
            (self.data['account_type']=='Actual')
            & (self.data['T']==0)
        ].copy()
        rs.drop(columns=['T', 'forecast_reporting_date', 'PD(t)', 'DF(t)', 'Marginal CR(t)', 'Write-off(t)'], inplace=True)
        return rs

    def summarise(self, by=('account_type', 'segment_id', 'forecast_reporting_date', 'scenario'), *args, **kwargs):
        '''
        Summarise the ECL results.

        :param by: a list of columns to summarise by. (Default: ``['account_type', 'segment_id', 'scenario', 'forecast_reporting_date']``)
        :param args, kwargs: Not currently used

        '''
        df = self.data[[*by, 'EAD(t)', 'P(S=1)', 'P(S=2)', 'P(S=3)', 'P(S=WO)', 'STAGE1(t)', 'STAGE2(t)', 'STAGE3(t)']].copy()

        # Calculate the stage conditional exposure
        df['Exposure(t)_1'] = df['EAD(t)'] * df['P(S=1)']
        df['Exposure(t)_2'] = df['EAD(t)'] * df['P(S=2)']
        df['Exposure(t)_3'] = df['EAD(t)'] * df['P(S=3)']
        df['Exposure(t)_wo'] = df['EAD(t)'] * df['P(S=WO)']

        # Calculate the stage conditional ECL (note that WO=Exposure)
        df['ECL(t)_1'] = df['STAGE1(t)'] * df['P(S=1)']
        df['ECL(t)_2'] = df['STAGE2(t)'] * df['P(S=2)']
        df['ECL(t)_3'] = df['STAGE3(t)'] * df['P(S=3)']
        df['ECL(t)_wo'] = df['Exposure(t)_wo']

        # Summarise the data to calculate the expected number of accounts, expected exposure an expected ECL in each stage
        rs = (
            df
            .groupby(by=list(by))
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
            .melt(id_vars=list(by))
        )

        var_split = rs['variable'].str.split('_', n=1, expand=True)
        rs['variable'] = var_split[0]
        rs['stage'] = var_split[1]

        rs = rs.pivot(index=[*by, 'stage'], columns='variable', values='value').reset_index()
        rs['cr'] = rs['ecl'] / rs['exposure']

        rs.rename(columns={'n': '#', 'exposure': 'Exposure(t)', 'ecl': 'ECL(t)', 'cr': 'CR(t)'}, inplace=True)
        return rs[[*by, 'stage', '#', 'Exposure(t)', 'ECL(t)', 'CR(t)']]

    def parameters(self, by=('segment_id', 'forecast_reporting_date', 'scenario'), *args, **kwargs):
        '''
        Summarise the parameters.

        :param by: a list of columns to summarise by. (Default: ``['segment_id', 'scenario', 'forecast_reporting_date']``)
        :param args, kwargs: Not currently used

        '''
        df = self.data[[*by, 'P(S=1)', 'P(S=2)', 'P(S=3)', 'Exposure(t)', '12mPD(t)', 'LGD(t)']].copy()
        df['N'] = (df['P(S=1)'] + df['P(S=2)'] + df['P(S=3)']) # Calculate the expected number of observations
        df['EPD'] = df['Exposure(t)'] * df['12mPD(t)'] # Calculate the exposure weighted PD
        df['ELGD'] = df['Exposure(t)'] * df['LGD(t)'] # Calculate the exposure weighted LGD

        rs = (
            df
            .groupby(by=list(by))
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

    def save(self, url: Path, *args, **kwargs):
        '''
        Save the results and reports to a zip archive.

        :param url: the path to a Zip archive.
        :param args: arguments passes to summarise & parameters
        :param kwargs: arguments passes to summarise & parameters

        '''
        if guess_extension(url) != '.zip':
            raise ValueError(f'The file path {url} is not a .zip file.')

        with ZipFile(url, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
            self.data.to_csv(zf.open('detailed-results.csv', 'w'), index=False)
            self.reporting_rate_results().to_csv(zf.open('reporting-date-results.csv', 'w'), index=False)
            self.summarise(*args, **kwargs).to_csv(zf.open('summary.csv', 'w'), index=False)
            self.parameters(*args, **kwargs).to_csv(zf.open('parameters.csv', 'w'), index=False)
