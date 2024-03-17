
import abc, os
import xml.etree.ElementTree as ET
from abc import abstractmethod
from time import gmtime, strftime
from datetime import datetime
from dataclasses import dataclass, replace
from typing import Optional
import zipfile
import atexit
import subprocess, re

@dataclass
class dat_descriptor():
    filename: str #name as it is in the DAT file. Must match to provide updatability.
    date    : datetime
    title   : Optional[str] = None #used for creating the description
    version : Optional[str] = None #note in description if version number is not in date format
    url     : Optional[str] = None #download path
    desc    : Optional[str] = None
    dtd     : Optional[str] = None
    
    def copy(self, **changes):
        if len(changes) != 0:
            return replace(self, **changes)
        else:
            return replace(self)

class container_set():
    @property
    def xml_filename(self):
        return self._xml_filename
    @property
    def zip_filename(self):
        return self._zip_filename
    @property
    def zip_object(self):
        return self._zip_object
    @property
    def zip_url(self):
        return self._zip_url
    @property
    def xml_root(self):
        return self._xml_root
    @xml_root.setter
    def xml_root(self, contents):
        self._xml_root = contents
        
    def __init__(self, source_id, xml_id: str, has_zip: bool):
        self._xml_filename = source_id + (("-"+xml_id) if xml_id != "" else "") + ".xml"
        if has_zip:
            self._zip_filename = self.xml_filename[:-4] + ".zip"
            self._zip_object = zipfile.ZipFile(self._zip_filename, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)
            atexit.register(self._close_zip, self.zip_object)
        
            if (os.getenv("GITHUB_REPOSITORY") != None and container_name != "source"): #if we are running as part of a Github workflow, produce the URL using the account which is running the workflow
                self._zip_url = f'https://github.com/{os.getenv("GITHUB_REPOSITORY")}/releases/download/{os.getenv("tag", os.getenv("GITHUB_REF_NAME"))}/{self._zip_filename[container_name]}'
            else:
                self._zip_url = None
        else:
            self._zip_filename = None
            self._zip_object = None
            self._zip_url = None
            
        self._xml_root = ET.Element("clrmamepro")
        
    def _close_zip(self, zip_object):
        zip_object.close()

class dat_handler(metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def SOURCE_ID(self):
        """A string that identifies all packages created by this handler.
        """
        pass
    @property
    @abstractmethod
    def AUTHOR(self):
        """A string which is used to identify the author of the DAT file in the CLRMamePro WWW-mode profiler.
        """
        pass
    @property
    @abstractmethod
    def URL_HOME(self):
        """The URL for the home of the project which produces the DATs that this handler utilises.
        """
        pass
    @property
    @abstractmethod
    def URL_DOWNLOADS(self):
        """The URL which acts as a general download page for the DATs that this handler utilises. 
        """
        pass
    @property
    @abstractmethod
    def XML_TYPES_WITH_ZIP(self):
        """A dict object defining the containers to create in this handler.
        :param key: A container name. May be blank for default. Code has special handling for the keyword ``source``. Non-blank keys will have the container name appended to the SOURCE_ID in the output files.
        :type key: str
        :param value: Whether this container requires the compilation of a ZIP file.
        :type value: bool
        """
        pass
    @property
    def regex(self):
        """A dict of regex search patterns. Optional. No regex are referenced by the ``dat_handler`` module, however they may be used in an inheriting class, so we provide a standardised storage.
        
        :param key: A human-readable name for the regex, unique within this handler.
        :type key: str
        :param value: The regex pattern as a raw string (denoted by prefixing with r, and wrapping in single quotes, eg. "r''")
        :type value: str, raw
        """
        pass
    @property
    def pack_gen_date(self):
        """Gives the date on which this handler was executed. Use this to document the latest running of the handler.
        Note that this should not be used to define a DAT's version, as it may not have been updated since the previous running.
        For those, utilise the version provided in the DAT itself where possible, or in the filename.

        :return: Date formatted as YYYY-MM-DD.
        :rtype: str
        """
        return self._pack_gen_date
    
    def __init__(self):
        self._pack_gen_date = strftime("%Y-%m-%d", gmtime())
        self.container_set  = dict()
        
        for container_name, has_zip in self.XML_TYPES_WITH_ZIP.items():
            self._cleanup_files(container_name)
            self.container_set[container_name] = container_set(self.SOURCE_ID, container_name, has_zip)
        return
    
    def pack_single_dat(self, xml_id: str, dat_tree: ET, dat_data: dat_descriptor, comment: str = ""):
        """Takes a DAT file (as ElementTree) and packs it to a single container. This will add it to a ZIP file if one is assigned to the container. 
        Whether it has a ZIP or not, the DAT will be added to the XML file for this container.
        
        :param xml_id: The key for the container to pack to.
        :type xml_id: str
        :param dat_tree: An ElementTree representation of an XML DAT file (obtained by calling ``ET.fromstring(datfile_contents)``). Alternately, a string object containing the contents of a CLRMamePro DAT file (eg. Redump's BIOS files)
        :type dat_tree: ET or str
        :param dat_data: A collection representing the key data that needs to be stored in the container XML.
        :type dat_data: dat_descriptor
        :param comment: The comment to append to this DAT's entry in the container XML.
        :type comment: str, optional
        """
        if self.XML_TYPES_WITH_ZIP[xml_id] == True:
            self.add_dat_tree_to_zip(dat_data.filename, dat_tree, xml_id, dat_data.dtd)
        self.add_dat_to_xml(dat_data, xml_id, comment)
        return
    @abc.abstractmethod    
    def pack_xml_dat_to_all(self, filename_in_zip: str, dat_tree: ET.ElementTree | str, orig_url: str=""):
        """This method should contain the logic to pack one individual DAT file into each container specified for the source.
        
        :param filename_in_zip: The filename to be used when writing the DAT file into the container ZIP.
        :type filename_in_zip: str
        :param dat_tree: An ElementTree representation of an XML DAT file (obtained by calling ``ET.fromstring(datfile_contents)``); or alternatively, a string object containing the contents of a CLRMamePro DAT file.
        :type dat_tree: ET, str
        :param orig_url: The original download location of the DAT file, used to produce source packages.
        :type orig_url: str
        """
        raise NotImplementedError("Interface violation on pack_xml_dat_to_all()")
    @abc.abstractmethod
    def find_dats(self) -> list:
        """This method should contain the logic to find all DATs that a source provides. 
        It is not required to actually source the DAT files as part of this logic, just to create a list of them.
        However, if it is not possible to create the list without downloading the files, they may be downloaded in this function. If so, ensure they are written to disk in this function, so that they can be operated on without needing to download a second time.
        """
        raise NotImplementedError("Interface violation on find_dats()")
    @abc.abstractmethod
    def process_all_dats(self):
        """This method should loop over all potential DAT entries returned by ``find_dats()``, and for each one, it should call `pack_xml_dat_to_all()`.
        This should include logic to extract multiple DATs from a ZIP file, if the site offers one.
        This function should also contain the logic to download the DATs, if it is not done as part of ``find_dats()``.
        """
        raise NotImplementedError("Interface violation on process_all_dats()")
    
    def _cleanup_files(self, xml_id: str = ""):
        """Deletes all files that may have been created on previous runs for this container.
        This function is called as part of initialising a ``dat_handler`` object, and should not need to be manually called.
        
        :param xml_id: The container to run the cleanup on. Defaults to the blank container.
        :type xml_id: str, optional
        """
        _xml_filename = self.SOURCE_ID + (("-"+xml_id) if xml_id != "" else "") + ".xml"
        _zip_filename = _xml_filename[:-4]+".zip"
        for f in [_xml_filename or None, _zip_filename or None]:
            if f is not None:
                g = os.path.abspath(f)
                if (os.path.exists(g)):
                    try:
                        os.remove(g)
                    except PermissionError:
                        pass
                
    
    def _create_XML_entry(self, datfile, version, name, description, url, file, author, comment):
        datfile_element = ET.SubElement(datfile, "datfile")
        ET.SubElement(datfile_element, "version").text = version
        ET.SubElement(datfile_element, "name").text = name
        ET.SubElement(datfile_element, "description").text = description
        ET.SubElement(datfile_element, "url").text = url
        ET.SubElement(datfile_element, "file").text = file
        ET.SubElement(datfile_element, "author").text = author
        ET.SubElement(datfile_element, "comment").text = comment
        return datfile_element
    
    def add_dat_to_xml(self, dat_descriptor: dat_descriptor, target_xml: str, comment: str):
        self._create_XML_entry(datfile=self.container_set[target_xml].xml_root, 
                        version=dat_descriptor.version,
                        name=dat_descriptor.title,
                        description=dat_descriptor.desc,
                        url=dat_descriptor.url or None,
                        file=dat_descriptor.filename,
                        author=self.AUTHOR,
                        comment=comment)
    
    def add_dat_tree_to_zip(self, filename, dat_tree, target_container_name, dtd=None):
            if type(dat_tree) == str:
                self.container_set[target_container_name].zip_object.writestr(filename, dat_tree)
            else:
                if dtd != None:
                    self.container_set[target_container_name].zip_object.writestr(filename, dtd+ET.tostring(dat_tree).decode())
                else:
                    self.container_set[target_container_name].zip_object.writestr(filename, ET.tostring(dat_tree))              
   
    def export_containers(self):
        for container_name, has_zip in self.XML_TYPES_WITH_ZIP.items():
            if len(self.container_set[container_name].xml_root) > 0:
                ET.indent(self.container_set[container_name].xml_root)
                xmldata = ET.tostring(self.container_set[container_name].xml_root).decode()
                with open(self.container_set[container_name].xml_filename, "w", encoding="utf-8") as xmlfile:
                    xmlfile.write(xmldata)
            else:
                if has_zip:
                    self._close_zip(self.container_set[container_name].zip_object)
                    os.remove(os.path.join(os.getcwd(), self.container_set[container_name].zip_filename))
        
        if (os.path.isdir("./DATs") and len(os.listdir("./DATS")) == 0):
            os.rmdir("./DATs") #clean up after ourselves
        return
    
class retool_interface():
    regex = {
        "retool_file": r"( \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\) \(\d+\).*?)(?=\.\w{3})"
    }
    
    def __init__(self, arguments: list):
        self.added_args = arguments
    
    def retool(self, calling_handler: dat_handler, dat_data: dat_descriptor):
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(os.path.join(dir_path, "retool-config"))
            command = ['pipenv', 'run', 'python', '../retool/retool.py', f"{str(os.fspath(calling_handler.datfile))}"]
            for x in self.added_args:
                command.append(x)
            retool_proc = subprocess.run(command, cwd=os.path.join(dir_path, "retool-config"), timeout=300)
            fileExists = len([f for f in os.listdir() if f.startswith(dat_data.title)])
            if fileExists > 0:
                newFile = [f for f in os.listdir() if f.startswith(dat_data.title)][0]
                rename_to = re.sub(self.regex["retool_file"], ")", newFile)
                os.rename(newFile, rename_to)
                with open(rename_to, "rb") as retool_dat:
                    dat_tree_retool = ET.fromstring(retool_dat.read())
                    dat_data_retool = dat_data.copy(filename=os.path.basename(rename_to),
                                                    title=dat_data.title+f" (Retool)",
                                                    desc=dat_data.desc+f" - Retooled",
                                                    url=calling_handler.container_set['retool'].zip_url)
                    calling_handler.pack_single_dat(xml_id='retool', dat_tree=dat_tree_retool, dat_data=dat_data_retool, comment=f"Downloaded as part of an archive pack, generated {calling_handler.pack_gen_date}, Retool applied")
                os.remove(rename_to)
            os.chdir(os.fspath(dir_path))
            print()
        except Exception as e:
            print(e)
            raise(e)