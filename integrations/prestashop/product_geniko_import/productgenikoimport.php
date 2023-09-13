<?php
/**
* 2007-2023 PrestaShop
*
* NOTICE OF LICENSE
*
* This source file is subject to the Academic Free License (AFL 3.0)
* that is bundled with this package in the file LICENSE.txt.
* It is also available through the world-wide-web at this URL:
* http://opensource.org/licenses/afl-3.0.php
* If you did not receive a copy of the license and are unable to
* obtain it through the world-wide-web, please send an email
* to license@prestashop.com so we can send you a copy immediately.
*
* DISCLAIMER
*
* Do not edit or add to this file if you wish to upgrade PrestaShop to newer
* versions in the future. If you wish to customize PrestaShop for your
* needs please refer to http://www.prestashop.com for more information.
*
*  @author    PrestaShop SA <contact@prestashop.com>
*  @copyright 2007-2023 PrestaShop SA
*  @license   http://opensource.org/licenses/afl-3.0.php  Academic Free License (AFL 3.0)
*  International Registered Trademark & Property of PrestaShop SA
*/

use PrestaShop\Module\Democustomfields17\Form\Product\Hooks\HookFieldsBuilderInterface;
use PrestaShop\Module\Democustomfields17\Form\Product\Hooks\HookFieldsBuilderFinder;
use PrestaShop\Module\Democustomfields17\Form\Product\Democustomfields17AdminForm;
use PrestaShop\Module\Democustomfields17\Form\Product\ProductFormDataHandler;
use PrestaShop\PrestaShop\Adapter\SymfonyContainer;
use PrestaShop\Module\Democustomfields17\Model\ProductCustomFields;

if (!defined('_PS_VERSION_')) {
    exit;
}

class ProductGenikoImport extends Module
{
    protected $config_form = false;

    public function __construct()
    {
        $this->name = 'productgenikoimport';
        $this->tab = 'administration';
        $this->version = '1.0.0';
        $this->author = 'Prestashop';
        $this->need_instance = 0;

        /**
         * Set $this->bootstrap to true if your module is compliant with bootstrap (PrestaShop 1.6)
         */
        $this->bootstrap = true;

        parent::__construct();

        $this->displayName = $this->l('ProductGenikoImport');
        $this->description = $this->l('Import για να μπαίνουν τα προιόντα απο την βάση μας');

        $this->ps_versions_compliancy = array('min' => '1.6', 'max' => _PS_VERSION_);
    }

    /**
     * Don't forget to create update methods if needed:
     * http://doc.prestashop.com/display/PS16/Enabling+the+Auto-Update
     */
    public function install()
    {
        Configuration::updateValue('PRODUCTGENIKOIMPORT_LIVE_MODE', false);

        return parent::install() &&
            $this->registerHook('header') &&
            $this->registerHook('displayBackOfficeHeader');
    }

    public function uninstall()
    {
        Configuration::deleteByName('PRODUCTGENIKOIMPORT_LIVE_MODE');

        return parent::uninstall();
    }

    /**
     * Load the configuration form
     */
    public function getContent()
    {
        /**
         * If values have been submitted in the form, process.
         */
        if (((bool)Tools::isSubmit('submitProductGenikoImportModule')) == true) {
            $this->postProcess();
        }

        $this->context->smarty->assign('module_dir', $this->_path);

        $this->context->smarty->assign('data',[]);
        $this->context->smarty->assign('data',$this->getAllProductCategories());
        $this->context->smarty->assign('data',$this->getProductsFromDbStepUpdate(true));
        $output = $this->context->smarty->fetch($this->local_path.'views/templates/admin/configure.tpl');

        return $output.$this->renderForm();
    }


    public function greeklish($new_text){

        $greek_len   = array('α','ά','Ά','Α','β','Β','γ', 'Γ', 'δ','Δ','ε','έ','Ε','Έ','ζ','Ζ','η','ή','Η','θ','Θ','ι','ί','ϊ','ΐ','Ι','Ί', 'κ','Κ','λ','Λ','μ','Μ','ν','Ν','ξ','Ξ','ο','ό','Ο','Ό','π','Π','ρ','Ρ','σ','ς', 'Σ','τ','Τ','υ','ύ','Υ','Ύ','φ','Φ','χ','Χ','ψ','Ψ','ω','ώ','Ω','Ώ',' ',"'","'",',');

        $english_len = array('a', 'a','A','A','b','B','g','G','d','D','e','e','E','E','z','Z','i','i','I','th','Th', 'i','i','i','i','I','I','k','K','l','L','m','M','n','N','x','X','o','o','O','O','p','P' ,'r','R','s','s','S','t','T','u','u','Y','Y','f','F','ch','Ch','ps','Ps','o','o','O','O',' ','',' ',' ');
        $new_text  = str_replace($greek_len,$english_len,$new_text);
        return $new_text;
    }


    /**
     * Creates slug for use in create category
     *
     */
    public function slugify($text, $divider = '-')
    {
        $text = $this->greeklish($text);
        // replace non letter or digits by divider
        $text = preg_replace('~[^\pL\d]+~u', $divider, $text);

        // transliterate
        $text = iconv('utf-8', 'us-ascii//TRANSLIT', $text);

        // remove unwanted characters
        $text = preg_replace('~[^-\w]+~', '', $text);

        // trim
        $text = trim($text, $divider);

        // remove duplicate divider
        $text = preg_replace('~-+~', $divider, $text);

        // lowercase
        $text = strtolower($text);

        if (empty($text)) {
            return 'n-a';
        }

        return $text;
    }
    public function flattenArray(array $array) {
        $return = array();
        array_walk_recursive($array, function($a , $key) use (&$return) { $return[$key] = $a; });
        return $return;
    }
    /**
     * Build an unflattened array of categoru ids , with the key as the path like so
     *  [0] => (
    [Bar] => 410
    [0] => (
    [Bar>Beverage dispensers] => 510
    )
    )
     * $skip used to skip first(home) category as entry and in path
     */
    public function iterategetCatKeys($cat , $indexpath = array() , $skip = false  ){
        if(!$skip){
            $indexpath[] = $cat['name'];
            $arrayret = [];
            $arrayret[implode(">",$indexpath)] = $cat['id_category'];

        }
        if(isset($cat['children']) && count($cat['children']) >= 1){
            foreach ($cat['children'] as $innercat ){
                $arrayret[] = $this->iterategetCatKeys($innercat , $indexpath );
            }
        }
        return $arrayret;
    }
    /**
     * Returns an array with this disposision from the prestashop database and saves result to json  to use cached (mainly used for fast testing)
    [Bar] => 410
    [Bar>Beverage dispensers] => 510
     */
    public function generateCsvMissingCats($source){
        $ret =  ["gen categs for ".$source];
        $catlevelslive = $this->getAllCategoriesBySource($source);
//        $ret[] = $this->getAllCategoriesBySource($source);
        $catlevelscurrent = $this->getPathIndexedIds(true);
//                $ret[] = $catlevelslive;

        $missing = [];
        $db = Db::getInstance();
        $getlastid = "SELECT max(id_category) as max FROM ps_category";
        $maxres = $db->executeS($getlastid);
        $max = $maxres[0]['max'];
//        $ret = [];
        foreach ($catlevelslive as $key=>$livecat){
            if(!isset($catlevelscurrent[trim($key)])){
                $allitems = explode(">",$key);

                array_pop($allitems);
                if(isset($catlevelscurrent[implode(">",$allitems)])){
                    ++$max;
                    $ret[] =  "gen categ ".print_r([$max, $livecat, $catlevelscurrent[implode(">",$allitems)]],1);
//                    $ret[] =  $this->getlusinicatpagedata($this->serializeurl(trim($key)) , $max);
                    $this->createCategory( $max, $livecat, $catlevelscurrent[implode(">",$allitems)]);

                }else{

                    //$missing[$key] = array("name"=>$livecat,"parent"=>"-");

                }
            }
        }
        $this->getPathIndexedIds(false);

        return $ret;

//        die();
        //        $csv = new \ParseCsv\Csv();
        //        $csv->linefeed = "\n";
        //        $csv->titles = array(
        //            "id",
        //            "cat",
        //            "Parent",
        //
        //        );
        //        $csv->delimiter = "~";
        //        $csv->data = $missing;
        //        $csv->save('parsednewcats.csv');
    }
    public function getPathIndexedIds($cache = false){
        $this_directory = dirname(__FILE__);

        if($cache && file_exists($this_directory.'/IndexedCats.json')){
            $array = json_decode(file_get_contents($this_directory.'/IndexedCats.json') , true);
        }else{
            $helpercats = new HelperTreeCategories('associated-categories-tree', 'Categories' , null , 1);
            $array = $this->flattenArray(
                $this->iterategetCatKeys(
                    $helpercats->getData()[2],
                    array(),
                    true
                )
            );

            $content = json_encode($array);
            $fp = fopen($this_directory . "/IndexedCats.json", "w+");
            fwrite($fp, $content);
            fclose($fp);

            $helpercats = new HelperTreeCategories('associated-categories-tree', 'Categories' , null , 2);
            $array_lang = $this->flattenArray(
                $this->iterategetCatKeys(
                    $helpercats->getData()[2],
                    array(),
                    true
                )
            );

            $content = json_encode($array_lang);
            $fp = fopen($this_directory . "/IndexedCats_lang.json", "w+");
            fwrite($fp, $content);
            fclose($fp);
        }


        return $array;


    }
    /**
     * Creates a category at prestashop
     * $translate is turned off for series as they have translatable names
     */
    public function createCategory($id , $name , $parent , $translate = true , $is_series = false){
//        print_r([$id , $name , $parent , $translate = true , $is_series = false]);
//        return;
//        $_GET['forceIDs'] = true;
        $cat = new Category();
        $cat->force_id = true;
        $cat->id = $id;
        $cat->description = [ 1 => '' , 2 => '' ];
        $cat->id_parent = $parent;
        $cat->is_root_category = false;
        $cat->link_rewrite =  [ 1 => $this->slugify($name) , 2 => $this->slugify($name)];
        $cat->meta_description = [ 1=> '', 2 => '' ];
        $cat->meta_keywords = [ 1=> '', 2 => ''];
        $cat->meta_title = [ 1=> '', 2 => '' ];
        if($translate ){
            $cat->name =  [ 1 => $name , 2 => $name ];

        }else{
            $cat->name =  [ 1 => $name , 2 => $name ];

        }
//        echo "<pre>".print_r($cat,1)."</pre>";
        $save = $cat->add();
//        $this->getPathIndexedIds(false);
//
//        return;
//        $save = $cat->add();
    }

    public function createMissingCategs(){
        $catlevelscurrent = $this->getPathIndexedIds(true);
        return $catlevelscurrent;
    }
    public function getAllCategoriesBySource($source){
        $sql = "SELECT * FROM `extern_cats` WHERE `source` = \"".$source."\" LIMIT 100000000; ";
        $cats = $this->dbQuery($sql);
        $pathindexed = ["Κατάλογος Προμηθευτών" => "Κατάλογος Προμηθευτών"];

        $sourceCap = mb_convert_case($source, MB_CASE_TITLE, "UTF-8");
        $parentProm =  "Κατάλογος Προμηθευτών>" . $sourceCap ;
        $pathindexed[$parentProm] = $sourceCap;
        foreach($cats as $cat){
            $key = "Κατάλογος Προμηθευτών>" . $sourceCap . ">" . $cat['fullpath'];
            $key = explode(">",$key);
            foreach ($key as &$keyval){
                $keyval = trim($keyval);
            }
            $key = implode(">",$key);
            $pathindexed[$key] = $cat['name'];
        }
        return $pathindexed;
    }
    public function getAllProductCategories(){
        $sources = $this->getAllProductSources();
        foreach ($sources as $source){
            $name = $source['source'];
            $ret[] =  $this->generateCsvMissingCats($name);

        }
    }
    public function getAllProductSources(){

        $sql = "SELECT * FROM `extern_sources` LIMIT 100000";

        return $this->dbQuery($sql);
    }
    public function getProductsFromDbStepUpdate($testing = false){
        $lastdate =  Configuration::get('PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME'); //return "1970-01-01 01:00:00";
        $diff = strtotime('now') - $lastdate;

        $hours = $diff / ( 60 * 60 );
        if(Configuration::get('PRODUCTGENIKOIMPORT_LIVE_MODE') == true){
            if($hours > 1){
                echo "Ξεκολάει τώρα...";
            }else{
                echo "Τρέχει ήδη εδώ και " . $hours. " ωρες";
                return;
            }
        }
        echo "<br />Αρχίζει import";

        Configuration::updateValue('PRODUCTGENIKOIMPORT_LIVE_MODE', true);

        $fmt = new IntlDateFormatter(
            'el_GR',
            IntlDateFormatter::GREGORIAN,
            IntlDateFormatter::NONE
        );
// call the format function to get in string
        $timestring = $fmt->format(time());

        $today = getdate();
        $lastedit = $timestring . " || " . $today['hours'] . ':' . $today['minutes'] ;
        Configuration::updateValue('PRODUCTGENIKOIMPORT_LAST_UPDATE', $lastedit);
        Configuration::updateValue('PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME', strtotime('now'));
        $sql = "SELECT p.* FROM `extern_products` as p
        LEFT JOIN extern_sources as r on p.source = r.source 
        where p.parsed = 0 AND r.state = 1 limit 200;";
        if($testing) {
            $sql = "SELECT p.* FROM `extern_products` as p
            where p.id = 3395 limit 200;";
        }
//        sleep(100);
//
//        $sql = "SELECT ep.* , ec.fullpath , ec.name as catname , ec.source as catsource FROM `extern_products` as ep
//        LEFT JOIN `extern_relations` as er on ep.id = er.prod_id AND er.meta_key LIKE \"cat_id\"
//        LEFT JOIN `extern_cats` as ec on ec.id = er.meta_value
//        where parsed = 0 limit 1;";
        $proddata = $this->dbQuery($sql);
        foreach($proddata as &$data){
            $timestring = $fmt->format(time());

            $today = getdate();
            $lastedit = $timestring . " || " . $today['hours'] . ':' . $today['minutes'] ;
            Configuration::updateValue('PRODUCTGENIKOIMPORT_LAST_UPDATE', $lastedit);
            Configuration::updateValue('PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME', strtotime('now'));
            $idtable = $data['id'];
            $sqlgetMeta = "SELECT er.* , ec.* FROM `extern_relations` as er
            LEFT JOIN `extern_cats` as ec on ec.id = er.meta_value
            WHERE er.prod_id = ".$data['id']."  AND er.meta_key LIKE \"cat_id\";";
            $data['cats'] = $this->dbQuery($sqlgetMeta);
            $sqlgetMeta = "SELECT er.* FROM `extern_relations` as er
            WHERE er.prod_id = ".$data['id']."  AND er.meta_key NOT LIKE \"cat_id\";";
            $prodMeta = $this->dbQuery($sqlgetMeta);
            $data['meta'] = [];
            foreach($prodMeta as $metarow){
//                print_r($metarow);
                $data['meta'][$metarow['meta_key']] = $metarow['meta_value'];
            }
            $sqlgetMeta = "SELECT * FROM `extern_images` WHERE prodid = ".$data['id']."  AND found =  \"1\";";
            $prodMeta = $this->dbQuery($sqlgetMeta);
            $data['imagesCdn'] = $prodMeta;

        }
        Configuration::updateValue('PRODUCTGENIKOIMPORT_LIVE_MODE', false);
        return $this->parseProdData($proddata);
    }
    public function addManufCategs($proddata){
        $catlevelscurrent = $this->getPathIndexedIds(true);
        foreach ($proddata as &$prod){
            $catpathpref = "Κατάλογος Προμηθευτών>" . mb_convert_case($prod['source'], MB_CASE_TITLE, "UTF-8"). ">";
            $catIds = [];
            foreach ($prod['cats'] as $cat ){
                $fullpath = $catpathpref.$cat['fullpath'];
                $fullpath = explode(">" , $fullpath);
                foreach ($fullpath as &$keyval){
                    $keyval = trim($keyval);
                }

                $fullpath = implode(">",$fullpath);
//                $catIds[] = $fullpath;
                if(isset($catlevelscurrent[$fullpath])){
                    $catIds[] = $catlevelscurrent[$fullpath];
                }
            }
            $prod['catIds'] = $catIds;
        }
        return $proddata;
    }
    public function parseProdData($proddata){
        $proddata = $this->addManufCategs($proddata);
        $retlog = [];
        $goldencategorymanager = Module::getInstanceByName('goldencategorymanager');

        foreach($proddata as &$prod){
            $retlog[] = $this->createSingleProd($prod , $goldencategorymanager );
        }

        return $retlog;
    }
    public function createSingleProd($prod , $goldencategorymanager)
    {
        $db = Db::getInstance();
        $id_manufacturer = null;
        $id_supplier = null;
        $retlog = [];
        $retlog[] = 'imagecdn '.print_r($prod['imagesCdn'] , 1);
        if(strlen(trim($prod['manufacturer'])) == 0){
            $rowprod['manufacturer'] = "unknown";
        }
        if ($manufacturer = Manufacturer::getIdByName($prod['manufacturer'])) {
            $retlog[] = "exists ".$prod['manufacturer']. " id ". (int) $manufacturer ;

            $id_manufacturer = (int) $manufacturer;
        }else {
            $retlog[] = "create ".$prod['manufacturer'];
            $manufacturer = new Manufacturer();
            $manufacturer->name = $prod['manufacturer'];
            $manufacturer->active = true;
            if ($manufacturer->add()) {
                $id_manufacturer = (int) $manufacturer->id;
                $manufacturer->associateTo(1);
            }
        }
        $suppl = mb_strtoupper($prod['source']);
        if ($supplier = Supplier::getIdByName($suppl)) {
            $retlog[] = "exists ".$suppl. " id ". (int) $supplier ;

            $id_supplier = (int) $supplier;
        }else {
            $retlog[] = "create ".$suppl;

            $supplier = new Supplier();
            $supplier->name = $suppl;
            $supplier->active = true;

            if ( $supplier->add()) {
                $id_supplier = (int) $supplier->id;
                $supplier->associateTo(1);
            }
        }
         $source = mb_convert_case($prod['source'], MB_CASE_TITLE, "UTF-8");

         $ref =   $id_supplier . "--" . $prod['sku_manuf'];
         $sqlCheckIfExists = "SELECT * FROM `ps_product` WHERE mpn LIKE \"".$ref."\"; ";
        $retlog[] = $sqlCheckIfExists;

         $rescheck = $db->executeS($sqlCheckIfExists);
         $prodalreadyExists = count($rescheck) >= 1;
         $product = null;
         if($prodalreadyExists) {
             $retlog[] = "prod with mpn exists ".$ref;
             $retlog[] = $sqlCheckIfExists;
             $id_product = (int) $rescheck[0]['id_product'];
             $product = new Product($id_product);
             $product->force_id = true;
             $product->id = $id_product;
             $retlog[] = "has id  ".$id_product;

         }else{
             $retlog[] = "prod with mpn does not exists ".$ref;

             $product = new Product();
         }

         //        echo "<pre>".$rowprod['id']." -- ".print_r($rowprod,1)."</pre>";


                 //setEntityDefaultValues
                 $members = get_object_vars($product);
                 $default_values = [
                     'id_category' => [(int) Configuration::get('PS_HOME_CATEGORY')],
                     'id_category_default' => null,
                     'active' => '1',
                     'width' => 0.000000,
                     'height' => 0.000000,
                     'depth' => 0.000000,
                     'weight' => 0.000000,
                     'visibility' => 'both',
                     'additional_shipping_cost' => 0.00,
                     'unit_price' => 0,
                     'quantity' => 0,
                     'minimal_quantity' => 1,
                     'low_stock_threshold' => null,
                     'low_stock_alert' => false,
                     'price' => 0,
                     'id_tax_rules_group' => 0,
                     'description_short' => [(int) Configuration::get('PS_LANG_DEFAULT') => ''],
                     'link_rewrite' => [(int) Configuration::get('PS_LANG_DEFAULT') => ''],
                     'online_only' => 0,
                     'condition' => 'new',
                     'available_date' => date('Y-m-d'),
                     'date_add' => date('Y-m-d H:i:s'),
                     'date_upd' => date('Y-m-d H:i:s'),
                     'customizable' => 0,
                     'uploadable_files' => 0,
                     'text_fields' => 0,
                     'advanced_stock_management' => 0,
                     'depends_on_stock' => 0,
                     'is_virtual' => 0,
                 ];
                 foreach ($default_values as $k => $v) {
                     if ((array_key_exists($k, $members) && $product->$k === null) || !array_key_exists($k, $members)) {
                         $product->$k = $v;
                     }
                 }
                 $isonsale = $prod['sale'] > 0;
                 $product->on_sale = $isonsale;
                 $product->reference = $ref;
                 $product->mpn = $ref;
                 if($isonsale){
                     $product->reduction_price = (float) $prod['price']  - (float) $prod['sale'];
                     $retlog[] = "isonsale " .$prod['sale'];
                     $retlog[] = "reduction " . $product->reduction_price;
                 }else{
                     $retlog[] =  "not_on_sale";

                 }
                 /*
         //        $product->width  = $rowprod['width'];
         //        $product->depth  = $rowprod['depth'];
         //        $product->height = $rowprod['height'];
*/
                 $product->shop = (int) Configuration::get('PS_SHOP_DEFAULT');
                 $product->id_shop_default = (int) Configuration::get('PS_SHOP_DEFAULT');

                 // link product to shops
                 $product->id_shop_list = [ $product->id_shop_default ];





                 $product->id_tax_rules_group = 1;
                 $address = $this->context->shop->getAddress();
                 $tax_manager = TaxManagerFactory::getManager($address, $product->id_tax_rules_group);
                 $product_tax_calculator = $tax_manager->getTaxCalculator();
                 $product->tax_rate = $product_tax_calculator->getTotalRate();
                 $product->price = floatval($prod['price']);
                 // If a tax is already included in price, withdraw it from price
                 if ($product->tax_rate) {
//                     $product->price = (float) number_format($product->price / (1 + $product->tax_rate / 100), 6, '.', '');
                     $retlog[] =  "price is ".$product->price;
                     $retlog[] =  "url ".$prod['url'];
//                     $retlog[] =  "url ".$prod['price'];


                 }
                 $product->active = 1;

                $product->id_manufacturer = (int) $id_manufacturer;
                $product->id_supplier = (int) $id_supplier;
                /* if ($manufacturer = Manufacturer::getIdByName($rowprod['manufacturer'])) {
                     $product->id_manufacturer = (int) $manufacturer;
                 }else {
                     echo "create ".$rowprod['manufacturer']."<br />";
                     $manufacturer = new Manufacturer();
                     $manufacturer->name = $rowprod['manufacturer'];
                     $manufacturer->active = true;
                     if ($manufacturer->add()) {
                         $product->id_manufacturer = (int) $manufacturer->id;
                         $manufacturer->associateTo(1);
                     }
                 }

                 if ($supplier = Supplier::getIdByName($rowprod['supplier'])) {
                     $product->id_supplier = (int) $supplier;
                 }*/
                $retlog[] = "cats are";
                 $retlog[] =  $prod['catIds'];

                 $product->category = $prod['catIds'];
                 $product->id_category = []; // Reset default values array
                $associated = $goldencategorymanager->getCategoryRel(false , $product->id);
                echo gettype($associated);
              
                if(gettype($associated) == "boolean" || count($associated) == 0){
                    $product->id_category[] =  12265 ;
                }else{
                    foreach($associated as $ass_Cat){
                        $product->id_category[] = $ass_Cat['targ_id_category'];
                    }
                }
                foreach ($product->category as $value) {
                     if (is_numeric($value)) {
                         if (Category::categoryExists((int) $value)) {
                             $associatedCat = $goldencategorymanager->getCategoryRel($value , false);
                             foreach($associatedCat as $ass_Cat){
                                 $product->id_category[] = $ass_Cat['targ_id_category'];
                             }
                             $product->id_category[] = (int) $value;
                         }
                     }
                 }
                 if(count($product->id_category) == 0){
                     $product->id_category[] = 2;
                 }

                $retlog[] = [  1 => $this->slugify($prod["name"]) , 2 => $this->slugify($prod["name"]) ];

                 $product->id_category = array_values(array_unique($product->id_category));
                 $product->id_category_default = (int) $product->id_category[0];
                 $product->link_rewrite = [  1 => $this->slugify($prod["name"]) , 2 => $this->slugify($prod["name"]) ];

                 $product->name = [ 1 => $prod["name"] , 2 => $prod["name"] ];
                 $product->description = [ 1 => $prod["desc"] , 2 => $prod["desc"] ];
//                 echo "<p>".$product->name[1]." --- ".$product->reference."</p>";
                 $valid_link = Validate::isLinkRewrite($product->link_rewrite[1]);
                 if (!$valid_link) {
                     $link_rewrite = Tools::link_rewrite($product->name[1]);
                     if ($link_rewrite == '') {
                         $link_rewrite = 'friendly-url-autogeneration-failed';
                     }
                 }
                $retlog[] = $product->link_rewrite;

                 if (!$valid_link) {
                     $product->link_rewrite = AdminImportController::createMultiLangField($link_rewrite);
                 }
                $retlog[] = $product->link_rewrite;
//                $retlog[] = $prod;

                $product->quantity = 0;
                echo "<pre>";
                print_r($product->name);
                echo "</pre>";
                $field_error = $product->validateFields("UNFRIENDLY_ERROR", true);
                $lang_field_error = $product->validateFieldsLang("UNFRIENDLY_ERROR", true);
//                $retlog[] = [$lang_field_error , $field_error ];



        $product->quantity = 0;

//        print_r($field_error);
        if ($field_error === true && $lang_field_error === true) {
//            echo "passed validity";
//            echo "passed validity<br>";
            $productExistsInDatabase = false;

            if ($product->id && Product::existsInDatabase((int) $product->id, 'product')) {
                $productExistsInDatabase = true;
                $product->update();
                $retlog[] =  "exists - update prod with id ".$product->id;
//                echo "- but exists ".$product->id."<br>";
            }else{
                $retlog[] =  "addd prod with id ".$product->id;

                if (isset($product->date_add) && $product->date_add != '') {
                    $res = $product->add(false);
                } else {
                    $res = $product->add();
                }
            }
        }else{
            return;
        }
        $retlog[] = "prod in db with id ".$product->id;

//        echo "- extrafor ".$product->id."<br>";

//        $updatetoindexed = 'UPDATE `ps_product_lang` SET `isindexed` = \'0\' WHERE `ps_product_lang`.`id_product` = '.$product->id.'; ';
//        $db->execute($updatetoindexed);

        StockAvailable::setProductOutOfStock((int) $product->id, (int) $product->out_of_stock);

//        $product = new Product($rowprod['IDPROD'], false);
        $found_sp_price = false;
        $specific_price = SpecificPrice::getSpecificPrice($product->id, 1, 0, 0, 0, 1, 0, 0, 0, 0);

        if (is_array($specific_price) && isset($specific_price['id_specific_price'])) {
            $specific_price = new SpecificPrice((int) $specific_price['id_specific_price']);
            $found_sp_price = true;
            $retlog[] = "found spec price ".$product->id;

        } else {
            $specific_price = new SpecificPrice();
            $retlog[] = "create spec price ".$product->id;

        }

        if((isset($product->reduction_price) && $product->reduction_price > 0)){
            $specific_price->id_product = (int) $product->id;
            $specific_price->id_specific_price_rule = 0;
            $specific_price->id_shop = 1;
            $specific_price->id_currency = 0;
            $specific_price->id_country = 0;
            $specific_price->id_group = 0;
            $specific_price->price = -1;
            $specific_price->id_customer = 0;
            $specific_price->from_quantity = 1;
            $specific_price->reduction = $product->reduction_price * 1.24;
            $specific_price->reduction_type = 'amount';
            $specific_price->from =  '0000-00-00 00:00:00';
            $specific_price->to = '2030-01-01 00:00:00';
            $specific_price->save();
        }elseif($found_sp_price){
            $retlog[] = "found spec price deleteing ".$product->id;
            $specific_price->delete();
        }

        $product->updateCategories(array_map('intval', $product->id_category));
        $retlog[] = "add cats with id ".print_r($product->id_category , 1);

        if(!$product->cache_default_attribute) {
            Product::updateDefaultAttribute($product->id);
        }
//        $features = $rowprod['features'];
/*
        foreach (explode("^", $rowprod['features']) as $single_feature) {
            if (empty($single_feature)) {
                continue;
            }
            $tab_feature = explode(':', $single_feature);
            $feature_name = isset($tab_feature[0]) ? trim($tab_feature[0]) : '';
            $feature_value = isset($tab_feature[1]) ? trim($tab_feature[1]) : '';
            $position = isset($tab_feature[2]) ? (int) $tab_feature[2] - 1 : false;
            $custom = isset($tab_feature[3]) ? (int) $tab_feature[3] : false;
            if (!empty($feature_name) && !empty($feature_value)) {
                $id_feature = (int) Feature::addFeatureImport($feature_name, $position);
                $id_product = (int) $product->id;
                $id_feature_value = (int) FeatureValue::addFeatureValueImport($id_feature, $feature_value, $id_product, 1, $custom);
//                $id_feature_value2 = (int) FeatureValue::addFeatureValueImport($id_feature, $feature_value, $id_product, 2, $custom);
                Product::addFeatureProductImport($product->id, $id_feature, $id_feature_value);
            }
        }
        Feature::cleanPositions();*/
        StockAvailable::setQuantity((int) $product->id, 0, (int) $prod['stock'], (int) 1);

        $datacustfields = new ProductFormDataHandler();
        $datatoupd = $datacustfields->getData(  [
                'id_product' => (int) $product->id
            ]
        );

        $datatoupd['id_product'] = $product->id;
        $datatoupd['id_langimport'] = 1;
//        if(isset($rowprod["id_category_default"])){
//            Db::getInstance()->update('product', array('id_category_default' => $rowprod['id_category_default']), 'id_product = ' . (int)$datatoupd['id_product']);
//            Db::getInstance()->update('product_shop', array('id_category_default' => $rowprod['id_category_default']), 'id_product = ' . (int)$datatoupd['id_product']);
//        }
//        $encoded_fields = array("stockquantity","content_count","content_unit","order_unit","allprices","delivery_days","titledata", "descriptionMulti", "imagesCDN", "imagesCDNMulti" , "attributesMulti"  );
        $ProductCustomFieldsDef = ProductCustomFields::$definition;
        foreach($ProductCustomFieldsDef['fields'] as $fname=>$field){
            if($fname != 'id_product'){
                if($fname == "imagesCDN"){
                    $arrImages = [];
                    foreach($prod['imagesCdn'] as $image){
                        $arrImages[] = str_replace("httpdocs","https://cdn.horeca.gr",$image['serverpath']);
                    }
                    $importval = json_encode($arrImages);
                    $retlog[] = $importval;
                    $datatoupd[$fname] = $importval;
                }
                if($fname == "content_count") {
                    if(isset($prod['meta']['syskevasia']) && is_numeric($prod['meta']['syskevasia'])){
                        $syskvsiaObj = new stdClass();
                        $syskvsiaObj->{$product->reference} = $prod['meta']['syskevasia'];
                        $importval = json_encode($syskvsiaObj);
                        $retlog[] = $importval;
                        $datatoupd[$fname] = $importval;

                    }
                }

//                if($fname == "content_count"){
//                    $arrImages = [];
//                    foreach($prod['imagesCdn'] as $image){
//                        $arrImages[] = str_replace("httpdocs","https://cdn.horeca.gr",$image['serverpath']);
//                    }
//                    $importval = json_encode($arrImages);
//                    $retlog[] = $importval;
//                    $datatoupd[$fname] = $importval;
//                }
//                if(isset($rowprod[$fname."_custom_field"])){
//                    $importval = $rowprod[$fname."_custom_field"];
//                    if(in_array($fname, $encoded_fields)){
//                        $importval = base64_decode($importval);
//                    }
//
//                    if(isset($field['lang']) && $field['lang'] == true){
//                        $datatoupd[$fname][1] = $importval;
//                    }else{
//                        $datatoupd[$fname] = $importval;
//                    }
////id|active|name|category|price_tex|id_tax_rules_group|wholesale_price|on_sale|reduction_price|reduction_percent|reduction_from|reduction_to|reference|supplier_reference|supplier|manufacturer|ean13|upc|mpn|titledata_custom_field|descriptionMulti_custom_field|imagesCDN_custom_field|imagesCDNMulti_custom_field|attributesMulti_custom_field
//                }
            }
        }
        $datatoupd['id_product'] = $product->id;

        $retlog[] = $prod['meta'];
        $retlog[] = $product->id;
        $datacustfields->save($datatoupd);
        /*
        $encoded_fields = array("stockquantity","content_count","content_unit","order_unit","allprices","delivery_days","titledata", "descriptionMulti", "imagesCDN", "imagesCDNMulti" , "attributesMulti"  );
        $ProductCustomFieldsDef = ProductCustomFields::$definition;
        foreach($ProductCustomFieldsDef['fields'] as $fname=>$field){
            if($fname != 'id_product'){
                if(isset($rowprod[$fname."_custom_field"])){
                    $importval = $rowprod[$fname."_custom_field"];
                    if(in_array($fname, $encoded_fields)){
                        $importval = base64_decode($importval);
                    }

                    if(isset($field['lang']) && $field['lang'] == true){
                        $datatoupd[$fname][1] = $importval;
                    }else{
                        $datatoupd[$fname] = $importval;
                    }
//id|active|name|category|price_tex|id_tax_rules_group|wholesale_price|on_sale|reduction_price|reduction_percent|reduction_from|reduction_to|reference|supplier_reference|supplier|manufacturer|ean13|upc|mpn|titledata_custom_field|descriptionMulti_custom_field|imagesCDN_custom_field|imagesCDNMulti_custom_field|attributesMulti_custom_field
                }
            }
        }
        $datacustfields->save($datatoupd);*/
//        }*/
        $sql = "UPDATE `extern_products` SET `parsed` = '1' WHERE `extern_products`.`id` = ".$prod['id'];
        $this->dbQuery($sql);
//
//        $sql = "SELECT ep.* , ec.fullpath , ec.name as catname , ec.source as catsource FROM `extern_products` as ep
//        LEFT JOIN `extern_relations` as er on ep.id = er.prod_id AND er.meta_key LIKE \"cat_id\"
//        LEFT JOIN `extern_cats` as ec on ec.id = er.meta_value
//        where parsed = 0 limit 1;";
//        $proddata = $this->dbQuery($sql);
        return $retlog;
    }


    public function dbQuery($sql = ""){
        $config = $this->getConfigFormValues();
        $servername = $config['PRODUCTGENIKOIMPORT_ACCOUNT_IP'];
        $username = $config['PRODUCTGENIKOIMPORT_ACCOUNT_USER'];
        $password = $config['PRODUCTGENIKOIMPORT_ACCOUNT_PASSWORD'];
        $db = $config['PRODUCTGENIKOIMPORT_ACCOUNT_DB'];

        // Create connection
        $conn = new mysqli($servername, $username, $password , $db);
        mysqli_set_charset($conn, "utf8");



        // Check connection
        if ($conn->connect_error) {
            return [];
//            return print_r([$servername, $username, $password , $db],1)."Connection failed: " . $conn->connect_error;

        }
        $result = $conn->query($sql);
        $ret = [];
        if ($result->num_rows > 0) {
            while($row = $result->fetch_assoc()) {
                $ret[] = $row;
            }

        }
        return $ret;
//        return "Connected successfully";
    }

    /**
     * Create the form that will be displayed in the configuration of your module.
     */
    protected function renderForm()
    {
        $helper = new HelperForm();

        $helper->show_toolbar = false;
        $helper->table = $this->table;
        $helper->module = $this;
        $helper->default_form_language = $this->context->language->id;
        $helper->allow_employee_form_lang = Configuration::get('PS_BO_ALLOW_EMPLOYEE_FORM_LANG', 0);

        $helper->identifier = $this->identifier;
        $helper->submit_action = 'submitProductGenikoImportModule';
        $helper->currentIndex = $this->context->link->getAdminLink('AdminModules', false)
            .'&configure='.$this->name.'&tab_module='.$this->tab.'&module_name='.$this->name;
        $helper->token = Tools::getAdminTokenLite('AdminModules');

        $helper->tpl_vars = array(
            'fields_value' => $this->getConfigFormValues(), /* Add values for your inputs */
            'languages' => $this->context->controller->getLanguages(),
            'id_language' => $this->context->language->id,
        );

        return $helper->generateForm(array($this->getConfigForm()));
    }

    /**
     * Create the structure of your form.
     */
    protected function getConfigForm()
    {
        return array(
            'form' => array(
                'legend' => array(
                'title' => $this->l('Settings'),
                'icon' => 'icon-cogs',
                ),
                'input' => array(
                    array(
                        'col' => 3,
                        'type' => 'text',
                        'prefix' => '<i class="icon icon-envelope"></i>',
                        'desc' => $this->l('Enter the server ip address'),
                        'name' => 'PRODUCTGENIKOIMPORT_ACCOUNT_IP',
                        'label' => $this->l('IP addresss'),
                    ),
                    array(
                        'col' => 3,
                        'type' => 'text',
                        'prefix' => '<i class="icon icon-envelope"></i>',
                        'desc' => $this->l('Enter a valid user'),
                        'name' => 'PRODUCTGENIKOIMPORT_ACCOUNT_USER',
                        'label' => $this->l('User'),
                    ),
                    array(
                        'col' => 3,
                        'type' => 'text',
                        'prefix' => '<i class="icon icon-envelope"></i>',
                        'desc' => $this->l('Enter a DB'),
                        'name' => 'PRODUCTGENIKOIMPORT_ACCOUNT_DB',
                        'label' => $this->l('DB'),
                    ),
                    array(
                        'type' => 'text',
                        'name' => 'PRODUCTGENIKOIMPORT_ACCOUNT_PASSWORD',
                        'label' => $this->l('Password'),
                    ),
                    array(
                        'type' => 'switch',
                        'name' => 'PRODUCTGENIKOIMPORT_LIVE_MODE',
                        'label' => $this->l('Τρέχει? ( Μήν το κάνετε Ναι , μόνο όχι αν εχει κολλήσει )'),
                    ),
                    array(
                        'type' => 'text',
                        'name' => 'PRODUCTGENIKOIMPORT_LAST_UPDATE',
                        'label' => $this->l('Τελευταία ενημέρωση (Αν εχει κολλήσει θα είναι πολλές ώρες πίσω)'),
                    ),
                    array(
                        'type' => 'text',
                        'name' => 'PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME',
                        'label' => $this->l('Τελευταία ενημέρωση timestring (Αν εχει κολλήσει θα είναι πολλές ώρες πίσω)'),
                    ),
                ),
                'submit' => array(
                    'title' => $this->l('Save'),
                ),
            ),
        );
    }

    /**
     * Set values for the inputs.
     */
    protected function getConfigFormValues()
    {
        return array(
            'PRODUCTGENIKOIMPORT_ACCOUNT_IP' => Configuration::get('PRODUCTGENIKOIMPORT_ACCOUNT_IP', true),
            'PRODUCTGENIKOIMPORT_ACCOUNT_USER' => Configuration::get('PRODUCTGENIKOIMPORT_ACCOUNT_USER', 'contact@prestashop.com'),
            'PRODUCTGENIKOIMPORT_ACCOUNT_DB' => Configuration::get('PRODUCTGENIKOIMPORT_ACCOUNT_DB'),
            'PRODUCTGENIKOIMPORT_ACCOUNT_PASSWORD' => Configuration::get('PRODUCTGENIKOIMPORT_ACCOUNT_PASSWORD', null),
            'PRODUCTGENIKOIMPORT_LIVE_MODE' => Configuration::get('PRODUCTGENIKOIMPORT_LIVE_MODE', null),
            'PRODUCTGENIKOIMPORT_LAST_UPDATE' => Configuration::get('PRODUCTGENIKOIMPORT_LAST_UPDATE', null),
            'PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME' => Configuration::get('PRODUCTGENIKOIMPORT_LAST_UPDATE_STRTOTIME', null),
        );
    }

    /**
     * Save form data.
     */
    protected function postProcess()
    {
        $form_values = $this->getConfigFormValues();

        foreach (array_keys($form_values) as $key) {
            Configuration::updateValue($key, Tools::getValue($key));
        }
    }

    /**
    * Add the CSS & JavaScript files you want to be loaded in the BO.
    */
    public function hookDisplayBackOfficeHeader()
    {
        if (Tools::getValue('configure') == $this->name) {
            $this->context->controller->addJS($this->_path.'views/js/back.js');
            $this->context->controller->addCSS($this->_path.'views/css/back.css');
        }
    }

    /**
     * Add the CSS & JavaScript files you want to be added on the FO.
     */
    public function hookHeader()
    {
        $this->context->controller->addJS($this->_path.'/views/js/front.js');
        $this->context->controller->addCSS($this->_path.'/views/css/front.css');
    }
}
