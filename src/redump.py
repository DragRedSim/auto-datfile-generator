#!/usr/bin/python
import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime, sleep
from utils.handler import dat_handler, dat_descriptor

from utils.handler import retool_interface
import requests
from io import BytesIO

class redump(dat_handler):
    SOURCE_ID           = "redump"
    AUTHOR              = "Redump.org"
    URL_HOME            = "http://redump.org/"
    URL_DOWNLOADS       = "http://redump.org/downloads/"
    XML_TYPES_WITH_ZIP  = {'': True, 'source': False, 'retool': True}
    regex = {
        "datfile"  : r'<a href=\"/datfile/(.*?)\">',
        "datfile_bios"  : r'<a href=\"/datfile/(.{0,10}-bios)/?\">BIOS Datfile</a>',
        "date"     : r'\) \(([\d\- ]*?)\)\.(?:dat|zip)',
        "name"     : r'filename="(.*?) Datfile',
        "filename" : r'filename="(.*?)"',
        "trim_filename" : r'filename=\"(.*?) Datfile \(\d+\) \([\d\s-]+\)(.{4})\"',
        "filename_from_header": r'filename=\"(.*?\)\.(?:dat|zip))'
    }
    retool_caller = retool_interface(["--exclude", "aAbcdPu", "-y"])

    def find_dats(self) -> list:
        failed_reqs = 0
        for i in range(1, 10+1):
            try:
                print(f"Trying to download DATs list page from Redump, try {i} of 10")
                download_page = requests.get(self.URL_DOWNLOADS, timeout=8) #Redump web server sets Keep-Alive timeout to 5, so this is more than enough
                if (download_page.status_code != 200):
                    download_page.raise_for_status()
                else:
                    print("Collected Redump DATs")
                    dat_files = re.findall(self.regex["datfile"], download_page.text)
                    dat_files_fullpath = []
                    for f in dat_files:
                        dat_files_fullpath.append(self.URL_HOME + "datfile/" + f)
                    return dat_files_fullpath
            except:
                failed_reqs+=1
                if failed_reqs >= 10:
                    raise ConnectionError
        
    def pack_xml_dat_to_all(self, filename_in_zip, dat_tree, orig_url="", dat_path=""):
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
        if 'retool' in self.container_set:
            self.retool_caller.retool(self, dat_path, dat_data)
        return
    
    def pack_clr_dat_to_all(self, filename_in_zip, dat_content, orig_url=""):
        from utils.clrmamepro_dat_parser import CMP_Dat_Parser
        parser = CMP_Dat_Parser(dat_content)
        header = parser.get_header()
        dat_data = dat_descriptor(filename=filename_in_zip,
                                  title=header['name'],
                                  date=datetime.strptime(header['version'], "%Y-%m-%d"),
                                  version=header['version'],
                                  url=self.container_set[''].zip_url,
                                  desc=header['description'])
        self.pack_single_dat('', dat_content, dat_data, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date}")
        if 'source' in self.container_set:
            dat_data_source = dat_data.copy(url=orig_url, desc=f"{dat_data.desc} - Direct Download from {self.URL_DOWNLOADS}")
            self.pack_single_dat(xml_id="source", dat_tree=dat_content, dat_data=dat_data_source, comment=f"Downloaded directly from {self.URL_DOWNLOADS}")
        #Retool cannot process CLR dats, so there is no need to pass them through here
        
    def process_all_dats(self):
        dat_list = self.find_dats()
        if type(dat_list) == None:
            raise(ConnectionError)
            sys.exit()

        for dat in dat_list:
            print(f"Downloading {dat}")

            response = requests.get(dat, timeout=30)
            content_header = response.headers["Content-Disposition"]
            
            try:
                version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d %H-%M-%S")
            except ValueError:
                try:
                    version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d")
                except Exception as e:
                    raise(e)                  
            
            # XML name & description
            temp_name = re.findall(self.regex["trim_filename"], content_header)[0][0]
            # trim the - from the end (if exists)
            if temp_name.endswith(" -"):
                temp_name = temp_name[:-2]
            elif temp_name.endswith("BIOS"):
                temp_name = temp_name + " Images"
            if response.headers["Content-Type"] == "application/zip":
                # extract datfile from zip to store in the DB zip
                zipdata = BytesIO()
                zipdata.write(response.content)
                with zipfile.ZipFile(zipdata) as zf:
                    dat_filenames = [f for f in zf.namelist() if f.endswith("dat")]
                    for df in dat_filenames:
                        dat_tree = ET.fromstring(zf.read(df))
                        if 'retool' in self.container_set:
                            dat_file = zf.extract(df)
                        self.dat_date = datetime.strftime(version_date, "%Y-%m-%d")
                        self.pack_xml_dat_to_all(df, dat_tree, dat, dat_file or None)
                        if dat_file:
                            os.unlink(dat_file)
                            dat_file = None
            else:
                # add datfile to DB zip file
                dat_content = response.text
                self.dat_date = datetime.strftime(version_date, "%Y-%m-%d")
                if dat_content[:12] == "clrmamepro (":
                    # This is a CLRMamePro dat, not a traditional XML dat.
                    self.pack_clr_dat_to_all(re.findall(self.regex['filename_from_header'], content_header)[0], dat_content, dat)
                else:
                    dat_tree = ET.fromstring(dat_content)
                    if 'retool' in self.container_set:
                        with open(f"{dat.name}.dat", 'w') as dat_file:
                            dat_file.write(dat_content)
                    self.pack_xml_dat_to_all(dat.name, dat_tree, dat.url, f"{dat.name}.dat" if os.path.exists(f"{dat.name}.dat") else None)
                    if 'retool' in self.container_set:
                        os.unlink(f"{dat.name}.dat")
            print(flush=True)
            #sleep(1)

        # store clrmamepro XML file
        self.export_containers()

        print("Finished")

if __name__ == "__main__":
    try:
        redump_packer = redump()
        redump_packer.process_all_dats()
    except KeyboardInterrupt:
        pass
