#python -m textblob.download_corpora

import time
import requests 
from bs4 import BeautifulSoup
import regex as re 
from textblob import TextBlob
from selenium import webdriver
import urllib.request
import threading
import csv
import nltk
from requests_html import HTMLSession
from urllib.parse import urlparse, urljoin
import language_check
tool = language_check.LanguageTool('en-US')

start = time.perf_counter()

final_dict = {}

urls = ['https://www.geeksforgeeks.org/python-3-basics/', \
	'https://techcrunch.com/', \
	'https://forge.medium.com/normal-is-the-last-thing-we-should-wish-for-9f4063994f1b', \
	'https://www.pyimagesearch.com/2020/06/22/turning-any-cnn-image-classifier-into-an-object-detector-with-keras-tensorflow-and-opencv/']

for url in urls:
	final_dict[url] = {}

def is_valid(url):
	parsed = urlparse(url)
	return bool(parsed.netloc) and bool(parsed.scheme)

def map_url_info(key, info):
	global urls, final_dict
	for i in range(len(info)):
		final_dict[urls[i]][key] = info[i]
	
soups = [BeautifulSoup(requests.get(url).content, 'html.parser') for url in urls]
#print(soup[0].prettify())



#Count of Advertisements



#Domain name - .com/.org, etc
def domain_name():
	global urls
	domain_names = [url.split('/')[2].split('.')[-1] for url in urls]
	map_url_info('Domain name', domain_names)


def website_text():
	global soups
	text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'em', 'strong', 'title', 'li']
	tag_data_list = [soup.find_all(text_tags) for soup in soups]
	text_data_list = []
	for tag_data in tag_data_list:
		text_data = ""
		for tag in tag_data:
			text_data += tag.text + ' '
		text_data_list.append(text_data) 
	return text_data_list

total_text = website_text()


#Availability of contact details (social media handles)
def contact_details():
	global total_text
	telephone = [re.findall(r"^(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$", text) for text in total_text]  # Phone regex, source: regex101.com
	emails = [re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z]+.[A-Za-z]{2,3}", text) for text in total_text]  #Email regex
	map_url_info('Telephone', telephone)
	map_url_info('Email', emails)


#Text to image ratio

def text_image_ratio():
	global total_text, urls, soups
	word_count = []
	for text in total_text:
		document = (text)
		text_blob_object = TextBlob(document)
		document_words = text_blob_object.words
		word_count.append(len(document_words))

	image_tags = ['img', 'svg']
	image_tag_data_list = [soup.find_all(image_tags) for soup in soups]
	image_count = []
	for tag_data in image_tag_data_list:
		count = 0
		for tag in tag_data:
			count += 1
		image_count.append(count)
	ratio = [f"{word_count[i]}/{image_count[i]}" for i in range(len(urls))]
	map_url_info('Text to image ratio', ratio)



#polarity and subjectivity
def senti():
	global total_text
	sentiment = [TextBlob(text).sentiment for text in total_text]
	map_url_info('Polarity and Subjectivity', sentiment)



#Modified date time
def modified_date_time():
	global soups, urls
	modified_dates = [soup.find("meta",  property="article:modified_time") for soup in soups]
	modified_dates_list = [modified_date["content"] if modified_date else 0 for modified_date in modified_dates]

	if 0 in modified_dates_list:
		for i in range(len(modified_dates_list)):
			if modified_dates_list[i] == 0:
				result = urlparse(urls[i])
				if result.scheme and result.netloc and result.path:
					header = requests.head(urls[i]).headers
					if 'Last-Modified' in header:
						modified_dates_list[i] = header['Last-Modified']

	if 0 in modified_dates_list:
		for i in range(len(modified_dates_list)):
			if modified_dates_list[i] == 0:
				driver_m = webdriver.Chrome(r'C:\Users\SUMANTH\Desktop\whatsapp_automated_alerts\covid19_alerts\chromedriver.exe')
				internet_archive = 'https://web.archive.org/web/*/' + urls[i]
				driver_m.get(internet_archive)
				#time.sleep(2)
				get_div = driver_m.find_element_by_xpath('''//*[@id="react-wayback-search"]/div[2]''')
				modified_dates_list[i] = get_div.text
				driver_m.close()

	map_url_info('Modified Date', modified_dates_list)



#PageLoad time
def pageload_time():
	global urls
	pageload_time = []
	for url in urls:
		req = urllib.request.Request(url, headers={"User-Agent": "Chrome"})
		page = urllib.request.urlopen(req)
		s = time.time()
		page.read()
		e = time.time()
		pageload_time.append(e-s)

	map_url_info('PageLoad Time', pageload_time)




#Count of outlinks.. in the domain as well as outside the domain separately
def outlinks():
	global urls
	internal_links_all, external_links_all = [], []
	for url in urls:
		internal_urls, external_urls = [], []
		# domain name of the URL without the protocol
		domain_name = urlparse(url).netloc
		# initialize an HTTP session
		session = HTMLSession()
		# make HTTP request & retrieve response
		response = session.get(url)
		# execute Javascript
		try:
			response.html.render()
		except:
			pass
		soup = BeautifulSoup(response.html.html, "html.parser")
		for a_tag in soup.findAll("a"):
			href = a_tag.attrs.get("href")
			if href == "" or href is None:
				# href empty tag
				continue
			# join the URL if it's relative (not absolute link)
			href = urljoin(url, href)
			parsed_href = urlparse(href)
			# remove URL GET parameters, URL fragments, etc.
			href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
			if not is_valid(href):
				continue
			if href in internal_urls:
				continue
			if domain_name not in href:
				if href not in external_urls:
					#print(f"External link: {href}")
					external_urls.append(href)
				continue
			#print(f"Internal link: {href}")
			internal_urls.append(href)
		#print("URL:", url)
		#print("Total Internal links:", len(internal_urls))
		#print("Total External links:", len(external_urls))
		#print("Total URLs:", len(external_urls) + len(internal_urls))
		#print()
		internal_links_all.append(len(internal_urls))
		external_links_all.append(len(external_urls))
	map_url_info('Internal links', internal_links_all)
	map_url_info('External links', external_links_all)



#Grammar and Spelling mistakes
def spelling_grammar_errors():
	global total_text
	spell_errors_list = []
	grammar_errors_list = []
	for text in total_text:
		temp_s = 0
		temp_g = 0
		sentences = nltk.tokenize.sent_tokenize(text)
		for sentence in sentences:
			matches = tool.check(sentence)
			for mistake in matches:	
				if mistake.locqualityissuetype == 'misspelling':
					temp_s += 1
				elif mistake.locqualityissuetype == 'grammar':
					temp_g += 1
		spell_errors_list.append(temp_s)
		grammar_errors_list.append(temp_g)
	map_url_info('Grammar_errors', grammar_errors_list)
	map_url_info('Spelling_errors', spell_errors_list)



#POS
def pos_count():
	global total_text
	count = []
	for text in total_text:
		temp_n = 0
		temp_v = 0
		temp_adj = 0
		temp_adv = 0
		sentences = nltk.tokenize.sent_tokenize(text)
		tokens = [nltk.tokenize.word_tokenize(s) for s in sentences]
		pos_tagged_tokens = [nltk.pos_tag(t) for t in tokens]
		for sen_token in pos_tagged_tokens:
			for word_pos in sen_token:
				if word_pos[1] in ['NN', 'NNS', 'NNP', 'NNPS']:
					temp_n += 1
				elif word_pos[1] in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
					temp_v += 1
				elif word_pos[1] in ['JJ', 'JJR', 'JJS']:
					temp_adj += 1
				elif word_pos[1] in ['RB', 'RBR', 'RBS', 'WRB']:
					temp_adv += 1
		count.append([temp_n, temp_v, temp_adj, temp_adv])
	map_url_info('POS count', count)



t1 = threading.Thread(target = domain_name)
t1.start()
t2 = threading.Thread(target = contact_details)
t2.start()
t3 = threading.Thread(target = text_image_ratio)
t3.start()
t4 = threading.Thread(target = senti)
t4.start()
t5 = threading.Thread(target = modified_date_time)
t5.start()
t6 = threading.Thread(target = pageload_time)
t6.start()
t7 = threading.Thread(target = outlinks)
t7.start()
t8 = threading.Thread(target = spelling_grammar_errors)
t8.start()
t9 = threading.Thread(target = pos_count)
t9.start()

	
for thread in [t1, t2, t3, t4, t5, t6, t7, t8, t9]:
	thread.join()

end = time.perf_counter()

print(f"\n\n{end-start} second(s) for the whole program execution\n\n")

print(final_dict)

with open("website_details.csv", "a", newline='') as f:
	fieldnames = ['Website name', 'TLD name', 'Last modified', 'Number of advertisements', 'Page Load time', 'Text2Image ratio', 'Polarity', 'Subjectivity', 'Contact Info(Yes/No)', 'Count of Inliks', 'Count of Outlinks', 'Grammar Correctness (Yes/No)', 'Spell Errors (Count)', 'POS Count (Noun, Verb, Adjective and Adverb)']	
	writer = csv.DictWriter(f, fieldnames = fieldnames)
	writer.writeheader()
	for key, value in final_dict.items():
		if len(final_dict[key]['Telephone']) == 0 and len(final_dict[key]['Email']) == 0:
			contact_info = 'No'
		else:
			contact_info = 'Yes'
		if final_dict[key]['Grammar_errors']>0:
			g_errors = 'Yes'
		else:
			g_errors = 'No'

		writer.writerow({'Website name': key, 'TLD name': final_dict[key]['Domain name'], 'Last modified': final_dict[key]['Modified Date'], 'Number of advertisements': 0, 'Page Load time': final_dict[key]['PageLoad Time'], 'Text2Image ratio': final_dict[key]['Text to image ratio'], 'Polarity': final_dict[key]['Polarity and Subjectivity'][0], 'Subjectivity': final_dict[key]['Polarity and Subjectivity'][1], 'Contact Info(Yes/No)': contact_info, 'Count of Inliks': final_dict[key]['Internal links'], 'Count of Outlinks': final_dict[key]['External links'], 'Grammar Correctness (Yes/No)': g_errors, 'Spell Errors (Count)': final_dict[key]['Spelling_errors'], 'POS Count (Noun, Verb, Adjective and Adverb)': final_dict[key]['POS count']})