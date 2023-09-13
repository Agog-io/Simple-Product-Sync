<?php

use Symfony\Component\Debug\Debug;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Symfony\Component\HttpKernel\HttpKernelInterface;
use PrestaShop\Module\Democustomfields17\Form\Product\Hooks\HookFieldsBuilderInterface;
use PrestaShop\Module\Democustomfields17\Form\Product\Hooks\HookFieldsBuilderFinder;
use PrestaShop\Module\Democustomfields17\Form\Product\Democustomfields17AdminForm;
use PrestaShop\Module\Democustomfields17\Form\Product\ProductFormDataHandler;
use PrestaShop\PrestaShop\Adapter\SymfonyContainer;
use PrestaShop\Module\Democustomfields17\Model\ProductCustomFields;


$interface = php_sapi_name();
//if($interface != "cli") die('Not Auth');
$home = getenv('HOME')."/httpdocs";

include_once($home.'/config/config.inc.php');
include_once(_PS_MODULE_DIR_.'democustomfields17'.DIRECTORY_SEPARATOR.'democustomfields17.php');
include_once('productgenikoimport.php');

define('_PS_ADMIN_DIR_', $home.'/adminpanel/');
define('PS_ADMIN_DIR', _PS_ADMIN_DIR_);
require_once  $home.'/app/AppKernel.php';
$kernel = new AppKernel(_PS_ENV_, _PS_MODE_DEV_);
$request = Request::createFromGlobals();



$module = new ProductGenikoImport();
$start_time = microtime(true);
//ini_set('display_errors', 1);
//ini_set('display_startup_errors', 1);
//error_reporting(E_ALL);
$module->getAllProductCategories();
$module->getProductsFromDbStepUpdate();

$end_time = microtime(true);

$execution_time = ($end_time - $start_time);

echo "Update time of script = ".$execution_time." sec";

//echo "<pre>".print_r($ret,1)."</pre>";