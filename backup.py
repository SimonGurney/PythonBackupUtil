from os import walk, path
from database import Database
from file import File

class Backup:
    db = None
    id = None
    inventory = None
    src = None
    dst = None
    db_name = "db.sql"
    def test_db(self):
        if not self.db.verify_tables():
            raise ValueError("There is a problem with the database")
    def register_backup(self):
        self.id = self.db.register_backup()
    def use_backup(self, id):
        if self.db.list_backups(str(id)):
            self.id = id
        else:
            raise ValueError("Backup id %s does not exist" % id)
    def list_backups(self):
        backups = self.db.list_backups()
        if backups is not None:
            print("Backup ID        || TimeStamp")
            for backup in backups:
                print(backup[0],"               ||",backup[1])
        else:
            print("No backups")
    def check_folders(self):
        if not path.exists(self.src):
            return False
        if not path.isdir(self.dst):
            return False
        return True
    def generate_inventory(self):
        if self.inventory:
            raise ValueError("Inventory already exists, dicard with discard_inventory") 
        self.inventory = []
        for root, dirs, filenames in walk(self.src):
            for filename in filenames:
                try:
                    f = File(root,filename)
                except PermissionError:
                    print("%s\\%s not readable" %(root, filename))
                else:
                    self.inventory.append(f)
    def backup_files(self):
        self.test_db()
        self.register_backup()
        self.generate_inventory()
        for file in self.inventory:
            if self.db.register_file(file) is 0:
                if file.backup_file(self.dst):
                    self.db.set_file_as_stored(file)
                    self.db.commit()
                    print("copied %s\\%s to repository" % (file.path, file.name) )
                else:
                    print("Could not copy file", file.name)
            else:
                print("No need to copy file, already have it")
            self.db.register_file_instance(file)
        self.db.commit()
    def restore_file(self, file, destination = None):
        if destination is None:
            destination = file.path
        if not path.isdir(destination):
            ValueError("Restore directory not suitable")
        if not file.restore_file(self.dst, destination):
            print("Restore failed")   
        
    def retreive_inventory(self):
        self.test_db()
        if self.inventory is not None:
            print("Inventory already exists, discard with discard_inventory")
            return 1
        if self.id is None:
            raise ValueError("No backup ID set")
        self.inventory = self.db.retreive_files_from_backup(self.id)
    def discard_inventory(self):
        self.inventory = None
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        if not self.check_folders():
            raise ValueError("bad dirs")
        self.db = Database(path.join(dst,self.db_name))
