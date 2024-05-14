import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime
from utils.handler import dat_handler, dat_descriptor

from github import Auth, Github
from io import BytesIO
import requests, types

class fbneo_specialty(dat_handler):
    SOURCE_ID           = "fbneo-specialty"
    AUTHOR              = "FinalBurn Neo"
    URL_HOME            = "http://github.com/libretro/FBNeo"
    URL_DOWNLOADS       = "http://github.com/libretro/FBNeo/dats/"
    XML_TYPES_WITH_ZIP  = {"": True}
    regex = {
        "platform_name" : r'XML, ([^/\\]*?)(?: Games)? only\)',
        "platform_driver" : r'',
    }
    BREAKOUT_PLATFORMS  = {
        # set these to key/value pairs of type str/str
        # key is what you would like to name the platform as
        # value is the sourcefile value in the arcade DAT
        "CPS1": "capcom/d_cps1.cpp",
        "CPS2": "capcom/d_cps2.cpp",
        "CPS3": "cps3/d_cps3.cpp",
    }

    def find_dats(self) -> list:
        print("Starting to find dats")
        if os.getenv("GITHUB_TOKEN"):
            a = Auth.Token(os.getenv("GITHUB_TOKEN"))
        else:
            a = None
        github_conn = Github(auth=a)
        r = github_conn.get_repo("libretro/FBNeo")
        all_dat_files = [f for f in r.get_contents("dats") if f.type == 'file']
        dat_files = list(filter(lambda dat: "arcade" in dat.name.lower(), all_dat_files))
        print(f"Found {len(dat_files)} files matching the search term \'arcade\'.")
        return dat_files
  
    def pack_xml_dat_to_all(self, filename_in_zip, dat_tree, orig_url=""):
        dat_data = dat_descriptor(filename=filename_in_zip,
                                  title=dat_tree.find("header").find("name").text,
                                  desc=dat_tree.find("header").find("description").text, 
                                  date=self.dat_date, 
                                  url=self.container_set[''].zip_url,
                                  version=dat_tree.find("header").find("version").text,
                                  dtd='<?xml version="1.0"?>\n<!DOCTYPE datafile PUBLIC "-//FinalBurn Neo//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n'
            )
        self.pack_single_dat(xml_id="", dat_tree=dat_tree, dat_data=dat_data, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date}")

    def process_all_dats(self):
        dat_list = self.find_dats() #should return a list of one element, the arcade dat

        dat = dat_list[0]
        print(f"Downloading {dat}")

        response = requests.get(dat.download_url)
        filepath = os.path.abspath(dat.name)
        with open(filepath, "wb") as save:
            save.write(response.content) #just as a safety, to read it back later if the response variable gets clobbered
            
        for plat in self.BREAKOUT_PLATFORMS.items():
            #plat[0] = name
            #plat[1] = sourcefile value
            print(f"Now creating {plat[0]} DAT using sourcefile value \"{plat[1]}\"")
            arcade_dat = ET.fromstring(response.text)
            for game in arcade_dat.findall("game"):
                if game.get("sourcefile") != plat[1]:
                    arcade_dat.remove(game)
            header = arcade_dat.find("header")
            dat_name = header.find("name")
            dat_name.text = f"FBN - Arcade Subset - {plat[0]}"
            dat_desc = header.find("description")
            dat_desc.text = f"FinalBurn Neo - Arcade Games - {plat[0]} - Sourcefile: \"{plat[1]}\""
            dat_version = header.find("version")
            dat_version.text = dat.last_modified_datetime.strftime("%Y-%m-%d %H:%M")
            
            dat_data = dat_descriptor(filename=f'{dat_name.text}.dat', title=dat_name.text, date=dat.last_modified_datetime, url=None, desc=dat_desc.text)
            ET.indent(arcade_dat)
            
            self.dat_date = datetime.strftime(dat.last_modified_datetime, "%Y-%m-%d")
            self.pack_xml_dat_to_all(dat_name.text, arcade_dat)
                
            print(flush=True)

        # store clrmamepro XML file
        self.export_containers()
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except PermissionError:
                pass
        print("Finished")

if __name__ == "__main__":
    try:
        fbneo_specialty_packer = fbneo_specialty()
        fbneo_specialty_packer.process_all_dats()
    except KeyboardInterrupt:
        pass
