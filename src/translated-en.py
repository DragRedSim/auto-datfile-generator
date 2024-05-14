#!/usr/bin/python
import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime
from utils.handler import dat_handler, dat_descriptor

import internetarchive as IA

class translated_en(dat_handler):
    SOURCE_ID           = "translated-en"
    AUTHOR              = "ChadMaster (archive.org)"
    URL_HOME            = "https://archive.org/details/En-ROMs"
    URL_DOWNLOADS       = "https://archive.org/download/En-ROMs/DATs/"
    XML_TYPES_WITH_ZIP  = {"": True, "source": False, "versionfix": True}
    #regex = {
    #    #select anything after a directory separator that has "[T-En] Collection"
    #    "dat_name"      : r'([^/\\]*? \[T-En\] Collection)',
    #    "platform_name" : r'([^/\\]*?) \[T-En\] Collection',
    #    "date"          : r'\((\d{1,2}-\d{1,2}-\d{4})\)'
    #}
    
    def find_dats(self) -> list:
        print("Starting to find dats")
        dat_files = [f for f in IA.get_files("En-ROMs", glob_pattern="DATs/*")]
        print(f"Found {len(dat_files)} files.")
        return dat_files

    #def handle_file(self, dat):
    #    # section for this dat in the XML file
    #    version = dat.date.strftime("%d-%m-%Y")
    #    description = f'{re.search(self.regex["platform_name"], dat.filename).group(1)} - English Translations (updated {dat.date.strftime("%Y-%m-%d")})'
    #    self.create_XML_entry(datfile=self.tag_clrmamepro, 
    #                    version=version,
    #                    name=dat.title,
    #                    description=description,
    #                    url=self.ZIP_URL,
    #                    file=dat.filename,
    #                    author=self.AUTHOR,
    #                    comment="Downloaded as part of an archive pack, generated " + self.pack_gen_date)
#
    #    print(f"DAT filename: {dat.filename}")
    #    
    #    if (self.CREATE_SOURCE_PKG): 
    #        self.create_XML_entry(datfile=self.tag_clrmamepro_source, 
    #                         version=version,
    #                         name=dat.title,
    #                         description=f"{description} - Direct Download from {self.URL_DOWNLOADS}",
    #                         url=dat.url,
    #                         file=dat.filename,
    #                         author=self.AUTHOR,
    #                         comment=f"Downloaded from {self.URL_DOWNLOADS}")
    #    return None
            
    #def pack_single_dat(self, xml_id: str, dat_tree, dat_data: dat_descriptor, comment: str = ""):
    #    if self.XML_TYPES_WITH_ZIP[xml_id] == True:
    #        self.add_dat_tree_to_zip(dat_data.filename, dat_tree, xml_id)
    #    self.add_dat_to_xml(dat_data, xml_id, comment)
    
    def pack_xml_dat_to_all(self, filename_in_zip, dat_tree, orig_url=""):
        dat_data = dat_descriptor(filename=filename_in_zip, 
                title=dat_tree.find("header").find("name").text,
                desc=dat_tree.find("header").find("description").text, 
                date=datetime.strptime(dat_tree.find("header").find("date").text, "%d-%m-%Y"), 
                url=self.container_set[''].zip_url,
                version=dat_tree.find("header").find("version").text
            )
        self.pack_single_dat(xml_id="", dat_tree=dat_tree, dat_data=dat_data, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date}")
        if 'source' in self.container_set:
            #create source XML
            dat_data_source = dat_data.copy(url=orig_url, desc=f"{dat_data.desc} - Direct Download from {self.URL_DOWNLOADS}")
            self.pack_single_dat(xml_id="source", dat_tree=dat_tree, dat_data=dat_data_source, comment=f"Downloaded directly from {self.URL_DOWNLOADS}")
        if 'versionfix' in self.container_set:
            #mangle version and pack
            new_ver = datetime.strptime(dat_tree.find("header").find("version").text, "%d-%m-%Y").strftime("%Y-%m-%d")
            dat_tree.find("header").find("version").text = new_ver
            dat_data_versionfix = dat_data.copy(version=new_ver, url=self.container_set["versionfix"].zip_url)
            self.pack_single_dat(xml_id="versionfix", dat_tree=dat_tree, dat_data=dat_data_versionfix, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date} (version fixed)")
        return
    
    def process_all_dats(self):
        dat_list = self.find_dats()
        for dat in dat_list:
            print(f"Downloading {dat}")
            dat.download()
            filepath = os.path.abspath(dat.name)
            if (filepath.endswith(".zip")):
                with zipfile.ZipFile(filepath, 'r') as zf:
                    #get a list of all filenames in the zip file, filter to only ones ending in '.dat'
                    dat_filenames = list(filter(lambda f: f.endswith('.dat'), zf.namelist()))
                    for df in dat_filenames:
                        dat_tree = ET.fromstring(zf.read(df))
                        self.pack_xml_dat_to_all(df, dat_tree, dat.url)        
            else:
                with open(filepath, "r") as df:
                    dat_tree = ET.fromstring(df.read())
                    self.pack_xml_dat_to_all(df, dat_tree, dat.url)
            print(flush=True)
            os.remove(filepath)

        # store clrmamepro XML file
        self.export_containers()
        print("Finished")
        return

if __name__ == "__main__":
    try:
        t_en_packer = translated_en()
        t_en_packer.process_all_dats()
    except KeyboardInterrupt:
        pass
