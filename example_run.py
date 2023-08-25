from bs4 import BeautifulSoup
import requests, openpyxl
from urllib.parse import urljoin
from requests_toolbelt.multipart.encoder import MultipartEncoder
from importing_fw_horeca import *
import socket
from urllib3.connection import HTTPConnection

def Get_All_Products(url , cat , id_par):
    global horecaImport , runningImport;

    if runningImport is False:
        return
        
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Right now we are in the product list of the category
    # We pull the links of all the products and crawl into
    # next pages if there are any to do the same
    products = soup.select('.product-thumb')

    for product in products:

        link = product.find( class_="name").find("a")['href']
        prodResponse = session.get(link)
        print(link)
        prodSoup = BeautifulSoup(prodResponse.content, 'html.parser')

        title = prodSoup.find('h1', class_="page-title").text

        # print(title, link)

        images = prodSoup.select('.additional-images img')
        imageList = []
        for image in images:
            imageList.append(image['src'].replace('150x150w','1000x1000w'))
            print(image['src'])

        if len(imageList) == 0:
            images = prodSoup.select('#content .product-image .main-image [data-index="0"] img')
            for image in images:
                imageList.append(image['src'])
                print(image['src'])

        descriptions = prodSoup.select('#product-product .product_blocks-top .block-content')
        try:
            desc = descriptions[0].decode_contents()
        except IndexError:
            desc = ''  
        try:
            desc = desc + " <br \> " + descriptions[1].decode_contents()
        except IndexError:
            desc = desc + ''
        syskevasia = 1;
        syskdiv = prodSoup.select("#product-product .product_blocks-top .block-content #tab-specification tr:-soup-contains(\"Συσκευασία\")")
        if len(syskdiv):
            syskevasia = syskdiv[0].select('td')[1].text
            if "/" in syskevasia: 
                x = syskevasia.split("/")
                # print(syskevasia)
                syskevasia = x[0]
                # print(syskevasia)
                # exit()
        
        avail = prodSoup.select('.product-stats .product-stock')[0].text.replace('Διαθεσιμότητα: ','')
        sku = prodSoup.select('.product-stats .product-model span')[0].text
        price = 0
        disc = '-'
        manufacturer = horecaImport.siteName;
        if len(prodSoup.select('.product-price-group .price-group .product-price')) :
            price = prodSoup.select('.product-price-group .price-group .product-price')[0].text.replace('€','')
            disc = '-'
        if len(prodSoup.select('.product-price-group .price-group .product-price-old')) :
            price = prodSoup.select('.product-price-group .price-group .product-price-old')[0].text.replace('€','')
            disc = prodSoup.select('.product-price-group .price-group .product-price-new')[0].text.replace('€','')
        if len(prodSoup.select('.product-info .product-manufacturer>a img')) :
            manufacturer = prodSoup.select('.product-info .product-manufacturer>a img')[0]['alt']

        # This is how the dictionary that holds the data needs to be
        # , so that the library can manipulate it and add it or update it 
        # into the database

        prodata = dict();
        prodata['name'] = title
        prodata['source'] = horecaImport.siteName
        prodata['url'] = link
        prodata['sku_manuf'] = sku
        prodata['id_supplier'] = sku
        prodata['availability'] = avail
        prodata['stock'] = 999999
        if " ΠΑΚ " in prodata['name'] or " ΠΑΚ."  in prodata['name'] :
            prodata['price'] = float(price.replace(',','.'))
            
            level = logging.ERROR
            logger.log(level , "ΕΧΕΙ ΠΑΚ ")
            logger.log(level ,prodata['name'])
        else:
            prodata['price'] = float(price.replace(',','.')) * int(syskevasia)
        prodata['catid'] = id_par
        prodata['images'] = ','.join(imageList).replace("150x150w","1700x1700w")
        prodata['imageList'] = imageList
        prodata['description'] = desc
        prodata['manufacturer'] = manufacturer
        prodata['syskevasia'] = syskevasia
        if disc == "-":
            prodata['sale'] = 0
        else:
            if " ΠΑΚ " in prodata['name'] or " ΠΑΚ."  in prodata['name'] :
                prodata['sale'] = float(disc.replace(',','.'))
            else:
                prodata['sale'] = float(disc.replace(',','.')) * int(syskevasia)
    
        # We save the product on to the database and get the id of the product
        # so we can connect its images to it
        idprod = horecaImport.checkAndAddProdToDb(prodata)
        
        # add images to product into db and CDN server using the id of the prod

        horecaImport.saveImages(prodata,idprod)
        


    # Pagination stuff
    
    next_page = soup.select_one('li>a.next')

    if next_page:
        next_url = next_page.get('href')
        url = urljoin(url, next_url)
        print(url)
        Get_All_Products(url , cat , id_par )

def Sub_Categories(url, parent , id_par):
    global horecaImport , runningImport;
    if runningImport is False:
        return 
    
    source = session.get(url)

    soup = BeautifulSoup(source.text,'html.parser')
    # in this case , we find the data of the subcategories
    # from a  widget in the actual category page. In other cases
    # we can pull this data directly from the megamenu of the site
    products = soup.select('.refine-item')

    if len(products):
        # if it is not a final category branch , search for more sub cats
        for product in products:
            if runningImport is False:
                return
            path = parent + " > "
            title = path + product.find('span', class_="links-text").text

            link = product.find('a')['href']
            idcat = horecaImport.checkAndAddCatToDb( product.find('span', class_="links-text").text , title , id_par , horecaImport.siteName , link )

            #print(title, link)
            # sheet.append([title, link])
            # exit()
            Sub_Categories(link, title , idcat )
    else:
        # if it is a final category branch we move on to 
        # scraping the products of it
        Get_All_Products(url , parent , id_par)


def doSync():
    global session, runningImport, horecaImport;
    # Step 1 : Scrape the navigation menu and 
    # get all the final - level categories , while adding them to the database
    # using the functions given in horecaImport class
    source = session.get('somesitename')

    soup = BeautifulSoup(source.text,'html.parser')

    categories = soup.select('.category') #first level category html element here
    firstind = True;
    for category in categories:
        
        if runningImport is False:
            return 



        title = category.find('span', class_="links-text").text #catname

        link = category.find('a')['href'] #catlink

        # now we add the category to our database if it 
        # does not exist and keep the id to connect its
        # children to it later
        idcat = horecaImport.checkAndAddCatToDb(title , title , 0 , horecaImport.siteName , link )
        
        if runningImport is False:
            return 
        # continue into finding sub categories
        Sub_Categories(link, title , idcat)
            
        if runningImport is False:
            return 

    if runningImport is False:
        return 
    horecaImport.ParceSourceMissing(horecaImport.siteName)

def stopSync():
    
    # print('did stop funct')
    horecaImport.stopBoRetries()
    # runningImport = False
  

HTTPConnection.default_socket_options = (
    HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
        (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
        (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
    ]
)
horecaImport = horeca_Import()
with requests.Session() as session:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) " \
                                        "AppleWebKit/537.36 (KHTML, like Gecko) " \
                                        "Chrome/90.0.4430.212 Safari/537.36"
    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) " \
                                        "AppleWebKit/537.36 (KHTML, like Gecko) " \
                                        "Chrome/90.0.4430.212 Safari/537.36"
    
    headersreq = {   
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
        "upgrade-insecure-requests": "1"}
    headersnorm = {  
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
    # If a login step is to be made for the scraping to work , uncomment and do the 
    # post for the login here 
    # request = session.post("https://somesite.com", 
    #                     params={"route": "account/login"}, 
    #                     headers=headersnorm,
    #                     cookies={"language": "el-gr", "currency": "EUR", "jrv": "1580"})
    session.headers = headersnorm;
    
    runningImport = True;
    horecaImport.siteName = 'SomeSiteName'
    Applic_instance  = horecaImport.initAppl(horecaImport.siteName , doSync , stopSync)
# print(Applic_instance)