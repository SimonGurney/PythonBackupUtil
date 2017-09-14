from jobs import Backup, Restore, Job
from database import Database
from cmd import Cmd
from os import path

class Cli(Cmd):
    backup_repository = None;
    def emptyline(self):
        pass #required as input() causes weird behaviour
    def do_return(self, arg):
        "Return to home menu"
        RootCli(self.backup_repository).cmdloop()
    def do_quit(self, arg):
        "Quit the CLI"            
        raise SystemExit(0)
    def __init__(self,backup_repository):
        super().__init__()
        self.backup_repository = backup_repository
    def are_you_sure(self, message = None):
        if message:
            print(message)
        if input("      are you sure? y/n (default is n) > ") != "y":
            return False
        else:
            return True
     
class RootCli(Cli):
    prompt = "> "
    def do_backup(self, args):
        """Enter backup task sub menu
        |   Syntax: backup <backup target>
        |       + backup '\\root\\'
        |       + backup 'C:\\temp' """  
        if (len(args) is not 0) and (len(args.split()) == 1):
            try:
                BackupCli(self.backup_repository,args).cmdloop()
            except ValueError as ErrorMessage:
                print(ErrorMessage)
        else:
            self.onecmd("help backup")
    def do_restore(self, args):
        "Enter restore task sub menu"
        RestoreCli(self.backup_repository).cmdloop()

    def do_database(self, args):
        "Enter database management sub menu"
        DatabaseCli(self.backup_repository).cmdloop()
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
class JobCli(Cli):
    j = None #Holds the job controller
    def __init__(self,backup_repository):
        super().__init__(backup_repository)
class BackupCli(JobCli):
    prompt = "Backup > "
    def do_backup(self, args):
        if self.j.backup_files():
            print("Success")
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
            self.onecmd("help browse_backup")
    ##### Building dirlist function atm
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
        if (len(args) > 0) and (len(args.split()) == 1):
            if args == "..":
                requested_path = path.split(self.path)[0]
            else:
                requested_path = self.path + "\\" + args
            if requested_path in self.j.dir_list:
                self.path = requested_path
            else:
                print("Path does not exist")
        else:
            self.onecmd("help cd")
    def do_restore(self, args):
        """Restore a file.
        |   Syntax: restore <file id> <dest>(optional)
        |       + restore 14
        |       + restore 14 c:\temp\recovered.pdf """
        dirname = False
        filename = False
        if len(args) > 0:
            args = args.split()
            if len(args) == 1:
                inventory_index = int(args[0])
                print(inventory_index)
            elif len(args) == 2:
                inventory_index = int(args[0])
                dirname, filename = path.split(args[1])
                if filename == "":
                    filename = False
                print(dirname," ",filename)
            else:
                self.onecmd("help restore")
            if self.j.inventory[inventory_index].restore_file(self.j.backup_repository,dirname,filename):
                print("success")
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
                print("tables are fine")
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
        
RootCli(r"C:\backup").cmdloop()
