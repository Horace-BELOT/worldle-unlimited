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
import geopandas as gpd
import tqdm
import matplotlib
import matplotlib.pyplot as plt
from typing import List, Any
matplotlib.use('Agg')

class OutlineDrawer:
    """
    Draws outline from naturalearthdata.com data.
    https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/
    """

    def __init__(
            self, 
            path_lake: str,
            path_no_lake: str,    
        ) -> None:
        print("Loading naturalearthdata.com data")
        self.gdf_lake: gpd.GeoDataFrame = gpd.read_file(path_lake)
        self.gdf_nolake: gpd.GeoDataFrame = gpd.read_file(path_no_lake)
        self.draw_all_countries()

    def draw_all_countries(self) -> None:
        # We iterate on the sub-unit (separating France from its islands etc...)
        pbar = tqdm.tqdm(enumerate(self.gdf_lake["GEOUNIT"].sort_values().items()), desc="")
        nrows: int = len(self.gdf_lake)
        for j, (idx, country_name) in pbar:
            pbar.set_description(f"Drawing country outlines: {country_name} ({j} / {nrows})")

            df_country_lake: gpd.GeoDataFrame = self.gdf_lake[self.gdf_lake["GEOUNIT"] == country_name]
            sov: str = df_country_lake["SOVEREIGNT"].iloc[0]
            df_country_no_lake: gpd.GeoDataFrame = self.gdf_lake[self.gdf_lake["SOVEREIGNT"] == sov]
            df = df_country_lake.overlay(right=df_country_no_lake, how="intersection")

            fig, ax = plt.subplots(figsize=(10, 10))
            fig.patch.set_facecolor('black')
            ax.set_facecolor('black')
            df.plot(ax=ax, facecolor='white', edgecolor='white')
            ax.set_axis_off()
            # We remove all non-alphanum characters and replace spaces with underscore
            file_name: str = __class__.get_file_name(country_name)
            file_path: str = f"files/outlines/{file_name}.png"
            self.gdf_lake.loc[idx, "file_name"] = file_name  # Saving file name to dataframe
            # We write the image to a PIL Image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, facecolor='black', dpi=300)
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
        df_path: str = "files/outlines/DATAFRAME.csv"
        self.gdf_lake.to_csv(df_path, sep=";", index=False)
        
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
    shp_path_without_lakes: str = os.path.join("files", "raw", "ne_10m_admin_0_countries_lakes", "ne_10m_admin_0_countries_lakes.shp")
    
    od = OutlineDrawer(
        path_lake=shp_path_with_lakes,
        path_no_lake=shp_path_without_lakes)
