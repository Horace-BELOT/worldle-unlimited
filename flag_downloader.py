"""
Downloads flag data and save it the files/flags/* folder.
"""
import requests
import os

from bs4 import BeautifulSoup, Tag, NavigableString
import tqdm
from typing import List, Any, Dict, Tuple
import pandas as pd


class FlagDownloader:

    def __init__(
            self,
            flag_folder: str,
        ) -> None:
        """"""
        self.flagpedia_url: str = "https://flagpedia.net"
        self.flag_folder: str = flag_folder

    @staticmethod
    def download_image(url: str, save_path: str) -> None:
        response: requests.Response = requests.get(url)
        with open(save_path, "wb") as file:
            file.write(response.content)

    def parse_flagpedia(self):
        url: str = self.flagpedia_url + "/index"
        resp: requests.Response = requests.get(url=url)

        soup = BeautifulSoup(resp.content, 'html.parser')

        out_records: List[Dict[str, Any]] = []  # Will be used to build a data dictionary
        flag_grid: Tag = soup.find("ul", class_="flag-grid")
        for country_tag in tqdm.tqdm([k for k in flag_grid if isinstance(k, Tag)],
                                     desc="Downloading flags"):
            country_data: Dict[str, Any] = {}
            try:
                tag_with_href: Tag = [*country_tag][0]
                country_data["population"] = tag_with_href.attrs.get("data-population")
                country_data["area"] = tag_with_href.attrs.get("data-area")
                # We can build the url of the page of the specific country
                country_url: str = self.flagpedia_url + tag_with_href.attrs["href"]
                # We can get the country name
                tag_with_name: Tag = tag_with_href.find("span")
                country_name: str = tag_with_name.text
                country_data["name"] = country_name

                # We fetch the data of the subpage
                country_resp: requests.Response = requests.get(url=country_url)
                country_soup = BeautifulSoup(country_resp.content, 'html.parser')
                
                # We get the flag
                flag_holder: Tag = country_soup.find("p", class_="flag-detail")
                flag_holder = [k for k in flag_holder if isinstance(k, Tag)][0]
                img_tag: Tag = flag_holder.find("img")
                img_path: str = self.flagpedia_url + img_tag.attrs["src"]
                img_save_folder: str = os.path.join(self.flag_folder, f"{country_name}.png")
                __class__.download_image(img_path, img_save_folder)
                country_data["flag_file_path"] = img_save_folder
                country_data["flag_file_name"] = f"{country_name}.png"

                # Additional data
                table_soup: Tag = country_soup.find("table", class_="table-dl")

                # We can get the capital as well
                capital_city: str = str(table_soup.text).split("Capital city")[1]
                capital_city = capital_city.split("\n\n")[0].replace("\n", "")
                country_data["capital"] = capital_city

                # We can get the continent
                continent: str = str(table_soup.text).split("Continent")[1]
                continent = continent.split("\n\n")[0].replace("\n", "")
                country_data["continent"] = continent
            except:
                pass
            if country_data.get("name") is not None:
                out_records.append(country_data)
        
        df: pd.DataFrame = pd.DataFrame.from_records(out_records)
        df.to_csv("files/df_flags.csv", sep=";", index=False)
        return
    
if __name__ == "__main__":
    fd = FlagDownloader(flag_folder="files/flags")
    fd.parse_flagpedia()