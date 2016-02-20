
 
 # This program is free software; you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation; either version 2 of the License, or
 # (at your option) any later version.
 # 
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.
 # 
 # You should have received a copy of the GNU General Public License
 # along with this program; if not, write to the Free Software
 # Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

 # Created:  Feb 25 10:16:17 2015
 # 
 # @author Edik Mkoyan
 # @version 1



import ConfigParser, os, datetime
from pysnmp.hlapi import *
from pymongo import MongoClient
from tendo import singleton
######### Enforce one running instance ###########################################
me = singleton.SingleInstance()

######### Accessing the configuration file #######################################
config = ConfigParser.RawConfigParser()
config.read('/etc/portmatrix/main.cfg')
sections = config.sections()

######### Connecting to the database #############################################
database = config.get('General','database')
username = config.get('General','mongoUser')
password = config.get('General','mongoPass')
host = config.get('General','mongoHost')
port = config.get('General','mongoPort')
collection = config.get('General', 'mongoColl')
client = MongoClient("mongodb://" + username + ":" + password + "@" + host + ":" + port + "/" + database)
db = client.yerevan
coll = db[collection]

######### Update the current map ##################################################
for currentSection in sections[1:]:
	portDensity = config.getint(currentSection, 'portDensity')
	stackSwitches = config.getint(currentSection, 'stackSwitches')
	IPAddress = config.get(currentSection, 'IPAddress')
	communityString = config.get(currentSection, 'communityString')
	snmpPort = config.get(currentSection, 'snmpPort')
	for (errorIndication,
     		errorStatus,
     		errorIndex,
     		varBinds) in bulkCmd(SnmpEngine(),
                          	CommunityData(communityString),
                          	UdpTransportTarget((IPAddress, snmpPort)),
                          	ContextData(),
                          	0, 25,
                          	ObjectType(ObjectIdentity('BRIDGE-MIB', 'dot1dTpFdbPort')),
			  	lexicographicMode=False,
                          	lookupMib=True):
		if errorIndication:
    			Exception(errorIndication)
		elif errorStatus:
    			Exception(errorStatus)
		else:

        		for varBind in varBinds:
				unit = varBind[1]/portDensity + 1
				port = varBind[1] % portDensity
				portNumber = str(currentSection) + "." + str(unit) + "." + str(port)
				macAddress = varBind[0].prettyPrint()[-17:]
            			if ( unit <= stackSwitches and port != 0 ):
					coll.update( { "_id":macAddress } , {"port_number" : portNumber, "date_updated" : datetime.datetime.utcnow() }, upsert=True)


