#!/usr/bin/env python
from Exscript                import Queue, Logger, FileLogger
from Exscript.util.log       import log_to
from Exscript.util.decorator import autologin
from Exscript.util.file      import get_hosts_from_file, get_accounts_from_file
from Exscript.util.report    import status, summarize
from Exscript.util.interact import read_login
from Exscript.util.match import first_match
import os,sys
os.system("mkdir -p ./logs/")
#logger = Logger() # Logs everything to memory.
logger = FileLogger("./logs/")

@log_to(logger)
#@autologin()
def do_something(job,host,conn):
	#if conn.guess_os() != 'ios':
	#        raise Exception('unsupported os: ' + repr(conn.guess_os()))

	# autoinit() automatically executes commands to make the remote
	# system behave more script-friendly. The specific commands depend
	# on the detected operating system, i.e. on what guess_os() returns.
	#conn.autoinit()
	conn.authenticate()
	#print repr(conn.response) #DEBUG
	#hostname = first_match(conn.response, r'^.*#$') #just for cisco match #
	#assert hostname
	commands = commandsfile.readlines()
	for command in commands:
		conn.execute(command)

try:
	commandsfile = open("commands.txt")
except:
	print """
Devi creare un file che si chiama commands.txt

dentro, uno per linea, metti i comandi che vuoi lanciare
"""
	sys.exit(0)

# Read input data.
#accounts = get_accounts_from_file('accounts.cfg')
accounts = read_login()
try:
	hosts    = get_hosts_from_file('hostlist.txt')
except:
	print """
Devi creare un file che si chiama hostlist.txt e dentro
ci sono linee di questo tipo:

ssh://192.168.0.1
"""
	sys.exit(0)
# Run do_something on each of the hosts. The given accounts are used
# round-robin. "verbose = 0" instructs the queue to not generate any
# output on stdout.
queue = Queue(verbose = 3, max_threads = 5)

queue.add_account(accounts)     # Adds one or more accounts.
queue.run(hosts, do_something)  # Asynchronously enqueues all hosts.
queue.shutdown()                # Waits until all hosts are completed.
commandsfile.close()
# Print a short report.
print status(logger)
print summarize(logger)
