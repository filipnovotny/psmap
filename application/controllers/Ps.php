<?php
defined('BASEPATH') OR exit('No direct script access allowed');
require_once APPPATH.'libraries/REST_Controller.php';

class Ps extends REST_Controller
{
	public function __construct()
    {
            parent::__construct();
            $this->load->model('pss_model');
    }

    public function index_get()
    {
    	if(isset($id)){
    		$prjs = $this->ps_model->projects();
			$this->response($prjs);
    	}
    	else $this->response($this->pss_model->get_all());
    }

    public function item_get($id)
    {
		$this->pss_model->set_pk($id);
		$me = $this->pss_model->get_item();
		$this->response($me);
    }

    public function item_patch($id)
    {
        $data = $this->patch();
        $this->pss_model->set_pk($id);
        $rows_affected = $this->pss_model->patch_item($data);
        $this->response($rows_affected);
    }

    public function by_year_get($year)
    {
        $this->response($this->pss_model->get_by_year($year));
    }

    public function years_get()
    {
        $this->response($this->pss_model->get_years_with_counts());
    }
}

