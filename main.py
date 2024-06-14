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

from ui import UI, CONST

NAME_COL: str = "FINAL_GEOUNIT"
STYLE_BUTTON_CENTER: Dict[str, str] = {
    'display': 'flex',
    'justifyContent': 'center',
    'alignItems': 'center',
}

app = dash.Dash(__name__)

ui = UI()

app.layout = ui.build_layout()

@app.callback(
    Output(CONST.ID.IMAGE_COUNTRY, 'src'),       # Country image
    Output(CONST.ID.TEXT_COUNTRY, "children"),
    Output(CONST.ID.TEXT_RESULT, "children"),    # Content of the text showing the result
    Output(CONST.ID.DROPDOWN_COUNTRY, 'value'),  # We reset the value of the dropdown each time
    Output(CONST.ID.DROPDOWN_COUNTRY, 'options'),  # We can change the options of the dropdown
    Output(CONST.ID.TEXT_RESULT, 'style'),       # Color of the text showing the result (red/green)
    Output(CONST.ID.TEXT_SCORE, "children"),     # Current score
    Output(CONST.ID.TEXT_TITLE, "children"),     # Title at the top of the screen (showing mode)
    Output(CONST.ID.BUTTON_MODE, 'children'),    # Text on the challenge/exploration button
    Output(CONST.ID.DIV_IMAGE, "style"),
    Output(CONST.ID.DIV_TEXT, "style"),
    Input(CONST.ID.DROPDOWN_COUNTRY, 'value'),   # Dropdown value changed
    Input(CONST.ID.BUTTON_RESET, 'n_clicks'),    # Reset button clicked
    Input(CONST.ID.BUTTON_MODE, 'n_clicks'),     # Mode button clicked
    # prevent_initial_call=True  
)
def update_image(
        value: str,                  # Dropdown: country guess
        n_clicks_reset_btn: int,     # Reset Button
        n_clicks_swapmode_btn: int,  # 
    ) -> Tuple[str, str, Optional[str], Dict[str, str], str, str]:

    # The callback context gives {prop id}.{prop attribute} (e.g: dropdown.value)
    triggered_input_id: str = dash.callback_context.triggered[0]['prop_id'].split(".")[0]  
    if triggered_input_id == CONST.ID.BUTTON_RESET:
        # In this case we reset everything.
        ui.reset_dataframe()
        ui.sample_new_question()
        ui.update_dropdown_options()
        if ui.s.quizz_input_value == "Outline":
            ui.s.image_data = ui.df.loc[ui.s.current_explore_idx, CONST.COL.OUTLINE_IMAGE_DATA]
        elif ui.s.quizz_input_value == "Flag":
            ui.s.image_data = ui.df.loc[ui.s.current_explore_idx, CONST.COL.FLAG_IMAGE_DATA]

    elif triggered_input_id == CONST.ID.BUTTON_MODE:
        # In this case we want to swap the mode of the game
        # The mode is swapping between challenge and explore, starting in challenge.
        ui.s.is_mode_challenge = not ui.s.is_mode_challenge
        if ui.s.is_mode_challenge:  # If we are now in mode challenge
            pass
        else:  # We are in mode exploration
            # The index of the country will be the first value in the data 
            # that matches the quizz right now
            ui.s.current_explore_idx = ui.df[ui.df[CONST.COL.CHALL_ELIGIBLE]].index[0]

    elif triggered_input_id == CONST.ID.DROPDOWN_COUNTRY:
        if value is None:  # No name was selected in the dropdown => we don't update anything
            raise PreventUpdate
        idx: int = int(value)
        if ui.s.is_mode_challenge: # Mode challenge
            if ui.s.quizz_target == "Name":
                target_col: str = CONST.COL.NAME
            elif ui.s.quizz_target == "Capital":
                target_col: str = CONST.COL.CAPITAL
            else:
                raise NotImplementedError
            your_answer: str = ui.df.loc[idx, target_col]
            real_answer: str = ui.df.loc[ui.s.current_guess_idx, target_col]

            if idx == ui.s.current_guess_idx:
                ui.s.answer = f"Congrats it was indeed: {your_answer}"
                ui.s.answer_style = {"color": "green"}
                ui.df.loc[idx, CONST.COL.CHALL_CORRECT] = True
            else:
                ui.s.answer = f"No it was not {your_answer}, it was: {real_answer}"
                ui.s.answer_style = {"color": "red"}
            ui.sample_new_question()  # Rolling a new country

        else:  # Mode exploration
            ui.s.current_explore_idx = idx
            ui.s.dropdown_value_idx = idx

    ui.update_score()
    ui.update_visuals()
    ui.update_dropdown_options()

    return (
        ui.s.image_data,           # What image to show as hint
        ui.s.text_to_guess,        # What text to show as hint
        ui.s.answer,               # The text of the answer (are we right or wrong)
        ui.s.dropdown_value_idx,   # Value in the dropdown (often None ie nothing select)
        ui.s.dropdown_options,
        ui.s.answer_style,         # The style of the answer (green or red)
        ui.s.score_text,           # Score text to show
        ui.s.header_title_text,    # What text should be at the top of the screen
        ui.s.mode_button_text,     # What text should be on the mode button
        ui.s.style_image_div,      # Whether the image div should be shown
        ui.s.style_text_div        # Whether the text div should be shown
    )

@app.callback(
    Output(CONST.ID.TEXT_THEORIC_TOTAL, "children"),
    Input(CONST.ID.CHECKLIST_CATEGORY, "value"), # Checklist changed
    Input(CONST.ID.CHECKLIST_CONTINENT, "value"), # Checklist changed
    Input(CONST.ID.RADIOITEMS_QUIZ_INPUT, "value"),
    Input(CONST.ID.RADIOITEMS_QUIZ_TARGET, "value"),
    # prevent_initial_call=True
)
def update_cat_checklist(
    checklist_cat: List[str],
    checklist_continent: List[str],
    quiz_input: str,
    quiz_target: str,
) -> str:
    """
    If we change the country categories, this will simply update
    the attribute in the UI class.
    """
    ui.s.categories = {cat: cat in checklist_cat for cat in ui.s.categories}
    ui.s.continents = {cont: cont in checklist_continent for cont in ui.s.continents}

    ui.s.quizz_input_value = quiz_input
    ui.s.quizz_target_value = quiz_target
    
    ui.update_theoric_total()
    return ui.s.theoric_total


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)