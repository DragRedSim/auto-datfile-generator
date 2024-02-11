import os, re
import xml.etree.ElementTree as ET
import zipfile, requests, types
from io import BytesIO
from time import gmtime, strftime
from github import Auth, Github
from handler import dat_handler, dat_data

class fbneo(dat_handler):
    AUTHOR              = "FBNeo Team"
    URL_HOME            = "http://github.com/libretro/FBNeo"
    URL_DOWNLOADS       = "http://github.com/libretro/FBNeo/dats/"
    CREATE_SOURCE_PKG   = True
    XML_FILENAME        = "fbneo.xml"
    ZIP_FILENAME        = "fbneo.zip"
    regex = {
        "platform_name" : r'XML, ([^/\\]*?)(?: Games)? only\)',
    }

    def _find_dats(self) -> list:
        print("Starting to find dats")
        github_conn = Github() #anonymous access
        r = github_conn.get_repo("libretro/FBNeo")
        dat_files = [f for f in r.get_contents("dats") if f.type == 'file']
        print(f"Found {len(dat_files)} files.")
        return dat_files

    def handle_file(self, dat):
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(self.tag_clrmamepro, "datfile")

        # XML version
        ET.SubElement(tag_datfile, "version").text = dat.version

        # XML name & description
        # trim the - from the end (if exists)
        ET.SubElement(tag_datfile, "name").text = dat.title
        ET.SubElement(tag_datfile, "description").text = f'FinalBurn Neo - {re.search(self.regex["platform_name"], dat.filename).group(1)} - updated {dat.date.strftime("%Y-%m-%d %H:%M")}'

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

        if (self.CREATE_SOURCE_PKG): 
            tag_datfile_source = ET.SubElement(self.tag_clrmamepro_source, "datfile")
            ET.SubElement(tag_datfile_source, "version").text = tag_datfile.find("version").text
            ET.SubElement(tag_datfile_source, "name").text = tag_datfile.find("name").text
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

            response = requests.get(dat.download_url)
            filepath = os.path.abspath(dat.name)
            
            if dat.download_url.endswith(".zip"):
                # extract datfile from zip to store in the DB zip
                zipdata = BytesIO()
                zipdata.write(response.content)
                with zipfile.ZipFile(zipdata) as zf:
                    dat_filenames = [f for f in archive.namelist() if f.endswith("dat")]
                    for df in dat_filenames:
                        self.zip_object.writestr(df, archive.read(df))
                        dat_obj = dat_data(filename=df, title=ET.fromstring(zf.read(df)).find("header").find("name").text, version=ET.fromstring(zf.read(df)).find("header").find("version").text, date=dat.last_modified_datetime, url=dat.download_url)
                        self.handle_file(dat_obj)
            else:
                # add datfile to DB zip file
                self.zip_object.writestr(dat.name, response.text)
                #dat_obj.content = response.text
                dat_obj = dat_data(filename=dat.name, title=ET.fromstring(response.text).find("header").find("name").text, version=ET.fromstring(response.text).find("header").find("version").text, date=dat.last_modified_datetime, url=dat.download_url)
                self.handle_file(dat_obj)
                
            print(flush=True)

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
    fbneo_packer = fbneo()
    fbneo_packer.update_XML()
except KeyboardInterrupt:
    pass
