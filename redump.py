import re
import xml.etree.ElementTree as ET
import zipfile, requests
from datetime import datetime
from io import BytesIO
from time import gmtime, strftime, sleep
from handler import dat_handler, dat_data
import subprocess

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
        version = dat.date.strftime("%Y-%m-%d %H-%M-%S")
        description = dat.filename[:-4]
        create_XML_entry(datfile=self.tag_clrmamepro, 
                        version=version,
                        name=dat.title,
                        description=description,
                        url=self.ZIP_URL,
                        file=dat.filename,
                        author=self.AUTHOR,
                        comment="Downloaded as part of an archive pack, generated " + self.pack_gen_date)
        
        if (self.CREATE_SOURCE_PKG): 
            create_XML_entry(datfile=self.tag_clrmamepro_source, 
                             version=version,
                             name=dat.title,
                             description=f"{description} - Direct Download from {self.URL_DOWNLOADS}",
                             url=dat.url,
                             file=dat.filename,
                             author=self.AUTHOR,
                             comment=f"Downloaded from {self.URL_DOWNLOADS}")

        return None
        
    def update_XML(self):
        dat_list = self._find_dats()

        for dat in dat_list:
            print(f"Downloading {dat}")

            response = requests.get(dat, timeout=30)
            content_header = response.headers["Content-Disposition"]
            
            try:
                version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d %H-%M-%S")
            except:
                version_date = datetime.strptime(re.findall(self.regex["date"], content_header)[0], "%Y-%m-%d")
            
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
                        dat_obj = dat_data(filename=df, title=ET.fromstring(zf.read(df)).find("header").find("name").text, date=version_date, url=dat)
                        self.zip_object.writestr(df, zf.read(df))
                        self.handle_file(dat_obj)
                        with open(df, "wb") as retool_dat_file:
                            retool_dat_file.write(zf.read(df))
                        retool = subprocess.check_output(['pipenv', 'run', 'python', './retool/retool.py', df]).decode()
                        os.unlink(df)
                        redump_zip.writestr(f'{ET.fromstring(retool).find("header").find("name").text}.dat', retool)
                        
                        print("Added Retool")
            else:
                # add datfile to DB zip file
                dat_obj = dat_data(filename=re.findall(self.regex["filename"], content_header)[0], title=temp_name, date=version_date, url=dat)
                self.zip_object.writestr(dat_obj.filename, response.text)
                self.handle_file(dat_obj)
            print(flush=True)
            sleep(1)

        # store clrmamepro XML file
        ET.indent(self.tag_clrmamepro)
        xmldata = ET.tostring(self.tag_clrmamepro).decode()
        with open(self.XML_FILENAME, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xmldata)
            
        if (self.CREATE_SOURCE_PKG):
            ET.indent(self.tag_clrmamepro_source)
            xmldata_archive = ET.tostring(self.tag_clrmamepro_source).decode()
            with open(self.XML_SOURCE_FILENAME, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(xmldata_archive)

        print("Finished")

try:
    with zipfile.ZipFile("redump-retool.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as retool_zip:
        tag_clrmamepro_retool = ET.Element("clrmamepro")
        redump_packer = redump()
        redump_packer.update_XML()
except KeyboardInterrupt:
    pass
