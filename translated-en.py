import os, re
import xml.etree.ElementTree as ET
import zipfile
import datetime
from internetarchive import get_item, get_files

# Config
URL_HOME      = "http://archive.org/details/En-ROMs"
URL_DOWNLOADS = "https://archive.org/download/En-ROMs/DATs/"
XML_FILENAME  = "translated-en.xml"
XML_URL       = "https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/translated-en.zip"

regex = {
    #select anything after a directory separator that has "[T-En] Collection"
    "name"      : r'([^/\\]*?) \[T-En\] Collection',
}

def _find_dats():
    print("Starting to find dats")
    dat_files = [f for f in get_files("En-ROMs", glob_pattern="DATs\\*")]
    print(f"Found {len(dat_files)} files.")
    return dat_files

def update_XML():
    dat_list = _find_dats()

    # zip file to store all DAT files
    zip_object = zipfile.ZipFile("translated-en.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)

    # clrmamepro XML file
    tag_clrmamepro = ET.Element("clrmamepro")

    for dat in dat_list:
        print(f"Downloading {dat}")

        dat.download()
        filepath = os.path.abspath(dat.name)
        with zipfile.ZipFile(filepath, 'r') as zf:
            #get a list of all filenames in the zip file, filter to only ones ending in '.dat'
            dat_filename = list(filter(lambda f: f.endswith('.dat'), zf.namelist()))
            for df in dat_filename:
                
                # section for this dat in the XML file
                tag_datfile = ET.SubElement(tag_clrmamepro, "datfile")
                
                # XML version
                dat_date = datetime.datetime.utcfromtimestamp(dat.mtime).strftime("%Y-%m-%d %H:%M")
                ET.SubElement(tag_datfile, "version").text = dat_date

                # XML name & description
                temp_name = re.search(regex["name"], df).group(1)
                # trim the - from the end (if exists)
                ET.SubElement(tag_datfile, "name").text = temp_name + " [T-En]"
                ET.SubElement(tag_datfile, "description").text = temp_name + " - English Translations"

                # URL tag in XML
                ET.SubElement(tag_datfile, "url").text = XML_URL

                # File tag in XML
                original_filename = df
                filename = f"{original_filename[:-4]}.dat"
                ET.SubElement(tag_datfile, "file").text = filename

                # Author tag in XML
                ET.SubElement(tag_datfile, "author").text = "ChadMaster (archive.org)"

                # Comment XML tag
                ET.SubElement(tag_datfile, "comment").text = "_"

                # Get the DAT file
                print(f"DAT filename: {df}")
                # add datfile to DB zip file
                zip_object.writestr(df, zf.read(df))
        print()
        os.remove(filepath)

    # store clrmamepro XML file
    xmldata = ET.tostring(tag_clrmamepro).decode()

    with open(XML_FILENAME, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xmldata)

    print("Finished")


try:
    update_XML()
except KeyboardInterrupt:
    pass
