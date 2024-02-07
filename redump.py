import re
import xml.etree.ElementTree as ET
import zipfile, requests
from datetime import datetime
from io import BytesIO
from time import gmtime, strftime, sleep
from handler import dat_handler, dat_data

class redump(dat_handler):
    AUTHOR              = "Redump.org"
    URL_HOME            = "http://redump.org/"
    URL_DOWNLOADS       = "http://redump.org/downloads/"
    CREATE_SOURCE_PKG   = True
    XML_FILENAME        = "redump.xml"
    ZIP_FILENAME        = "redump.zip"
    regex = {
        "datfile"  : r'<a href="/datfile/(.*?)">',
        "date"     : r"\) \((.*?)\)\.",
        "name"     : r'filename="(.*?) Datfile',
        "filename" : r'filename="(.*?)"',
        "trim_filename" : r'filename=\"(.*?) Datfile \(\d+\) \([\d\s-]+\)(.{4})\"'
    }

    def _find_dats(self) -> list:
        for i in range(0, 10):
            try:
                download_page = requests.get(self.URL_DOWNLOADS, timeout=30)
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
                pass
            else:
                raise ConnectionError

    def handle_file(self, dat):
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(self.tag_clrmamepro, "datfile")
        
        # XML version
        ET.SubElement(tag_datfile, "version").text = dat.date.strftime("%Y-%m-%d %H:%M")

        # XML name & description
        print(f"DAT filename: {dat.shortname}")
        ET.SubElement(tag_datfile, "name").text = dat.name
        ET.SubElement(tag_datfile, "description").text = dat.shortname[:-4]

        # URL tag in XML
        ET.SubElement(tag_datfile, "url").text = self.ZIP_URL

        # File tag in XML
        ET.SubElement(tag_datfile, "file").text = dat.shortname or dat.name

        # Author tag in XML
        ET.SubElement(tag_datfile, "author").text = self.AUTHOR

        # Command XML tag
        ET.SubElement(tag_datfile, "comment").text = "Downloaded as part of an archive pack, generated " + self.pack_gen_date
        
        if (self.CREATE_SOURCE_PKG): 
            tag_datfile_source = ET.SubElement(self.tag_clrmamepro_source, "datfile")
            ET.SubElement(tag_datfile_source, "version").text = tag_datfile.find("version").text
            ET.SubElement(tag_datfile_source, "name").text = dat.name
            ET.SubElement(tag_datfile_source, "description").text = tag_datfile.find("description").text + f" - Direct Download from {self.URL_DOWNLOADS}"
            ET.SubElement(tag_datfile_source, "url").text = dat.url
            ET.SubElement(tag_datfile_source, "file").text = tag_datfile.find("file").text
            ET.SubElement(tag_datfile_source, "author").text = tag_datfile.find("author").text
            ET.SubElement(tag_datfile_source, "comment").text = f"Downloaded from {self.URL_DOWNLOADS}"
        
        return None
        
    def update_XML(self):
        dat_list = self._find_dats()

        for dat in dat_list:
            print(f"Downloading {dat}")

            response = requests.get(dat, timeout=30)
            content_header = response.headers["Content-Disposition"]
            
            # Get the DAT file
            datfile_name = ''.join(re.findall(self.regex["trim_filename"], content_header)[0])
            
            try:
                version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d %H-%M-%S")
            except:
                version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d")
            dat_obj = dat_data(name=datfile_name, date=version_date, url=dat)
            # XML name & description
            temp_name = re.findall(self.regex["trim_filename"], content_header)[0][0]
            # trim the - from the end (if exists)
            if temp_name.endswith(" -"):
                temp_name = temp_name[:-2]
            elif temp_name.endswith("BIOS"):
                temp_name = temp_name + " Images"
            dat_obj.shortname = temp_name+".dat"
            if response.headers["Content-Type"] == "application/zip":
                # extract datfile from zip to store in the DB zip
                zipdata = BytesIO()
                zipdata.write(response.content)
                archive = zipfile.ZipFile(zipdata)
                datfile_names_in_zip = [f for f in archive.namelist() if f.endswith("dat")]
                for f in datfile_names_in_zip:
                    dat_obj.name = f[:-4]
                    self.zip_object.writestr(dat_obj.shortname, archive.read(f))
                    self.handle_file(dat_obj)
            else:
                # add datfile to DB zip file
                self.zip_object.writestr(datfile_name, response.text)
                self.handle_file(dat_obj)
            print(flush=True)
            sleep(1)

        # store clrmamepro XML file
        xmldata = ET.tostring(self.tag_clrmamepro).decode()
        with open(self.XML_FILENAME, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xmldata)
            
        if (self.CREATE_SOURCE_PKG):
            xmldata_archive = ET.tostring(self.tag_clrmamepro_source).decode()
            with open(self.XML_SOURCE_FILENAME, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(xmldata_archive)

        print("Finished")

try:
    redump_packer = redump()
    redump_packer.update_XML()
except KeyboardInterrupt:
    pass
