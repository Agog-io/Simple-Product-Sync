
# --External Libraries--
from bs4 import BeautifulSoup
# BS4: Library used for parsing and extracting data from web pages
import requests
# Requests : Used for downloading web pages
from urllib.parse import urljoin
# urljoin : Used for parsing relative web page urls when nessecary
# Absolute url = http://facebook.com/login
# Relative url = /login  (it is relative to the webpage that contains it)
from requests_toolbelt.multipart.encoder import MultipartEncoder
# MultipartEncoder : Used for crafting POST request to login on sites 
# that are hide some or all data from the public.
import socket
# socket : Used to get some constants , to make HTTP request more 
# stable by enabling KEEPALIVE
from urllib3.connection import HTTPConnection
# HTTPConnection : Used to configure HTTP request made by this program
import logging
# logging : Python logging lib
# --//--


from product_sync import product_sync , logger
# The product_sync library that updates the Database with product details and 
# FTP server with the product images.
# Logger is used to display the user with messages.




class scraping_example:

    def __init__(self):
        # Setting up KEEPALIVE
        HTTPConnection.default_socket_options = (
            HTTPConnection.default_socket_options + [
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
                (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
                (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
            ]
        )
        
        # Variable to keep track if import is running.
        # usefull when terminating program to halt every procedure as 
        # the logging window runs on separate thread and terminating it
        # does not terminate the actual scraping procedures , leaving the program
        # running even if the user closes the window.
        self.runningImport = True
         
        # Creating a new Session with headers mimiking a chrome browser to get past some 
        # firewalls and user agent detection logic some sites have

        self.session = requests.Session()
        
        headers = {  
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9,el-GR;q=0.8,el;q=0.7",
                "cache-control": "max-age=0",
                "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1"
        }
        
        self.session.headers = headers; 
            

        # Iniatilize Product Sync Instance
        self.sync_instance = product_sync()

        # For demo purposes.
        # (Writes SQL queries to a txt file and uses the program folder as the FTP server)
        self.sync_instance.isDemo = 1

        # This sets the source of the products pulled in the database.
        # Usefull for both knowing from where the product was pulled , as
        # well as separating different products with the same SKU.
        self.sync_instance.siteName = 'Commerce Layer (DEMO)'

        # Setting Up the logging window instance and passing this class to it.
        # This class needs to have a doSync & stopSync method accordingly.
        self.logging_instance = self.sync_instance.initAppl(self.sync_instance.siteName , self)
    
    # Helper function to return the text of a tag stripped of whitespace
    def getTagText(self , el , selector  ):
        tag = el.select_one(selector)
        return tag.text.strip()
    
    def doSync(self):
        level = logging.INFO
        logger.log(level,'startsync')

        # Step 1 : Parse the webpage with BS4
        hmtl_example = open('category-page.html','r')

        soup = BeautifulSoup(hmtl_example,'html.parser')

        
        products = soup.select('.column .box') 
        # Register the category (if it does not exist) in the database
        # Second parameter is the path ( example "home>clothes" )
        # Third is the id of the parent ( 0 if it is a root one )

        idcat = self.sync_instance.checkAndAddCatToDb("home" , "home" , 0 , self.sync_instance.siteName , 'category-page.html' )

        for product in products:
            
            prodata = dict();
            prodata['name'] = self.getTagText(product,"h4")
            prodata['source'] = self.sync_instance.siteName
            prodata['url'] = "category-page.html"
            prodata['sku_manuf'] =  self.getTagText(product,"p.help")
            prodata['id_supplier'] = self.getTagText(product,"p.help")

            #in this case , a disabled a-tag indicates that the product is unavailable
            input_tag = product.select_one('a[disabled]')
            if input_tag:
                prodata['availability'] = "Unavailable"    
                prodata['stock'] = 0
                prodata['price'] = 0
            else:
                prodata['availability'] = "Available"    
                # in case of no stock management on target site , set this
                # to a high enough number so that it shows as available
                prodata['stock'] = 99999
                prodata['price'] = float(self.getTagText(product,'.clayer-price .amount').replace('$',''))

            

            prodata['catid'] = idcat
            image_tag = product.select_one('img')

            #todo remove the comma separated images field
            prodata['images'] = image_tag['src']
            prodata['imageList'] = [image_tag['src']]
            
            prodata['description'] = ""
            prodata['manufacturer'] = self.sync_instance.siteName
            
            # todo translate to english
            # "syskevasia" means items per pack 
            prodata['syskevasia'] = 1
            
            original_price_tag = product.select_one(".compare-at-amount")
            if original_price_tag != None:
                original_price = float(original_price_tag.text.strip().replace('$',"")) 
                prodata['sale'] = original_price - prodata['price']
                prodata['price'] = original_price
            else:
                prodata['sale'] = 0
        
            # We save the product on to the database and get the id of the product
            # so we can connect its images to it

            idprod = self.sync_instance.checkAndAddProdToDb(prodata)
            
            # add images to product into db and FTP server using the id of the prod

            self.sync_instance.saveImages(prodata,idprod)
            level = logging.INFO
            logger.log(level,'DONE : '+prodata['name'])    

        
        self.stopSync()

    def stopSync(self):
        level = logging.INFO
        logger.log(level,'stopsync')    
        self.sync_instance.stopUpdating()
    
scraping_example()