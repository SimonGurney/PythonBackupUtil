from jobs import Backup, Restore, Job
from database import Database
from cmd import Cmd
from os import path, sep
import logging
class Cli(Cmd):
    backup_repository = None;
    def emptyline(self):
        logging.debug("Empty line registered")
        pass #required as input() causes weird behaviour
    def do_return(self, arg):
        "Return to home menu"
        logging.debug("Returning to home menu")
        RootCli(self.backup_repository).cmdloop()
    def do_quit(self, arg):
        logging.info("Quit command issued, calling sys exit")
        "Quit the CLI"            
        raise SystemExit(0)
    def __init__(self,backup_repository):
        super().__init__()
        self.backup_repository = backup_repository
    def are_you_sure(self, message = None):
        if message:
            logging.debug("Prompt message is %s",message)
            print(message)
        if input("      are you sure? y/n (default is n) > ") != "y":
            logging.info("User did not enter 'y' to are you sure prompt")
            return False
        else:
            logging.info("User entered 'y' to are you sure prompt")
            return True
     
class RootCli(Cli):
    prompt = "> "
    def do_backup(self, args):
        """Enter backup task sub menu
        |   Syntax: backup <backup target>
        |       + backup '\\root\\'
        |       + backup 'C:\\temp' """  
        if (len(args) is not 0): # and (len(args.split()) == 1):
            try:
                BackupCli(self.backup_repository,args).cmdloop()
            except ValueError as ErrorMessage:
                print(ErrorMessage)
        else:
            self.onecmd("help backup")
    def do_restore(self, args):
        "Enter restore task sub menu"
        try:
            RestoreCli(self.backup_repository).cmdloop()
        except ValueError as ErrorMessage:
            print(ErrorMessage)
    def do_database(self, args):
        "Enter database management sub menu"
        try:
            DatabaseCli(self.backup_repository).cmdloop()
        except ValueError as ErrorMessage:
            print(ErrorMessage)
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
class JobCli(Cli):
    j = None #Holds the job controller
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
class BackupCli(JobCli):
    prompt = "Backup > "
    def do_backup(self, args):
        """Take a backup
        |   Syntax: backup""" 
        logging.debug("Entered backupCli with target %s",self.backup_target)
        if self.j.backup_files():
            logging.info("Successfully backed up %s",self.backup_target)
            print("Success")
            self.j.discard_inventory()
            logging.debug("Discarded inventory so a new backup can be run immediately")
        else:
            logging.info("Failed to back up %s",self.backup_target)
            print("Backup failed")
    def __init__(self,backup_repository,backup_target):
        super().__init__(backup_repository)
        self.backup_target = backup_target
        self.j = Backup(self.backup_target,self.backup_repository)
class RestoreCli(JobCli):
    prompt = "Restore > "
    def do_list_backups(self,args):
        """List all backups in the database
        |   Syntax: list_backups""" 
        self.j.list_backups()
    def do_use_backup(self,args):
        """Select a backup in the database
        |   Syntax: use_backup <backup id>
        |       + use_backup 14""" 
        if (len(args) > 0) and (len(args.split()) == 1):
            if not self.j.use_backup(args):
                print("Could not select backup id %s! Does it exist?" %args)
            else:
                print("Active backup set to %s" %self.j.id)
        else:
            self.onecmd("help use_backup")  
    def do_browse(self, args):
        """Browse the directory of a backup in the database
        |   Syntax: browse_backup <backup id>(optional if backup id already selected)
        |       + browse
        |       + browse 14""" 
        if (len(args) > 0) and (len(args.split()) == 1):
            self.do_use_backup(args)
        if self.j.id:
            if not self.j.retrieve_inventory():
                print("Could not retrieve inventory from backup")
                return False
            if not self.j.build_dir_list():
                print("Could not build list of directories")
                return False
            BrowseCli(self.j).cmdloop()
        else:
            self.onecmd("help browse")
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
        self.j = Restore(backup_repository)
class BrowseCli(Cli):
    prompt = "Restore > Browse > "
    path = None
    def do_ls(self, args):
        """List directory of a backup in the database
        |   Syntax: ls
        |       + ls""" 
        if (len(args) == 0):
            print(" id\t|| type\t|| name") 
            for record in self.j.return_path_contents(self.path):
                print(" %s\t|| %s\t|| %s" % (record["id"],record["type"],record["name"]))
        else:
            self.onecmd("help ls")
    def do_pwd(self, args):
        """Print current working directory
        |   Syntax: pwd 
        |       + pwd"""
        if len(args) == 0:
            print(self.path)
        else:
            self.onecmd("help pwd")
    def do_cd(self, args):
        """Change the current working directory. Use ".." for back
        |   Syntax: cd <directory>
        |       + cd folder1
        |       + cd .. """
        if (len(args) > 0):# and (len(args.split()) == 1):
            if args == "..":
                requested_path = path.split(self.path)[0]
            else:
                requested_path = self.path + "\\" + args.rstrip(sep)
            logging.debug("requested_path is set to '%s'",requested_path)
            logging.debug("self.j.dir_list is \n%s",self.j.dir_list)
            if (requested_path in self.j.dir_list) or (requested_path + sep in self.j.dir_list):
                logging.info("requested_path found in the dir_list, allowing cd")
                self.path = requested_path.rstrip(sep)
            else:
                logging.info("requested_path not found in the dir_list, disallowing cd")
                print("Path does not exist")
        else:
            self.onecmd("help cd")
    def do_restore(self, args):
        """Restore a file.
        |   Syntax: restore <file id> <dest>(optional)
        |       + restore 14
        |       + restore 14 c:\temp\recovered.pdf """
        destination = False
        if len(args) > 0:
            args = args.split(" ",1)
            if len(args) == 1:
                inventory_index = int(args[0])
                logging.debug("User requested restore of %s without the optional destination",inventory_index)
            elif len(args) > 1:
                destination = args[1]
                inventory_index = int(args[0])
                logging.debug("User requested restore of %s with the optional destination %s",inventory_index,destination)
            else:
                self.onecmd("help restore")
            if self.j.restore_file(inventory_index,destination):
                logging.info("Restore was successful")
                print("success")
            else:
                logging.warning("Restore failed")
        else:
            self.onecmd("help restore")            
    def __init__(self,j):
        super().__init__(j.backup_repository)
        self.j = j
        self.path = self.j.backup_target
class DatabaseCli(Cli):
    prompt = "Database > "
    db = None
    def do_verify(self,args):
        """Check the database for issues
        |   Syntax: verify <option>
        |       + verify tables - Check database is correctly configured
        |       + verify """  
        if args == "tables":
            if self.db.verify_tables():
                print("Tables are fine")
            else:
                print("Tables are broken, troubleshoot or rebuild with create_tables")
        elif args == "dummy":
            pass
        else:
            self.onecmd("help verify")
    def do_dump(self,args):
        """Dump a table from the database
        |   Syntax: dump <table name>
        |       + dump files
        |       + dump backup_files  
        |       + .."""  
        if (len(args) > 0) and (len(args.split()) == 1):
            self.db.dump_table(args)
        else:
            self.onecmd("help dump")
    def do_drop_tables(self,args):
        """Drop all tables from the database
        |   Syntax: drop_tables"""  
        if self.are_you_sure("This will clear the database and is not recoverable!"):
            self.db.drop_tables()
    def do_create_tables(self,args):
        """Create all tables for the database
        |   Syntax: create_tables"""
        if self.db.verify_tables()and self.are_you_sure("Working tables exist, I will have to drop them!"):
            self.db.drop_tables()
        self.db.create_tables()
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
        self.db = Job(self.backup_repository).db
