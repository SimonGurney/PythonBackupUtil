from cli import RootCli
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)5s %(filename)10s %(funcName)15s() %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

RootCli(r"C:\users\simon\backup").cmdloop()