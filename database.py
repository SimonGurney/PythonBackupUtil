import sqlite3
from file import File
import logging

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
        logging.debug("Entered the retreive_files_from_backup method from Database")
        self.cursor.execute("SELECT path, name, file_hash FROM backup_files WHERE backup_id LIKE ?",[backupid])
        returnable = []
        file_instances = self.cursor.fetchall()
        logging.debug("Retrieved the following file instances...\n%s",file_instances)
        for path,name,file_hash in file_instances:
            self.cursor.execute("SELECT size FROM files WHERE hash = ?",[file_hash])
            size = self.cursor.fetchone()[0]
            logging.debug("Fetched the size '%s' for file hash '%s'", size, file_hash)
            returnable.append(File(path,name,file_hash,size))
            logging.debug("Appended the following file \n%s",name)
        logging.debug("Returning %d objects",len(returnable))
        return returnable
    def verify_tables(self):
        logging.debug("Entered the verify_tables method from Database")
        logging.debug("Gold standard should be...\n%s",self.tables)
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if len(self.cursor.fetchall()) - 1 is not len(self.tables):
            logging.info("Incorrect number of tables in the Database")
            return False
        for table in self.tables:
            logging.debug("Verifying the '%s' table", table["name"])
            self.cursor.execute("PRAGMA table_info(%s);" %(table["name"]))
            columns = self.cursor.fetchall()
            logging.debug("Columns returned from SQL transaction...\n%s",columns)
            if len(columns) is not len(table["columns"]):
                logging.info("The '%s' table has an incorrect number of columns", table["name"])
                return False
            for column in columns:
                logging.debug("Verifying the '%s' column from the '%s' table from the database",column[1],table["name"])
                if column[1] not in table["columns"]:
                    logging.info("The '%s' column should not exist in the '%s' table", column[1],table["name"])
                    return False   
            logging.debug("The '%s' table is fine",table["name"])
        logging.info("All tables are fine")
        return True
    def __init__(self, path):
        self.path = path

        self.connect()