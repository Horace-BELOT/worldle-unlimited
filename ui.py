"""Dash UI of the application"""
import os
import random
import base64

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

NAME_COL: str = "FINAL_GEOUNIT"

app = dash.Dash(__name__)

class UI:

    def __init__(self) -> None:
        self.df: pd.DataFrame = pd.read_csv("files/DATAFRAME_outlines.csv", sep=";")
        self.categories: Dict[str, bool] = {}
        self.flag_data()
        image_folder: str = os.path.join("files", "outlines")
        # image_folder: str = "/files/outlines/"
        self.df.sort_values(by=[NAME_COL], ascending=True, inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        for idx, file_name in self.df["file_name"].items():
            # self.df.loc[idx, "image_path"] = image_folder + f"{file_name}.png"
            image_path: str = os.path.join(image_folder, f"{file_name}.png")
            self.df.loc[idx, "image_data"] = __class__.encode_image(image_path)

        self.dropdown_options: List[Dict[str, str]] = [
            {"label": name, "value": idx}
            for idx, name in self.df[NAME_COL].items()
        ]
        self.mode_challenge: bool = True
        self.reset_dataframe()
        self.n: int = len(self.df)
        self.current_image: int
        self.sample_new_country()

    def sample_new_country(self) -> None:
        """Sample a random country amongst the ones not sampled so far"""
        n_remaining: int = (~self.df["done"]).sum() - 1
        idx: int = random.randint(0, n_remaining)
        self.current_image: int = self.df[~self.df["done"]].index[idx]
        self.df.loc[self.current_image, "done"] = True

    def reset_dataframe(self) -> None:
        """Resets the dataframe to start parameters"""
        self.df.loc[:, "done"] = False
        self.df.loc[:, "correct"] = False
        # We then filter the categories
        self.df.loc[:, "current_challenge"] = True
        # If category IS NOT ENABLED ==> we remove it
        for cat in [k for k,v in self.categories.items() if not v]:
            self.df["current_challenge"] &= ~self.df[cat]

    def get_score(self) -> str:
        """Outputs the score"""
        n_correct: int = self.df["correct"].sum() 
        n_guess: int = self.df["done"].sum()
        return f"{n_correct} / {n_guess - 1}"  # We remove 1 because one is currently being guessed

    def get_header(self) -> str:
        """Outputs the header at the top of the file:"""
        if self.mode_challenge:
            return "No-limit Worldle (challenge mode)"
        return "No-limit Worldle (exploration mode)"
    
    def get_modebutton_text(self) -> str:
        """Outputs the text that will be written on the mode button"""
        if self.mode_challenge:
            return "Swap to explore mode"
        return "Swap to challenge mode"

    def get_checklist_options(self) -> List[Dict[str, str]]:
        """Builds the option data that will be in the checklist"""
        options: List[Dict[str, str]] = []
        for category_name in self.categories:
            options.append({"label": category_name, "value": category_name})
        return options
    
    def get_checklist_value(self) -> List[str]:
        """Builds the value data that will be in the checklist"""
        return [k for k,v in self.categories.items() if v]


    def flag_data(self) -> None:
        d: Dict[str, List[str]] = {
            "Small islands" : [
                "Aland", "American Samoa", "Anguilla",
                "Aruba", "Azores", "Barbados",
                "British Indian Ocean Territory", "British Virgin Islands"
                "Bermuda", "Cabo Verde", "Carribean Netherlands",
                "Cayman Islands", "Christmas Islands",
                "Cocos (Keeling) Islands", "Comoros",
                "Cook Islands", "Dominica", "Falkland Islands",
                "Faroe Islands", "Federated States of Micronesia",
                "Fiji", "French Polynesia", "French Southern and Antarctic Lands",
                "Grenada", "Guadeloupe", "Guam", "Guernsey",
                "Heard Island and McDonald Islands", "Isle of Man", "Jersey",
                "Kiribati", "Madeira", "Maldives", "Marshall Islands",
                "Martinique", "Mauritius", "Mayotte", "Montserrat",
                "New Caledonia", "Niue", "Norfolk Island"
                "Northern Mariana Islands", "Palau", "Paracel Islands",
                "Pitcairn Islands", "Reunion", "Saint Kitts and Nevis",
                "Saint Lucia", "Saint Pierre and Miquelon",
                "Saint Vincent and the Grenadines", "Samoa",
                "São Tomé and Principe", "Serranilla Bank",
                "Seychelles", "Solomon Islands", "South Georgia and the Islands",
                "Spratly Islands", "Svalbard", "The Bahamas", "Tonga",
                "Trinidad and Tobago", "Turks and Caicos Islands",
                "Tuvalu", "United States Virgin Islands", "Vanuatu",
                "Wallis and Futuna",
            ],
            "Small Land Countries": [
                "Bahrain", "Andorra", "Brunei",
                "Djibouti", "East Timor",
                "Hong Kong S.A.R.", "Macao S.A.R",
                "Kuwait", "Qatar",
                "Liechtenstein", "Monaco", "San Marino"
                "Singapore", "Vatican"
            ]
        }
        for cat, elem_in_cat in d.items():
            self.df[cat] = self.df["FINAL_GEOUNIT"].isin(elem_in_cat).fillna(False)
        self.categories = {k: True for k in d.keys()}



    @staticmethod
    def encode_image(image_path: str) -> str:
        encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode('ascii')
        return 'data:image/png;base64,{}'.format(encoded_image)

ui = UI()

# Define the layout of the app
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H2("Score", style={"color": "white"}),
                html.H2(id="score-text", children=ui.get_score(), style={"color": "white"}),
                html.Button("Reset game", id="reset-button", n_clicks=0),
                html.Button(children=ui.get_modebutton_text(), id="mode-button", n_clicks=0),

                html.Hr(),

                html.H2("Country options", style={"color": "white"}),
                dcc.Checklist(
                    id="category-checklist",
                    options=ui.get_checklist_options(),
                    value=ui.get_checklist_value(),
                    style={"color": "white"},
                    inline=False,
                )
            ],
            id="fixed-div", 
            style={
                "position": "fixed",
                "left": 0,
                "top": 0,
                "height": "100%",
                "width": "200px",
                "background-color": "#050505"
            }),
        html.Div(
            children=[
                html.H1(
                    children=ui.get_header(), 
                    style={"color": "white"},
                    id="title-header"
                ),
                dcc.Dropdown(
                    id='dropdown',
                    options=ui.dropdown_options,
                    placeholder="Enter country name",
                    multi=False,  # Change to True if multiple selections are needed
                    searchable=True,  # Enable the search functionality
                    # style={"backgroundColor": "#000000", "color": "white"}
                ),
                html.Img(id='country-image', src=ui.df.loc[ui.current_image, "image_data"], style={'width': '50%'}),
                html.H2(children="", id="output-result", style={"fontSize": 40}),
            ], 
            style={
                "backgroundColor": "#000000",
                "height": "100vh",
                "width": "60vw",
                "margin-left": "200px"
            }
        )
    ], 
    style={
        "backgroundColor": "#000000",
        "height": "100vh",
        "width": "100vw",
        "overflow": "hidden",
    }
)

# Define callback to update the output container based on dropdown selection
@app.callback(
    Output('country-image', 'src'),      # Country image
    Output("output-result", "children"), # Content of the text showing the result
    Output('dropdown', 'value'),         # We reset the value of the dropdown each time
    Output('output-result', 'style'),    # Color of the text showing the result (red/green)
    Output('score-text', "children"),    # Current score
    Output('title-header', "children"),  # Title at the top of the screen (showing mode)
    Output('mode-button', 'children'),   # Text on the challenge/exploration button
    Input('dropdown', 'value'),
    Input('reset-button', 'n_clicks'),
    Input('mode-button', 'n_clicks'),
    prevent_initial_call=True  
)
def update_image(
        value: str,                  # Dropdown: country guess
        n_clicks_reset_btn: int,     # Reset Button
        n_clicks_swapmode_btn: int,  # 
    ) -> Tuple[str, str, Optional[str], Dict[str, str], str, str]:
    # We define default values
    out_str: str = ""
    out_style: Dict[str, str] = {}
    dropdown_value: Optional[str] = None
    # The callback context gives {prop id}.{prop attribute} (e.g: dropdown.value)
    triggered_input_id = dash.callback_context.triggered[0]['prop_id'].split(".")[0]  
    if triggered_input_id == "reset-button":
        # In this case we reset everything.
        ui.reset_dataframe()
        ui.sample_new_country()
        image_data: str = ui.df.loc[ui.current_image, "image_data"]
    elif triggered_input_id == "mode-button":
        # In this case we want to swap the mode of the game
        # The mode is swapping between challenge and explore, starting in challenge.
        ui.mode_challenge = not ui.mode_challenge
        if ui.mode_challenge:  # If we are now in mode challenge
            image_data: str = ui.df.loc[ui.current_image, "image_data"]
        else:  # We are in mode exploration
            idx = ui.df.index[0]
            dropdown_value = idx
            image_data: str = ui.df.loc[idx, "image_data"]

    else:  # Otherwise its normal case
        if value is None:  # No new name
            raise PreventUpdate
        idx: int = int(value)
        if ui.mode_challenge: # Mode challenge
            if idx == ui.current_image:
                out_str: str = f"Congrats it was indeed: {ui.df.loc[idx, NAME_COL]}"
                out_style = {"color": "green"}
                ui.df.loc[ui.current_image, "correct"] = True
            else:
                out_str: str = f"No it was not {ui.df.loc[idx, NAME_COL]}, it was: {ui.df.loc[ui.current_image, NAME_COL]}"
                out_style = {"color": "red"}
            ui.sample_new_country()  # Rolling a new country
            image_data: str = ui.df.loc[ui.current_image, "image_data"]  # Image of new country
        else:  # Mode exploration
            image_data: str = ui.df.loc[idx, "image_data"]
            dropdown_value = idx

    return (
        image_data, 
        out_str, 
        dropdown_value, 
        out_style, 
        ui.get_score(), 
        ui.get_header(),
        ui.get_modebutton_text()
    )

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)