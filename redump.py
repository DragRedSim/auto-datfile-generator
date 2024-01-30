import re
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from time import gmtime, strftime, sleep
import requests

# Config
URL_HOME      = "http://redump.org/"
URL_DOWNLOADS = "http://redump.org/downloads/"
XML_FILENAME  = "redump.xml"
XML_DIRECT    = "redump-direct.xml"
XML_URL       = "https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/redump.zip"

regex = {
    "datfile"  : r'<a href="/datfile/(.*?)">',
    "date"     : r"\) \((.*?)\)\.",
    "name"     : r'filename="(.*?) Datfile',
    "filename" : r'filename="(.*?)"',
}

def _find_dats():
    download_page = requests.get(URL_DOWNLOADS, timeout=30)
    if (download_page.status_code != 200):
        download_page.raise_for_status()
    else:
        print("Collected Redump DATs")
        dat_files = re.findall(regex["datfile"], download_page.text)
        return dat_files


def update_XML():
    dat_list = _find_dats()
    
    pack_gen_date = strftime("%Y-%m-%d", gmtime())

    # zip file to store all DAT files
    zip_object = zipfile.ZipFile("redump.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)

    # clrmamepro XML file
    tag_clrmamepro = ET.Element("clrmamepro")
    tag_clrmamepro_direct = ET.Element("clrmamepro")

    for dat in dat_list:
        print(f"Downloading {dat}")
        # section for this dat in the XML file
        tag_datfile = ET.SubElement(tag_clrmamepro, "datfile")
        tag_datfile_direct = ET.SubElement(tag_clrmamepro_direct, "datfile")

        response = requests.get(URL_HOME + "datfile/" + dat, timeout=30)
        content_header = response.headers["Content-Disposition"]

        # XML version
        dat_date = re.findall(regex["date"], content_header)[0]
        ET.SubElement(tag_datfile, "version").text = dat_date
        ET.SubElement(tag_datfile_direct, "version").text = dat_date

        # XML name & description
        temp_name = re.findall(regex["name"], content_header)[0]
        # trim the - from the end (if exists)
        if temp_name.endswith("-"):
            temp_name = temp_name[:-2]
        elif temp_name.endswith("BIOS"):
            temp_name = temp_name + " Images"
        ET.SubElement(tag_datfile, "name").text = temp_name
        ET.SubElement(tag_datfile_direct, "name").text = temp_name
        ET.SubElement(tag_datfile, "description").text = temp_name
        ET.SubElement(tag_datfile_direct, "description").text = temp_name + " - Direct Download from redump.org"

        # URL tag in XML
        ET.SubElement(tag_datfile, "url").text = XML_URL
        ET.SubElement(tag_datfile_direct, "url").text = URL_HOME + "datfile/" + dat

        # File tag in XML
        original_filename = re.findall(regex["filename"], content_header)[0]
        filename = f"{original_filename[:-4]}.dat"
        ET.SubElement(tag_datfile, "file").text = filename
        ET.SubElement(tag_datfile_direct, "file").text = filename

        # Author tag in XML
        ET.SubElement(tag_datfile, "author").text = "redump.org"
        ET.SubElement(tag_datfile_direct, "author").text = "redump.org"

        # Command XML tag
        ET.SubElement(tag_datfile, "comment").text = "Downloaded as part of an archive pack, generated " + pack_gen_date
        ET.SubElement(tag_datfile_direct, "comment").text = "Downloaded from redump.org"

        # Get the DAT file
        datfile_name = f"{filename[:-4]}.dat"
        print(f"DAT filename: {datfile_name}")
        if original_filename.endswith(".zip"):
            # extract datfile from zip to store in the DB zip
            zipdata = BytesIO()
            zipdata.write(response.content)
            archive = zipfile.ZipFile(zipdata)
            zip_object.writestr(datfile_name, archive.read(datfile_name))
        else:
            # add datfile to DB zip file
            datfile = response.text
            zip_object.writestr(datfile_name, datfile)
        print(flush=True)
        sleep(5)

    # store clrmamepro XML file
    xmldata = ET.tostring(tag_clrmamepro).decode()
    with open(XML_FILENAME, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xmldata)
    xmldata_direct = ET.tostring(tag_clrmamepro_direct).decode()
    with open(XML_DIRECT, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xmldata_direct)

    print("Finished")

try:
    update_XML()
except KeyboardInterrupt:
    pass
