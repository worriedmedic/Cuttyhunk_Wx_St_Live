from __future__ import print_function
import serial, io
import time
import datetime
import requests
import os.path
import csv
import codecs
import urllib2
import json

debug = False				#True if you want to use made up data
					#False if you want to use serial input
baud            	= 9600		# baud rate for serial port
txt_logging      	= True		# Enable/Disable logging to TXT file
verbose             	= False
address             	= '/dev/ttyACM0'
thingspeak_update   	= True
internet		= True
## Values to store data

## Data that will change every day
today = [None]
yesterday = [None]
tomorrow = [None]
fname = [None]
sheetname =[None]
fdir = [None]

## Helper variables for tides
tide_datetime = [None]
tide_next_time = [None]
tide_next_type = [None]
tide_next_mag = [None]
tide_following_time = [None]
tide_following_type = [None]
tide_following_mag = [None]
tide_list = []
tide_time = [None]
tide_type = [None]
tide_mag = [None]

## Helper variables for sun
sun_list = []
sun_rise = [None]
sun_down = [None]

## Expected Hi and Lo
wunder_site_json = 'http://api.wunderground.com/api/1f86b1c989ac268c/forecast/q/ma/cuttyhunk.json'
onlinejson = [None]
forecast = [None]
exp_hi = [None]
exp_lo = [None]

## Cheating the wind data
ch_avg_wind_speed = [None]
ch_wind_dir = [None]
ch_max_wind_speed = [None]

## Data that will change on every packet
buff = [None] * 50
addr  = [None]	
temp  = [None] * 5
press = [None] * 5
humid = [None] * 5
volt  = [None] * 5
rssi  = [None] * 5
wind_speed = [None] * 5
wind_dir = [None] * 5

## Station 0 - Inside the house. Top floor.
temp_0 = [None]

## Station 1 - Inside the house. Bottom floor
temp_1 = [None]

## Station 2 - Outside, near the barn.
temp_2 = [None]
press_2 = [None]
humid_2 = [None]




## YEARLY SHIT
## Shit to get the tides in a csv. Once its done dont touch it.
## All we gotta do is grab one each new day. Thats it. Simple shieeeeet

if (False):
	tide_text = '8448376_annual.txt'
	tide_csv = 'cutty_tide.csv'
	in_txt = csv.reader(open(tide_text,"rb"), delimiter = '\t')
	temp_csv = csv.writer(open(tide_csv, "wb"))
	temp_csv.writerows(in_txt)
	temp_csv.close()

## SUNRISE - SUNSET SHIT GOES HERE

## Or not



##functions
def get_tide(tide_day):
	## Grab the tide for the day that you input
	## Requires today or tomorrow as input
	with open('cutty_tide.csv', 'rb') as tide_csv:
		tide_reader = csv.reader(tide_csv, delimiter =',')
		day = tide_day.strftime("%Y/%m/%d")
		temp_list = []
		for row in tide_reader:
			if (row[0] == day):
				tide_time = row[2]
				tide_mag = row[3]
				tide_type = row[7]
				temp_list.append([tide_time,tide_type,tide_mag])
	return temp_list



pt = serial.Serial(address,9600,timeout=None)
spb = io.TextIOWrapper(io.BufferedRWPair(pt,pt,1),encoding='ascii', errors='ignore',line_buffering=True)
print(spb.readline())
print(spb.readline())
print(spb.readline())


while(1):
	'''
	Executing loop. Code should be running all day.
	Will have daily goals that need to be updated.
	Yearly goals will need to manually done.
	Yearly goals are sunset data, and tide data.
	'''
	
	## Daily tasks
	if (today != datetime.date.today()):
		'''
		If our value for today is wrong, we have passed onto the next day
		These tasks are:
			Update tide clock for new day
			Update sunrise and sundown
			Update Expected Hi and Lo
			Update Date
			Create new day's log files
		'''
		
		#Update today's logs
		today = datetime.date.today()
		yesterday = datetime.date.today() + datetime.timedelta(days=-1)
		tomorrow = datetime.date.today() + datetime.timedelta(days=1)
		fname = str(today) + '.log'
		sheetname = str(today) + '.csv'	
		fdir = 'data_log'
		if not os.path.exists(fdir):
			os.makedirs(fdir)


		## Open the top line of the spreadsheet and write the column names
		## NOTE: WILL HAVE TO UPDATE THIS WHEN WEATHER DATA IS HERE
		if not os.path.isfile(fdir+'/'+sheetname):
			with open(os.path.join(fdir,sheetname),'wb') as logcsv:
				topline = csv.writer(logcsv)
				topline.writerow( ('Time','Address', 'Temperature', 'Pressure', 'Humidity', 'Dew', 'Voltage', 'RSSI') )
				logcsv.close()
		## Done updating today's logs

		## Grabbing tides
		# This will pull down the list of tides for today
		if tide_list == []:
			tide_list = get_tide(today)
			tide_next_time = '12:00 AM'
			tide_datetime = datetime.datetime.strptime(tide_next_time,'%I:%M %p')
			tide_datetime = tide_datetime.replace(today.year,today.month,today.day)
		
		# Open up sunrise / sunset data
		with open('Sun_data.csv', 'rb') as sun_csv:
			sun_reader = csv.reader(sun_csv, delimiter =',')
			sun_day = today.strftime("%Y/%m/%d")
			for row in sun_reader:
				if (row[0] == sun_day):
					sun_rise = str(row[1])
					sun_down = str(row[2])
		sun_rise = sun_rise[1]+':'+ sun_rise[2:]
		sun_down = sun_down[0:2] + ':' + sun_down[2:]


		## Update expected Hi and Lo
		# Assumptions:
		# 	Internet is working an never quits
		#	API calls to Wunderground work
		#	Wunderground hasnt changed its format on its API
		
		# Likely will break this out to another if/else that clarifies 
		# if we have internet or not. If we dont have internet, 
		# grab data from yesterday and use that as expected hi and lo
		if internet:
			if not os.path.isfile(str(today)+'_forecast.json'):
				try:
					onlinejson = requests.get(wunder_site_json)
					localjson = open(str(today)+'_forecast.json', 'wb')
					if os.path.isfile(str(yesterday)+'_forecast.json'):
						os.remove(str(yesterday)+'_forecast.json')
					for chunk in onlinejson.iter_content(100000):
						localjson.write(chunk)
					onlinejson.close()
					localjson.close()
				except requests.exceptions.ConnectionError as e:
					print("Issue loading Wunder JSON")
					
			localjson = open(str(today)+'_forecast.json','rb')
			json_string = localjson.read()
			parsed_json = json.loads(json_string)
			exp_hi = parsed_json['forecast']['simpleforecast']['forecastday'][0]['high']['fahrenheit']
			exp_lo = parsed_json['forecast']['simpleforecast']['forecastday'][0]['low']['fahrenheit']
			#print(exp_hi)
			#print(exp_lo)
		

			## Cheat and get wind speed / dir
			ch_avg_wind_speed = parsed_json['forecast']['simpleforecast']['forecastday'][0]['avewind']['mph']
			ch_wind_dir = parsed_json['forecast']['simpleforecast']['forecastday'][0]['avewind']['dir']
			ch_max_wind_speed = parsed_json['forecast']['simpleforecast']['forecastday'][0]['maxwind']['mph']
			#print(ch_wind_speed)
			#print(ch_wind_dir)
		

		### END OF DAILY TASKS, BEGIN STREAMING DATA

	# Update the tide
	# Tide will be output as a list for the day. 
	# In this list will be smaller lists with the values for 
	# Time, High or Low, and magnitude of the tide
	# Should be no more than 5 tides and no fewer than 3.
	# Avg case is 4.
	print (time.strftime('%y:%m:%d:%H:%M:%S'))
	minute = datetime.datetime.now()

	while(minute > tide_datetime):
		if len(tide_list)<=1:
			tide_list = get_tide(tomorrow)
			tide_next_time = tide_list[0][0]
			dummy = datetime.datetime.strptime(tide_next_time,'%I:%M %p')
			tide_datetime = tide_datetime.replace(tomorrow.year, tomorrow.month, tomorrow.day, dummy.hour,dummy.minute)
			tide_next_type = tide_list[0][1]
			tide_next_mag = tide_list[0][2]
		else:
			tide_list = tide_list[1:]
			tide_next_time = tide_list[0][0]
			dummy = datetime.datetime.strptime(tide_next_time,'%I:%M %p')
			
			tide_datetime = tide_datetime.replace(today.year, today.month, today.day, dummy.hour,dummy.minute)
			#print(tide_list)
			tide_next_type = tide_list[0][1]
			tide_next_mag = tide_list[0][2]
			if len(tide_list)==1:
				helper =get_tide(tomorrow)
				for item in helper:
					tide_list.append(item)
				if(minute > tide_datetime):
					tide_list = tide_list[1:]
					tide_next_time = tide_list[0][0]
					tide_next_type = tide_list[0][1]
					tide_next_mag = tide_list[0][2]
					dummy = datetime.datetime.strptime(tide_next_time,'%I:%M %p')
					tide_datetime = tide_datetime.replace(tomorrow.year, tomorrow.month, tomorrow.day, dummy.hour,dummy.minute)
			tide_following_time = tide_list[1][0]
			tide_following_type = tide_list[1][1]
			tide_following_mag = tide_list[1][2]
	
	#print(tide_list)
	#print(tide_next_type)
	#### Initialization of serial usb port
	#buff = read_buffer()
	buff = spb.read(35)
	print(buff, end = '')	
	now =str(time.strftime('%H:%M:%S'))
	curr_time = str(time.strftime('%H:%M'))
	if txt_logging:
		txt_log = open(os.path.join(fdir,fname),'a')
		txt_log.write(str(now)+' '+buff)
		txt_log.flush()
	
	# Probably just int this fucker right here
	addr  = buff[0:2]
	if int(addr) >= 0 and int(addr) <=4:
		temp  = buff[4:9]
		press = buff[11:16]
		humid = buff[18:23]
		volt  = buff[25:30]
		rssi  = buff[31:34]
		dew = float(temp) - ((100 - float(humid)) / 5 )
	if (int(addr) == 0):
		temp_0 = temp
	elif (int(addr) == 1):
		temp_1 = temp
	elif (int(addr) == 2):
		temp_2 = temp
		press_2 = press
		humid_2 = humid
	
	## Output data to the svg
	
	output = codecs.open('WX_TEMPLATE.svg', 'r', encoding='utf-8').read()
	output = output.replace('CURDATE', today.strftime("%m/%d/%Y"))
	output = output.replace('CURTIME', str(curr_time))
	output = output.replace('SNRISE', sun_rise)
	output = output.replace('SNSET', sun_down)
	if internet:
		output = output.replace('FORHI', exp_hi)
		output = output.replace('FORLO', exp_lo)
		output = output.replace('WSP', str(ch_avg_wind_speed))
		output = output.replace('WGUS', str(ch_max_wind_speed))
	output = output.replace('TMPE',str(temp_2))
	output = output.replace('TMPI',str(temp_0))
	output = output.replace('TMPG',str(temp))
	output = output.replace('TMPD',str(temp_1))
	output = output.replace('PRESS',  str(press_2))
	output = output.replace('RLHUM',str(humid_2))
	output = output.replace('DWPNT',"{0:.2f}".format(dew))
	output = output.replace('TDNTY',str(tide_next_type))
	output = output.replace('TDNTM',str(tide_next_time))
	output = output.replace('TDNLV',str(tide_next_mag))
	output = output.replace('TDFTY',str(tide_following_type))
	output = output.replace('TDFTM',str(tide_following_time))
	output = output.replace('TDFLV',str(tide_following_mag))
	
	codecs.open('TEST.svg', 'w', encoding='utf-8').write(output)

	with open(os.path.join(fdir,sheetname),'a') as logcsv:
		xyz = csv.writer(logcsv)
		xyz.writerow( (str(now),addr,temp,press,humid,dew,volt,rssi) )
		logcsv.close()
	

	## Logging to thinkspeak
	try:
		if thingspeak_update:
			url = 'https://api.thingspeak.com/update.json'

			if addr == '00':
				api_key = 'TFGVV0YYM18ALONJ'
				payload = {'api_key': api_key, 'field1': addr, 'field2': temp, 'field3': press, 'field4': humid,
				       'field5': volt, 'field6': rssi}
				r = requests.post(url,data=payload)
				if verbose:
				    print(r.text)

			elif addr == '01':
				api_key = 'ARPQ7GWOHTQSYWYW'
				payload = {'api_key': api_key, 'field1': addr, 'field2': temp, 'field3': press, 'field4': humid,
				       'field5': volt, 'field6': rssi}
				r = requests.post(url, data=payload)
				if verbose:
				    print(r.text)
			elif addr == '02':
				api_key = 'GVWSJ8V12MIPJBLY'
				payload = {'api_key': api_key, 'field1': addr, 'field2': temp, 'field3': press, 'field4': humid,
				       'field5': volt, 'field6': rssi}
				r = requests.post(url, data=payload)
				if verbose:
				    print(r.text)

			else:
				print("SENSOR ID NOT FOUND")
	except requests.exceptions.ConnectionError as e:
		print("Internet is not connected at "+ str(now))









