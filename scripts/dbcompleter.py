from pygeocoder import Geocoder,GeocoderError
from pykml import parser
from geopy.distance import vincenty, great_circle

from os import path

from data import regions, region_numbers, departement_capitals, regions_names
from locations import Region, BigCity, Ure, Transfo

import MySQLdb

from collections import OrderedDict
import time
import sys
import argparse
from contextlib import closing
import re

from difflib import SequenceMatcher

def similar(a, b):
	bonus = 0.0;
	if a in b or b in a:
		bonus+=0.1
	return SequenceMatcher(None, a, b).ratio()+bonus

argparser = argparse.ArgumentParser(description='Insert data into db.')
argparser.add_argument('-kml_path', default='ps.kml', help='path of the kml file to process')
argparser.add_argument('-filter_table', default='gpc_ps', help='Only reference entries from this table')
argparser.add_argument('-dbhost', default='localhost', help='database host')
argparser.add_argument('-dbuser', default='root', help='database login')
argparser.add_argument('-dbpass',  default='', help='database password')
argparser.add_argument('-dbname', default='planningcapex', help='database name')

argparser.add_argument('-apikey', default='AIzaSyAGNS0KorSJ6bRl1aV9uExQ2KWju2m89co', help='google maps api key')


args = argparser.parse_args()

db=MySQLdb.connect(args.dbhost, args.dbuser, args.dbpass, args.dbname)

places = [dict(),dict(),dict()]

def process_name(name):
	return name.upper().replace("-"," ").replace("."," ").replace("_"," ")
def compare_names(name1,name2):
	return process_name(name1)==process_name(name2)

def get_coordinates_by_name(kml_filename,name,code, match_class=0):	
	opt_code=None
	opt_coord = None
	opt_ret=None
	opt_comment=""
	
	simil_map = dict()
	
	results = dict()
	f = open(kml_filename)
	doc = parser.parse(f).getroot()
	for placemark in doc.Document.Folder.Placemark:
		coords = str(placemark.Point.coordinates).split(",")
		transfo_light = Transfo(db,placemark.name.text, 0,0,[float(coords[1]),float(coords[0])])
		#print("comparing name: %s and %s and code: %s and %s" % (name, transfo_light.name,code, transfo_light.short_name))
		if(compare_names(transfo_light.name, name) and transfo_light.short_name == code) and match_class==0:
			places[0][transfo_light.short_name] = (float(coords[1]),float(coords[0]))
			return code,places[0][code],0,"Correspondance forte"
		elif (compare_names(transfo_light.name, name)) and match_class==1: #same name but different code		
			#this name is already used (but with different code)and there are coordinates for it			
			#or the place has a new code which matches coordinates
			if transfo_light.short_name in places[0]:
				continue
			
			places[1][name] = (float(coords[1]),float(coords[0]))			
			return transfo_light.short_name,places[1][name],0,"Correspondance par nom seul, code mis a jour. Ancien(BDD): %s Nouveau (fichier edf): %s" % (code,transfo_light.short_name)
		elif (transfo_light.short_name == code) and match_class==2: #same code but different name
			if code in places[0] and name in places[1]: #my code and name match are already taken
				
				try:
					code[-1] = str(int(code[-1])+1)
				except:
					code = code[:-1] + "0"
					
				places[0][code] = coords
				return code,places[0][code],1
			else:
				if code in places[0]: #has the same code but is 
					#places[1][name+"_dup"] = coords
					print("dupplicate record! : %s,%s" % (code,name))
					continue
				elif name in places[1]: #
					print("dupplicate name but its ok! : %s,%s" % (code,name))
					places[0][code] = coords				
				else:
					places[0][code] = coords
			return code,places[0][code],0,"Correspondance par code seul, nom non modifié. Actuel(BDD): %s Fichier edf: %s" % (name,transfo_light.name)

		elif (similar(process_name(transfo_light.name) , process_name(name))) > 0.6 and match_class==3:
			
			if transfo_light.short_name=="" or code =="":
				pass
			else:
				if(similar(transfo_light.short_name , code) < 0.5):
					continue
			
			sim = similar(process_name(transfo_light.name) , process_name(name))
			
			print ("similarities between %s and %s are %f" % (transfo_light.name , name, sim))
			if transfo_light.short_name in simil_map:
				if simil_map[transfo_light.short_name] > sim:
					print ("discarded")
					continue
				else: #discard previous candidate from map
					del places[0][transfo_light.short_name]
					
			coords = (float(coords[1]),float(coords[0]))
			if code in places[0] and name in places[1]: #my code and name match are already taken
				try:
					code[-1] = str(int(code[-1])+1)
				except:
					code = code[:-1] + "0"
					
				places[0][code] = coords
				
				opt_code = transfo_light.short_name
				opt_coord = places[0][transfo_light.short_name]
				opt_ret = 1
			else:
				if transfo_light.short_name in places[0]: #has the same code but is 
					#places[1][name+"_dup"] = coords
					print("dupplicate record! : %s,%s" % (transfo_light.short_name,name))
					print(places[0])
					continue
					opt_ret = 1
				elif name in places[1]:
					#places[0][code+"_dup"] = coords
					print("dupplicate record! : %s,%s" % (code,name))
					print(places[1])
					opt_ret = 1
				else:
					places[0][transfo_light.short_name] = coords
					opt_ret = 0
					
			opt_code = transfo_light.short_name
			opt_coord = places[0][transfo_light.short_name]
			opt_comment = "ATTENTION!!! Ni le nom, ni le code ne correspondent. En base: (%s,%s) Dans le fichier: (%s,%s). Cette correspondance a été établie avec %f%% de certitude. Le nom est laisse tel quel, le code a ete modifie (nouvelle valeur: %s)" % (name,code,transfo_light.name,transfo_light.short_name, sim*100,transfo_light.short_name)
			
			simil_map[transfo_light.short_name] = sim
				
	return opt_code,opt_coord,opt_ret,opt_comment

def get_closest_city_to(coordinates, bigcities):
	min = 100000.
	min_bigcity = None
	for bigcity_name, bigcity in bigcities.items():
		if (great_circle(bigcity["coords"],coordinates).miles) < min:
			min_bigcity = bigcity
			min = great_circle(bigcity["coords"],coordinates).miles
			
	return min_bigcity
	
statement = "SELECT idgpc_ps,PS_Nom, PS_Nat, char_length(PS_Nom) as PS_Length, PS_Plaque,PS_AMEPS,PS_Supprime FROM gpc_ps ORDER BY PS_Length DESC"
cnt = 1
substs = dict()

bigcities_statement = "SELECT AM_Nom FROM gpc_ameps"
bigcities = dict()
"""
print("computing big cities")
with closing(db.cursor()) as cur:
	cur.execute(bigcities_statement)
	for i in range(cur.rowcount):
		row = cur.fetchone()
		name = re.sub('\W+',' ', str(row[0]) )
		
		while True:
			try:
				results = Geocoder.geocode(name)
				bigcities[row[0]] = {"name": name, "coords" : results[0].coordinates }
				break
			except GeocoderError as e:
				if e.status == "ZERO_RESULTS":
					name = " ".join(name.split(" ")[:-1])
					continue
		print ("%s computed as %s : %f,%f"% (str(row[0]).encode('utf-8'),name,results[0].coordinates[0],results[0].coordinates[1]))
"""

descriptions = dict()
valids = []
override_m=0
for m in range(0,4):
	with closing(db.cursor()) as cur:
		cur.execute(statement)
		for i in range(cur.rowcount):
			
			row = cur.fetchone()
			if row[0] in valids:
				continue
			name = row[1]
			#bigcity_computed = bigcities[row[3]]
			code,coords,ret,comment = get_coordinates_by_name(args.kml_path,process_name(name),row[2], match_class = m)
			override_m = m
			if(ret is None):
				if m<3:
					print( "Error finding file reference for ", name.encode('utf-8'), "(%s)" % row[2].encode('utf-8'))
					continue
				else:
					code = row[1]
					coords = (float(-1),float(-1))
					ret = 0
					comment = "ATTENTION!!! ERREUR!!! Ce poste n'a pas ete trouve dans le fichier EDF. Il a été recopié de table à table sans aucun controle. Impossible de déterminer ses coordonnées. Coordonnées mises à -1,-1."
					override_m = 4
			description = ""
			if ret > 0:
				description = "%s :modified from %s" % (row[1],row[2])
			else:
				description = "%s :valid record" % (row[1])
			valids.append(row[0])
			descriptions[row[0]] = {"desc" : description, "code" : code, "coords" : coords, "match_quality" : override_m, "comment" : comment,
				"sql"  : 
				"INSERT INTO gpc_ps_tmp ( idgpc_ps,PS_Nom,PS_Plaque,PS_AMEPS,PS_Supprime,PS_Nat,PS_Longitude,PS_Latitude,PS_Description, PS_Confiance, PS_Commentaire) VALUES (\"%d\",\"%s\",\"%d\",\"%d\",\"%d\",\"%s\",\"%f\",\"%f\",\"%s\",\"%d\",\"%s\");" %
				(row[0],row[1], row[4],row[5],row[6],code, float(coords[1]),float(coords[0]),"%s-%s" % (row[1],code), override_m, comment)
			}

for desc,val in descriptions.items():
	#print (desc,val)
	print (val["sql"])