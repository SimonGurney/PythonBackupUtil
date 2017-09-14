import sqlite3
from file import File

class Database:
    path = None
    db = None
    cursor = None
    tables = ({"name": "files", "columns": ("hash","size","stored")},
              {"name": "backups", "columns": ("id", "created","path")}, 
              {"name":"backup_files", "columns":("id", "path", "name", "file_hash", "backup_id")})
    backupid = None
    def commit(self):
        self.db.commit()
    def drop_tables(self):
        droptables = """PRAGMA writable_schema = 1;
                      delete from sqlite_master where type in ('table', 'index', 'trigger');
                      PRAGMA writable_schema = 0;
                      VACUUM;
                      PRAGMA INTEGRITY_CHECK;"""
        self.cursor.executescript(droptables)
    def create_tables(self):
        self.drop_tables()
        self.cursor.execute('''CREATE TABLE files(hash CHAR(128) PRIMARY KEY, size INTEGER NOT NULL, stored BOOLEAN NOT NULL)''')
        self.cursor.execute('''CREATE TABLE backups(id INTEGER PRIMARY KEY AUTOINCREMENT, created CHAR(128) NOT NULL, path CHAR(300) NOT NULL)''')
        self.cursor.execute('''CREATE TABLE backup_files(id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, name TEXT NOT NULL, file_hash CHAR(64) NOT NULL, backup_id INTEGER NOT NULL, FOREIGN KEY(file_hash) REFERENCES files(hash), FOREIGN KEY(backup_id) REFERENCES backups(id))''')
    def connect(self):
        self.db = sqlite3.connect(self.path)
        self.cursor = self.db.cursor()
    def dump_table(self, table="backup_files"):
        if any(element["name"] == table for element in self.tables):
            self.cursor.execute("SELECT * FROM %s" % table)
            for row in self.cursor:
                print(row)
        else:
            print("No such table")
    def register_backup(self,path):
        if self.backupid is None:
            self.backupid = (self.cursor.execute('''INSERT into backups(created, path) VALUES (CURRENT_TIMESTAMP, ?)''',[path])).lastrowid
        return self.backupid
    def list_backups(self, backupid = "%"):
        self.cursor.execute("SELECT * FROM backups WHERE id LIKE ?",[backupid])
        return self.cursor.fetchall()
    def register_file(self,f):
        try:
            self.cursor.execute('''INSERT into files(hash, size, stored) VALUES (?,?,?)''',(f.hash,f.size,0))
            return 0
        except sqlite3.IntegrityError:
            self.cursor.execute("SELECT stored FROM files WHERE hash = ?", [f.hash])
            return(self.cursor.fetchone()[0]) # Return the stored flag
    def set_file_as_stored(self, f):
        self.cursor.execute('''UPDATE files SET stored = 1 WHERE hash = ?''',[f.hash])
    def register_file_instance(self, f): 
        self.cursor.execute('''INSERT into backup_files(path, name, file_hash, backup_id) VALUES (?,?,?,?)''',(f.path,f.name,f.hash,self.backupid))
    def retreive_files_from_backup(self, backupid = "%"):
        self.cursor.execute("SELECT path, name, file_hash FROM backup_files WHERE backup_id LIKE ?",[backupid])
        returnable = []
        file_instances = self.cursor.fetchall()
        for path,name,file_hash in file_instances:
            self.cursor.execute("SELECT size FROM files WHERE hash = ?",[file_hash])
            size = self.cursor.fetchone()[0]
            returnable.append(File(path,name,file_hash,size))
        return returnable
    def verify_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if len(self.cursor.fetchall()) - 1 is not len(self.tables):
            return False
        for table in self.tables:
            self.cursor.execute("PRAGMA table_info(%s);" %(table["name"]))
            columns = self.cursor.fetchall()
            if len(columns) is not len(table["columns"]):
                return False
            for column in columns:
                if column[1] not in table["columns"]:
                   return False                    
        return True
    def __init__(self, path):
        self.path = path
        self.connect()
            
