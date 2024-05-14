#!/usr/bin/python
import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime
from utils.handler import dat_handler, dat_descriptor
from no_intro import no_intro

class no_intro_parent_clone(no_intro):
    SOURCE_ID           = "no-intro_parent-clone"
    AUTHOR              = "no-intro.org"
    URL_HOME            = "https://datomatic.no-intro.org/"
    URL_DOWNLOADS       = "https://datomatic.no-intro.org/"
    XML_TYPES_WITH_ZIP  = {'': True}
    PACK_TYPE           = "parent-clone"
    regex = {
        "date"     : r"[0-9]{8}-[0-9]{6}",
        "name"     : r"(.*?.)( \([0-9]{8}-[0-9]{6}\).dat)"
    }
    
    def download_nointro_zip(self):
        super().download_nointro_zip()
            
    def find_dats(self) -> list:    
        return super().find_dats()

if __name__ == "__main__":
    try:
        no_intro_parent_clone_packer = no_intro_parent_clone()
        no_intro_parent_clone_packer.process_all_dats()
    except Exception as e:
        raise(e)