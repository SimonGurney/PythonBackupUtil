from hashlib import sha512
from os import path
from shutil import copyfile
import logging
logger = logging.getLogger('log')
BLOCK_SIZE = 1024
#
class File:
    name = None
    path = None
    stored = None
    hash = None
    size = None
    
    def calc_hash(self):
        if self.hash is None:
            sha = sha512()
            with open((path.join(self.path, self.name)), "rb") as f:
                while True:
                    buf = f.read(BLOCK_SIZE)
                    if not buf:
                        break
                    sha.update(buf)
                self.hash = sha.hexdigest()
    def get_size(self):
        if self.size is None:
            self.size = path.getsize(path.join(self.path, self.name))
    def backup_file(self, destination):
        try:
            copyfile(path.join(self.path, self.name),path.join(destination, self.hash))
            return True
        except:
            return False
    def restore_file(self, backup_repository, destination = False, name = False):
        if not name:
            name = self.name
        if not destination:
            destination = self.path
        try:
            copyfile(path.join(backup_repository, self.hash),path.join(destination, name))
            return True
        except:
            return False    
    def __init__(self, path, name, hash = None, size = None):
        self.name = name.lower()
        self.path = path.lower()
        self.hash = hash
        self.size = size
        if not self.hash:
            self.calc_hash()
        if not self.size:
            self.get_size()