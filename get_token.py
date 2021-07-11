import PySimpleGUI as sg
import requests

# Very basic form.  Return values as a list
SCOPE = "ZohoReports.fullaccess.all"


def get_form_entry():
    form = sg.FlexForm('Simple data entry form')  # begin with a blank form

    layout = [
        [sg.Text('Please enter ')],
        [sg.Text('ClientID', size=(50, 1)), sg.InputText('')],
        [sg.Text('ClientSecret', size=(50, 1)), sg.InputText('')],
        [sg.Text('Code', size=(50, 1)), sg.InputText('')],
        [sg.Text('Zoho Data Centre', size=(50, 1)), sg.Combo(['.COM', '.COM.AU', '.IN', '.COM.CN', '.EU'])],
        [sg.Submit(), sg.Cancel()]
    ]

    button, values = form.Layout(layout).Read()
    return button, values[0], values[1], values[2], values[3]


def post_token_request(client_id, client_secret, code, data_centre):
    url = f"https://accounts.zoho{data_centre}/oauth/v2/token".lower()
    r = requests.post(url, data={"code": code, "client_id": client_id,
                                 "client_secret": client_secret,
                                 "grant_type": "authorization_code",
                                 "scope": SCOPE})
    return r.json()


if __name__ == "__main__":
    button, client_id, client_secret, code, data_centre = get_form_entry()
    result = post_token_request(client_id, client_secret, code, data_centre)
    print(result)
