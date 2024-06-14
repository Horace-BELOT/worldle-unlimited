"""
The goal of this script will mainly be to merge data from the outline & the flag datasets.
"""
import math
import os

from typing import Dict, Any, Set, Iterable, List, Tuple
import pandas as pd


class Ngram:
    replace_map: Dict[str, str] = {
        "_": " ",
        ".png": "",
        "Å": "A",
        "é": "e",
        "ê": "e",
        "ç": "c",
    }

    def __init__(self, s: str, n: int = 3) -> None:
        """Represents the ngram of a string"""
        self.n: int = n
        self.original_s: str = s
        for k, v in __class__.replace_map.items():
            s = s.replace(k,v)
        s = s.lower()
        self.s: str = s

        self.d: Dict[str, int] = {}
        nchar: int = len(s)
        if nchar < n:  # Not enough letters to even build 1 ngram
            return
        # We build an iterator with a start and end index
        for (i1, i2) in zip(range(0, nchar - n + 1), range(n, nchar + 1)):
            ngram: str = s[i1:i2]
            self.d[ngram] = (self.d.get(ngram) or 0) + 1

    def sim(self, other: "Ngram") -> float:
        return __class__.similarity(self, other)
    
    def __str__(self) -> str:
        return self.original_s
    
    @staticmethod
    def similarity(a: "Ngram", b: "Ngram") -> float:
        """Cosine similarity"""
        # We compute the dot product:
        out: float = sum(v * b.d.get(k, 0) for k, v in a.d.items())
        # We then compute the norm of each vector
        n1: float = math.sqrt(sum(v ** 2 for v in a.d.values()))
        n2: float = math.sqrt(sum(v ** 2 for v in b.d.values()))
        if n1 * n2 == 0: return 0.0
        return out / (n1 * n2)
    
    @staticmethod
    def build_similarity_map(
        s1: Iterable[str], 
        s2: Iterable[str],
        n: int = 3,
    ) -> pd.DataFrame:
        """
        Build a 2D similarity map between 2 sets of strings
        s1 will be in dataframe index
        s2 will be in dataframe column
        """
        ngrams_1: List[Ngram] = [Ngram(s=k, n=n) for k in s1]
        ngrams_2: List[Ngram] = [Ngram(s=k, n=n) for k in s2]

        df = pd.concat([
            pd.DataFrame(
                {str(ngram_col): [ngram_col.sim(ngram_idx) for ngram_idx in ngrams_1]})
            for ngram_col in ngrams_2
        ], axis=1)
        df.index = [str(k) for k in ngrams_1]
        return df
    

class DataMerger:

    def __init__(
            self,
            df_flag_path: str,
            df_outlines_path: str,
            folder_flag_path: str,
            folder_outlines_path: str
        ) -> None:
        """"""
        self.df_flag_path: str = df_flag_path
        self.df_outlines_path: str = df_outlines_path
        self.folder_flag_path: str = folder_flag_path
        self.folder_outlines_path: str = folder_outlines_path

    def merge_datasets(
            self,
            df_save_path: str,
    ) -> pd.DataFrame:
        """
        In order to associate outline & flag data together, we will process
        the lowercased file name of both folders, get the n-grams of the name
        and then make a similarity measure.
        """
        s1: List[str] = os.listdir(self.folder_flag_path)
        s2: List[str] = os.listdir(self.folder_outlines_path)

        df: pd.DataFrame = Ngram.build_similarity_map(s1, s2)

        d, df2 = DataMerger.solve_similarity_map(df, 0.48)
        # Manually updating the outliers:
        d.update({
            "Côte d'Ivoire.png": "Ivory_Coast.png",  # Traduction
            "DR Congo.png": "Democratic_Republic_of_the_Congo.png",
            "Macau.png": "Macao_S.A.R.png",
            "Timor-Leste.png": "East_Timor.png",     # Traduction
        })
        # Loading flag df and adding column to merge
        df_flag = pd.read_csv(self.df_flag_path, sep=";")
        df_flag["outline_file_name"] = df_flag["flag_file_name"].map(d)
        # Loading outline df
        df_outline = pd.read_csv(self.df_outlines_path, sep=";")

        df = pd.merge(
            left=df_flag,
            right=df_outline,
            on=["outline_file_name"],
            how="outer",
        )
        # the map will be d[flag] => outlines
        outline_removed: List[str] = [
            "Ashmore and Cartier Islands",
            "Bajo Nuevo Bank (Petrel Is.)",
            "Baker Island",
            "Bir Tawil", "Bouvet Island",
            "Brazilian Island", "Clipperton Island",
            "Coral Sea Islands", "Gaza", "Gibraltar",
            "Howland Island", "Jan Mayen", "Jarvis Island",
            "Johnston Atoll", "Kingman Reef",
            "Midway Islands", "Navassa Island",
            "Palmyra Atoll", "Saint Barthelemy",
            "Scarborough Reef", "Siachen Glacier",
            "West Bank", "Western Sahara", "Seranilla Bank"
            "Southern Patagonian Ice Field",
            "Heard Island and McDonald Islands",
            "Nauru", "Saint Helena", "Saint Martin",
            "Sint Maarten", "Tokelau", "UNDOF",
            "US Naval Base Guantanamo Bay", "Wake Atoll",
        ]
        # We make some outlines unusable
        df.loc[:, "outline_unuseable"] = df["FINAL_GEOUNIT"].isin(outline_removed).fillna(False)

        df.to_csv(df_save_path, sep=";", index=False)
        return df
    
    @staticmethod
    def solve_similarity_map(df: pd.DataFrame, threshold: float) -> Tuple[
            Dict[str, str], 
            pd.DataFrame
        ]:
        d, df2 = __class__.__solve_similarity_map(df, threshold)
        d_final: Dict[str, str] = {}
        i: int = 1
        while d:
            print(f"solve_similarity_map | Step {i} | {len(d)} pairs created")
            d_final = {**d_final, **d}
            d, df2 = __class__.__solve_similarity_map(df2, threshold)
        return d_final, df2



    @staticmethod
    def __solve_similarity_map(df: pd.DataFrame, threshold: float) -> Tuple[
            Dict[str, str], 
            pd.DataFrame
        ]:
        """Solves the similarity map and returns a mapping s1 => s2"""
        d_1: Dict[str, str] = {}
        for name_1, row in df.iterrows():
            s: pd.Series = row[row >= threshold].sort_values(ascending=False)
            if len(s) >= 1:
                d_1[name_1] = s.index[0]
        d_2: Dict[str, str] = {}
        for name_2, col in df.transpose().iterrows():
            s: pd.Series = col[col >= threshold].sort_values(ascending=False)
            if len(s) >= 1:
                d_2[name_2] = s.index[0]
        s = pd.Series(d_1)
        d = s[s.map(d_2) == s.index].to_dict()
        return d, df.loc[~df.index.isin(d.keys()), ~df.columns.isin(d.values())]

if __name__ == "__main__":
    dm = DataMerger(
        df_flag_path="files/df_flags.csv",
        df_outlines_path="files/df_outlines.csv",
        folder_flag_path="files/flags",
        folder_outlines_path="files/outlines",
    )
    df_path: str = "files/merged_df.csv"
    dm.merge_datasets(df_save_path=df_path)