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

NAME_COL: str = "NAME_EN"

app = dash.Dash(__name__)

class UI:

    def __init__(self) -> None:
        self.df: pd.DataFrame = pd.read_csv("files/outlines/DATAFRAME.csv", sep=";")
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
        self.df["correct"] = False

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
                html.Button("Swap to explore mode", id="mode-button", n_clicks=0),
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
    Output('country-image', 'src'),
    Output("output-result", "children"),
    Output('dropdown', 'value'),
    Output('output-result', 'style'),
    Output('score-text', "children"),
    Output('title-header', "children"),
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

    return (image_data, out_str, dropdown_value, out_style, ui.get_score(), ui.get_header())

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)