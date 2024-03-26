#!/usr/bin/python
import os, re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from time import gmtime, strftime, sleep
from handler import dat_handler, dat_descriptor

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import subprocess
from handler import retool_interface

dir_path = os.path.dirname(os.path.realpath(__file__))

class no_intro(dat_handler):
    SOURCE_ID           = "no-intro"
    AUTHOR              = "no-intro.org"
    URL_HOME            = "https://datomatic.no-intro.org/"
    URL_DOWNLOADS       = "https://datomatic.no-intro.org/"
    XML_TYPES_WITH_ZIP  = {'': True, 'retool': True}
    PACK_TYPE           = "standard"
    regex = {
        "date"     : r"\(([0-9]{8}-[0-9]{6})\)",
        "name"     : r"(.*?.)( \([0-9]{8}-[0-9]{6}\).dat)",
        "retool_file": r"( \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\) \(\d+\).*?)\.\w{3}"
    }
    retool_caller = retool_interface(["--exclude", "aAbcdPu", "-y"])
    
    def download_nointro_zip(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        archive_name = "dl-no-intro-files.zip" if self.PACK_TYPE == "standard" else f"dl-no-intro-{self.PACK_TYPE}-files.zip"
        archive_full = os.path.join(dir_path, archive_name)
        if os.path.exists(f".\\{archive_name}"):
            print("Using locally cached file!")
        else:
            #set up Firefox options to get the ZIP packs from No-Intro
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", True)
            options.set_preference("browser.download.dir", dir_path)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            options.add_argument("-headless")
            service = webdriver.FirefoxService(log_output = "firefox-webdriver.log" , service_args = ["--log", "debug"])
            driver = webdriver.Firefox(service=service, options=options)
            driver.implicitly_wait(10)

            # load website
            driver.get("https://datomatic.no-intro.org")
            print("Loaded no-intro datomatic ...")

            def click_element(driver, path, pathtype=By.XPATH):
                try:
                    target_element_present = EC.presence_of_element_located((pathtype, path))
                    WebDriverWait(driver, 10).until(target_element_present)
                    target_element = driver.find_element(by=pathtype, value=path)
                    target_element.click()
                except TimeoutException as e:
                    print("Timeout in loading page")
                    raise(e)
                except Exception as e:
                    print("General error")
                    raise(e)

            # select "DOWNLOAD"
            click_element(driver, "/html/body/div/header/nav/ul/li[3]/a", By.XPATH)

            # select "daily"
            click_element(driver, "/html/body/div/section/article/table[1]/tbody/tr/td/a[5]", By.XPATH)

            #set the type of dat file
            if self.PACK_TYPE == "standard" :
                click_element(driver, "//input[@name='dat_type' and @value='standard']")
            if self.PACK_TYPE == "parent-clone" :
                click_element(driver, "//input[@name='dat_type' and @value='xml']")
            print(f"Set dat type to {self.PACK_TYPE} ...")

            # select "Request"
            click_element(driver, "daily_day", By.NAME)

            # select "Download"
            click_element(driver, "//article/div/form/input[@type='submit']", By.XPATH)
            print("Triggered download. Waiting for download to complete ...")

            # wait until file is found
            FOUND = False
            NAME = None
            TIME_SLEPT = 0
            while not FOUND:
                if TIME_SLEPT > 900:
                    raise FileNotFoundError(f"No-Intro {self.PACK_TYPE} zip file not found, timeout reached")

                for f in os.listdir(dir_path):
                    if "No-Intro Love Pack" in f and not f.endswith(".part"):
                        try:
                            zipfile.ZipFile(os.path.join(dir_path, f))
                            NAME = f
                            FOUND = True
                            print("No-Intro zip file download completed ...")
                            break
                        except zipfile.BadZipfile:
                            pass

                if FOUND == True:
                    break
                # wait 5 seconds
                sleep(5)
                TIME_SLEPT += 5

            if NAME == None:
                raise FileNotFoundError(f"No-Intro {self.PACK_TYPE} zip file not found, download failed")
            
            driver.close()
            #setup archive path and rename
            archive_name = "dl-no-intro-files.zip" if self.PACK_TYPE == "standard" else f"dl-no-intro-{self.PACK_TYPE}-files.zip"
            archive_full = os.path.join(dir_path, archive_name)
            os.rename(os.path.join(dir_path, NAME), os.fspath(archive_full))

        try:
            # load & extract zip file, there is currently no way to remove files from zip archive
            with zipfile.ZipFile(os.fspath(archive_full), mode="r") as orig_archive:
                orig_archive.extractall(path=f"./{self.PACK_TYPE}/")
                # delete unneeded files
                os.remove(f"./{self.PACK_TYPE}/index.txt")
        except Exception as e:
            print("Error extracting ZIP file")
            raise(e)
            
    def find_dats(self) -> list:    
        self.download_nointro_zip()
        dat_files = list()
        for f in os.walk(f"./{self.PACK_TYPE}/"):
            if len(f[2]) > 0:
                for g in f[2]:
                    compiled_path = os.path.join(os.getcwd(), f[0], g)
                    ext = os.path.splitext(compiled_path)[1].lower()
                    match ext:
                        case ".xml" | ".dat":
                            dat_files.append(os.path.realpath(os.path.join(os.getcwd(), f[0], g)))
                        case _:
                            pass
        return dat_files                    
        
    def pack_xml_dat_to_all(self, filename_in_zip, dat_tree, orig_url="", dat_path=""):
        dat_data = dat_descriptor(filename=filename_in_zip,
                                  title=dat_tree.find("header").find("name").text,
                                  desc=dat_tree.find("header").find("description").text, 
                                  date=self.dat_date, 
                                  url=self.container_set[''].zip_url,
                                  version=dat_tree.find("header").find("version").text
                                  )
        self.pack_single_dat(xml_id='', dat_tree=dat_tree, dat_data=dat_data, comment=f"Downloaded as part of an archive pack, generated {self.pack_gen_date}")
        if 'retool' in self.container_set:
            self.retool_caller.retool(self, dat_path, dat_data)
        
    def process_all_dats(self):
        dat_list = self.find_dats()
        
        for dat in dat_list:
            print(f"Processing {dat}")
            try:
                version_date = datetime.strptime(re.findall(self.regex["date"], dat)[0], "%Y%m%d-%H%M%S")
            except ValueError:
                try:
                    version_date = datetime.strptime(re.findall(self.regex["date"], dat)[0], "%Y%m%d")
                except Exception as e:
                    raise(e)
            with open(dat, "rt") as datfile:
                self.dat_date = datetime.strftime(version_date, "%Y%m%d-%H%M%S")
                dat_content = datfile.read()
                if dat_content[:12] == "clrmamepro (":
                    # This is a CLRMamePro dat, not a traditional XML dat.
                    raise()
                else:
                    dat_tree = ET.fromstring(dat_content)
                    self.pack_xml_dat_to_all(os.path.basename(dat), dat_tree, dat_path=dat)
        
        # store clrmamepro XML file
        self.export_containers()
        
        import shutil
        shutil.rmtree(f"./{self.PACK_TYPE}/")

        print("Finished")

if __name__ == "__main__":
    try:
        no_intro_packer = no_intro()
        no_intro_packer.process_all_dats()
    except Exception as e:
        raise(e)
