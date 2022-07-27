from pathlib import Path
import PySimpleGUI as sg
from time import sleep
from rsa.pkcs1 import VerificationError
from z_model.forecast import forecast
from z_model.logging import logging, setup_logging
from z_model.__main__ import run, __copyright__, __version__, license, ForecastType
from z_model.exeutor import Methods

setup_logging()
logo = (Path.cwd() / __file__).with_name('data') / 'deloitte.png'
icon = (Path.cwd() / __file__).with_name('data') / 'icon.ico'
license_message = f'{license.information.get("company_name")}, Expiration date: {license.information.get("expiration_date")}'

theme_dict = {
    'BACKGROUND': '#404040',
    'TEXT': '#FFFFFF',
    'INPUT': '#4D4D4D',
    'TEXT_INPUT': '#FFFFFF',
    'SCROLL': '#707070',
    'BUTTON': ('#000000', '#86BC25'),
    'PROGRESS': ('#000000', '#000000'),
    'BORDER': 1,
    'SLIDER_DEPTH': 0,
    'PROGRESS_DEPTH': 0
}

sg.DEFAULT_FONT = 'Calibri'

sg.theme_add_new('Dashboard', theme_dict)
sg.theme('Dashboard')

forecast_type = {
    'Static Balance sheet': ForecastType.StaticBalanceSheetForecast,
    'Dynamic Balance sheet': ForecastType.DynamicBalanceSheetForecast,
    'Business Plan': ForecastType.BusinessPlanForecast
}

top_banner = [
    [sg.Image(source=str(logo)), sg.Text(' |  Z-Model', font=('Calibri', 28))],
]

inputs = [
    [sg.Text('Model Inputs', font=('Calibri', 20))],
    [sg.Text('Forecast Type:\t\t'), sg.Combo(list(forecast_type.keys()), default_value=list(forecast_type.keys())[0], key='-FORECAST-TYPE-', readonly=True, expand_x=True)],
    [sg.Text('Account data:\t\t'), sg.Input(size=(20,0)), sg.FileBrowse(key='-ACCOUNT_DATA-')],
    [sg.Text('Assumptions:\t\t'), sg.Input(size=(20,0)), sg.FileBrowse(key='-ASSUMPTIONS-')],
    [sg.Text('Macroeconomic Scenarios:\t'), sg.Input(size=(20,0)), sg.FileBrowse(key='-SCENARIOS-')],
    [sg.Text('Results:\t\t\t'), sg.Input(size=(20,0)), sg.FileSaveAs('Browse', key='-RESULTS-', default_extension='.zip', file_types=(('application/zip', '*.zip'),))],
    [sg.Text('Portfolio Assumptions:\t'), sg.Input(size=(20,0),default_text='Optional'), sg.FileBrowse(key='-PORTFOLIO-ASSUMPTIONS-')],
    [sg.Text('Climate Risk Adjustments:\t'), sg.Input(size=(20,0),default_text='Optional'), sg.FileBrowse(key='-CRVA-')],
]

actions = [
    [sg.Button('Submit', size=(23, 2), border_width=0), sg.Button('Exit', size=(23, 2), border_width=0)],
    [sg.ProgressBar(100, orientation='h', size=(36, 20), border_width=0, key='progressbar', pad=(0,10))],
]

notes = [
    [sg.Text(f'\xa9 {__copyright__}, Version: {__version__}', font='Calibri 8', pad=(0,0))],
    [sg.Text(f'User license: {license_message}', font='Calibri 8', pad=(0,0))],
]

layout = [
    [sg.Column(top_banner, size=(400, 60))],
    [sg.HorizontalSeparator(pad=(0,5))],
    [sg.Column(inputs, size=(400, 280))],
    [sg.HorizontalSeparator(pad=(0,10))],
    [sg.Column(actions, size=(400, 80))],
    [sg.Column(notes, size=(400, 40))],
]

window = sg.Window(
    'Deloitte | Z-Model',
    layout,
    margins=(10,5),
    element_justification='c',
    no_titlebar=True,
    grab_anywhere=True,
    icon=icon
)

def main():
    try:
        if license.is_valid():
            logging.info('Starting Z-model GUI.')
            while True:
                event, values = window.read()
                logging.debug(f'GUI {event=}, {values=}')
                if event == sg.WIN_CLOSED or event == 'Exit':
                    break
                elif event == 'Submit':
                    if values['-ACCOUNT_DATA-'] == '' and values['-ASSUMPTIONS-'] == '' and values['-SCENARIOS-'] == '' and values['-RESULTS-'] == '':
                        sg.popup_ok(f'Not all required inputs were provided. Please provide required inputs and try again.', title='Z-Model', icon=icon)
                    else:
                        sg.popup_quick('The model is running and might take some time to compete and appear to be frozen. Please be patient.', title='Z-Model', icon=icon)
                        window['progressbar'].update_bar(20)

                        run(
                            forecast_type=forecast_type.get(values['-FORECAST-TYPE-']),
                            account_data=Path(values['-ACCOUNT_DATA-']),
                            assumptions=Path(values['-ASSUMPTIONS-']),
                            scenarios=Path(values['-SCENARIOS-']),
                            outfile=Path(values['-RESULTS-']),
                            portfolio_assumptions=Path(values['-PORTFOLIO-ASSUMPTIONS-']) if values['-PORTFOLIO-ASSUMPTIONS-'] else None,
                            climate_risk_scenarios=Path(values['-CRVA-']) if values['-CRVA-'] else None,
                            method=Methods.ProgressMap
                        )
                        window['progressbar'].update_bar(100)
                        sg.popup_ok(f'The model is done running and results are saved to the following location: {values["-RESULTS-"]}', title='Z-Model', icon=icon)
                        break
            window.close()
        else:
            sg.popup_ok(
                f"The Z-Model user license is not valid.\n\n"

                f"User License Information:\n"
                f"=========================\n"
                f"Company Name: {license.information.get('company_name', 'unknown')}\n"
                f"Email: {license.information.get('email', 'unknown')}\n"
                f"Expiration Date: {license.information.get('expiration_date', 'unknown')}\n"
                f"Product Code: {license.signature[:10]}...\n",
                title='Z-Model',
                icon=sg.SYSTEM_TRAY_MESSAGE_ICON_WARNING
            )
    except Exception as e:
        logging.error(e, exc_info=True)
        sg.popup_ok(
            f"ERROR 500\n\n"
            f"{str(e)}\n\n"
            f"Please check log for more information:\n",
            title='Z-Model',
            icon=sg.SYSTEM_TRAY_MESSAGE_ICON_WARNING,
        )


if __name__ == '__main__':
    main()