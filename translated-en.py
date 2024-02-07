import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime
from internetarchive import get_item, get_files
from handler import dat_handler, dat_data

class translated_en(dat_handler):
    AUTHOR              = "ChadMaster (archive.org)"
    URL_HOME            = "https://archive.org/details/En-ROMs"
    URL_DOWNLOADS       = "https://archive.org/download/En-ROMs/DATs/"
    CREATE_SOURCE_PKG   = True
    XML_FILENAME        = "translated-en.xml"
    ZIP_FILENAME        = "translated-en.zip"
    regex = {
        #select anything after a directory separator that has "[T-En] Collection"
        "dat_name"      : r'([^/\\]*? \[T-En\] Collection)',
        "platform_name" : r'([^/\\]*?) \[T-En\] Collection',
        "date"          : r'\((\d{1,2}-\d{1,2}-\d{4})\)'
    }
    
    def _find_dats(self) -> list:
        print("Starting to find dats")
        dat_files = [f for f in get_files("En-ROMs", glob_pattern="DATs/*")]
        print(f"Found {len(dat_files)} files.")
        return dat_files

    def handle_file(self, dat):
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(self.tag_clrmamepro, "datfile")
        
        # XML version
        ET.SubElement(tag_datfile, "version").text = dat.date.strftime("%Y-%m-%d")

        # XML name & description
        # trim the - from the end (if exists)
        ET.SubElement(tag_datfile, "name").text = re.search(self.regex["dat_name"], dat.name).group(1)
        ET.SubElement(tag_datfile, "description").text = re.search(self.regex["platform_name"], dat.name).group(1) + " - English Translations"

        # URL tag in XML
        ET.SubElement(tag_datfile, "url").text = self.ZIP_URL

        # File tag in XML
        ET.SubElement(tag_datfile, "file").text = dat.name

        # Author tag in XML
        ET.SubElement(tag_datfile, "author").text = self.AUTHOR

        # Comment XML tag
        ET.SubElement(tag_datfile, "comment").text = "Downloaded as part of an archive pack, generated " + self.pack_gen_date

        # Get the DAT file
        print(f"DAT filename: {dat.name}")
        
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

            dat.download()
            filepath = os.path.abspath(dat.name)
            
            #dat_obj = dat_data(name=dat.name, date=datetime.fromtimestamp(dat.mtime), url=dat.url)
            dat_obj = dat_data(name=dat.name, date=datetime.strptime(re.search(self.regex["date"], dat.name).group(), "(%d-%m-%Y)"), url=dat.url)
            
            if (filepath.endswith(".zip")):
                with zipfile.ZipFile(filepath, 'r') as zf:
                    #get a list of all filenames in the zip file, filter to only ones ending in '.dat'
                    dat_filename = list(filter(lambda f: f.endswith('.dat'), zf.namelist()))
                    for df in dat_filename:
                        dat_obj.name = df
                        self.zip_object.writestr(df, zf.read(df))
                        self.handle_file(dat_obj)
            else:
                self.zip_object.write(filepath, dat.filename)
                self.handle_file(dat_obj)
                    
            print(flush=True)
            os.remove(filepath)

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
    t_en_packer = translated_en()
    t_en_packer.update_XML()
except KeyboardInterrupt:
    pass
