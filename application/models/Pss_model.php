<?php
class Pss_model extends CI_Model {

		protected $gpc_ps_table;
		protected $pk;

        public function __construct()
        {
            $this->load->database();
            $this->load->model('projects_model');
            $this->load->model('trs_model');
            $this->gpc_ps_table = "gpc_ps_tmp";
        }

        public function set_pk($pk){
        	$this->pk = $pk;
        }

        private function join_ps_and_projects(){
        	$this->db->select('idgpc_ps, PS_Nom, PS_Nat, PS_Longitude, PS_Latitude, PS_Confiance, count(idgpc_ps) as PS_Nb_Projects');
			$this->db->from($this->gpc_ps_table);
			$this->db->join('gpc_projets', sprintf('%s.idgpc_ps = gpc_projets.PR_PS',$this->gpc_ps_table));
			$this->db->where('PS_Supprime',0);
			$this->db->group_by("idgpc_ps");
        }

        public function get_by_year($year){
        	$this->join_ps_and_projects();
			$this->db->where('PR_Annee',$year);
			
			$query = $this->db->get();
			return $query->result();
        }

        public function get_all(){
        	$this->join_ps_and_projects();

            //$this->db->where('PS_Confiance',2);

        	$query = $this->db->get();
			return $query->result();
        }

        public function get_projects(){
        	$this->db->select('idgpc_projets, PR_Libelle, PR_Statut, PR_Annee, PR_Debut, PR_Fin, PR_Termine, PR_Commentaires');
			$this->db->from('gpc_projets');
			$this->db->where('PR_PS',$this->pk);

        	$query = $this->db->get();
			return $query->result('projects_model');
        }

        public function get_transfos(){
        	$this->db->select('*');
			$this->db->from('gpc_tr');
			$this->db->where('TR_PS',$this->pk);

        	$query = $this->db->get();
			return $query->result('trs_model');
        }

        public function get_item(){
        	$this->db->select('idgpc_ps, PS_Nom, PS_Nat, PS_Longitude, PS_Latitude, PS_Commentaire');
			$this->db->from($this->gpc_ps_table);
			$this->db->where('idgpc_ps',$this->pk);
			$query = $this->db->get();
			$it = $query->result('pss_model');

			if($it){
        		$it[0]->projects = $this->get_projects();
        		$it[0]->trs = $this->get_transfos();
        		return $it[0];
			}
        	else return $it;
        }

        public function get_years_with_counts(){
            $this->db->select('PR_Annee, count(gpc_projets.idgpc_projets) as PS_Nb_Projects, count(gpc_ps_tmp.idgpc_ps) as PS_Nb_Ps');
            $this->db->from($this->gpc_ps_table);
            $this->db->join('gpc_projets', sprintf('%s.idgpc_ps = gpc_projets.PR_PS',$this->gpc_ps_table),'inner');
            $this->db->where('PS_Supprime',0);
            $this->db->group_by("PR_Annee");

            $query = $this->db->get();

            return $query->result();
        }
}

?>