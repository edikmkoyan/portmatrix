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


