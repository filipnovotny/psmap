<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Main extends CI_Controller {

	public function index()
	{
		$this->load->library('Twig');
		$this->twig->render('map', array("STATIC_URL" => STATIC_URL));
	}

	public function about()
	{
		$this->load->library('Twig');
		$this->twig->render('about', array("STATIC_URL" => STATIC_URL));
	}

	public function contact()
	{
		$this->load->library('Twig');
		$this->twig->render('contact', array("STATIC_URL" => STATIC_URL));
	}
}
