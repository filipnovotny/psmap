from pygeocoder import Geocoder,GeocoderError
from pykml import parser
from os import path

from data import regions, region_numbers, departement_capitals, regions_names
from locations import Region, BigCity, Ure, Transfo

import MySQLdb

from collections import OrderedDict
import time
import sys
import argparse

kml_file = 'D:\\coding\\postessecours\\ps.kml'
f = open(kml_file)
doc = parser.parse(f).getroot()

cnt=0
init_region = 3
init_bigcity = 12
init_ure = 4
init_transfo = 343

#generate absolute queries
bigcity_idx = init_bigcity+1
region_idx = init_region+1
ure_idx = init_ure+1
transfo_idx = init_transfo+1

region_dict = OrderedDict()
bigcity_dict = OrderedDict()
ure_dict = []

inputfile = ''
outputfile = ''

parser = argparse.ArgumentParser(description='Insert data into db.')
parser.add_argument('-kml_path', default='ps.kml', help='path of the kml file to process')
parser.add_argument('-filter_table', default='gpc_ps', help='Only reference entries from this table')

args = parser.parse_args()

	

db=MySQLdb.connect('localhost', 'root', '', 'planningcapex')

for reg_name in regions_names:
	region_dict[reg_name] = (Region(db,reg_name))
	region_dict[reg_name].execute_insert()
	

for bigcity_depid,bigcity_name in departement_capitals.items():
	bigcity_dict[bigcity_name]=(BigCity(db,bigcity_name,region_dict[regions[bigcity_depid]].idx))
	bigcity_dict[bigcity_name].execute_insert()

for reg_name in regions_names:
	ure = Ure(db,reg_name,region_dict[reg_name].idx)
	ure_dict.append(ure)
	ure.execute_insert()
	
print ("################ REGION NAMES (gpc_plaques) ####################")
for key, value in region_dict.items():
	print(value.db_statement())

print ("################ URE (gpc_ure) ####################")
for ure in ure_dict:
	print(ure.db_statement())
	
print ("################ CITIES (gpc_ameps) ####################")
for key, value in bigcity_dict.items():
	print(value.db_statement())


print ("################ PLACES (gpc_ps_tmp) ####################")

for placemark in doc.Document.Folder.Placemark:
	cnt+=1	
	coords = str(placemark.Point.coordinates).split(",")
	transfo_light = Transfo(db,placemark.name.text, 0,0,[float(coords[1]),float(coords[0])])
	if (args.filter_table and transfo_light.is_present(args.filter_table)) or args.filter_table=="": #only treat existing records
		timeout = 1
		#print("##### processing record "+ placemark.name.text)
		while (True):
			try:
				results = Geocoder('AIzaSyBSrBoayfbXR1j3DEY7Rkru-EmVfuODVoM').reverse_geocode(float(coords[1]),float(coords[0]))
				break;
			except GeocoderError:
				sys.stderr.write("WARNING: Too many queries, Geocoder blocked. Waiting to be authorized again (%d) seconds...\n" % timeout);
				sys.stderr.flush()
				time.sleep(timeout)
				timeout*=2
		
		#department code has 3 or 2 characters
		reg_code = str(results[0].postal_code)[:3]
		if not (reg_code in regions):
			reg_code = str(results[0].postal_code)[:2]
			
		if reg_code in regions:
			#print (cnt,".",placemark.name.text)
			reg_name = regions[reg_code]
			bigcity_name = departement_capitals[reg_code]
			transfo = Transfo(db,placemark.name.text, region_dict[reg_name].idx,bigcity_dict[bigcity_name].idx,[float(coords[1]),float(coords[0])])
			transfo.execute_insert()
			print(transfo.db_statement())
			transfo_idx+=1
		else:
			print ("[SPEC]",cnt,".",placemark.name.text)
			print(reg_code)
			
		#print ("---")