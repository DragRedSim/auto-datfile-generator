#!/usr/bin/python
import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime
from utils.handler import dat_handler, dat_descriptor

from github import Auth, Github
from io import BytesIO
import requests, types

class fbneo(dat_handler):
    SOURCE_ID           = "fbneo"
    AUTHOR              = "FBNeo Team"
    URL_HOME            = "http://github.com/libretro/FBNeo"
    URL_DOWNLOADS       = "http://github.com/libretro/FBNeo/dats/"
    XML_TYPES_WITH_ZIP  = {"": True, "source": False, "versionasdate": True}
    regex = {
        "platform_name" : r'XML, ([^/\\]*?)(?: Games)? only\)',
    }

    def find_dats(self) -> list:
        print("Starting to find dats")
        if os.getenv("GITHUB_TOKEN"):
            a = Auth.Token(os.getenv("GITHUB_TOKEN"))
        else:
            a = None
        github_conn = Github(auth=a)
        r = github_conn.get_repo("libretro/FBNeo")
        dat_files = [f for f in r.get_contents("dats") if f.type == 'file']
        print(f"Found {len(dat_files)} files.")
        return dat_files
    
    def pack_xml_dat_to_all(self, filename_in_zip, dat_tree, orig_url=""):
        dat_data = dat_descriptor(filename=filename_in_zip,
                                  title=dat_tree.find("header").find("name").text,
                                  desc=dat_tree.find("header").find("description").text, 
                                  date=self.dat_date, 
                                  url=self.container_set[''].zip_url,
                                  version=dat_tree.find("header").find("version").text
            )
        self.pack_single_dat(xml_id="", dat_tree=dat_tree, dat_data=dat_data, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date}")
        if 'source' in self.container_set:
            dat_data_source = dat_data.copy(url=orig_url, desc=f"{dat_data.desc} - Direct Download from {self.URL_DOWNLOADS}")
            self.pack_single_dat(xml_id="source", dat_tree=dat_tree, dat_data=dat_data_source, comment=f"Downloaded directly from {self.URL_DOWNLOADS}")
        if 'versionasdate' in self.container_set:
            new_ver = self.dat_date
            dat_tree.find("header").find("version").text = new_ver
            dat_data_versionasdate = dat_data.copy(version=new_ver, url=self.container_set["versionasdate"].zip_url)
            self.pack_single_dat(xml_id="versionasdate", dat_tree=dat_tree, dat_data=dat_data_versionasdate, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date} - version overwritten as date")
        return

    def process_all_dats(self):
        dat_list = self.find_dats()

        for dat in dat_list:
            print(f"Downloading {dat}")

            response = requests.get(dat.download_url)
            filepath = os.path.abspath(dat.name)
            
            if dat.download_url.endswith(".zip"):
                # extract datfile from zip to store in the DB zip
                zipdata = BytesIO()
                zipdata.write(response.content)
                with zipfile.ZipFile(zipdata) as zf:
                    dat_filenames = [f for f in archive.namelist() if f.endswith("dat")]
                    for df in dat_filenames:
                        dat_tree = ET.fromstring(zf.read(df))
                        self.dat_date = datetime.strftime(dat.last_modified_datetime, "%Y-%m-%d")
                        self.pack_xml_dat_to_all(df, dat_tree, dat.url)
            else:
                dat_content = response.text
                self.dat_date = datetime.strftime(dat.last_modified_datetime, "%Y-%m-%d")
                dat_tree = ET.fromstring(dat_content)
                self.pack_xml_dat_to_all(dat.name, dat_tree, dat.url)
                
            print(flush=True)

        # store clrmamepro XML file
        self.export_containers()
        print("Finished")
        return

if __name__ == "__main__":
    try:
        fbneo_packer = fbneo()
        fbneo_packer.process_all_dats()
    except KeyboardInterrupt:
        pass
