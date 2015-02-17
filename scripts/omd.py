#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function 	#To get the 3.0 print function in Python 2.X
import os				#Miscellaneous operating system interfaces module (https://docs.python.org/2/library/os.html)
import collections			#One-line Tree in Python (https://gist.github.com/hrldcpr/2012250)
import re				#Regular Expression module (https://docs.python.org/2/library/re.html)
import pypyodbc				#odbc api / module (https://code.google.com/p/pypyodbc/)
import shutil				#module used to remove a folder which is not empty.
import time
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#############
#Declaration#
#############

def tree(): return collections.defaultdict(tree)  #One-line Tree in Python (https://gist.github.com/hrldcpr/2012250)

#map MonitorHostgroup to a WATO folder
foldertree = tree()    
foldertree['INTERNET-ROUTER'] = 'networking/router-internet'
foldertree['MANAP-IPVPN-ROUTER'] = 'networking/router-ipvpn'
foldertree['MANAP-IPVPN-ROUTER-BANDW'] = 'networking/router-ipvpn'
foldertree['MANAP-SWITCH'] = 'networking/switch-manap'
foldertree['MANAP-IPVPN-SWITCH'] = 'networking/switch-ipvpn'
foldertree['MANAP-IPVPN-SWITCH-BANDW'] = 'networking/switch-ipvpn'
foldertree['MANAP-PTP-SWITCH'] = 'networking/switch-ptp'
foldertree['MANAP-PTP-SWITCH-BANDW'] = 'networking/switch-ptp'
foldertree['MANAP-PTP-AP-BANDW'] = 'networking/wireless-ptp'    
foldertree['UPS'] = 'ups'

'''
#test
watopath = '/home/local/ICA/rc01865a/scripts/omd/output/wato/'    
autocheckpath = '/home/local/ICA/rc01865a/scripts/omd/output/autochecks/'
logpath = '/home/local/ICA/rc01865a/scripts/omd/output/logs/'
'''

#prodcutie
watopath = '/opt/omd/sites/telecom/etc/check_mk/conf.d/wato/'    
autocheckpath = '/opt/omd/sites/telecom/var/check_mk/autochecks/'
logpath = '/home/local/ICA/rc01865a/output/'
notespath = '/opt/omd/sites/telecom/etc/check_mk/notes/hosts/'


###########
#functions#
###########

def generateoutput(string):
	global output
	global outputhtml
	output = output + string + '\n'
	outputhtml = outputhtml + string + '<br>'
	print(string)

def getbmvdata():
	generateoutput("step 1: getmbvdata STARTED")
	#https://code.google.com/p/pypyodbc/wiki/PyPyODBC_Example_Tutorial
	conn = pypyodbc.connect('Driver=FreeTDS;Server=172.20.5.42;port=1441;uid=OmdPTelecomSql;pwd=Omd@2014!!!;database=bmvd0001')
	cur = conn.cursor()
	cur.execute('''Select
    o.name as 'Object naam',
    ot.Name as 'Type Naam',
    p.Prompt as 'Eigenschap Naam',
    case
    when p.DataType = 'C' then (select cv.Description from CodeValue cv where (op.CodeValueID=cv.ID))
    when p.DataType = 'D' then cast(day(op.DateValue) as varchar(2)) +'/' + cast(month(op.DateValue) as varchar(2))+'/'  + cast(year(op.DateValue) as varchar(4))
    when p.DataType = 'S' then op.StringValue
    when p.DataType = 'N' then cast (op.NumericValue as varchar(800))
    when p.DataType = 'H' then op.StringValue   
    when p.DataType = 'B' then cast (op.NumericValue as varchar(800))
    when p.DataType = 'E' then op.StringValue
    when p.DataType = 'R' then cast (op.NumericValue as varchar(800))
    else p.DataType/*'Ongekend'*/
    end as 'Eigenschap Value'
    from dbo.ObjectType ot with (nolock) inner join dbo.ObjectTypeProperty otp with (nolock) on (ot.ID=otp.ObjectTypeID)
    inner join dbo.Property p with (nolock) on(p.ID=otp.PropertyID)
    inner join Object o with (nolock) on (o.ObjectTypeID=ot.ID and o.IsArchived=0)
    inner join ObjectProperty op with (nolock) on (op.ObjectTypePropertyID=otp.ID and op.ObjectID=O.ID and op.deletedon is null)   
    inner join dbo.ObjectTypeProperty otp2 with (nolock) on (ot.ID=otp2.ObjectTypeID)
    inner join dbo.Property p2 with (nolock) on(p2.ID=otp2.PropertyID)
    inner join ObjectProperty op2 with (nolock) on (op2.ObjectTypePropertyID=otp2.ID and op2.ObjectID=O.ID and op2.deletedon is null)
    where ot.Name = 'netwerk component'
    and p.Prompt in ('Klant','MACAdres','MonitorHostgroup','NetwerkUplink','NetwerkModel','NetwerkIP','Status')
    and p2.prompt = ('MonitorHostgroup')
    and
        case
            when p2.DataType = 'C' then (select cv2.Description from CodeValue cv2 where (op2.CodeValueID=cv2.ID))
            when p2.DataType = 'D' then cast(day(op2.DateValue) as varchar(2)) +'/' + cast(month(op2.DateValue) as varchar(2))+'/'  + cast(year(op2.DateValue) as varchar(4))
            when p2.DataType = 'S' then op2.StringValue
            when p2.DataType = 'N' then cast (op2.NumericValue as varchar(800))
            when p2.DataType = 'H' then op2.StringValue
            when p2.DataType = 'B' then cast (op2.NumericValue as varchar(800))
            when p2.DataType = 'E' then op.StringValue
            when p2.DataType = 'R' then cast (op2.NumericValue as varchar(800))
            else p2.DataType/*'Ongekend'*/
        end <> 'None'
    UNION
    SELECT
        O1.Name as 'Object naam',
        OT1.Name as 'Type Naam',
        OT2.Name as 'Eigenschap Naam',
        O2.Name as 'Eigenschap Value'
    FROM relation R with (nolock)
        INNER JOIN Object O1 with (nolock) ON (R.Object1ID = O1.ID and o1.IsArchived=0)
        INNER JOIN ObjectType OT1 with (nolock) ON O1.ObjectTypeID = OT1.ID
        inner join dbo.ObjectTypeProperty otp1 with (nolock) on (ot1.ID=otp1.ObjectTypeID)
        inner join dbo.Property p1 with (nolock) on(p1.ID=otp1.PropertyID)
        inner join ObjectProperty op1 with (nolock) on (op1.ObjectTypePropertyID=otp1.ID and op1.ObjectID=O1.ID and op1.deletedon is null)     
        inner join Object O2 with (nolock) ON (R.Object2ID = O2.ID and o2.IsArchived=0)
        INNER JOIN ObjectType OT2 with (nolock) ON O2.ObjectTypeID = OT2.ID
    where  OT1.Name = 'Netwerk component'       
        and OT2.Name = 'Adres'
        and p1.prompt = ('MonitorHostgroup')
        and
        case
            when p1.DataType = 'C' then (select cv1.Description from CodeValue cv1 where (op1.CodeValueID=cv1.ID))
            when p1.DataType = 'D' then cast(day(op1.DateValue) as varchar(2)) +'/' + cast(month(op1.DateValue) as varchar(2))+'/'  + cast(year(op1.DateValue) as varchar(4))
            when p1.DataType = 'S' then op1.StringValue
            when p1.DataType = 'N' then cast (op1.NumericValue as varchar(800))
            when p1.DataType = 'H' then op1.StringValue
            when p1.DataType = 'B' then cast (op1.NumericValue as varchar(800))
            when p1.DataType = 'E' then op1.StringValue
            when p1.DataType = 'R' then cast (op1.NumericValue as varchar(800))
            else p1.DataType/*'Ongekend'*/
        end <> 'None'
  UNION
    SELECT
        o.Name as 'Object naam',
        ot.Name as 'Type Naam',
        'BMVId' as 'Eigenschap Naam',
        cast (o.ID as varchar(10)) as 'Eigenschap Value'
    FROM Object o with (nolock)
        INNER JOIN ObjectType ot with (nolock) ON (o.ObjectTypeID = ot.ID and o.IsArchived=0)
        inner join dbo.ObjectTypeProperty otp with (nolock) on (ot.ID=otp.ObjectTypeID)
        inner join dbo.Property p with (nolock) on(p.ID=otp.PropertyID)
        inner join ObjectProperty op with (nolock) on (op.ObjectTypePropertyID=otp.ID and op.ObjectID=o.ID and op.deletedon is null)
    where ot.Name = 'Netwerk component'      
        and p.prompt = ('Monitorhostgroup')
        and
        case
            when p.DataType = 'C' then (select cv1.Description from CodeValue cv1 where (op.CodeValueID=cv1.ID))
            when p.DataType = 'D' then cast(day(op.DateValue) as varchar(2)) +'/' + cast(month(op.DateValue) as varchar(2))+'/'  + cast(year(op.DateValue) as varchar(4))
            when p.DataType = 'S' then op.StringValue
            when p.DataType = 'N' then cast (op.NumericValue as varchar(800))
            when p.DataType = 'H' then op.StringValue
            when p.DataType = 'B' then cast (op.NumericValue as varchar(800))
            when p.DataType = 'E' then op.StringValue
            when p.DataType = 'R' then cast (op.NumericValue as varchar(800))
            else p.DataType/*'Ongekend'*/
        end <> 'None'
order by o.Name, ot.Name''')

	#fetch alle rijen en plaats in dictionary
	#rij 0 = NAAM
	#rij 1 = TYPE
	#rij 2 = Eigenschap
	#rij 3 = Waarde
	bmv = tree()
	for row in cur.fetchall():
		name = row[0]
		name = name.upper()
		name = re.sub(r"_UNIT.*",'',name)
		if not bmv[name][row[2]]:
			name = name.strip()
			bmv[name][row[2]] = row[3]
	#close the cursor and connection
	cur.close()
	conn.close()

	#edit the global gotostep variable to 2
	global gotostep
	gotostep = 2

	generateoutput("step 1: getmbvdata COMPLETED")
	#print (bmv)

	#return the dictionary
	return bmv

def processbmvdict(bmv):
	generateoutput("step 2: processmbvdata STARTED")
	#hostgroups = ["MANAP-PTP-AP-BANDW", "MANAP-IPVPN-SWITCH-BANDW", "MANAP-IPVPN-SWITCH", "MANAP-SWITCH", "UPS"]
	hostgroups = ["UPS", "MANAP-IPVPN-SWITCH", "MANAP-SWITCH", "MANAP-PTP-AP-BANDW", "INTERNET-ROUTER"]
	#hostgroups = ["UPS"]
	folders = {}

	for middel in bmv:

		hostgroup = bmv[middel]['MonitorHostgroup']
		if hostgroup == "MANAP-IPVPN-SWITCH-BANDW":
			hostgroup = "MANAP-IPVPN-SWITCH"
			#print(bmv[middel] + "\n")

		if "UPS_" in middel:
			hostgroup = "UPS"

		if hostgroup in hostgroups:

			folders.setdefault(hostgroup,[])
			###Interface###
			#Check if uplink is available (default is dict)
			if isinstance(bmv[middel]['NetwerkUplink'], str):
				interf = bmv[middel]['NetwerkUplink']
				interf = interf.strip()
			else:
				interf = ""
			#print("interface = " + interf + "\n")

			#Strip tailing zeros (convert to interger)
			searchObj = re.search( r'([0-9]{1,4})', interf, re.M|re.I)
			if searchObj:
				interf = searchObj.group()
				#print("interface = " + interf + "\n")
			#else:
				#print("Nothing found!! (%s)" %interf)

			#if length is 1 digit, add zero
			if len(interf) == 1:
				interf = "0" + interf
				#print("interface = " + interf + "\n")
		
			###IP-Adress###
			if isinstance(bmv[middel]['NetwerkIP'], str):
				ipaddress = bmv[middel]['NetwerkIP']            
				ipaddress = ipaddress.strip()
			else:
				ipaddress = ""

			if isinstance(bmv[middel]['BMVId'], str):
				bmvid = bmv[middel]['BMVId']
			else:
				bmvid = ""

			###Alias###
			if isinstance(bmv[middel]['NetwerkModel'], str) and bmv[middel]['NetwerkModel']:
				netwerkmodel = bmv[middel]['NetwerkModel']
				netwerkmodel.strip()
			else:
				netwerkmodel = "geen netwerkmodel gedefinieerd"
		
			if isinstance(bmv[middel]['Adres'], str) and bmv[middel]['Adres']:
				adres = bmv[middel]['Adres']
				adres.strip()
			else:
				adres = "geen adres gedefinieerd"

			alias = adres + " | " + netwerkmodel            
			alias = alias.replace("'", "")

			#Check Alias for UTF-8 charset
			try:
				alias.decode('utf-8')
			except UnicodeDecodeError:
				alias = "geen UTF-8 charset"
			
			#convert not allowed characters to dash symbol
			middel1 = re.sub("[^a-zA-Z0-9-_]+", "-", middel)
			
			if ipaddress and bmv[middel]['Status'] == "Actief - Operationeel":
				folders[hostgroup].append((middel1,alias,ipaddress,interf,bmvid))

	#print(folders)

	global gotostep
	gotostep = 3

	generateoutput("step 2: processmbvdata COMPLETED")
	return folders


def checkobjects(bmv):
	generateoutput("step 3: checkobjects STARTED")
	l_filenames = []
	l_filenames1 = []
	b_filenames = []
	new_items = []
	delete_items = []
	
	#Get the object in checkmk based on the watofolder (from bmv!)	
	for key in foldertree:
		host_mk = watopath + foldertree[key] + "/hosts.mk"
		if os.path.isfile(host_mk):
			with open(host_mk) as f:
				for line in f:
					searchObj = re.search(r"([a-zA-Z0-9_-]+)\|snmp", line)
					if searchObj:						
						filename = searchObj.group(1)						
						l_filenames1.append(filename)	

	#Get the objects in checkmk based on the autocheckfolder
	for root, dirs, files in os.walk(autocheckpath):
		for filename in files:
			searchObj = re.search("([a-zA-Z0-9_-]+)", filename, re.M|re.I)
			if searchObj:								
				filename = searchObj.group()
				#check if object is from bmv
				if filename in l_filenames1:
					l_filenames.append(filename)
	
	#Get all the object from bmv
	for hostgroup in bmv:
		for name, s_alias, ipaddress, interf, bmvid in bmv[hostgroup]:
			b_filenames.append(name)
	
	#which items are not in checkmk yet (bmv - checkmk)
	new_items = list(set(b_filenames) - set(l_filenames))
	#which items should be delete from checkmk (checkmk - bmv)
	delete_items = list(set(l_filenames) - set(b_filenames))
	
	global gotostep
	gotostep = 4
	
	#print output
	generateoutput("step 3.x: %s host(s) to CREATE" % len(new_items))
	if new_items:
		for i in range(len(new_items)):
			generateoutput("step 3.x: hosts %s: %s" % (i+1, new_items[i]))
	generateoutput("step 3.x: %s host(s) to DELETE" % len(delete_items))
	if delete_items:
		for i in range(len(delete_items)):
			generateoutput("step 3.x: hosts %s: %s" % (i+1, delete_items[i]))
	generateoutput("step 3: checkobjects COMPLETED")
	
	return(new_items,delete_items)

def createfiles(bmv):
	generateoutput("step 4: createfiles STARTED")
	
	#Create WATO files and folders
	for folder in bmv:		
		try:
			os.makedirs(watopath + foldertree[folder])
			generateoutput("step 4.x: wato Folder %s created" % folder)
		except os.error:
			generateoutput("step 4.x: wato Folder %s already exist" % foldertree[folder])
			pass

		#all the properties for the WATO file
		all_hosts = "" 
		host_attributes = "" 
		ips = ""
		extra_host_conf = ""
		explicit_snmp_community = ""


		for name, s_alias, ipaddress, interf, bmvid in bmv[folder]:
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
		generateoutput("step 4.x: hosts.mk file in folder %s created" % foldertree[folder])
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

	#Create autocheck file
	for folder in bmv:
		for name, s_alias, ipaddress, interf, bmvid in bmv[folder]:
			if not os.path.isfile(autocheckpath + name + '.mk'):
				autocheck_mk = open(autocheckpath + name + '.mk','w')
				autocheck_mk.write("[\n")
				if interf:
					if folder == "MANAP-PTP-AP-BANDW":
						autocheck_mk.write("  (\'%s\', \'if64\', \'%s\', {\'state\': [\'1\']}),\n" % (name, interf) )
					else:
						autocheck_mk.write("  (\'%s\', \'if64\', \'0000%s\', {\'state\': [\'1\']}),\n" % (name, interf) )
				autocheck_mk.write("  (\"%s\", \"snmp_info\", None, None),\n" % name)
				autocheck_mk.write("  (\"%s\", \"snmp_uptime\", None, None),\n" % name)
				autocheck_mk.write("]\n")
				autocheck_mk.close
				generateoutput("step 4.x: autocheck file %s.mk created" % name)
				
			'''
			else:
				print("autocheck file exist")
			'''
	#Create notes file
	for folder in bmv:
		for name, s_alias, ipaddress, interf, bmvid in bmv[folder]:
			if not os.path.isfile(notespath + name):
				notes = open(notespath + name,'w')
				notes.write("<HTML><BODY>\n")
				notes.write("<A HREF=\"http://www.bmv.local/ObjectViewer.aspx?Id=%s\">link naar BMV</A>\n" % bmvid)
				notes.write("</BODY></HTML>\n")
				notes.close
				generateoutput("step 4.x: notes file %s created" % name)
	
	global gotostep
	gotostep = 5
	
	generateoutput("step 4: createfiles COMPLETED")
	
	

def deletewato(bmv):
	generateoutput("step 5: deletewato STARTED")
	for root, dirs, files in os.walk(watopath):
		#go through all the folders
		for name in dirs:
			keys = []
			delete = 1
			#add the path to the folder
			if root.endswith('/'):
				path = root + name
			else:
				path = root + "/" + name
			#print(path)
			
			#check which hostgroups are mapped to that folder and put them in an array
			for key in foldertree:
				if foldertree[key] in path:
					#print(key + " : " + path)
					keys.append(key)
			
			
			#check if any of the hostgroups are still used in bmv.
			if keys:
				for hostgroup in bmv:
					if hostgroup in keys:
						delete = 0
						break
			else:
				delete = 0
			
			#If not in use, delete the folder
			if delete:
				shutil.rmtree(path)				
				generateoutput("step 5.x: watofolder %s deleted" % name)
	global gotostep
	gotostep = 6
	
	generateoutput("step 5: deletewato COMPLETED")

def deleteautocheck(hosts):
	generateoutput("step 6: deleteautocheck STARTED")
	if hosts:
		for host in hosts:
			os.remove(autocheckpath + host + ".mk")
			generateoutput("step 6.x: autocheck file %s.mk deleted" % host)	

	global gotostep
	gotostep = 7
	
	generateoutput("step 6: deleteautocheck COMPLETED")
		
def checkautocheck(bmv):
	generateoutput("step 7: checkautocheck STARTED")
	#check every autocheck file if bmv uplink interface is used
	for hostgroup in bmv:
		for name, s_alias, ipaddress, interf, bmvid in bmv[hostgroup]:
			
			autocheck_mk = open(autocheckpath + name + '.mk','rw')
			txt = autocheck_mk.read()
			searchObj = re.search( r'(%s)' % interf, txt, re.M|re.I)
			autocheck_mk.close
			
			#If interface is not found, add it to the file
			if not searchObj:				
				f = open(autocheckpath + name + '.mk', "r")
				contents = f.readlines()
				f.close()

				contents.insert(1, "  (\'%s\', \'if64\', \'0000%s\', {\'state\': [\'1\']}),\n" % (name, interf))

				f = open(autocheckpath + name + '.mk', "w")
				contents = "".join(contents)
				f.write(contents)
				f.close()
				generateoutput("step 7.x: autocheck file %s.mk modified, added interface %s" % (name, interf))
				global mail
				mail = 1
	
	generateoutput("step 7: checkautocheck COMPLETED")
	
def sendmail(output):
	me = "omd_telecom@digipolis.be"
	you = "ruud.vandervelpen@digipolis.be"
	
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "omd change"
	msg['From'] = me
	msg['To'] = you
	
	html = """\
<html>
  <head></head>
  <body>
"""
	html = html + output
	html += """\        
  </body>
</html>
"""
	part = MIMEText(html, 'html')
	msg.attach(part)
	
	s = smtplib.SMTP('192.168.251.17')
	s.sendmail(me, you, msg.as_string())
	s.quit()

##############
#Start Script#
##############

gotostep = 1
output = "START SCRIPT\n"
outputhtml = "START SCRIPT<br>"
mail = 0
new_hosts = []
delete_hosts = []

while gotostep != 'x' and gotostep != 's':
	if gotostep == 1:
		d_objects = getbmvdata()		
	if gotostep == 2:
		d_object_processed = processbmvdict(d_objects)		
	if gotostep == 3:
		new_hosts, delete_hosts = checkobjects(d_object_processed)		
	if new_hosts or delete_hosts:
		mail = 1
		if gotostep == 4:
			createfiles(d_object_processed)
		if gotostep == 5:
			deletewato(d_object_processed)
		if gotostep == 6:
			deleteautocheck(delete_hosts)
	if gotostep == 4 or gotostep == 7:
		checkautocheck(d_object_processed)
		gotostep = 'x'

if mail:
	#print("MAIL YES")
	timestr = time.strftime("%Y%m%d-%H%M%S")
	logfile = open(logpath + timestr + "_omdimport.log", "w")
	logfile.write(output)	
	logfile.close
	sendmail(outputhtml)
