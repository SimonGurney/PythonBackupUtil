from hashlib import sha512
from os import path
from shutil import copyfile
import logging
logger = logging.getLogger('log')
BLOCK_SIZE = 1024

class File:
    name = None
    path = None
    stored = None
    hash = None
    size = None
    
    def calc_hash(self):
        if self.hash is None:
            logging.debug("Calculating hash")
            sha = sha512()
            with open((path.join(self.path, self.name)), "rb") as f:
                while True:
                    buf = f.read(BLOCK_SIZE)
                    if not buf:
                        break
                    sha.update(buf)
                self.hash = sha.hexdigest()
        else:
            logging.debug("self.hash already set so not recalculating")
    def get_size(self):
        if self.size is None:
            logging.debug("Calculating size")
            self.size = path.getsize(path.join(self.path, self.name))
        else:
            logging.debug("self.size already set so not recalculating")
    def backup_file(self, destination):
        logging.info("Backing up file %s to destination: %s",self.name,destination)
        try:
            copyfile(path.join(self.path, self.name),path.join(destination, self.hash))
            logging.debug("File copy successful, returning true")
            return True
        except:
            logging.debug("File copy unsuccessful, returning false")
            return False
    def restore_file(self, backup_repository, destination = False, name = False):
        if not name:
            logging.debug("Name set to False")
            name = self.name
            logging.debug("Name set to %s",name)
        if not destination:
            logging.debug("Destination set to False")
            destination = self.path
            logging.debug("Destination set to %s",destination)
        try:
            logging.debug("copying file")
            copyfile(path.join(backup_repository, self.hash),path.join(destination, name))
            logging.debug("File copy successful, returning True")
            return True
        except ValueError as ErrorMessage:
            logging.debug(ErrorMessage)
            return False    
    def __init__(self, path, name, hash = None, size = None):
        self.name = name.lower()
        logging.debug("Name set to %s",self.name)
        self.path = path.lower()
        logging.debug("Path set to %s",self.path)
        self.hash = hash
        self.size = size
        if not self.hash:
            self.calc_hash()
        if not self.size:
            self.get_size()
        logging.debug("Hash set to %s",self.hash)
        logging.debug("Size set to %s",self.size)