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

    public function by_year_get($year)
    {
        $this->response($this->pss_model->get_by_year($year));
    }

    public function index_post()
    {
        // Create a new book
    }
}

