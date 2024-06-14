"""
This file contains the code that creates the image outlines of all countries.

The image outline data comes from:
https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/
Two files are needed:
    - The data without the neighboring lakes
    - The map unit data (island and overseas territories are split from mainland)

"""
import os
import io
import time

from PIL import Image
import pyproj
import geopandas as gpd
import pandas as pd
import tqdm
import matplotlib
import matplotlib.pyplot as plt
from shapely.ops import transform
from typing import List, Any, Dict, Set
matplotlib.use('Agg')

NAME_COL = "NAME_EN"


def shift_geometry(geometry, offset: float):
    """
    geometry: geopandas geometry object
    offset in [0,360]
    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj(proj='latlong'), 
        pyproj.Proj(proj='latlong', lon_0=offset)
    ).transform
    return transform(project, geometry)

class OutlineDrawer:
    """
    Draws outline from naturalearthdata.com data.
    https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/
    """

    def __init__(
            self, 
            path_lake: str,
            path_no_lake: str,
            debug: bool = False,
        ) -> None:
        print("Loading naturalearthdata.com data")
        gdf_lake: gpd.GeoDataFrame = gpd.read_file(path_lake)
        gdf_nolake: gpd.GeoDataFrame = gpd.read_file(path_no_lake)
        self.df: gpd.GeoDataFrame = self.remove_lakes(gdf_lake, gdf_nolake)
        self.df = self.merge_countries()

        self.df.sort_values(NAME_COL, inplace=True)
        self.df.reset_index(inplace=True, drop=True)

        self.shift_countries()
        self.draw_all_countries()
    
    def shift_countries(self):
        """
        Some countries like Russia, new zealand, are distorted because
        they are on the left & right side of the used common projection
        """
        geometry_shift: Dict[str, float] = {
            "Russia": 180,
            "United States of America": 180,
            "New Zealand": 180,
            "Fiji": 180,
            "Kiribati": 180,
        }
        for country_name, offset in geometry_shift.items():
            m: pd.Series = self.df["FINAL_GEOUNIT"] == country_name
            self.df.loc[m, "geometry"] = self.df.loc[m, "geometry"].apply(
                lambda geom: shift_geometry(geom, offset)
            )


    def merge_countries(self) -> gpd.GeoDataFrame:
        """Manually merges country together"""

        d_map: Dict[str, str] = {
            # Georgia
            "Ajaria": "Georgia",
            "Georgia": "Georgia",
            # Cyprus
            "Akrotiri Sovereign Base Area": "Cyprus",
            "Dhekelia Sovereign Base Area": "Cyprus",
            "Cyprus No Mans Area": "Cyprus",
            "Northern Cyprus": "Cyprus",
            "Cyprus": "Cyprus",
            # Antigua & Barbuda
            "Antigua": "Antigua and Barbuda",
            "Barbuda": "Antigua and Barbuda",
            # Bosnia and Herzegovina
            "Brcko District": "Bosnia and Herzegovina",
            "Bosnia and Herzegovina": "Bosnia and Herzegovina",
            "Republic Srpska": "Bosnia and Herzegovina",
            # Solomon Islands
            "Bougainville": "Solomon Islands",
            # Belgium
            "Brussels Capital Region": "Belgium",
            "Flemish Region": "Belgium",
            "Walloon Region": "Belgium",
            # Iraq
            "Iraqi Kurdistan": "Iraq",
            "Iraq": "Iraq",
            # Kazakhstan
            "Baykonur Cosmodrome": "Kazakhstan",
            "Kazakhstan": "Kazakhstan",
            # South Korea
            "Korean Demilitarized Zone (south)": "South Korea",
            "South Korea": "South Korea",
            # North Korea
            "Korean Demilitarized Zone (north)": "North Korea",
            "North Korea": "North Korea",
            # United Kingdom
            "Northern Ireland": "United Kingdom",
            "Scotland": "United Kingdom",
            "Wales": "United Kingdom",
            "England": "United Kingdom",
            # Somalia
            "Puntland": "Somalia",
            "Somalia": "Somalia",
            "Somaliland": "Somalia",
            # Serbia
            "Serbia": "Serbia",
            "Vojvodina" : "Serbia",
            # Tanzania
            "Zanzibar": "Tanzania",
            "Tanzania": "Tanzania",
        }
        self.df.reset_index(inplace=True, drop=True)
        self.df["FINAL_GEOUNIT"] = self.df["GEOUNIT"].map(d_map)  # Initializing column as empty
        m = self.df["FINAL_GEOUNIT"].isna()
        self.df.loc[m, "FINAL_GEOUNIT"] = self.df.loc[m, "GEOUNIT"]
        return self.df


    def remove_lakes(
            self, 
            gdf_lake: gpd.GeoDataFrame,
            gdf_nolake: gpd.GeoDataFrame,
        ) -> gpd.GeoDataFrame:
        out: List[pd.DataFrame] = []
        pbar = tqdm.tqdm(enumerate(gdf_lake["GEOUNIT"].sort_values().items()), desc="")
        nrows: int = len(gdf_lake)
        for j, (idx, country_name) in pbar:
            pbar.set_description(f"Removing lakes: {country_name} ({j + 1} / {nrows})")

            df_country_lake: gpd.GeoDataFrame = gdf_lake[gdf_lake["GEOUNIT"] == country_name]
            sov: str = df_country_lake["SOVEREIGNT"].iloc[0]
            df_country_no_lake: gpd.GeoDataFrame = gdf_nolake[gdf_nolake["SOVEREIGNT"] == sov]
            if df_country_no_lake.empty:
                print(f"No no-lake data for {country_name} (sovereignty = {sov})")
            else:
                df = df_country_lake.overlay(
                    right=df_country_no_lake[["geometry"]],
                    how="intersection",
                    keep_geom_type=False
                )
                out.append(df)
        return pd.concat(out)

    def draw_all_countries(self) -> None:
        # We iterate on the sub-unit (separating France from its islands etc...)
        self.df.sort_values(by="FINAL_GEOUNIT", inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        pbar = tqdm.tqdm(enumerate(self.df["FINAL_GEOUNIT"].unique()), desc="")
        nrows: int = len(self.df)
        out_records: List[Dict[str, str]] = []
        for j, country_name in pbar:
            pbar.set_description(f"Drawing country outlines: {country_name} ({j} / {nrows})")
            df = self.df.loc[self.df["FINAL_GEOUNIT"] == country_name, :]

            fig, ax = plt.subplots(figsize=(10, 10))
            fig.patch.set_facecolor('black')
            ax.set_facecolor('black')
            df.plot(ax=ax, facecolor='white', edgecolor='white')
            ax.set_axis_off()
            # We remove all non-alphanum characters and replace spaces with underscore
            file_name: str = __class__.get_file_name(country_name)
            file_path: str = f"files/outlines/{file_name}.png"
            out_records.append({
                "outline_file_name": f"{file_name}.png",
                "outline_file_path": file_path,
                "FINAL_GEOUNIT": country_name,
            })
            # We write the image to a PIL Image
            buf = io.BytesIO()
            plt.savefig(
                buf, format='png', bbox_inches='tight', 
                pad_inches=0, facecolor='black', dpi=300)
            buf.seek(0)
            # We ensure that the image is square
            image: Image = Image.open(buf)
            image = __class__.square_image(image)
            image.save(file_path)
            time.sleep(1)
            try:
                plt.close()
            except:
                pass
        df_path: str = "files/df_outlines.csv"
        df = pd.DataFrame.from_records(out_records)
        df.to_csv(df_path, sep=";", index=False)
        
    @staticmethod
    def get_file_name(country_name: str) -> str:
        if len(country_name) == 0: raise ValueError("Empty country name")
        words: List[str] = country_name.split(" ")
        return "_".join(
            ["".join(
                [letter for letter in word if letter])
                for word in words
            ])
    
    @staticmethod
    def square_image(image: Image) -> Image:
        width: int; height: int
        width, height = image.size
        n: int = max(width, height)
        return __class__.pad_image(image, target_height=n, target_width=n)

    @staticmethod
    def pad_image(image: Image, target_width: int, target_height: int) -> Image:
        original_width: int; original_height: int
        original_width, original_height = image.size

        # Calculate the padding needed on each side
        left_padding: int = (target_width - original_width) // 2
        top_padding: int = (target_height - original_height) // 2
        right_padding: int = target_width - original_width - left_padding
        bottom_padding: int = target_height - original_height - top_padding

        # Create a new image with the target dimensions and a black background
        new_image: Image = Image.new("RGB", (target_width, target_height), color=(0, 0, 0))

        # Paste the original image onto the center of the new image
        new_image.paste(image, (left_padding, top_padding))

        return new_image


if __name__ == "__main__":
    shp_path_with_lakes: str = os.path.join("files", "raw", "ne_10m_admin_0_map_units", "ne_10m_admin_0_map_units.shp")
    # shp_path_with_lakes: str = os.path.join("files", "raw", "ne_10m_admin_0_countries_iso", "ne_10m_admin_0_countries_iso.shp")
    shp_path_without_lakes: str = os.path.join("files", "raw", "ne_10m_admin_0_countries_lakes", "ne_10m_admin_0_countries_lakes.shp")
    
    od = OutlineDrawer(
        path_lake=shp_path_with_lakes,
        path_no_lake=shp_path_without_lakes)
