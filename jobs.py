from os import walk, path, access, R_OK, W_OK, X_OK, sep
from database import Database
from file import File
from re import search, escape
import logging

class Job:
    db = None
    id = None
    inventory = None
    backup_repository = None
    backup_target = None
    db_name = "db.sql"
    
    def test_db(self):
        if not self.db.verify_tables():
            logging.info("There is a problem with the database")
            return False
        return True
    def use_backup(self, id):
        logging.debug("Entered the use_backup method of Job from jobs with id %s",id)
        backup = self.db.list_backups(str(id))
        logging.debug("list_backups returned...\n%s",backup)
        if not backup:
            logging.info("Returning false as nothing returned from call to list_backups")
            return False
        self.id = backup[0][0]
        self.backup_target = backup[0][2].rstrip(sep)
        logging.debug("Self.id = '%s', Self.backup_target = '%s'",self.id,self.backup_target)
        logging.debug("Returning true")
        return True
    def check_path(self, target, force_dir = False, force_writable = False):
        logging.debug("Entered the check_path method of Job from jobs with target: %s",target)
        if not path.isdir(target):
            logging.debug("Target is not a directory")
            if force_dir:
                logging.info("Path is not a directory but force_dir set to true")
                logging.debug("Returning False")
                return False
            else:
                logging.info("Path is not a directory and force_dir is false, testing if its a file and returning result")
                return path.isfile(target)
        logging.debug("Target is a directory")
        if (force_writable and not access(target,W_OK | X_OK)):
            logging.info("Target does not have write permissions but force_writable set to true")
            logging.debug("Returning false")
            return False
        elif not access(target,R_OK):
            logging.debug("Target is not readable")
            logging.debug("Returning false")
            return False
        logging.debug("Target is suitable by virtue of not failing earlier checks")
        logging.debug("Returning true")
        return True
    def discard_inventory(self):
        if self.inventory is None:
            logging.info("No inventory to discard")
            return
        if isinstance(self.inventory,list):
            logging.debug("Inventory currently contains %s items",len(self.inventory))
        else:
            logging.warning("Inventory is not a list, this is not expected behaviour. Contents:\n%s",self.inventory)
        self.inventory = False
        logging.info("Discarded inventory")
        logging.debug("Inventory has been discarded")
    def __init__(self, backup_repository):
        logging.debug("db_name set to %s",self.db_name)
        logging.debug("backup_repository provided as %s",backup_repository)
        self.backup_repository = backup_repository
        if not self.check_path(self.backup_repository, True):
            logging.info("The provided backup repository is not suitable")
            raise ValueError("Backup repository not suitable for reading backups")
        self.db = Database(path.join(self.backup_repository,self.db_name))
        logging.debug("self.db set")

class Restore(Job):
    dir_list = None;
    def list_backups(self):
        backups = self.db.list_backups()
        if backups is not None:
            logging.debug("Backups returned:\n%s",backups)
            print("Backup ID\t\t|| TimeStamp\t\t\t|| Base path")
            print("-------------------------------------------------------------------------------")
            for backup in backups:
                print(backup[0],"\t\t\t||",backup[1],"\t\t||",backup[2])
        else:
            logging.info("No backups returned from the database")
            print("No backups")
    def restore_file(self, file, destination = False):
        logging.debug("Entered restore_file function with file set to: %s",file)
        if type(file) is str:
            file = int(file)
        if type(file) is int:
            file = File(self.inventory[file].path, self.inventory[file].name, self.inventory[file].hash, self.inventory[file].size)
        if not file.hash:
            ValueError("Need a file object or inventory index reference")
        name = False
        if destination:
            logging.debug("Destination set to %s",destination)
        if not destination:
            logging.debug("Destination was set to False, not passing a destination path or filename")
        elif self.check_path(destination, True, True):
            logging.debug("Destination path is a directory and writeable")
        elif self.check_path((path.split(destination)[0]),True,True):
            logging.debug("Destination path including a filename so storing name in name variable")
            destination,name = path.split(destination)
        else:
            raise ValueError("Restore path not suitable")
        logging.debug("Backup repositry for restore set to %s",self.backup_repository)
        logging.debug("Destination path for restore set to %s",destination)
        logging.debug("Destination file name set to %s",name)
        if not file.restore_file(self.backup_repository, destination, name):
            logging.warn("Restore Failed")
            return False
        else:
            logging.info("Restore Successful")
            return True
    def retrieve_inventory(self):
        if not self.test_db():
            return False
        if self.inventory:
            logging.warning("Inventory already exists, discard with discard_inventory") 
            return False
        if self.id is None:
            logging.warning("No backup ID set")
            return False
        self.inventory = self.db.retreive_files_from_backup(self.id)
        if self.inventory:
            logging.info("Inventory retrieved and contains at least one item")
            return True
    def build_dir_list(self):
        logging.debug("Entered the build_dir_list function of Restore from jobs")
        if not self.inventory:
            logging.info("No inventory to work with")
            return False
        dir_list = set()
        for File in self.inventory:
            dir_list.add(File.path)
            logging.debug("Added the following file path - '%s'",File.path)
            logging.debug("Beginning the loop to add upstream paths to the dir_list")
            buf = path.split(File.path)[0]
            while True:
                if buf in dir_list:
                    logging.debug("Breaking loop as file path already in dir_list")
                    break
                dir_list.add(buf)
                logging.debug("Added '%s' to dir_list",buf)
                if path.split(buf)[1] == "":
                    logging.debug("Reached the root file path, no more directories to add")
                    break
                buf = path.split(buf)[0]
        logging.debug("Beginning the loop to add upstream paths for the dir_list")
        buf = path.split(self.backup_target)[0]
        while True:
            dir_list.add(buf)
            logging.debug("Added '%s' to dir_list",buf)
            if path.split(buf)[1] == "":
                logging.debug("Reached the root file path, no more directories to add")
                break
            buf = path.split(buf)[0]
        self.dir_list = sorted(dir_list)
        logging.debug("dir_list built and is as follows...\n%s",self.dir_list)
        logging.info("dir_list set")
        return True
    def return_path_contents(self, path):
        logging.debug("Entering the 'return_path_contents' function of Restore from jobs")
        logging.debug("path = '%s'",path)
        path = path.lower()
        path = path.rstrip(sep)
        logging.debug("After normalising, path = '%s'", path)
        if not self.dir_list:
            logging.info("Not built a directory list yet")
            return False
        dirs = set()
        returnable = list()
        pattern = r"(?<="+escape(path)+r"\\)[^\\\/]*"
        for file_path in self.dir_list:
            if path in file_path:
                re = search(pattern,file_path)
                if re:
                    match = re.group(0)
                    logging.debug("Regex returned the following match '%s'",match)
                    if match:
                        dirs.add(match)
        for dir in dirs:
            logging.debug("Appending directory - '%s'",dir)
            returnable.append({"id":"Nil","type":"dir","name":dir})
        for File in self.inventory:
            if (File.path == path) or (File.path == (path + sep)):
                returnable.append({"id":self.inventory.index(File),"type":"file","name":File.name})
        if not returnable:
            return False
        return sorted(returnable, key=lambda k: k['name'])
        
    def __init__(self, backup_repository):
        super().__init__(backup_repository)           
class Backup(Job):
    backup_file = False
    def register_backup(self):
        self.id = self.db.register_backup(self.backup_target)
        logging.debug("Self.id set to %s",self.id)
    def generate_inventory(self):
        if self.inventory:
            logging.warning("Inventory already exists, discard with discard_inventory")
            return False
        self.inventory = []
        if self.backup_file:
                self.inventory.append(File(*path.split(self.backup_target)))
                return
        for root, dirs, filenames in walk(self.backup_target):
            for filename in filenames:
                try:
                    f = File(root,filename)
                except PermissionError:
                    logging.warning("%s\\%s not readable, ommitting it from backup",root, filename)
                except:
                    logging.warning("%s\\%s has a problem, ommitting it from backup",root,filename)
                else:
                    self.inventory.append(f)
        if self.inventory:
            return True
    def backup_files(self):
        if not self.test_db():
            return False
        if not self.id:
            logging.debug("No backup id set so registering a new backup to use")
            self.register_backup()
        logging.debug("self.id is set to %s",self.id)
        if not self.generate_inventory():
            logging.warn("Could not generate inventory, returning false")
            return False
        for file in self.inventory:
            if self.db.register_file(file) is 0:
                if file.backup_file(self.backup_repository):
                    self.db.set_file_as_stored(file)
                    logging.debug("File set as stored in the DB, need to commit DB to ensure consistency")
                    self.db.commit()
                    logging.info("copied %s%s to repository", file.path, file.name)
                else:
                    logging.warn("%s needs to be backed up but could not copy it.  Will register file instance in the DB in case we manage to get it in a later backup", file.name)
            else:
                logging.debug("No need to copy file, already have it")
            logging.debug("Now need to register the instance of the file")
            self.db.register_file_instance(file)
        logging.debug("Finished processing files, commiting the database")
        self.db.commit() 
        return True

    def __init__(self, backup_target, backup_repository):
        super().__init__(backup_repository)
        self.backup_target = backup_target.lower()
        if not self.check_path(self.backup_target):
            raise ValueError("Backup target is not readable")
        if not self.check_path(self.backup_target, True):
            self.backup_file = True
            print("file")
        if not self.check_path(self.backup_repository, True, True):
            raise ValueError("Backup repository not suitable for writing backups")          