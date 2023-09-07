
# Simple Product Sync

Simple Product Sync App with a logging window that abstracts the insertion and updating of data and images. 

Contains example that scrapes a webpage and passes it into the library.

## The problem
Working on a e-commerce site with a lot of affiliate shops , I was tasked with creating an automated proccess of creating and updating the products our affiliate shops provided us on our e-commerce site. Those shop usually lacked any kind of structured data , other than their website .  This project started as a simple python scraping app that took this data and inserted it to a .xls file that the site then parsed, but this solution proved problematic as it bombarded our websites server with both database and ftp traffic , as well as all the update logic that comes with updating products , categories and images. Our server provider also has a policy against mass web scraping which meant we had to move all the http calls outside the server our site run on as more and more affiliate shops were being added. 

We also had some affiliates that either had or promised to provide us  with some sort of product feed like an XML  and I  wanted to make a singular codebase that works both ways , either the data comes from a scraping program or it a file with some data.

## The Solution
The solution I came up with was creating a separate database on a separate server , and move all the update logic and downloading of images out of the site and into this python program.  The program takes all the product data in an array and updates the database accordingly. It also tracks when these products were changed so that the website updates only when it is absolutely required.

Images of the product are downloaded on the pc this program runs on and then uploaded to the server using sFTP.

Also I did make some changes to make the general scraping and updating procedure more reliable , like adding retries to all HTTP , mySQL and sFTP calls ( Both our and other servers dropped connections regularly , due to poor hosting , meaning the program errored out when that happened and the whole procedure had to restart ) 

## Usage

Import [Database.sql](https://github.com/Agog-io/Simple-Product-Sync/blob/main/Database.sql "Database.sql") in to a  database and provide its connection details to the [config copy.json](https://github.com/Agog-io/Simple-Product-Sync/blob/main/config%20copy.json "config copy.json")

Provide [config copy.json](https://github.com/Agog-io/Simple-Product-Sync/blob/main/config%20copy.json "config copy.json") with the appropriate sFTP details (used for uploading images)

[example_run_scrape.py](https://github.com/Agog-io/Simple-Product-Sync/blob/main/example_run_scrape.py "example_run_scrape.py") provides a commented example with exactly how to get this running. Use this as the sceleton to your use case. This is the file you run to execute the program. 

[product_sync.py](https://github.com/Agog-io/Simple-Product-Sync/blob/main/product_sync.py "product_sync.py") contains all the updating logic in the product_sync class.

[logging_window.py](https://github.com/Agog-io/Simple-Product-Sync/blob/main/logging_window.py "logging_window.py") is the implementation of the logging window.

Currently this works only on windows but [logging_window.py](https://github.com/Agog-io/Simple-Product-Sync/blob/main/logging_window.py "logging_window.py") and all the functions related to the loging window can be easily changed to run on different platforms.
