import os, re
import xml.etree.ElementTree as ET
import zipfile, requests, types
from io import BytesIO
from time import gmtime, strftime
from github import Auth, Github
from handler import dat_handler, dat_data

class fbneo_specialty(dat_handler):
    AUTHOR              = "FinalBurn Neo"
    URL_HOME            = "http://github.com/libretro/FBNeo"
    URL_DOWNLOADS       = "http://github.com/libretro/FBNeo/dats/"
    CREATE_SOURCE_PKG   = False #since we're extracting parts of the Arcade DAT, these cannot be provided as direct links
    XML_FILENAME        = "fbneo-specialty.xml"
    ZIP_FILENAME        = "fbneo-specialty.zip"
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

    def _find_dats(self) -> list:
        print("Starting to find dats")
        github_conn = Github() #anonymous access
        r = github_conn.get_repo("libretro/FBNeo")
        all_dat_files = [f for f in r.get_contents("dats") if f.type == 'file']
        dat_files = list(filter(lambda dat: "arcade" in dat.name.lower(), all_dat_files))
        print(f"Found {len(dat_files)} files matching the search term \'arcade\'.")
        return dat_files

    def handle_file(self, dat):
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(self.tag_clrmamepro, "datfile")

        # XML version
        ET.SubElement(tag_datfile, "version").text = dat.date.strftime("%Y-%m-%d %H:%M")

        # XML name & description
        # trim the - from the end (if exists)
        ET.SubElement(tag_datfile, "name").text = dat.title
        ET.SubElement(tag_datfile, "description").text = f"FinalBurn Neo - {dat.desc[31:]} - Arcade Extraction"

        # URL tag in XML
        ET.SubElement(tag_datfile, "url").text = self.ZIP_URL

        # File tag in XML
        ET.SubElement(tag_datfile, "file").text = dat.filename

        # Author tag in XML
        ET.SubElement(tag_datfile, "author").text = self.AUTHOR

        # Comment XML tag
        ET.SubElement(tag_datfile, "comment").text = "Downloaded as part of an archive pack, generated " + self.pack_gen_date

        # Get the DAT file
        print(f"DAT filename: {dat.filename}")
            
        return None

    def update_XML(self):
        dat_list = self._find_dats() #should return a list of one element, the arcade dat

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
            
            dat_obj = dat_data(filename=f'{dat_name.text}.dat', title=dat_name.text, date=dat.last_modified_datetime, url=None, desc=dat_desc.text)
            ET.indent(arcade_dat)
            
            # add datfile to DB zip file
            self.zip_object.writestr(dat_obj.filename, 
                                     '<?xml version="1.0"?>\n<!DOCTYPE datafile PUBLIC "-//FinalBurn Neo//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n'
                                     +ET.tostring(arcade_dat).decode())
            #dat_obj.content = response.text
            self.handle_file(dat_obj)
                
            print(flush=True)

        # store clrmamepro XML file
        ET.indent(self.tag_clrmamepro)
        xmldata = ET.tostring(self.tag_clrmamepro).decode()
        with open(self.XML_FILENAME, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xmldata)

        print("Finished")

try:
    fbneo_specialty_packer = fbneo_specialty()
    fbneo_specialty_packer.update_XML()
except KeyboardInterrupt:
    pass
