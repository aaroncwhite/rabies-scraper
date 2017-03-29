''' 
Scraper!  
by Aaron White
for Python 2.7.x

Made especially for Alyssa Bilinski.
Assumes you have the html file in your working directory.  

Usage:
>>> scrape(locations, output_filename)
Ex.
1 - Download data
>>> raw = scraper.import_raw('info.html')

2 - Get rid of all the info we don't need
>>> data = scraper.important(raw)

3 - Scrape and parse parse all that info into a csv file!
>>> formatted = scrape(data, 'alyssa owes me big time 2.0')

Returns list of lists and outputs data to 'alyssa owes me big time.csv' and
'alyssa owes me big time-species.csv' in the same working directory. Tables are related
on the sdid column. 
'''

import csv
from bs4 import BeautifulSoup as bs
from urllib2 import urlopen

# PARSE MAIN PAGE 
# Import HTML data (the main page)
def import_raw(filename): # Assuming this is in the same working directory
	f = open(filename)
	messy_data = f.read()
	data = bs(messy_data) # Use BeautifulSoup to clean up output
	f.close()
	return data
	
# Read the important lines
def important(data):
	# Find all <a href> tags first
	raw = data.find_all('a')
	for link in range(len(raw)):
		raw[link] = raw[link].get('href')
	# Just the javascript:show_detail lines
	halfway = []
	for link in raw:
		link = str(link) # str() gets around unicode issue
		if "javascript:show_detail" in link:
			link = link[24:] # Starting index for what we want. 
			replace = [")","'"]
			for r in replace:
				link = link.replace(r, "")
			link = link.replace(",", " ").split() # Returns list with values
			halfway = halfway + [link] # Creates list of lists with your values
	return halfway # Each list contains [CountryID, Y, M, DiseaseID, SDID]

# Generate specific URL to load
def gen_url(countryid, y, m, admin1, diseaseid, sdid, detail):

	url = "http://www.oie.int/wahis_2/public/wahid.php/Diseaseinformation/statusdetail/popup?"
	# y, m, admin1, and detail don't seem to be important for the table output
	url = url + "diseaseid=" + diseaseid + "&country=" + countryid + "&y=" + y
	url = url +  "&m=" + m + "&admin1=" + admin1 + "&detail=" + detail + "&sdid=" + sdid
	return url
	
def get_specific(url):
	page = urlopen(url)
	page = bs(page)
	return page
	
# PARSE INDIVIDUAL PAGES
def page_tables(page):
	tables = page.find_all('table')
	return tables

def table_rows(table):
	rows = table.find_all('tr')
	return rows
	
def strip_row(row):
	row = row.find_all('td')
	for cell in range(len(row)):
		row[cell] = str(row[cell].get_text())
	return row

def find_cases(url):
	#Pull just table rows from the HTML
	data = get_specific(url)
	title = data.b # First bold tag has the name of the specific region in it
	title = title.get_text()
	tables = page_tables(data) # 3 tables
	
	# Total Outbreaks
	# outbreaks = table_rows(tables[0])
	# outbreaks = strip_row(outbreaks[1])
	
	# Wild Species
	wild = table_rows(tables[1])
	wild = strip_row(wild[1]) 
	# Output Cases, Deaths, Destroyed
	try: # Need error handling if no records found
		w = [data[1][2]] + [data[1][3]] + [data[1][4]]
	except:
		w = ["NA"] + ["NA"] + ["NA"]

	
	# Domestic Species
	domestic = table_rows(tables[2])
	domestic = domestic[1:] # 1 removes header line
	for c in range(len(domestic)): 
		domestic[c] = strip_row(domestic[c])
	
	# Sum cases, deaths, and destroyed for all animals reported. NO ERROR HANDLING IF NONE
	try:
		cases = 0
		deaths = 0
		destroyed = 0
		for animal in domestic:
			if animal[2] is not '':
				cases = cases + int(animal[2])
			if animal[3] is not '':
				deaths = deaths + int(animal[3])
			if animal[4] is not '':
				destroyed = destroyed + int(animal[4])
		aggregate = [cases, deaths, destroyed]
	except:
		aggregate = ["NA"] + ["NA"] + ["NA"]	
		domestic = "NA"
	

	return [str(title)] + w + aggregate + [domestic]


def download_data(countryid, y, m, admin1, diseaseid, sdid, detail):
	url = gen_url(countryid, y, m, admin1, diseaseid, sdid, detail)
	data = find_cases(url)
	return data
	
# Let's put it together

# def list_animals(locations):
def pull_animals(row, filename):
	file = open(str(filename + '-species.csv'), 'a')
	wr = csv.writer(file, quoting=csv.QUOTE_ALL)
	animal = []
	animals = row[-1]
	if animals is not "NA":
		for a in range(len(animals)):
			animal = [row[5]] # sdid
			animal = animal + animals[a]
			wr.writerow(animal)
	file.close()	


def scrape(locations, filename): # No .csv on filename
	num_locations = len(locations)
	print "Downloading", num_locations, "records."
	if num_locations > 20:
		print "This will take a while."
			# In hindsight, I would rework this to write the lines immediately to a csv 
			# instead of just storing it in a list. That way on errors, it could pick up
			# where it last failed. 

	scraped = []
	for i in locations:
		x = i
		try:
			data = download_data(i[0],i[1],i[2],i[3],i[4],i[5],i[6])
			print i[0] + " " + data[0] 
			# Add title
			x = x + data[0:4] + data[4:]
			scraped = scraped + [x]
		except:
			print i[0], "Error in link data. Skipping."
	
	# Output the csv
	print "Writing main csv"
	file = str(filename + '.csv')
	file = open(file, "wb")
	wr = csv.writer(file, quoting=csv.QUOTE_ALL)
	wr.writerow(['countryid', 'y', 'm', 'admin1', 'diseaseid', 'sdid', 'detail', 'title','wild_cases', 'wild_deaths', 'wild_destroyed', 'dom_cases', 'dom_deaths', 'dom_destroyed', 'animals'])
	for row in range(len(scraped)):
		wr.writerow(scraped[row])
	file.close()

	# Output the specific animals with SDID
	print "Writing species csv"
	file = open(str(filename+ '-species.csv'),'w')
	wr = csv.writer(file, quoting=csv.QUOTE_ALL)
	wr.writerow(['sdid', 'species', 'susceptible', 'cases', 'deaths', 'destroyed', 'slaughtered'] )
	
	file.close()
	
	for row in range(len(scraped)):
		pull_animals(scraped[row], filename)

	return scraped

	
	
	
	
	
	
	
	