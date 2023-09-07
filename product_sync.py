import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from logging_window import *
import paramiko
import os
from urllib.parse import urlparse
import shutil
import time
import socket
from urllib3.connection import HTTPConnection
import pymysql
import json
from pathlib import Path

class product_sync:
    def __init__(self):
        self.isDemo = False;
        config_file = Path(__file__).with_name('config.json')
        with config_file.open('r') as f:
            self.config_data = json.load(f)
        #Helps with long response times on slow servers
        HTTPConnection.default_socket_options = (
            HTTPConnection.default_socket_options + [
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
                (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
                (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
            ]
        )
        #setting up session, with a fake user agent that mimics a browser
        self.session = requests.Session()

        self.session.headers = self.config_data["headers_http"];
        self.do_retries = True


    def logForDemo(self , logText):
        logfile = Path(__file__).with_name('logDatabase.txt')
        with logfile.open('a+') as f:
            f.write(logText+"\n")
    # Every database , http and ftp call has retry functionality due to the 
    # inconsistency of both the host and the server connections. When do_retries
    # go false that means a certain threshold of retrying has been reached in any
    # of those connections that warrants the whole program to halt , or that the user
    # has closed the program window.

    def stopUpdating(self):
        self.do_retries = False

    def getConnection(self , retries = 0):
        
        if self.isDemo :
            return

        mydb = None
        if self.do_retries == False:
            exit()
        
        try:
            mydb = pymysql.connect(
                host=self.config_data["pymysql_config"]['host'],
                user=self.config_data["pymysql_config"]['user'],
                password=self.config_data["pymysql_config"]['password'],
                database=self.config_data["pymysql_config"]['database'],
                charset=self.config_data["pymysql_config"]['charset'],
                read_timeout=self.config_data["pymysql_config"]['read_timeout'],
                write_timeout=self.config_data["pymysql_config"]['write_timeout']
            )
        except Exception as error:
            if hasattr(mydb, 'close') and callable(mydb.close):
                mydb.close()

            self.logIntoWindow("!!!!An exception occurred getConnection!!!" , True)
            self.logIntoWindow(error , True)
            self.logIntoWindow("!!!!An exception occurred getConnection!!!" , True)

            if retries < 4 :
                time.sleep(retries)
            else:
                time.sleep(4)
            
            retriesn = retries + 1
            
            return self.getConnection(retriesn)
        
        return mydb
    
    def fetchFromDb(self,sql , val = [] , retries = 0):

        if self.do_retries == False:
            exit()

        if self.isDemo :
            self.logForDemo(sql)
            return

        mydb = self.getConnection()

        mycursor = mydb.cursor()
        try:
            if len(val):       
                mycursor.execute(sql , val)
            else:
                mycursor.execute(sql)

        except Exception as error:
            mycursor.close()
            mydb.close()


            self.logIntoWindow("!!!!An exception occurred fetchFromDb!!!" , True)
            self.logIntoWindow(error , True)
            self.logIntoWindow(sql , True)
            self.logIntoWindow("!!!!An exception occurred fetchFromDb!!!" , True)
            if retries < 4 :
                time.sleep(retries)
            else:
                time.sleep(4)
            retriesn = retries + 1
            return self.fetchFromDb(sql , val , retriesn)

        columns = mycursor.description
        result = []
        for value in mycursor.fetchall():
            tmp = {}
            for (index,column) in enumerate(value):
                tmp[columns[index][0]] = column
            result.append(tmp)
        mydb.commit()
        mycursor.close()
        mydb.close()
        return result

    def logIntoWindow(self , error , iscrit = False):
        windowHelpers.logIntoWindow(error , iscrit)

    def queryDb(self , sql , val = [] , retries = 0):

        if self.do_retries == False:
            exit()
        
        if self.isDemo :
            self.logForDemo(sql)
            return
        
        mydb = self.getConnection()
        mycursor = mydb.cursor()
        try:
            if len(val):       
                mycursor.execute(sql , val)
            else:
                mycursor.execute(sql)
    
        except Exception as error:
            mycursor.close()
            mydb.close()
            self.logIntoWindow("!!!!An exception occurred queryDb!!!" , True)
            self.logIntoWindow(error , True)
            self.logIntoWindow(sql , True)
            self.logIntoWindow("!!!!An exception occurred queryDb!!!" , True)
            if retries < 4 :
                time.sleep(retries)
            else:
                time.sleep(4)
            retriesn = retries + 1
            return self.queryDb(sql , val , retriesn)


        mydb.commit()
        mycursor.close()
        mydb.close()
    
    # Retry connection with url in  case of error code , so
    # that the whole program continues execution in case of cache miss /
    # server downtime or other
    def retryableHttpSessionCall(self , url, **kwargs):
        
        num_retries = 5
        
        success_list=[200]
        for _ in range(num_retries):
            try:
                response = self.session.get(url, **kwargs)
                if response.status_code in success_list:
                    return response

            except requests.exceptions.ConnectionError:
                pass

            time.sleep(1)
        return None

    def checkAndAddImageToCDN(self, source_id , idprod , imageurl, idimg ,source_dir):
        check = self.fetchFromDb("SELECT * FROM `extern_images` WHERE sourceid LIKE \""+str(source_id)+"\" AND imageurl LIKE \""+imageurl+"\" AND prodid = "+str(idprod)+";");
        
        
        if self.isDemo :
            self.logIntoWindow("IMGDL : 1) IDPROD : "+str(idprod)+" downloaded "+imageurl , True)
            return
        
        if len(check):
            if check[0]['serverpath'] :
                print('has been downloaded dont do anything')
            else:
                url = imageurl
                path = urlparse(url).path
                ext = os.path.splitext(path)[1]
                r = self.retryableHttpSessionCall(imageurl, stream=True)
                if r == None:
                    return 
                r.raw.decode_content = True
                self.logIntoWindow("IMGDL : 1) IDPROD : "+str(idprod)+" downloaded "+imageurl , True)
                
                imageserver = source_dir + "/"+str(idimg)+ext
                fname = str(idimg)+ext
                self.logIntoWindow("IMGDL : 2) CDNURL : " + imageserver , True)
                self.saveFileSftp(imageserver , r )

                sql = "UPDATE `extern_images` SET `serverpath` = %s WHERE `extern_images`.`id` LIKE %s;"
                val = (imageserver , idimg )        
                self.queryDb(sql , val)
            
                sql = "UPDATE `extern_images` SET `imagename` = %s WHERE `extern_images`.`id` LIKE %s;"
                val = (fname , idimg )         
                self.queryDb(sql , val)

    def saveFileSftp(self , imageserver , r , retries = 1):
        transport = None
        sftp = None
        try:
            transport = paramiko.Transport((self.config_data["sftp"]['host'], 22))
            transport.connect(username = self.config_data["sftp"]['username'], password = self.config_data["sftp"]['password'])
            sftp = paramiko.SFTPClient.from_transport(transport)

            with sftp.open(imageserver, mode="w") as remote_file:
                shutil.copyfileobj(r.raw, remote_file)
            
            transport.close()
            sftp.close()
        except Exception as error:
            
            if hasattr(transport, 'close') and callable(transport.close):
                transport.close()

            if hasattr(sftp, 'close') and callable(sftp.close):
                sftp.close()


            self.logIntoWindow("!!!!An exception occurred saveFileSftp!!!" , True)
            self.logIntoWindow(error , True)
            self.logIntoWindow("!!!!An exception occurred saveFileSftp!!!" , True)
            if retries < 4 :
                time.sleep(retries)
            else:
                time.sleep(4)
            
            retriesn = retries + 1
            return self.saveFileSftp(imageserver , r , retriesn)

    def checkAddSourceToDb(self , source_name):
      
        
        check = self.fetchFromDb("SELECT * FROM `extern_sources` WHERE `source` LIKE \""+str(source_name)+"\";")
        # print("SELECT * FROM `extern_sources` WHERE \"source\" LIKE \""+str(source_name)+"\";");
        # print(len(check))
      
        if self.isDemo :
            return 1  
        if len(check):
            return check[0]['id']
        
        sql = 'INSERT INTO `extern_sources` (`id`, `source`, `state` ) '
        sql = sql + 'VALUES (NULL, %s,  1);';
        val = (source_name)
        self.queryDb(sql , val)
        return self.checkAddSourceToDb(source_name)

    def checkAndAddImageToDb(self , source_id , idprod , imageurl):
        if self.isDemo :
            return 1
        
        check = self.fetchFromDb("SELECT * FROM `extern_images` WHERE sourceid LIKE \""+str(source_id)+"\" AND imageurl LIKE \""+imageurl+"\" AND prodid = "+str(idprod)+";");
        if len(check):
            
            sql = "UPDATE `extern_images` SET `found` = '1' WHERE `extern_images`.`id` LIKE %s;"
            val = [check[0]['id']]
                
            self.queryDb(sql , val)
            return check[0]['id']
        else:
            sql = 'INSERT INTO `extern_images` (`id`, `sourceid`, `imageurl`, `prodid` , `found` ) '
            sql = sql + 'VALUES (NULL, %s, %s, %s , 1);';
            val = (source_id , imageurl , idprod )
            self.queryDb(sql , val)

            return self.checkAndAddImageToDb(source_id , idprod , imageurl);
    
    def saveImages(self , proddata , idprod , retries = 1):
        if self.isDemo :
            return

        transport = None
        sftp = None
        try:
            transport = paramiko.Transport((self.config_data["sftp"]['host'], 22))
            transport.connect(username = self.config_data["sftp"]['username'], password = self.config_data["sftp"]['password'])
            sftp = paramiko.SFTPClient.from_transport(transport)
            
        except Exception as error:
            
            if hasattr(transport, 'close') and callable(transport.close):
                transport.close()

            if hasattr(sftp, 'close') and callable(sftp.close):
                sftp.close()


            self.logIntoWindow("!!!!An exception occurred saveImages!!!" , True)
            self.logIntoWindow(error , True)
            self.logIntoWindow("!!!!An exception occurred saveImages!!!" , True)
            if retries < 4 :
                time.sleep(retries)
            else:
                time.sleep(4)
            
            retriesn = retries + 1
            return self.saveImages(proddata , idprod , retriesn )


        
        get_soucrerows = self.fetchFromDb("SELECT * FROM `extern_sources` WHERE source LIKE \""+proddata['source']+"\";");
        source_id = get_soucrerows[0]['id']
        source_dir = "httpdocs/sources/"+str(source_id)
        try:
            sftp.chdir(source_dir)  # Test if remote_path exists
        except IOError:
            sftp.mkdir(source_dir)  # Create remote_path
            sftp.chdir(source_dir)


        source_dir = str(idprod)
        # print(source_dir)
        try:
            sftp.chdir(source_dir)  # Test if remote_path exists
        except IOError:
            sftp.mkdir(source_dir)  # Create remote_path
            sftp.chdir(source_dir)
        
        if hasattr(transport, 'close') and callable(transport.close):
            transport.close()

        if hasattr(sftp, 'close') and callable(sftp.close):
            sftp.close()
            
        source_dir = "httpdocs/sources/"+str(source_id)+"/"+str(idprod)

        for image in  proddata['imageList']:
            idimg = self.checkAndAddImageToDb(source_id , idprod , image)
            self.checkAndAddImageToCDN(source_id , idprod , image , idimg ,source_dir)
            # filename = image.split("/")[-1]
            # print(filename)
            # r = requests.get(image_url, stream = True)

        # Open the url image, set stream to True, this will return the stream content.

        # try:
        #     sftp.chdir(sources_dir)  # Test if remote_path exists
        # except IOError:
        #     sftp.mkdir(sources_dir)  # Create remote_path
        #     sftp.chdir(sources_dir)
        # sftp.chdir('')
        # source_dir = "httpdocs/sources/"+str(source_id)
        # try:
        #     sftp.chdir(source_dir)  # Test if remote_path exists
        # except IOError:
        #     sftp.mkdir(source_dir)  # Create remote_path
        #     sftp.chdir(source_dir)
    
    def initSourceMissing(self , source):
        self.logIntoWindow("Initializing Db For Import Job" , False);

        check = self.fetchFromDb("SELECT COUNT(*) as cnt FROM `extern_products` WHERE source LIKE \""+source+"\" ;");
        if self.isDemo :
            self.initProgressBar( 3 )
        else:
            self.initProgressBar( check[0]['cnt'] )
        sql = "UPDATE `extern_products` SET `found` = '0' WHERE `extern_products`.`source` LIKE %s;"
        val = [source]
        self.queryDb(sql , val)        

    def initProgressBar(self , count):
        windowHelpers.getThirdUi().countInDb = count
        windowHelpers.getThirdUi().started = time.time()
        windowHelpers.getThirdUi().progress()

    def updateProgressBar(self):
        windowHelpers.getThirdUi().countNow += 1
        windowHelpers.getThirdUi().progress()

    def ParceSourceMissing(self , source):

        self.logIntoWindow("Finalize Db For Import Job" , True);

        sql = "UPDATE `extern_products` SET `found` = 2   WHERE `extern_products`.`found` = 0 AND `extern_products`.`source` LIKE  %s;"
        val = [source]
        self.queryDb(sql , val)
        sql = "UPDATE `extern_relations` SET `found` = '2' WHERE  `extern_relations`.`found` = 0 AND `extern_relations`.`source` LIKE %s;"
        val = [source]
        self.queryDb(sql , val)
        sql = "UPDATE `extern_sources` SET `state` = '1' WHERE `extern_sources`.`source` LIKE %s;"
        val = [source]
        self.queryDb(sql , val)

    def initImportState(self, source):

        self.checkAddSourceToDb(source)
        sql = "UPDATE `extern_products` SET `parsed` = '0' WHERE `extern_products`.`source` LIKE %s;"
        val = [source]
        self.queryDb(sql , val)
        sql = "UPDATE `extern_sources` SET `state` = '2' WHERE `extern_sources`.`source` LIKE %s;"
        val = [source]
        self.queryDb(sql , val)

    def addCatToDb(self , catname , catpath , parent  , source , link):
        sql = 'INSERT INTO `extern_cats` (`id`, `source`, `fullpath`, `name`, `parent_id` , `url` ) VALUES (NULL, %s, %s, %s, %s , %s);';
        val = (source , catpath , catname , str(parent) , link)
        self.queryDb(sql , val)

    def checkAndAddCatToDb(self, catname , catpath , parent  , source , link):

        check = self.fetchFromDb("SELECT * FROM `extern_cats` WHERE source LIKE \""+source+"\" AND fullpath = \""+catpath+"\";");
        if self.isDemo :
            self.logIntoWindow("CTG : EXISTS " + catpath);
            self.addCatToDb(catname , catpath , parent  , source , link)
            return 1

        if len(check):
            # print(check)
            self.logIntoWindow("CTG : EXISTS " + catpath);

            return check[0]['id']
        else:
            self.logIntoWindow("CTG : CREATE  " + catpath )
            self.addCatToDb(catname , catpath , parent  , source , link)
            return self.checkAndAddCatToDb(catname , catpath , parent  , source , link)

        # print(catname , catpath , parent  , source)

    def addProdToDb(self,proddata):

        # logIntoWindow("Inserting Prod to db ");

        sql = 'INSERT INTO `extern_products` ';
        sql = sql + '(`id`,  `name`,  `source` , `url` ,`manufacturer`,  `sku_manuf`, `id_supplier`, `stock`, `availability` , `price` , `sale`) VALUES ';
        sql = sql + '( NULL,   %s,   %s  , %s,    %s,  %s,  %s, %s,%s, %s, %s);';
        val = ( proddata['name'] , proddata['source'] , proddata['url'] ,  proddata['manufacturer'] , proddata['sku_manuf'] , proddata['id_supplier'], proddata['stock'], proddata['availability'] , proddata['price'] , proddata['sale'])
        self.queryDb(sql , val)

    def updateProdToDb(self,idprod , proddata):

        sql = 'UPDATE `extern_products` SET ';
        
        sql = sql + ' `name` = %s ,  `manufacturer` = %s , `url` = %s , `stock` = %s , `availability` = %s , `price` = %s , `sale` = %s , `desc` = %s , `images` = %s , `found` = 1 ';
        # sql = sql + ' `name` = %s , `found` = 1 ';
        
        sql = sql +  "WHERE `extern_products`.`id` = %s;";
        
        val = ( proddata['name'] ,  proddata['manufacturer'] , proddata['url'],  proddata['stock'], proddata['availability'] , proddata['price'] , proddata['sale'] , proddata['description'] , proddata['images']  , idprod)
        # val = ( proddata['name'], idprod)
        self.queryDb(sql , val)
    
    def checkAndAddProdToDb(self,proddata):

        check = self.fetchFromDb("SELECT * FROM `extern_products` WHERE sku_manuf LIKE \""+proddata['sku_manuf']+"\" AND source LIKE \""+proddata['source']+"\" ;");
        if self.isDemo :
            self.addProdToDb(proddata)
            self.updateProgressBar()
            return 1

        if len(check):
            self.updateProdToDb(check[0]['id'],proddata);
            self.updateProdMeta(check[0]['id'],proddata)
            self.logIntoWindow("PRD : 1) IDDB : "+str(check[0]['id'])+" SKU : " + proddata['sku_manuf'] + " MANUF SKU : " + proddata['sku_manuf'] + " IDSUPPLIER : " + proddata['id_supplier'] )
            self.logIntoWindow("PRD : 2) NAME : " + proddata['name'] + " MANUF : "+ proddata['manufacturer'])
            self.updateProgressBar()
            return check[0]['id']
        else:
            self.addProdToDb(proddata)
            return self.checkAndAddProdToDb(proddata)
        
    # Connects product with its category and source in the scraping database
    def insertCatRel(self , idprod , proddata):
        # logIntoWindow("New Category Relation ");

        sql = 'INSERT INTO `extern_relations` ';
        sql = sql + '(`id`,  `cat_id`,  `prod_id` , `source` ,  `found` ) VALUES ';
        sql = sql + '( NULL,   %s,   %s ,   %s  , 1);';
        val = ( proddata['catid'] ,  str(idprod),  proddata['source'])
        self.queryDb(sql , val)

    def updateCatRel(self ,idprod , proddata):
        sql = 'UPDATE `extern_relations` SET ';
        
        sql = sql + ' `found` = 1 ';
        # sql = sql + ' `name` = %s , `found` = 1 ';
        
        sql = sql +  "WHERE `cat_id` LIKE %s  AND  `prod_id` LIKE %s;";
        
        val = ( proddata['catid'] ,  str(idprod))
        # val = ( proddata['name'], idprod)
        self.queryDb(sql , val)

    def updateProdMeta(self, idprod , proddata):
        self.fetchFromDb("DELETE FROM extern_relations WHERE `extern_relations`.`prod_id` = "+str(idprod));
        insert = "INSERT INTO extern_relations "
        insert = insert + "(`id`, `meta_key`, `meta_value`, `prod_id`, `source`, `found`) VALUES "
        insert = insert + "(NULL, 'cat_id', '"+str(proddata['catid'])+"', '"+str(idprod)+"', '"+proddata['source']+"', '');";
        # print(insert) 
        self.fetchFromDb(insert) 
        insert = "INSERT INTO extern_relations "
        insert = insert + "(`id`, `meta_key`, `meta_value`, `prod_id`, `source`, `found`) VALUES "
        insert = insert + "(NULL, 'syskevasia', '"+str(proddata['syskevasia'])+"', '"+str(idprod)+"', '"+proddata['source']+"', '');";
        # print(insert)
        self.fetchFromDb(insert)
        # check = fetchFromDb("SELECT * FROM `extern_relations` WHERE prod_id = "+str(idprod)+" AND cat_id = "+str(proddata['catid'])+" ;");
        # if len(check):
            # updateCatRel(idprod , proddata)
        # else:
            # insertCatRel(idprod , proddata)

    def initAppl(self , source , updateClass ):
        windowHelpers.initLog(source , updateClass , self.initSourceMissing)


