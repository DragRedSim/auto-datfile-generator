import abc, os
from abc import ABCMeta, abstractmethod
import xml.etree.ElementTree as ET
from time import gmtime, strftime
from datetime import datetime
from dataclasses import dataclass
import zipfile

@dataclass
class dat_data():
    name    : str #name as it is in the DAT file. Must match to provide updatability.
    date    : datetime
    url     : str #download path
    
class dat_handler(metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def AUTHOR(self):
        pass
    @property
    @abstractmethod
    def URL_HOME(self):
        pass
    @property
    @abstractmethod
    def URL_DOWNLOADS(self):
        pass
    @property
    @abstractmethod
    def XML_FILENAME(self):
        pass
    @property
    @abstractmethod
    def ZIP_FILENAME(self):
        pass
    @property
    @abstractmethod
    def CREATE_SOURCE_PKG(self):
        pass
    @property
    @abstractmethod
    def regex(self):
        pass

    def __init__(self):
        self.tag_clrmamepro     = ET.Element("clrmamepro")
        self.pack_gen_date      = strftime("%Y-%m-%d", gmtime())
        self.zip_object         = zipfile.ZipFile(self.ZIP_FILENAME, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)
        if (self.CREATE_SOURCE_PKG):
            self.XML_SOURCE_FILENAME = self.XML_FILENAME[:-4]+"-source"+self.XML_FILENAME[-4:]
            self.tag_clrmamepro_source = ET.Element("clrmamepro")
        if (os.getenv("GITHUB_REPOSITORY") != None):
            self.ZIP_URL = f'https://github.com/{os.getenv("GITHUB_REPOSITORY")}/releases/latest/download/{self.ZIP_FILENAME}'
        else:
            self.ZIP_URL = None
    
    @abc.abstractmethod    
    def handle_file(self, dat_file):
        raise NotImplementedError("Interface violation on handle_file()")
    @abc.abstractmethod
    def _find_dats(self, file) -> list:
        raise NotImplementedError("Interface violation on _find_dats()")
    @abc.abstractmethod
    def update_XML(self):
        raise NotImplementedError("Interface violation on update_XML()")