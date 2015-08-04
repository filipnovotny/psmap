<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Main extends CI_Controller {

	public function add_debug_info($context){
		$context["config"] = array(
				"JSDEBUG" => true
			);
		return $context;
	}

	public function index()
	{
		$this->load->library('Twig');
		$this->load->helper('url');
		$context = array("STATIC_URL" => STATIC_URL, "BASE_URL" => base_url());
		
		$this->twig->render('map', $this->add_debug_info($context));
	}

	public function about()
	{
		$this->load->library('Twig');
		$this->load->helper('url');
		$this->twig->render('about', $this->add_debug_info(array("STATIC_URL" => STATIC_URL, "BASE_URL" => base_url())));
	}

	public function contact()
	{
		$this->load->library('Twig');
		$this->load->helper('url');
		$this->twig->render('contact', $this->add_debug_info(array("STATIC_URL" => STATIC_URL, "BASE_URL" => base_url())));
	}
}
