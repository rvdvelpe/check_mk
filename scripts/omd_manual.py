#!/usr/bin/env python
# encoding: utf-8


from __future__ import print_function 	#To get the 3.0 print function in Python 2.X
import os				#Miscellaneous operating system interfaces module (https://docs.python.org/2/library/os.html)
import collections			#One-line Tree in Python (https://gist.github.com/hrldcpr/2012250)
import re				#Regular Expression module (https://docs.python.org/2/library/re.html)
import csv

#############
#Declaration#
#############

def tree(): return collections.defaultdict(tree)  #One-line Tree in Python (https://gist.github.com/hrldcpr/2012250)

#map filename to a WATO folder
foldertree = tree()    
foldertree['telefonie'] = 'telefonie'
foldertree['switch-core'] = 'networking/switch-core'
foldertree['switch-dmz'] = 'networking/switch-dmz'
foldertree['switch-chassis'] = 'networking/switch-chassis'
foldertree['ironport'] = 'security/ironport'
foldertree['f5'] = 'security/f5'
foldertree['palo alto'] = 'security/palo alto'

#paths
filepath = '/home/local/ICA/rc01865a/check_mk/scripts/files/'
#watopath = '/home/local/ICA/rc01865a/output/'    
watopath = '/opt/omd/sites/telecom/etc/check_mk/conf.d/wato/'    


def getallobjectsnotmanual():
	#Get all objects which are imported by this script.
	l_filenames1 = []
	
	#Go through all files	
	for root, dirs, files in os.walk(watopath):
		for filename in files:
			#if the file is hosts.mk get the wato folder which is used by foldertree
			if filename == "hosts.mk":				
				fileloc = root + "/" + filename				
				searchObj = re.search(r"wato\/(.*)\/hosts\.mk", fileloc)
				if searchObj:
					folderdir = searchObj.group(1)					
					#if not in foldertree (thus bmv or manual insert) save all the objecst in dict
					if folderdir not in foldertree.values():						
						with open(fileloc) as f:
							for line in f:						
								searchObje = re.search(r"'([a-zA-Z0-9_-]*)'[ ]{0,3}: u'([0-9.]*)'", line)
								if searchObje:
									name = searchObje.group(1)
									name = name.upper()									
									ip = searchObje.group(2)									
									l_filenames1.append(name)
	
	global gotostep
	gotostep = 2	
	
	return l_filenames1


def processfiles(filepath, object_notmanual):
	#removes duplicate names.
	#first one which is processed is used (need to written !)
	
	objects = tree()	
	
	#check all the files
	for root, dirs, files in os.walk(filepath):
		#use the filename to map to a WATO folder with dict foldertree
		for filename in files:			
			print(filename)
			csvfile = open(filepath + filename, 'rb')
			reader = csv.reader(csvfile, delimiter=';')
			
			rownum = 0
			#for each row
			for row in reader:
				#use the first row as header
				if rownum == 0:
					header = row
				#process the rows
				else:
					colnum = 0
					for col in row:
						#first column is the name
						if colnum == 0:
							name = re.sub("[^a-zA-Z0-9-_]+", "-", col)
							name = name.upper()							
						#second column is the IP, store this is dict						
						elif colnum == 1:
							ip = col
							if not name in object_notmanual:
								objects[filename][name] = ip								
							else:
								print("Object " + name + " is already included")														
						colnum += 1
				rownum += 1		
	
	global gotostep
	gotostep = 3
		
	return objects


def checkobjects(objects):
	
	l_filenames = []
	l_filenames1 = []
	b_filenames = []
	new_items = []
	delete_items = []
	
	#Get the object in checkmk based on the watofolder (from files only!)
	#Go to all the folders and get the objects with ip
	for key in foldertree:
		host_mk = watopath + foldertree[key] + "/hosts.mk"
		if os.path.isfile(host_mk):
			with open(host_mk) as f:
				for line in f:
					searchObj = re.search(r"'([a-zA-Z0-9_-]*)'[ ]{0,3}: u'([0-9.]*)'", line)
					if searchObj:						
						filename = searchObj.group(1)
						#print(filename)
						ip = searchObj.group(2)
						#regex not 100%, this need to be excluded.
						if filename != "ipaddress":
							l_filenames1.append(filename)	
	
	#Get all the object from files
	for hostgroup in objects:
		for name in objects[hostgroup]:
			b_filenames.append(name)
	
	#which items are not in checkmk yet (bmv - checkmk)
	new_items = list(set(b_filenames) - set(l_filenames1))
	#which items should be delete from checkmk (checkmk - bmv)
	delete_items = list(set(l_filenames1) - set(b_filenames))	
		
	print("new")
	print(new_items)
	print("delete")
	print(delete_items)	
	
	global gotostep
	#gotostep = 'x'
	gotostep = 4
	
	return(new_items,delete_items)


def createfiles(objects):	
	
	#Create WATO files and folders
	for folder in objects:		
		try:
			os.makedirs(watopath + foldertree[folder])			
			#generateoutput("step 4.x: wato Folder %s created" % folder)
		except os.error:			
			#generateoutput("step 4.x: wato Folder %s already exist" % foldertree[folder])
			pass

		#all the properties for the WATO file
		all_hosts = "" 
		host_attributes = "" 
		ips = ""
		extra_host_conf = ""
		explicit_snmp_community = ""


		for name in objects[folder]:
			s_alias = folder
			ipaddress = objects[folder][name]
			
			all_hosts += "\"%s|snmp-only|prod|snmp|lan|wato|/\" + FOLDER_PATH + \"/\",\n" % (name)
			#all_hosts += "'%s',\n" % (name)
			if ipaddress:
				host_attributes += "'%s' : {'alias' : u'%s', 'ipaddress' : u'%s' },\n" % (name, s_alias, ipaddress)
				ips += "'%s' : u'%s',\n" % ( name, ipaddress )
				explicit_snmp_community += "'%s': u'snmp4all',\n" % name
				extra_host_conf += "(u'%s', ['%s']),\n" % (s_alias, name)
			else:
				host_attributes += "'%s' : {'alias' : u'%s' },\n" % (name, s_alias)
				explicit_snmp_community += "'%s': u'snmp4all',\n" % name
				extra_host_conf += "(u'%s', ['%s']),\n" % (s_alias, name)
	
		hosts_mk = open(watopath + foldertree[folder] + '/hosts.mk','w')
		#generateoutput("step 4.x: hosts.mk file in folder %s created" % foldertree[folder])
		hosts_mk.write('# Written by WATO\n')
		hosts_mk.write('# encoding: utf-8\n\n')
		hosts_mk.write('all_hosts += [')
		hosts_mk.write(all_hosts)
		hosts_mk.write(']\n\n')
		
		if len(ips) > 0:
			hosts_mk.write('ipaddresses.update({')
			hosts_mk.write(ips)
			hosts_mk.write('})\n\n')
	
		hosts_mk.write('explicit_snmp_communities.update({')
		hosts_mk.write(explicit_snmp_community)
		hosts_mk.write('})\n\n')
		
		hosts_mk.write('extra_host_conf.setdefault(\'alias\', []).extend([')
		hosts_mk.write(extra_host_conf)
		hosts_mk.write('])\n\n')
		
		hosts_mk.write('host_attributes.update({')
		hosts_mk.write(host_attributes)
		hosts_mk.write('})\n\n')
		
		hosts_mk.close()	
	
	global gotostep
	gotostep = 'x'		


##############
#Start Script#
##############

gotostep = 1
new_hosts = []
delete_hosts = []

while gotostep != 'x' and gotostep != 's':	
	
	if gotostep == 1:
		print("start 1")
		object_notmanual = getallobjectsnotmanual()
	if gotostep == 2:
		print("start 2")
		d_object_processed = processfiles(filepath, object_notmanual)
		#gotostep = x
	if gotostep == 3:
		print("start 3")
		new_hosts, delete_hosts = checkobjects(d_object_processed)		
	if new_hosts or delete_hosts:
		print("start 4")
		if gotostep == 4:
			createfiles(d_object_processed)
	else:
		gotostep = 'x'

