'''
File Readers and Writers

Create a common API to read multiple file types

'''
import pandas as pd
from pathlib import Path

__READERS__ = {
        '.csv': pd.read_csv,
        '.csv.gz': pd.read_csv,
        '.xlsx': pd.read_excel,
        '.xlx': pd.read_excel,
        '.json': pd.read_json,
        '.html': pd.read_html,
        '.parquet': pd.read_parquet,
        '.feather': pd.read_feather,
        '.dta': pd.read_stata,
        '.sas7bdat': pd.read_sas,
        '.xpt': pd.read_sas,
        '.sav': pd.read_spss,
        '.zsav': pd.read_spss,
        '.pkl': pd.read_pickle
}

__WRITERS__ = {
        '.csv': 'to_csv',
        '.csv.gz': 'to_csv',
        '.xlsx': 'to_excel',
        '.xlx': 'to_excel',
        '.json': 'to_json',
        '.html': 'to_html',
        '.parquet': 'to_parquet',
        '.feather': 'to_feather',
        '.pkl': 'to_pickle'
}

def guess_extension(url: Path):
    '''
    Guess Extension

    Determine the file extension based on the url.

    :param url: the path to the file.
    '''
    return ''.join(url.suffixes).lower()


def read_file(url: Path, *args, **kwargs):
    '''
    Read File

    Read a file based on the file extension.

    :param url: the path to the file.
    :param args: addtional arguments passed to the reader.
    :param kwargs: additional key word arguments passed to teh reader.

    '''
    return __READERS__.get(guess_extension(url), pd.read_table)(url, *args, **kwargs)


def write_file(df: pd.DataFrame, url: Path, *args, **kwargs):
    '''
    Write File

    Write a file based on the file extension.

    :param df: a pandas dataframe.
    :param url: the path to the file.
    :param args: addtional arguments passed to the writer.
    :param kwargs: additional key word arguments passed to teh writer.

    '''
    getattr(df, __WRITERS__.get(guess_extension(url), 'to_csv'))(url, *args, **kwargs)

