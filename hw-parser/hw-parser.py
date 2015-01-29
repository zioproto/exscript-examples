#!/usr/bin/env python
from Exscript                import Queue, Logger, FileLogger
from Exscript.util.log       import log_to
from Exscript.util.decorator import autologin
from Exscript.util.file      import get_hosts_from_file, get_accounts_from_file
from Exscript.util.report    import status, summarize
from Exscript.util.interact import read_login
from Exscript.util.match import first_match

#from xml.etree import cElementTree as ET
import lxml.etree as ET
import os,sys,time
os.system("mkdir -p ./logs/")
#logger = Logger() # Logs everything to memory.
logger = FileLogger("./logs/")

def getnamespace(root):
       return root[0].tag[root[0].tag.find('{'):root[0].tag.find('}')+1]


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

	#print conn.guess_os() #junos o ios
	operatingsystem = conn.guess_os()

	if operatingsystem == 'ios':
		assert False

	if operatingsystem == 'junos':
		f = open(host.name + ".inventory",'w')
		conn.execute("show chassis hardware | display xml | no-more")
		thexml = conn.response
		start = thexml.find("<rpc-reply")
		end = thexml.find("</rpc-reply>")+len("</rpc-reply>")
		#print "\n\n\n\n\n" + thexml[start:end] + "\n\n\n\n\n"
		root = ET.fromstring(thexml[start:end])
		#namespace = '{http://xml.juniper.net/junos/11.4R5/junos}'
		#namespace = '{http://xml.juniper.net/junos/11.4R5/junos-chassis}'
		namespace = getnamespace(root)
		#modules = root.findall('{0}chassis-inventory/{0}chassis/{0}chassis-module'.format(namespace))
		
		f.write("\n\nSummary of FPC for " + host.name + "\n")
		for fpc in root.findall('.//{0}chassis-module'.format(namespace)):
			if fpc.find('{0}name'.format(namespace)).text.split(" ")[0] == "FPC":
				description = fpc.find('{0}description'.format(namespace)).text
				slot = fpc.find('{0}name'.format(namespace)).text.split(" ")[1]
				serial = fpc.find('{0}serial-number'.format(namespace)).text
				f.write(description + "\t\t\tSlot: " + slot + "\t\t\tSerial: " + serial + "\n")

		f.write("\n\nSummary of MIC for " + host.name + "\n")
		for mic in root.findall('.//{0}chassis-sub-module'.format(namespace)):
			if mic.find('{0}name'.format(namespace)).text.split(" ")[0] == "MIC":
				description = mic.find('{0}description'.format(namespace)).text
				slot = mic.find('{0}name'.format(namespace)).text.split(" ")[1]
				serial = mic.find('{0}serial-number'.format(namespace)).text
				fpc = mic.getparent().find('{0}name'.format(namespace)).text.split(" ")[1]
				f.write(description + "\t\t\tSlot: " + fpc+"/"+slot + "\t\t\tSerial: " + serial + "\n")

		f.write("\n\nSummary of PIC for " + host.name + "\n")
		for pic in root.findall('.//{0}chassis-sub-sub-module'.format(namespace)):
			if pic.find('{0}name'.format(namespace)).text.split(" ")[0] == "PIC":
				description = pic.find('{0}description'.format(namespace)).text
				slot = pic.find('{0}name'.format(namespace)).text.split(" ")[1]
				serial = pic.find('{0}serial-number'.format(namespace)).text
				mic = pic.getparent().find('{0}name'.format(namespace)).text.split(" ")[1]
				fpc = pic.getparent().getparent().find('{0}name'.format(namespace)).text.split(" ")[1]
				f.write(description + "\t\t\tSlot: " + fpc+"/"+slot + "\t\t\tSerial: " + serial + "\n")

		f.write("\n\nSummary of Optics for " + host.name + "\n")
		# Match all sub sub sub modules
		for optic in root.findall('.//{0}chassis-sub-sub-sub-module'.format(namespace)):
			#debug to see what matches
			#for x in optic.getiterator():
			#	print x
			#	print dir(x)

			name = optic.find('{0}name'.format(namespace)).text
			serial = optic.find('{0}serial-number'.format(namespace)).text
			description = optic.find('{0}description'.format(namespace)).text
			pic = optic.getparent().find('{0}name'.format(namespace)).text
			mic = optic.getparent().getparent().find('{0}name'.format(namespace)).text
			fpc = optic.getparent().getparent().getparent().find('{0}name'.format(namespace)).text
			intf = fpc.split(" ")[1]+"/"+ pic.split(" ")[1] +"/"+name.split(" ")[1]
			
			f.write(description + "\t\t\t" + intf + "\t\t\t" + "Serial: " + serial +  "\n")
		

		f.close()


# Read input data.
#accounts = get_accounts_from_file('accounts.cfg')
accounts = read_login()
try:
	hosts    = get_hosts_from_file('hostlist.txt')
except:
	print """
Devi creare un file che si chiama hostlist.txt e dentro
ci sono linee di questo tipo:

ssh://r.rm2.garr.net
"""
	sys.exit(0)
# Run do_something on each of the hosts. The given accounts are used
# round-robin. "verbose = 0" instructs the queue to not generate any
# output on stdout.
queue = Queue(verbose = 3, max_threads = 5)

queue.add_account(accounts)     # Adds one or more accounts.
queue.run(hosts, do_something)  # Asynchronously enqueues all hosts.
queue.shutdown()                # Waits until all hosts are completed.
# Print a short report.
print status(logger)
print summarize(logger)
