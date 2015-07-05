import sys
from contextlib import closing
import MySQLdb
import re

def process_for_like(name):
	parts = re.split(";| |,|'|-|_",name)
	return '%'.join(parts)
	
class Location:
	name = ""
	idx = 0
	def __init__(self, db, name):
		self.name = name
		self.db = db
		self.new_record = True
	
	def execute_insert(self):
		ret = self.is_present(self.table)
		
		with closing(self.db.cursor()) as cur:
			if(ret):
				cur.execute(self.update_statement(ret))
				self.idx = ret
				self.new_record = False
			else:
				cur.execute(self.insert_statement())
				self.idx = cur.lastrowid
				self.new_record = True
				

	def db_statement(self):
		if(self.new_record):
			return self.insert_statement()
		else:
			return self.update_statement(self.idx)
		
	def is_present(self,table):
		statement = self.select_statement(table)
		with closing(self.db.cursor()) as cur:
			cur.execute(statement)
			ret = cur.fetchone()
			if ret is None:
				return None
			else:
				return ret[0]
			
class Region(Location):
	def __init__(self, db, name):
		self.table = "gpc_plaques"
		super().__init__(db, name)
		
	def select_statement(self, table):
		return "SELECT idgcp_plaques FROM `%s` WHERE `PL_Nom` LIKE '%s'" % (table, process_for_like(self.name))
		
	def insert_statement(self):
		# region
		return ("INSERT INTO `gpc_plaques`(`PL_Nom`, `PL_Ref_Date`, `PL_Ref_User`) VALUES ('%(reg_name)s',NULL,NULL)" % {"reg_name" : self.name })
	
	def update_statement(self, idx):
		# region
		return "UPDATE `gpc_plaques` SET PL_Nom='%(reg_name)s' WHERE idgcp_plaques = '%(idgcp_plaques)d'"  % {"reg_name" : self.name, "idgcp_plaques" : idx}
		
	def delete_statement(self,base_index):
		# region
		return ("DELETE FROM `gcp_plaques` WHERE `PL_Nom`='%(reg_name)s') AND idgcp_plaques>'%(base_index)d'" % {"reg_name" : self.name, "base_index" : base_index })
	
		
class BigCity(Location):
	def __init__(self, db, name, reg_fk):
		self.table = "gpc_ameps"
		super().__init__(db, name)
		self.reg_fk = reg_fk
	
	def select_statement(self, table):
		return "SELECT idgpc_ameps FROM `%s` WHERE `AM_Nom` LIKE '%s'" % (table, process_for_like(self.name))
		
	def insert_statement(self):
		return "INSERT INTO `gpc_ameps`(`AM_Nom`, `AM_URE`, `AM_Plaque`, `AM_Ref_Date`, `AM_Ref_User`, `AM_Mail`, `AM_Delai`) VALUES ('%(bigcity_name)s','%(reg_fk)d','%(reg_fk)d',NOW(),NULL,NULL,'12')" % {"bigcity_name" : self.name, "reg_fk" : self.reg_fk }
	
	def update_statement(self, idx):
		return "UPDATE `gpc_ameps` SET AM_Nom='%(bigcity_name)s' WHERE idgpc_ameps = '%(idgpc_ameps)d'"  % {"bigcity_name" : self.name, "idgpc_ameps" : idx}
	
	def delete_statement(self,base_index):
		return "DELETE FROM `gpc_ameps` WHERE `AM_Nom`='%(bigcity_name)s' AND idgpc_ameps>'%(base_index)d'" % {"bigcity_name" : self.name, "base_index" : base_index }
		
class Ure(Location):
	def __init__(self, db, name, reg_fk):
		self.table = "gpc_ure"
		super().__init__(db, name)
		self.reg_fk = reg_fk
		
	def select_statement(self, table):
		return "SELECT idgpc_ure FROM `%s` WHERE `UR_Nom` LIKE '%s'" % (table, process_for_like(self.name))
		
	def insert_statement(self):
		return "INSERT INTO `gpc_ure`(`UR_Nom`, `UR_Plaque`, `UR_ValidationAuto`, `UR_Mail`, `UR_MailACR`, `UR_MailARD`, `UR_Delai`) VALUES ('%(reg_name)s','%(reg_fk)d',0,NULL,NULL,NULL,12)" % {"reg_name" : self.name, "reg_fk" : self.reg_fk }
	
	def update_statement(self, idx):
		# region
		return "UPDATE `gpc_ure` SET UR_Nom='%(reg_name)s' WHERE idgpc_ure = '%(idgpc_ure)d'"  % {"reg_name" : self.name, "idgpc_ure" : idx}
		
	def delete_statement(self,base_index):
		return "DELETE FROM `gpc_ure` WHERE `UR_Nom`='%(reg_name)s' AND idgpc_ure>'%(base_index)d'" % {"reg_name" : self.name, "base_index" : base_index }
	
class Transfo(Location):
	def __init__(self, db, name, reg_fk,bigcity_fk, coords):
		tmp_name = name
		parts = name.split("-")
		self.short_name = ""
		self.table = "gpc_ps_tmp"
		if(len(parts)>1):
			name = " ".join(parts[:-1])
			self.name = name
			self.short_name = parts[-1]
			if (self.short_name != self.generate_shortname(name)):
				sys.stderr.write("WARNING for string %s: shortname not compatible. Generated %s. Expected: %s.\n" % (tmp_name,self.generate_shortname(name),self.short_name))
		else:
			self.short_name = self.generate_shortname(name)
		
		super().__init__(db, name)
		self.reg_fk = reg_fk
		self.bigcity_fk = bigcity_fk
		self.coords = coords
		
	def select_statement(self, table):
		return "SELECT idgpc_ps FROM `%s` WHERE `PS_Nom` LIKE '%s' OR `PS_Nat` = '%s'" % (table, process_for_like(self.name), self.short_name)
	
	def generate_shortname(self,name):
		parts = name.split(" ")
		res  = ""
		if(len(parts)==1):
			res = parts[0][:5]
		else:
			res = parts[0][0] + "." + parts[-1][:3]
		#res = res + ("_" * (5-len(res)))
		return res
		
	def insert_statement(self):
		return "INSERT INTO `gpc_ps_tmp`(`PS_Nom`, `PS_Plaque`, `PS_AMEPS`, `PS_Supprime`, `PS_Nat`,`PS_Coords`, `PS_Description`) VALUES ('%(city_name)s','%(reg_fk)d','%(bigcity_fk)d','0','%(short_name)s',POINT(%(lon)f,%(lat)f),'%(description)s')" % {"city_name" : self.name, "bigcity_fk" : self.bigcity_fk, "reg_fk" : self.reg_fk, "short_name" : self.short_name,"description": self.name + "-"+self.short_name, "lon" : self.coords[0] , "lat" : self.coords[1]}
			
	def update_statement(self, idx):
		return "UPDATE `gpc_ps_tmp` SET PS_Nat='%(short_name)s', PS_Description='%(description)s', PS_Coords=POINT(%(lon)f,%(lat)f) WHERE idgpc_ps = '%(idgpc_ps)d'"  % {"short_name" : self.short_name,"description": self.name + "-"+self.short_name, "lon" : self.coords[0] , "lat" : self.coords[1], "idgpc_ps" : idx}