"""
Dash UI of the application
TODO: a header to specify is the expected answer is a capital or a country name
TODO: Button to remove already passed countries in the dropdown options (to toggle or not)
TODO: fix NaN in dataframe
"""
import os
import random
import base64

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Literal, Set

NAME_COL: str = "FINAL_GEOUNIT"
STYLE_BUTTON_CENTER: Dict[str, str] = {
    'display': 'flex',
    'justifyContent': 'center',
    'alignItems': 'center',
}

class CONST:
    class ID:
        IMAGE_COUNTRY: str = "country-image"
        TEXT_COUNTRY: str = "country-text"
        TEXT_RESULT: str = "text-result"
        DROPDOWN_COUNTRY: str = "country-dropdown"
        TEXT_SCORE: str = "text-score"
        TEXT_TITLE: str = "text-title"
        BUTTON_MODE: str = "button-mode"
        BUTTON_RESET: str = "button-reset"
        CHECKLIST_CATEGORY: str = "checklist-cat"
        CHECKLIST_CONTINENT: str = "continent-cat"
        TEXT_THEORIC_TOTAL: str = "text-theorictotal"
        RADIOITEMS_QUIZ_INPUT: str = "ri-quiz-input"
        RADIOITEMS_QUIZ_TARGET: str = "ri-quiz-target"
        DIV_IMAGE: str = "image-hint-holder"
        DIV_TEXT: str = "text-hint-holder"

    class COL:
        CAPITAL: str = "capital"
        CONTINENT: str = "continent"
        NAME: str = "name"
        # Which row is included in the current challenge
        CHALL_ELIGIBLE: str = "CHALL_ELIGIBLE"
        # Which row was already guessed in the quizz
        CHALL_DONE: str = "CHALL_DONE"
        # Which row was correctly guessed in the quizz
        CHALL_CORRECT: str = "CHALL_CORRECT"
        # Bytes data of the image of the country's outline
        OUTLINE_IMAGE_DATA: str = "OUTLINE_IMAGE_DATA"
        # Bytes data of the image of the country's outline
        FLAG_IMAGE_DATA: str = "FLAG_IMAGE_DATA"
        # UNUSEABLE OUTLINE
        OUTLINE_UNUSEABLE: str = "outline_unuseable"
        # FINAL GEOUNIT (name column from outlines dataframe)
        FINAL_GEOUNIT: str = "FINAL_GEOUNIT"


class Status:
    """
    Represents the status of the UI, holds the variable that describe the Dash app.
    Could be a simple datastructure
    """
    def __init__(
            self,
        ) -> None:
        # Input / Question parameters
        self.current_guess_idx: int = 0
        self.current_explore_idx: int = 0

        # Dropdown text output
        self.dropdown_value_idx: int = None
        self.dropdown_options: List[Dict[str, str]] = []

        # Mode
        self._n_correct: int = 0
        self._n_questions: int = 0
        self._n_total: int = 0
        self.is_mode_challenge: bool = True  # Current value, for current quizz
        
        # Quiz input type
        self.quizz_input_options: List[str] = ["Flag", "Outline", "Capital", "Name"]
        self.quizz_input_value: Literal["Flag", "Outline", "Capital", "Name"] = "Outline"
        # Current value, for current quizz
        self.quizz_input: Literal["Flag", "Outline", "Capital", "Name"] = self.quizz_input_value

        # Quiz target type
        self.quizz_target_options: List[str] = ["Capital", "Name"]
        self.quizz_target_value: Literal["Capital", "Name"] = "Name"
        # Current value, for current quizz
        self.quizz_target: Literal["Flag", "Outline", "Capital", "Name"] = self.quizz_target_value

        # Country categories
        self.categories: Dict[str, bool] = {}

        # Continents
        self.continents: Dict[str, bool] = {}

        # Theoric total
        self._theoric_total: int = 0

        # Hint given
        self.image_data: str = ""
        self.show_image: bool = True
        self.text_to_guess: str = ""
        self.show_text: bool = False
        # Answer
        self.answer: str = ""
        self.answer_style: Dict[str, str] = {}
        
    @property
    def score_text(self) -> str:
        """Outputs the score"""
        msg: str = f"{self._n_correct} / {self._n_questions - 1}" 
        msg += f" (Total: {self._n_total})"
        return msg

    @property
    def header_title_text(self) -> str:
        """Outputs the header at the top of the file:"""
        if self.is_mode_challenge:
            return "No-limit Worldle (challenge mode)"
        return "No-limit Worldle (exploration mode)"
    
    @property
    def mode_button_text(self) -> str:
        """Returns the text on the button to swap modes"""
        if self.is_mode_challenge:
            return "Swap to explore mode"
        return "Swap to challenge mode"
    
    @property
    def theoric_total(self) -> str:
        """Outputs the string that should be in the TEXT_THEORIC_TOTAL div"""
        return f"Total with new settings: {self._theoric_total}"
    
    @property
    def style_image_div(self) -> Dict[str, Optional[str]]:
        if self.show_image:
            return {"display": "inline-block", "vertical-align": "top", "width": "50%"}
        return {"display": None}

    @property
    def style_text_div(self) -> Dict[str, Optional[str]]:
        if self.show_text:
            return {"display": "inline-block", "vertical-align": "top", "width": "50%"}
        return {"display": None}
    
    @property
    def category_checklist_options(self) -> List[str]:
        return [*self.categories.keys()]
    
    @property
    def category_checklist_value(self) -> str:
        return [cat for cat, b in self.categories.items() if b]
    
    @property
    def continent_checklist_options(self) -> List[str]:
        return [*self.continents.keys()]
    
    @property
    def continent_checklist_value(self) -> str:
        return [cat for cat, b in self.continents.items() if b]

class UI:

    def __init__(self) -> None:
        self.df: pd.DataFrame = self.load_dataframe()
        categories, continents = self.tag_data_with_info()
        self.s: Status = Status()

        self.s.categories = categories
        self.s.continents = continents
        self.reset_dataframe()
        self.n: int = len(self.df)

        self.update_dropdown_options()
        self.sample_new_question()

    def load_dataframe(self) -> pd.DataFrame:
        """Loads and process the merged dataframe"""
        df: pd.DataFrame = pd.read_csv("files/merged_df.csv", sep=";")
        df.sort_values(by=[NAME_COL], ascending=True, inplace=True)
        df.reset_index(inplace=True, drop=True)
        # Now we prepare the image data
        image_folder: str = os.path.join("files", "outlines")
        m: pd.Series = df["outline_file_name"].notna()
        for idx, file_name in df.loc[m, "outline_file_name"].items():
            image_path: str = os.path.join(image_folder, file_name)
            df.loc[idx, CONST.COL.OUTLINE_IMAGE_DATA] = __class__.encode_image(image_path)
        df.loc[df[CONST.COL.OUTLINE_UNUSEABLE], CONST.COL.OUTLINE_IMAGE_DATA] = None
        # Same with flag images
        image_folder: str = os.path.join("files", "flags")
        m: pd.Series = df["flag_file_name"].notna()
        for idx, file_name in df.loc[m, "flag_file_name"].items():
            image_path: str = os.path.join(image_folder, file_name)
            df.loc[idx, CONST.COL.FLAG_IMAGE_DATA] = __class__.encode_image(image_path)

        m: pd.Series = df[CONST.COL.NAME].isna()
        df.loc[m, CONST.COL.NAME] = df.loc[m, CONST.COL.FINAL_GEOUNIT]
        return df

    def update_dropdown_options(self) -> None:
        """Builds the answer dropdown options"""
        if self.s.quizz_target == "Capital":
            m: pd.Series = self.df[CONST.COL.CHALL_ELIGIBLE]
            options: List[Dict[str, str]] = [
                {"label": name, "value": idx}
                for idx, name in self.df.loc[m, CONST.COL.CAPITAL].items()
            ]
        elif self.s.quizz_target == "Flag":
            raise NotImplementedError
        elif self.s.quizz_target == "Name":
            m: pd.Series = self.df[CONST.COL.CHALL_ELIGIBLE]
            options: List[Dict[str, str]] = [
                {"label": name, "value": idx}
                for idx, name in self.df.loc[m, CONST.COL.NAME].items()
            ]
        elif self.s.quizz_target == "Outline":
            raise NotImplementedError
        else:
            raise NotImplementedError
        self.s.dropdown_options = options

    def sample_new_question(self) -> None:
        """
        Sample a random country amongst the ones not sampled so far, 
        so it can be guessed
        """
        # Counting the number of countries that are eligible but not done yet
        m: pd.Series = (~self.df[CONST.COL.CHALL_DONE] &
                            self.df[CONST.COL.CHALL_ELIGIBLE])
        n_remaining: int = m.sum()
        # We roll a random number for a random new country
        idx: int = random.randint(0, n_remaining - 1)
        self.s.current_guess_idx = self.df[m].index[idx]
        # We flag that new country as now done
        self.df.loc[self.s.current_guess_idx, CONST.COL.CHALL_DONE] = True

    def update_visuals(self) -> None:
        """
        Updates the image / text of the question input / output
        """
        if self.s.is_mode_challenge:
            idx: int = self.s.current_guess_idx
        else:  # Exploration index
            idx: int = self.s.current_explore_idx
        if self.s.quizz_input == "Outline":
            self.s.image_data = self.df.loc[idx, CONST.COL.OUTLINE_IMAGE_DATA]
        elif self.s.quizz_input == "Flag":
            self.s.image_data = self.df.loc[idx, CONST.COL.FLAG_IMAGE_DATA]
        elif self.s.quizz_input == "Capital":
            self.s.text_to_guess = self.df.loc[idx, CONST.COL.CAPITAL]
        elif self.s.quizz_input == "Name":
            self.s.text_to_guess = self.df.loc[idx, CONST.COL.NAME]
        else:
            raise NotImplementedError


    def reset_dataframe(self) -> None:
        """
        Resets the dataframe to starting parameters. Score is reset
        and you can guess all the countries again
        """
        self.df.loc[:, CONST.COL.CHALL_DONE] = False
        self.df.loc[:, CONST.COL.CHALL_CORRECT] = False
        self.df.loc[:, CONST.COL.CHALL_ELIGIBLE] = self._compute_mask_eligible()

        self.s.quizz_input = self.s.quizz_input_value
        self.s.quizz_target = self.s.quizz_target_value
        self.s.show_image = (self.s.quizz_input in ["Flag", "Outline"])
        self.s.show_text = not self.s.show_image
            
    def _compute_mask_eligible(self) -> pd.Series:
        """
        Computes the mask of the rows that are eligible for the
        quizz with the current parameters
        """
        m: pd.Series = pd.Series({idx: True for idx in self.df.index})
        if (self.s.quizz_input_value == "Capital") or (self.s.quizz_target_value == "Capital"):
            m &= self.df[CONST.COL.CAPITAL].notna()
        if (self.s.quizz_input_value == "Name") or (self.s.quizz_target_value == "Name"):
            m &= self.df[CONST.COL.NAME].notna()
        if (self.s.quizz_input_value == "Outline") or (self.s.quizz_target_value == "Outline"):
            m &= self.df[CONST.COL.OUTLINE_IMAGE_DATA].notna()
        if (self.s.quizz_input_value == "Flag") or (self.s.quizz_target_value == "Flag"):
            m &= self.df[CONST.COL.OUTLINE_IMAGE_DATA].notna()
        # Checking for categories
        for cat in [k for k,v in self.s.categories.items() if not v]:
            m &= ~self.df[cat]
        
        # Then we check for the continents: everything is false until we find a continent
        m_cont: pd.Series = pd.Series({idx: False for idx in self.df.index})
        for continent in [k for k,v in self.s.continents.items() if v]:
            # Some countries can be on multiple continents (Russia).
            # Hence we add a country if he belongs to at least 1 selected continent
            m_cont |= self.df[f"continent_{continent}"].fillna(False)
        return m & m_cont
    
    def update_score(self) -> None:
        """Computes new score"""
        self.s._n_correct = self.df[CONST.COL.CHALL_CORRECT].sum()
        self.s._n_questions = self.df[CONST.COL.CHALL_DONE].sum()
        self.s._n_total = self.df[CONST.COL.CHALL_ELIGIBLE].sum()
        # We remove 1 because one is currently being guessed
    
    def update_theoric_total(self) -> None:
        """
        This functions compute the number of countries that would be 
        in the game with the new settings
        """
        m = self._compute_mask_eligible()
        self.s._theoric_total = m.sum()

    def tag_data_with_info(self) -> Tuple[Dict[str, bool], Dict[str, bool]]:
        d: Dict[str, List[str]] = {
            "Small islands" : [
                "Aland", "Cabo Verde", "Falkland Islands",
                "Faroe Islands", "Isle of Man", "Kiribati", "Maldives", 
                "Malta", "Jamaica", "New Caledonia", "Taiwan", 
                "Puerto Rico", "Solomon Islands", "Svalbard", "The Bahamas", 
            ],
            "Very small islands": [
                "Wallis and Futuna", "Vanuatu", "United States Virgin Islands", 
                "Tuvalu", "Turks and Caicos Islands", "Trinidad and Tobago", "Tonga",
                "Spratly Islands", "South Georgia and the Islands", "Seychelles",
                "São Tomé and Principe", "Samoa", "Saint Vincent and the Grenadines",
                "Saint Pierre and Miquelon", "Saint Lucia", "Saint Kitts and Nevis",
                "Reunion", "Pitcairn Islands", "Paracel Islands", "Palau", 
                "Northern Mariana Islands", "Norfolk Island", "Niue", "Montserrat",
                "Mayotte", "Mauritius", "Martinique", "Marshall Islands","Madeira",
                "Madeira", "Jersey", "Guernsey", "Guam", "Guadeloupe", "Grenada", 
                "French Southern and Antarctic Lands", "French Polynesia", 
                "Fiji", "Federated States of Micronesia", "Dominica", 
                "Curaçao", "Cook Islands", "Comoros", "Christmas Islands",
                "Cocos (Keeling) Islands", "Cayman Islands", "Carribean Netherlands",
                "British Virgin Islands", "British Indian Ocean Territory", 
                "Bermuda", "Barbados", "Azores", "Aruba", "Antigua and Barbuda",
                "Anguilla", "American Samoa", 
            ],
            "Small Land Countries": [
                "Bahrain", "Andorra", "Brunei",
                "Djibouti", "East Timor",
                "Hong Kong S.A.R.", "Macao S.A.R",
                "Kuwait", "Qatar",
                "Liechtenstein", "San Marino"
                "Singapore", "Eswatini"
            ],
            "Ill-shaped": [
                "Vatican", "Monaco", 
            ]
        }
        for cat, elem_in_cat in d.items():
            self.df[cat] = self.df["FINAL_GEOUNIT"].isin(elem_in_cat).fillna(False)

        # Continents
        self.df.fillna(value={CONST.COL.CONTINENT: "Undefined"}, inplace=True)
        set_cont: Set[str] = self.df[CONST.COL.CONTINENT].dropna().apply(
            lambda x: x.split(",")[0]).unique()
        for continent in set_cont:
            self.df[f"continent_{continent}"] = self.df[CONST.COL.CONTINENT].str.contains(continent)
        return {k: True for k in d.keys()}, {continent: True for continent in set_cont}

    def build_layout(self) -> html.Div:
        """Builds the app layout"""
        ######################################################################
        ######################################################################
        left_panel: html.Div = html.Div(  # Left window on the left, fixed
            children=[
                html.H2("Score", style={"color": "white"}),
                html.H2(
                    id=CONST.ID.TEXT_SCORE, 
                    children=self.s.score_text, 
                    style={"color": "white"}
                ),
                html.Button(
                    "Reset game", 
                    id=CONST.ID.BUTTON_RESET, 
                    n_clicks=0, 
                    style=STYLE_BUTTON_CENTER
                ),
                html.Button(  # Button to swap between challenge and exploration mode
                    children=self.s.mode_button_text, 
                    id=CONST.ID.BUTTON_MODE, 
                    n_clicks=0,
                    style=STYLE_BUTTON_CENTER,
                ),

                html.Hr(),  # Horizontal bar
                html.Hr(),  # Horizontal bar
                html.H2("Quiz input", style={"color": "white"}),
                dcc.RadioItems(
                    id=CONST.ID.RADIOITEMS_QUIZ_INPUT,
                    options=self.s.quizz_input_options,
                    value=self.s.quizz_input_value, 
                    inline=False,
                    style={"color": "white"}
                ),
                html.H2("Quiz answer", style={"color": "white"}),
                dcc.RadioItems(
                    id=CONST.ID.RADIOITEMS_QUIZ_TARGET,
                    options=self.s.quizz_target_options, 
                    value=self.s.quizz_target_value, 
                    inline=False,
                    style={"color": "white"}
                ),

                html.Hr(),  # Horizontal bar
                html.H2("Country options", style={"color": "white"}),
                dcc.Checklist(
                    id=CONST.ID.CHECKLIST_CATEGORY,
                    options=self.s.category_checklist_options,
                    value=self.s.category_checklist_value,
                    style={"color": "white", 'display': 'block'},
                ),

                html.Hr(),  # Horizontal bar
                html.H2("Continent options", style={"color": "white"}),
                dcc.Checklist(
                    id=CONST.ID.CHECKLIST_CONTINENT,
                    options=self.s.continent_checklist_options,
                    value=self.s.continent_checklist_value,
                    style={"color": "white", 'display': 'block', "color": "white"},
                ),

                html.Div(
                    children=self.s.theoric_total, 
                    id=CONST.ID.TEXT_THEORIC_TOTAL,
                    style={"color": "white"},
                ),
            ],
            style={
                "position": "fixed",
                "left": 0,
                "top": 0,
                "height": "100%",
                "width": "200px",
                "background-color": "#050505",
            })
        ######################################################################
        ######################################################################
        # Right panel with the quiz
        right_panel: html.Div = html.Div(
            children=[
                html.H1(
                    children=self.s.header_title_text, 
                    style={"color": "white"},
                    id=CONST.ID.TEXT_TITLE
                ),
                html.Div(
                    id=CONST.ID.DIV_IMAGE, 
                    style=self.s.style_image_div,
                    children=[
                        html.Img(
                            id=CONST.ID.IMAGE_COUNTRY, 
                            src=self.s.image_data, 
                            style={'width': '50%'}
                        ),
                    ]
                ),
                html.Div(
                    id=CONST.ID.DIV_TEXT, 
                    style=self.s.style_text_div,
                    children=[
                        html.H2(
                            id=CONST.ID.TEXT_COUNTRY, 
                            children=self.s.text_to_guess, 
                            style={'width': '50%', "color": "white"}
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.H2(
                            children=" ", 
                            id=CONST.ID.TEXT_RESULT, 
                            style={"fontSize": 40, "margin-bottom": "10px"}
                        ),
                        dcc.Dropdown(
                            id=CONST.ID.DROPDOWN_COUNTRY,
                            options=self.s.dropdown_options,
                            placeholder="Enter country name",
                            multi=False,  # Change to True if multiple selections are needed
                            searchable=True,  # Enable the search functionality
                        ),
                    ],
                    style={"display": "inline-block", "vertical-align": "top", "width": "50%"}
                )
                
            ], 
            style={
                "backgroundColor": "#000000",
                "height": "100vh",
                "width": "60vw",
                "margin-left": "200px"
            }
        )
        ######################################################################
        ######################################################################
        return html.Div(
            children=[left_panel, right_panel], 
            style={
                "backgroundColor": "#000000",
                "height": "100%",
                "width": "100vw",
                "overflow": "hidden",
            }
        )


    @staticmethod
    def encode_image(image_path: str) -> str:
        encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode('ascii')
        return 'data:image/png;base64,{}'.format(encoded_image)
