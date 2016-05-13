# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template, request, redirect, session
from wtforms import Form, TextAreaField, validators, StringField,IntegerField
import pickle
import os
import numpy as np
import datetime
from datetime import timedelta
from dateutil import parser
from pymongo import MongoClient
import json
import pandas as pd
import holidays
import time
from werkzeug.serving import BaseRequestHandler
from werkzeug.contrib.profiler import ProfilerMiddleware
from noaa.forecast import daily_forecast_by_lat_lon as forecastgps
import sys


yearlist=[2016,2017]

epoch=datetime.datetime.utcfromtimestamp(0)

class MyFancyRequestHandler(BaseRequestHandler):
    """Extend werkzeug request handler to suit our needs."""
    def handle(self):
        self.fancyStarted = time.time()
        rv = super(MyFancyRequestHandler, self).handle()
        return rv

    def send_response(self, *args, **kw):
        self.fancyProcessed = time.time()
        super(MyFancyRequestHandler, self).send_response(*args, **kw)

    def log_request(self, code='-', size='-'):
        duration = int((self.fancyProcessed - self.fancyStarted) * 1000)
        self.log('info', '"{0}" {1} {2} [{3}ms]'.format(self.requestline, code, size, duration))



#MUSTBEMANUALLY UPDATED

listofhols=[datetime.date(2016, 1, 1), datetime.date(2016, 1, 18), datetime.date(2016, 2, 15), datetime.date(2016, 5, 30), datetime.date(2016, 7, 4), datetime.date(2016, 9, 5), datetime.date(2016, 10, 10), datetime.date(2016, 11, 11), datetime.date(2016, 11, 24), datetime.date(2016, 12, 25), datetime.date(2016, 12, 26), datetime.date(2017, 1, 1), datetime.date(2017, 1, 2), datetime.date(2017, 1, 16), datetime.date(2017, 2, 20), datetime.date(2017, 5, 29), datetime.date(2017, 7, 4), datetime.date(2017, 9, 4), datetime.date(2017, 10, 9), datetime.date(2017, 11, 10), datetime.date(2017, 11, 11), datetime.date(2017, 11, 23), datetime.date(2017, 12, 25)]


dictofdates={datetime.date(2016, 9, 5): 'Labor Day', datetime.date(2017, 5, 29): 'Memorial Day', datetime.date(2016, 11, 11): 'Veterans Day', datetime.date(2016, 5, 30): 'Memorial Day', datetime.date(2017, 1, 2): "New Year's Day (Observed)", datetime.date(2016, 7, 4): 'Independence Day', datetime.date(2017, 11, 11): 'Veterans Day', datetime.date(2016, 12, 25): 'Christmas Day', datetime.date(2017, 11, 10): 'Veterans Day (Observed)', datetime.date(2017, 1, 16): 'Martin Luther King, Jr. Day', datetime.date(2017, 10, 9): 'Columbus Day', datetime.date(2016, 10, 10): 'Columbus Day', datetime.date(2017, 9, 4): 'Labor Day', datetime.date(2016, 2, 15): "Washington's Birthday", datetime.date(2016, 12, 26): 'Christmas Day (Observed)', datetime.date(2017, 2, 20): "Washington's Birthday", datetime.date(2017, 7, 4): 'Independence Day', datetime.date(2016, 1, 1): "New Year's Day", datetime.date(2016, 11, 24): 'Thanksgiving', datetime.date(2016, 1, 18): 'Martin Luther King, Jr. Day', datetime.date(2017, 12, 25): 'Christmas Day', datetime.date(2017, 1, 1): "New Year's Day", datetime.date(2017, 11, 23): 'Thanksgiving'}


def find_nearest(value,array): #value is a datetine
    c=[]
    p=[array[0]]
    m=[]
    holdate=datetime.date
    for dates in array:
       d=abs(dates-value).days
       if d<abs(p[-1]-value).days:
           p.append(dates)
           m.append(d)
    return (dictofdates[p[-1]],m[-1],p[-1])



def unix_time(dt):
    return(dt-epoch).total_seconds()*1000

app=Flask(__name__)




app.secret_key=b'\xe33\xb9\x1c\xee\xcf\x88\xbe?\xe0\x8am\x8e\x96\xd6\xde#<q=\xe5Vo"'

dict={'FLL - Fort Lauderdale-Hollywood International Airport - Fort Lauderdale, FL': 'FLL', 'YAK - Yakutat Airport - Yakutat, AK': 'YAK', 'HYA - Barnstable Municipal Airport-Boardman/Polando Field - Hyannis, MA': 'HYA', 'DRT - Del Rio International Airport - Del Rio, TX': 'DRT', 'RKS - Rock Springs-Sweetwater County Airport - Rock Springs, WY': 'RKS', 'ALB - Albany County Airport - Albany, NY': 'ALB', 'BTV - Burlington International Airport - Burlington, VT': 'BTV', 'DAL - Dallas Love Field - Dallas, TX': 'DAL', 'CID - The Eastern Iowa Airport - Cedar Rapids/Iowa City, IA': 'CID', 'OMA - Eppley Airfield - Omaha, NE': 'OMA', 'GSO - Piedmont Triad International Airport - Greensboro/High Point, NC': 'GSO', 'ATL - Hartsfield - Jackson Atlanta International Airport - Atlanta, GA': 'ATL', 'JNU - Juneau International Airport - Juneau, AK': 'JNU', 'SBN - South Bend Regional Airport - South Bend, IN': 'SBN', 'PSE - Mercedita Airport - Ponce, PR': 'PSE', 'EGE - Eagle County Regional Airport - Eagle, CO': 'EGE', 'GRR - Gerald R. Ford International Airport - Grand Rapids, MI': 'GRR', 'MEI - Key Field Airport - Meridian, MS': 'MEI', 'PIH - Pocatello Regional Airport - Pocatello, ID': 'PIH', 'ART - Watertown International Airport - Watertown, NY': 'ART', 'ACK - Nantucket Memorial Airport - Nantucket, MA': 'ACK', 'CDV - Merle K. (Mudhole) Smith Airport - Cordova, AK': 'CDV', 'LCH - Lake Charles Regional Airport - Lake Charles, LA': 'LCH', "MVY - Martha's Vineyard Airport - Martha's Vineyard, MA": 'MVY', 'ERI - Erie International Airport - Erie, PA': 'ERI', 'MKE - General Mitchell International Airport - Milwaukee, WI': 'MKE', 'PLN - Pellston Regional Airport of Emmet County - Pellston, MI': 'PLN', 'SJC - San Jose International Airport - San Jose, CA': 'SJC', 'LAX - Los Angeles International Airport - Los Angeles, CA': 'LAX', 'GFK - Grand Forks International Airport - Grand Forks, ND': 'GFK', 'IYK - Inyokern Airport - Inyokern, CA': 'IYK', 'ABI - Abilene Regional Airport - Abilene, TX': 'ABI', 'SAT - San Antonio International Airport - San Antonio, TX': 'SAT', 'EAU - Chippewa Valley Regional Airport - Eau Claire, WI': 'EAU', 'TPA - Tampa International Airport - Tampa, FL': 'TPA', 'CLE - Cleveland-Hopkins International Airport - Cleveland, OH': 'CLE', 'BPT - Jefferson County Airport - Beaumont/Port Arthur, TX': 'BPT', 'GGG - Gregg County Airport - Longview, TX': 'GGG', 'TYS - McGhee Tyson Airport - Knoxville, TN': 'TYS', 'DSM - Des Moines International Airport - Des Moines, IA': 'DSM', 'XNA - Northwest Arkansas Regional Airport - Fayetteville, AR': 'XNA', 'ROC - Greater Rochester International Airport - Rochester, NY': 'ROC', 'BLI - Bellingham International Airport - Bellingham, WA': 'BLI', 'MKG - Muskegon County Airport - Muskegon, MI': 'MKG', 'MDW - Chicago Midway Airport - Chicago, IL': 'MDW', 'BZN - Gallatin Field Airport - Bozeman, MT': 'BZN', 'SBA - Santa Barbara Municipal Airport - Santa Barbara, CA': 'SBA', 'CRW - Yeager Airport - Charleston/Dunbar, WV': 'CRW', 'AVP - Wilkes-Barre/Scranton International Airport - Scranton/Wilkes-Barre, PA': 'AVP', 'PSG - Petersburg Seaplane Base - Petersburg, AK': 'PSG', 'RDM - Roberts Field-Redmond Municipal Airport - Bend/Redmond, OR': 'RDM', 'ILM - Wilmington International Airport - Wilmington, NC': 'ILM', 'STX - Henry E Rohlsen Airport - Christiansted, VI': 'STX', 'CPR - Natrona County International Airport - Casper, WY': 'CPR', 'CMX - Houghton County Memorial Airport - Hancock/Houghton, MI': 'CMX', 'TYR - Tyler Pounds Field - Tyler, TX': 'TYR', 'BGM - Binghamton Regional Airport-Edwin A Link Field - Binghamton, NY': 'BGM', 'MGM - Dannelly Field - Montgomery, AL': 'MGM', 'KTN - Ketchikan International Airport - Ketchikan, AK': 'KTN', 'PUB - Pueblo Memorial Airport - Pueblo, CO': 'PUB', 'DIK - Dickinson Municipal Airport - Dickinson, ND': 'DIK', 'STL - Lambert St. Louis International Airport - St. Louis, MO': 'STL', 'ACV - Arcata-Eureka Airport - Arcata/Eureka, CA': 'ACV', 'MSY - Louis Armstrong New Orleans International Airport - New Orleans, LA': 'MSY', 'LBB - Lubbock International Airport - Lubbock, TX': 'LBB', 'SDF - Standiford Field - Louisville, KY': 'SDF', 'FLG - Flagstaff Pulliam Airport - Flagstaff, AZ': 'FLG', 'RNO - Reno/Tahoe International Airport - Reno, NV': 'RNO', 'TVC - Cherry Capital Airport - Traverse City, MI': 'TVC', 'CMI - University of Illinois Willard Airport - Champaign/Urbana, IL': 'CMI', 'JMS - Jamestown Municipal Airport - Jamestown, ND': 'JMS', 'ITH - Ithaca Tompkins Regional Airport - Ithaca/Cortland, NY': 'ITH', 'JFK - John F Kennedy International Airport - New York, NY': 'JFK', 'SRQ - Sarasota / Bradenton International Airport - Sarasota/Bradenton, FL': 'SRQ', 'PHL - Philadelphia International Airport - Philadelphia, PA': 'PHL', 'PWM - Portland International Jetport - Portland, ME': 'PWM', 'LEX - Blue Grass Airport - Lexington, KY': 'LEX', 'JAN - Jackson-Evers International Airport - Jackson/Vicksburg, MS': 'JAN', 'CAK - Akron-Canton Regional Airport - Akron, OH': 'CAK', 'AKN - King Salmon Airport - King Salmon, AK': 'AKN', 'JAC - Jackson Hole Airport - Jackson, WY': 'JAC', 'FSD - Joe Foss Field - Sioux Falls, SD': 'FSD', 'MHT - Manchester Airport - Manchester, NH': 'MHT', 'DBQ - Dubuque Regional Airport - Dubuque, IA': 'DBQ', 'DCA - Ronald Reagan Washington National Airport - Washington, DC': 'DCA', 'BRO - Brownsville-South Padre Island International Airport - Brownsville, TX': 'BRO', 'ITO - Hilo International Airport - Hilo, HI': 'ITO', 'CAE - Columbia Metropolitan Airport - Columbia, SC': 'CAE', 'BIS - Bismarck Municipal Airport - Bismarck/Mandan, ND': 'BIS', 'MIA - Miami International Airport - Miami, FL': 'MIA', 'OAK - Metropolitan Oakland International Airport - Oakland, CA': 'OAK', 'TTN - Trenton Mercer Airport - Trenton, NJ': 'TTN', 'ABQ - Albuquerque International Airport - Albuquerque, NM': 'ABQ', 'MOT - Minot International Airport - Minot, ND': 'MOT', 'SFO - San Francisco International Airport - San Francisco, CA': 'SFO', 'ISN - Sloulin Field International Airport - Williston, ND': 'ISN', 'CSG - Columbus Metropolitan Airport - Columbus, GA': 'CSG', 'VEL - Vernal Airport - Vernal, UT': 'VEL', 'SHV - Shreveport Regional Airport - Shreveport, LA': 'SHV', 'OTZ - Ralph Wien Memorial Airport - Kotzebue, AK': 'OTZ', 'GUC - Gunnison County Airport - Gunnison, CO': 'GUC', 'BDL - Bradley International Airport - Hartford, CT': 'BDL', 'PPG - Pago Pago International Airport - Pago Pago, TT': 'PPG', 'PNS - Pensacola Regional Airport - Pensacola, FL': 'PNS', 'HOU - William P Hobby Airport - Houston, TX': 'HOU', 'SEA - Seattle-Tacoma International Airport - Seattle, WA': 'SEA', 'HNL - Honolulu International Airport - Honolulu, HI': 'HNL', 'WRG - Wrangell Airport - Wrangell, AK': 'WRG', 'GEG - Spokane International Airport - Spokane, WA': 'GEG', 'SJT - Mathis Field - San Angelo, TX': 'SJT', 'LIT - Adams Field - Little Rock, AR': 'LIT', 'CVG - Cincinnati-Northern Kentucky International Airport - Cincinnati, OH': 'CVG', 'ABE - Lehigh Valley International Airport - Allentown/Bethlehem/Easton, PA': 'ABE', 'WYS - Yellowstone Airport - West Yellowstone, MT': 'WYS', 'MBS - MBS International Airport - Saginaw/Bay City/Midland, MI': 'MBS', 'SMF - Sacramento International Airport - Sacramento, CA': 'SMF', 'UST - St Augustine Airport - St. Augustine, FL': 'UST', 'ADK - Adak Airport - Adak Island, AK': 'ADK', 'PHF - Newport News-Williamsburg International Airport - Newport News/Williamsburg, VA': 'PHF', 'ABY - Southwest Georgia Regional Airport - Albany, GA': 'ABY', "ORD - Chicago O'Hare International Airport - Chicago, IL": 'ORD', 'RST - Rochester, Rochester International Airport - Rochester, MN': 'RST', 'STT - Cyril E. King Airport - Charlotte Amalie, VI': 'STT', 'DAB - Daytona Beach International Airport - Daytona Beach, FL': 'DAB', 'MDT - Harrisburg International Airport - Harrisburg, PA': 'MDT', 'SUN - Friedman Memorial Airport - Sun Valley/Hailey/Ketchum, ID': 'SUN', 'PIA - General Downing - Peoria International Airport - Peoria, IL': 'PIA', 'SGF - Springfield-Branson National Airport - Springfield, MO': 'SGF', 'MLB - Melbourne International Airport - Melbourne, FL': 'MLB', 'MLI - Quad City International Airport - Moline, IL': 'MLI', 'LFT - Lafayette Regional Airport - Lafayette, LA': 'LFT', 'SPS - Sheppard Air Force Base/Wichita Falls Municipal Airport - Wichita Falls, TX': 'SPS', 'LGA - La Guardia Airport - New York, NY': 'LGA', 'CMH - Port Columbus International Airport - Columbus, OH': 'CMH', 'TWF - Twin Falls Airport - Twin Falls, ID': 'TWF', 'INL - Falls International Airport - International Falls, MN': 'INL', 'LGB - Long Beach Airport (Daugherty Field) - Long Beach, CA': 'LGB', 'BMI - Central Illinois Regional Airport at Bloomington-Normal - Bloomington/Normal, IL': 'BMI', 'OKC - Will Rogers World Airport - Oklahoma City, OK': 'OKC', 'DTW - Detroit Metropolitan Wayne County Airport - Detroit, MI': 'DTW', 'MQT - Sawyer International Airport - Marquette, MI': 'MQT', 'RDU - Raleigh-Durham International Airport - Raleigh/Durham, NC': 'RDU', 'RIC - Richmond International Airport - Richmond, VA': 'RIC', 'MMH - Mammoth Lakes Airport - Mammoth Lakes, CA': 'MMH', 'CEC - Jack Mc Namara Field Airport - Crescent City, CA': 'CEC', 'LNK - Lincoln Municipal Airport - Lincoln, NE': 'LNK', 'CIC - Chico Municipal Airport - Chico, CA': 'CIC', 'HLN - Helena Regional Airport - Helena, MT': 'HLN', 'HPN - Westchester County Airport - White Plains, NY': 'HPN', 'OAJ - Albert J. Ellis Airport - Jacksonville/Camp Lejeune, NC': 'OAJ', 'MHK - Manhattan Regional Airport - Manhattan/Ft. Riley, KS': 'MHK', 'SJU - Luis Munoz Marin International Airport - San Juan, PR': 'SJU', 'HIB - Range Regional Airport - Hibbing, MN': 'HIB', 'DLG - Dillingham Airport - Dillingham, AK': 'DLG', 'COS - Colorado Springs Airport - Colorado Springs, CO': 'COS', 'TXK - Texarkana Regional Airport - Texarkana, AR': 'TXK', 'AUS - Austin-Bergstrom International Airport - Austin, TX': 'AUS', 'OGG - Kahului Airport - Kahului, HI': 'OGG', 'LAW - Lawton Municipal Airport - Lawton/Fort Sill, OK': 'LAW', 'HOB - Hobbs Airport - Hobbs, NM': 'HOB', 'ILG - New Castle Airport - Wilmington, DE': 'ILG', 'CNY - Canyonlands Field - Moab, UT': 'CNY', 'BIL - Logan International Airport - Billings, MT': 'BIL', 'HSV - Huntsville International Airport-Carl T Jones Field - Huntsville, AL': 'HSV', 'ONT - Ontario International Airport - Ontario, CA': 'ONT', 'ADQ - Kodiak Airport - Kodiak, AK': 'ADQ', 'BWI - Baltimore-Washington International Airport - Baltimore, MD': 'BWI', 'ESC - Delta County Airport - Escanaba, MI': 'ESC', 'AGS - Augusta Regional Airport - Augusta, GA': 'AGS', 'TUS - Tucson International Airport - Tucson, AZ': 'TUS', 'MLU - Monroe Regional Airport - Monroe, LA': 'MLU', 'AZO - Kalamazoo-Battle Creek International Airport - Kalamazoo, MI': 'AZO', 'PHX - Phoenix Sky Harbor International Airport - Phoenix, AZ': 'PHX', 'ELP - El Paso International Airport - El Paso, TX': 'ELP', 'GTF - Great Falls International Airport - Great Falls, MT': 'GTF', 'EYW - Key West International Airport - Key West, FL': 'EYW', 'GNV - Gainesville Regional Airport - Gainesville, FL': 'GNV', 'SPI - Abraham Lincoln Capital Airport - Springfield, IL': 'SPI', 'IPL - Imperial County Airport - El Centro, CA': 'IPL', 'BET - Bethel Airport - Bethel, AK': 'BET', 'BQN - Rafael Hernandez Airport - Aguadilla, PR': 'BQN', 'HYS - Hays Municipal Airport - Hays, KS': 'HYS', 'CDC - Cedar City Regional Airport - Cedar City, UT': 'CDC', 'LSE - La Crosse Municipal Airport - La Crosse, WI': 'LSE', 'CLD - McClellan-Palomar Airport - Carlsbad, CA': 'CLD', 'RAP - Rapid City Regional Airport - Rapid City, SD': 'RAP', 'GPT - Gulfport-Biloxi Regional Airport - Gulfport/Biloxi, MS': 'GPT', 'CIU - Chippewa County International Airport - Sault Ste. Marie, MI': 'CIU', 'CHO - Charlottesville-Albemarle Airport - Charlottesville, VA': 'CHO', 'ORH - Worcester, Worcester Regional Airport - Worcester, MA': 'ORH', 'OME - Nome Airport - Nome, AK': 'OME', 'GST - Gustavus Airport - Gustavus, AK': 'GST', 'FAT - Fresno Air Terminal Airport - Fresno, CA': 'FAT', 'BRD - Brainerd-Crow Wing County Regional Airport - Brainerd, MN': 'BRD', 'MCI - Kansas City International Airport - Kansas City, MO': 'MCI', 'MCN - Middle Georgia Regional Airport - Macon, GA': 'MCN', 'BOI - Boise Air Terminal - Boise, ID': 'BOI', 'GRK - Fort Hood, Robert Gray AAF Ft Hood - Killeen, TX': 'GRK', 'PSC - Tri-Cities Airport - Pasco/Kennewick/Richland, WA': 'PSC', 'GSP - Greenville-Spartanburg Airport - Greer, SC': 'GSP', 'STC - St. Cloud Regional Airport - St. Cloud, MN': 'STC', 'PVD - Theodore Francis Green State Airport - Providence, RI': 'PVD', 'CHA - Lovell Field - Chattanooga, TN': 'CHA', 'AMA - Rick Husband Amarillo International Airport - Amarillo, TX': 'AMA', 'CLT - Charlotte/Douglas International Airport - Charlotte, NC': 'CLT', 'FNT - Bishop International Airport - Flint, MI': 'FNT', 'PAH - Barkley Regional Airport - Paducah, KY': 'PAH', 'FCA - Glacier Park International Airport - Kalispell, MT': 'FCA', 'FSM - Fort Smith Municipal Airport - Fort Smith, AR': 'FSM', 'YUM - Yuma International Airport - Yuma, AZ': 'YUM', 'JAX - Jacksonville International Airport - Jacksonville, FL': 'JAX', 'TUL - Tulsa International Airport - Tulsa, OK': 'TUL', 'MFR - Rogue Valley International - Medford Airport - Medford, OR': 'MFR', 'AZA - Phoenix-Mesa Gateway Airport - Phoenix, AZ': 'AZA', 'COD - Yellowstone Regional Airport - Cody, WY': 'COD', 'BQK - Brunswick Golden Isles Airport - Brunswick, GA': 'BQK', 'LAN - Lansing, Capital City Airport - Lansing, MI': 'LAN', 'GJT - BLM Fire Center Heliport - Grand Junction, CO': 'GJT', 'SBP - San Luis Obispo County Airport - San Luis Obispo, CA': 'SBP', 'KOA - Kona International Airport - Kona, HI': 'KOA', 'GTR - Golden Triangle Regional Airport - Columbus, MS': 'GTR', 'PIT - Pittsburgh International Airport - Pittsburgh, PA': 'PIT', 'GCC - Gillette-Campbell County Airport - Gillette, WY': 'GCC', 'SYR - Syracuse Hancock International Airport - Syracuse, NY': 'SYR', 'IAD - Washington Dulles International Airport - Washington, DC': 'IAD', 'TLH - Tallahassee Regional Airport - Tallahassee, FL': 'TLH', 'LIH - Lihue Airport - Lihue, HI': 'LIH', 'EWN - Coastal Carolina Regional Airport - New Bern/Morehead/Beaufort, NC': 'EWN', 'FAI - Fairbanks International Airport - Fairbanks, AK': 'FAI', 'FAR - Hector International Airport - Fargo, ND': 'FAR', 'LWS - Lewiston Nez Perce County Airport - Lewiston, ID': 'LWS', 'CLL - Easterwood Field - College Station/Bryan, TX': 'CLL', 'DVL - Devils Lake Municipal Airport - Devils Lake, ND': 'DVL', 'SCE - University Park Airport - State College, PA': 'SCE', 'ATW - Outagamie County Airport - Appleton, WI': 'ATW', 'MFE - McAllen Miller International Airport - Mission/McAllen/Edinburg, TX': 'MFE', 'CHS - Charleston International Airport - Charleston, SC': 'CHS', 'PBI - Palm Beach International - West Palm Beach/Palm Beach, FL': 'PBI', 'HDN - Yampa Valley Airport - Hayden, CO': 'HDN', 'BJI - Bemidji-Beltrami County Airport - Bemidji, MN': 'BJI', 'FAY - Fayetteville Municipal Airport - Fayetteville, NC': 'FAY', 'RFD - Chicago/Rockford International Airport - Rockford, IL': 'RFD', 'GRB - Austin Straubel International Airport - Green Bay, WI': 'GRB', 'TRI - Tri-Cities Regional Airport - Bristol/Johnson City/Kingsport, TN': 'TRI', 'HRL - Rio Grande Valley International Airport - Harlingen/San Benito, TX': 'HRL', 'IAG - Niagara Falls International Airport - Niagara Falls, NY': 'IAG', 'LAS - Mc Carran International Airport - Las Vegas, NV': 'LAS', 'COU - Columbia Regional Airport - Columbia, MO': 'COU', 'BUR - Bob Hope Airport - Burbank, CA': 'BUR', 'SAF - Santa Fe Municipal Airport - Santa Fe, NM': 'SAF', 'JLN - Joplin Regional Airport - Joplin, MO': 'JLN', 'DFW - Dallas/Fort Worth International Airport - Dallas/Fort Worth, TX': 'DFW', 'SAN - San Diego International Airport - San Diego, CA': 'SAN', 'SCC - Deadhorse Airport - Deadhorse, AK': 'SCC', 'MSO - Missoula International Airport - Missoula, MT': 'MSO', 'SLC - Salt Lake City International Airport - Salt Lake City, UT': 'SLC', 'ICT - Wichita Mid-Continent Airport - Wichita, KS': 'ICT', 'GCK - Garden City Regional Airport - Garden City, KS': 'GCK', 'MTJ - Montrose Regional Airport - Montrose/Delta, CO': 'MTJ', 'CRP - Corpus Christi International Airport - Corpus Christi, TX': 'CRP', 'BTR - Baton Rouge Metropolitan Airport - Baton Rouge, LA': 'BTR', 'MAF - Midland International Airport - Midland/Odessa, TX': 'MAF', 'RDD - Redding Municipal Airport - Redding, CA': 'RDD', 'BNA - Nashville International Airport - Nashville, TN': 'BNA', 'CWA - Central Wisconsin Airport - Mosinee, WI': 'CWA', 'AEX - Alexandria International Airport - Alexandria, LA': 'AEX', 'IAH - George Bush Intercontinental/Houston Airport - Houston, TX': 'IAH', 'ROA - Roanoke Regional Airport-Woodrum Field - Roanoke, VA': 'ROA', 'PDX - Portland International Airport - Portland, OR': 'PDX', 'AVL - Asheville Regional Airport - Asheville, NC': 'AVL', 'MRY - Monterey Peninsula Airport - Monterey, CA': 'MRY', 'SIT - Sitka Rocky Gutierrez Airport - Sitka, AK': 'SIT', 'SMX - Santa Maria Airport - Santa Maria, CA': 'SMX', 'VPS - Valparaiso / Eglin Air Force Base - Valparaiso, FL': 'VPS', 'ACY - Atlantic City International Airport - Atlantic City, NJ': 'ACY', 'MCO - Orlando International Airport - Orlando, FL': 'MCO', 'GRI - Central Nebraska Regional Airport - Grand Island, NE': 'GRI', 'IMT - Ford Airport - Iron Mountain/Kingsfd, MI': 'IMT', 'BGR - Bangor International Airport - Bangor, ME': 'BGR', 'LBE - Arnold Palmer Regional Airport - Latrobe, PA': 'LBE', 'MSN - Dane County Regional Airport - Madison, WI': 'MSN', 'ANC - Anchorage International Airport - Anchorage, AK': 'ANC', 'ELM - Elmira-Corning Regional Airport - Elmira/Corning, NY': 'ELM', 'LMT - Klamath Falls Airport - Klamath Falls, OR': 'LMT', 'BHM - Birmingham-Shuttlesworth International Airport - Birmingham, AL': 'BHM', 'APN - Alpena County Regional Airport - Alpena, MI': 'APN', 'SGU - Saint George Municipal Airport - St. George, UT': 'SGU', 'BTM - Bert Mooney Airport - Butte, MT': 'BTM', 'BFL - Meadows Field - Bakersfield, CA': 'BFL', 'DAY - James M Cox Dayton International Airport - Dayton, OH': 'DAY', 'MOB - Mobile Regional Airport - Mobile, AL': 'MOB', 'DHN - Dothan Regional Airport - Dothan, AL': 'DHN', 'LRD - Laredo International Airport - Laredo, TX': 'LRD', 'ALO - Waterloo Municipal Airport - Waterloo, IA': 'ALO', 'RHI - Rhinelander-Oneida County Airport - Rhinelander, WI': 'RHI', 'BRW - Wiley Post-Will Rogers Memorial Airport - Barrow, AK': 'BRW', 'BOS - General Edward Lawrence Logan International Airport - Boston, MA': 'BOS', 'FWA - Fort Wayne International Airport - Fort Wayne, IN': 'FWA', 'SPN - Francisco C. Ada International Airport - Saipan, TT': 'SPN', 'PIB - Pine Belt Regional Airport - Hattiesburg/Laurel, MS': 'PIB', 'BUF - Greater Buffalo International Airport - Buffalo, NY': 'BUF', 'DEN - Denver International Airport - Denver, CO': 'DEN', 'SUX - Sioux Gateway Airport/Col. Bud Day Field - Sioux City, IA': 'SUX', 'PSP - Palm Springs International Airport - Palm Springs, CA': 'PSP', 'EWR - Newark International Airport - Newark, NJ': 'EWR', 'LAR - Laramie Regional Airport - Laramie, WY': 'LAR', 'VLD - Valdosta Regional Airport - Valdosta, GA': 'VLD', 'EUG - Mahlon Sweet Field Airport - Eugene, OR': 'EUG', 'SNA - John Wayne-Orange County Airport - Santa Ana, CA': 'SNA', 'ROW - Roswell Industrial Air Center Airport - Roswell, NM': 'ROW', 'EKO - Elko Regional Airport - Elko, NV': 'EKO', 'MYR - Myrtle Beach International Airport - Myrtle Beach, SC': 'MYR', 'RSW - Southwest Florida International Airport - Fort Myers, FL': 'RSW', 'IDA - Fanning Field - Idaho Falls, ID': 'IDA', 'SHD - Shenandoah Valley Regional Airport - Staunton, VA': 'SHD', 'FOE - Forbes Field Airport - Topeka, KS': 'FOE', 'TOL - Toledo Express Airport - Toledo, OH': 'TOL', 'DLH - Duluth International Airport - Duluth, MN': 'DLH', 'EVV - Evansville Regional Airport - Evansville, IN': 'EVV', 'DRO - Durango-La Plata County Airport - Durango, CO': 'DRO', 'ORF - Norfolk International Airport - Norfolk, VA': 'ORF', 'GUM - Antonio B. Won Pat International Airport - Guam, TT': 'GUM', 'ISP - Long Island Mac Arthur Airport - Islip, NY': 'ISP', 'SAV - Savannah International Airport - Savannah, GA': 'SAV', 'MSP - Minneapolis-Saint Paul International Airport - Minneapolis, MN': 'MSP', 'ASE - Aspen-Pitkin County Airport-Sardy Field - Aspen, CO': 'ASE', 'IND - Indianapolis International Airport - Indianapolis, IN': 'IND', 'SWF - Stewart International Airport - Newburgh/Poughkeepsie, NY': 'SWF', 'PBG - Plattsburgh Air Force Base - Plattsburgh, NY': 'PBG', 'ECP - Northwest Florida Beaches International Airport - Panama City, FL': 'ECP', 'OTH - Southwest Oregon Regional Airport - North Bend/Coos Bay, OR': 'OTH', 'MOD - Modesto City-County Airport - Modesto, CA': 'MOD', 'ACT - Waco Regional Airport - Waco, TX': 'ACT', 'ABR - Aberdeen Regional Airport - Aberdeen, SD': 'ABR', 'MEM - Memphis International Airport - Memphis, TN': 'MEM', 'BKG - Branson Airport - Branson, MO': 'BKG'}


#loadpickleobjects
cur_dir=os.path.dirname(__file__)
#clf=pickle.load(open(os.path.join(cur_dir,'pkl_objects/dmodel24.p'),'rb'))
clf=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/dlog.p'),'rb'))
#clf2=pickle.load(open(os.path.join(cur_dir,'pkl_objects/amodel24.p'),'rb'))
clf2=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/alog.p'),'rb'))
dest=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/dest.p'),'rb'))
origin=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/origin.p'),'rb'))
ucc=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/carrier.p'),'rb'))
onehot=pickle.load(open(os.path.join(cur_dir,'pkl_objects/obj/onehotencoder.p'),'rb'))
x=open('pkl_objects/dictionary_for_weather/lat.p','rb')
latdict=pickle.load(x)
x.close()

y=open('pkl_objects/dictionary_for_weather/lng.p','rb')
lngdict=pickle.load(y)
y.close()


#onehot=pickle.load(open(os.path.join(cur_dir,'pkl_objects/onehot.p'),'rb'))


#setupconnectiontomongodb


#fn to find best and worst months
def findwstmth(monthcomp, maxmthvalue):
    for months in monthcomp:
        if months[1] == maxmthvalue:
            wstmth = months[0]
            return wstmth


def findbstmth(monthcomp, minmthvalue):
    for months in monthcomp:
        if months[1] == minmthvalue:
            bstmth = months[0]
            return bstmth




#defineclassifier
def classify(MONTH,DAY_OF_WEEK,UNIQUE_CARRIER,ORIGIN,DEST,DaysFrmNearest,hour,type):

    if type=="dep":
        label={0:"Not Delayed",1:"Delayed"}
        a=MONTH
        b=DAY_OF_WEEK
        c=ucc.transform(UNIQUE_CARRIER)
        e=origin.transform(ORIGIN)
        f=dest.transform(DEST)
        predictor=onehot.transform([a,b,c,e,f,DaysFrmNearest,hour])
        #y=clf.predict(predictor)
        x=clf.predict_proba(predictor)
        q=(x[0][1].astype(float))
        if q>0.5:
            prediction=label[1]
        else:
            prediction=label[0]
        q="{0:.0f}%".format(q*100)
        return (prediction,q)
    if type=="arr":
        label={0:"Not Delayed",1:"Delayed"}
        a=MONTH
        b=DAY_OF_WEEK
        c=ucc.transform(UNIQUE_CARRIER)
        e=origin.transform(ORIGIN)
        f=dest.transform(DEST)
        predictor = onehot.transform([a, b, c, e, f, DaysFrmNearest, hour])
        #y=clf2.predict(predictor)
        x=clf2.predict_proba(predictor)
        q=(x[0][1].astype(float))
        q=(x[0][1].astype(float))
        if q>0.5:
            prediction=label[1]
        else:
            prediction=label[0]
        q="{0:.0f}%".format(q*100)
        return (prediction,q)
        q="{0:.0f}%".format(q*100)
        return (prediction,q)
#["MONTH","DAY_OF_WEEK","UNIQUE_CARRIER","ORIGIN","DEST",'DaysFrmNearest','hour']

def probability(MONTH,DAY_OF_WEEK,UNIQUE_CARRIER,ORIGIN,DEST,DaysFrmNearest,hour,type):
    if type=='dep':
        label={0:"Not Delayed",1:"Delayed"}
        a=MONTH
        b=DAY_OF_WEEK
        c=ucc.transform(UNIQUE_CARRIER)
        e=origin.transform(ORIGIN)
        f=dest.transform(DEST)
        predictor = [a, b, c, e, f, DaysFrmNearest, hour]
        y=clf.predict_proba(predictor)
        a=(y[0][1].astype(float))
        a="{0:.0f}%".format(a*100)
        return a
    if type=="arr":
        label={0:"Not Delayed",1:"Delayed"}
        a=MONTH
        b=DAY_OF_WEEK
        c=ucc.transform(UNIQUE_CARRIER)
        e=origin.transform(ORIGIN)
        f=dest.transform(DEST)
        predictor = [a, b, c, e, f, DaysFrmNearest, hour]
        y=clf2.predict_proba(predictor)
        a=(y[0][1].astype(float))
        a="{0:.0f}%".format(a*100)
        return a


def generatelistofdates(searchdate, x):
    dt = searchdate
    dt2=datetime.datetime.today()
    a = dt - dt2

    if a.days>=x:

        d=dt-timedelta(days=x)

        y=x

        rng=pd.date_range(dt,periods=x+1, freq="D")

        rng2=pd.date_range(d,periods=(x),freq="D")



        rng.tolist()
        rng2.tolist()

        c=rng.union(rng2)

        return(c,y)



    else:



        d = dt - timedelta(days=(a.days+1))

        rng = pd.date_range(dt, periods=x+1, freq="D")

        rng2 = pd.date_range(d, periods=(a.days+1), freq="D")

        rng.tolist()
        rng2.tolist()

        c = rng + rng2

        y=(int(a.days)+1)

        return(c,y)


#getpredictordata in a form
class flightdata(Form):
    MONTH=IntegerField('Month')
    DAY_OF_WEEK=IntegerField('Day') #needtofix this later
    CARRIER=StringField('Carrier')
    FL_NUM=IntegerField('FlightNumber')
    ORIGIN=StringField('OriginAirport')
    DEST=StringField('DestinationAirport')


validitycollection=['True']

#def getdata(withid, frequency,Origin,Destination,Carrier,FL_NUM):
    #client = MongoClient()
    #Dictoftimes = {0: "12AM", 1: "1AM", 2: "2AM", 3: "3AM", 4: "4AM", 5: "5AM", 6: "6AM", 7: "7AM", 8: "8AM", 9: '9AM',
                   #10: '10AM', 11: "11AM", 12: '12AM', 13: "1PM", 14: "2PM", 15: '3PM', 16: '4PM', 17: "5PM", 18: '6PM',
                   #19: '7PM', 20: '8PM', 21: '9PM', 22: '10PM', 23: '11PM'}# -*- coding: utf-8 -*-

#setupconnectiontomongodb


#fn to find best and worst months






def getdata(withid, frequency,Origin,Destination,Carrier,FL_NUM,client):
    Dictoftimes = {0: "12AM", 1: "1AM", 2: "2AM", 3: "3AM", 4: "4AM", 5: "5AM", 6: "6AM", 7: "7AM", 8: "8AM", 9: '9AM',
                   10: '10AM', 11: "11AM", 12: '12AM', 13: "1PM", 14: "2PM", 15: '3PM', 16: '4PM', 17: "5PM", 18: '6PM',
                   19: '7PM', 20: '8PM', 21: '9PM', 22: '10PM', 23: '11PM'}
    DictofMonths = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep",
                    10: "Oct", 11: "Nov", 12: "Dec"}
    DictofMonths2 = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May",
                     "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
                     "Oct": "October", "Nov": "November", "Dec": "December"}
    DictofDays = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thur', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
    DictofDays2 = {'Mon':'Monday','Tue':'Tuesday','Wed':"Wednesday",'Thur':'Thursday','Fri':'Friday','Sat':"Saturday",'Sun':"Sunday"}
    if withid==False:
        db=client.final.data



        if frequency=="h":



            hourcomp = []
            hrs = []

            try:

                hravgdelay = list(db.find({'identifier': "h" +" "+ str(Origin) + " " + str(Destination) + " "+str(Carrier)},
                                           {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}).limit(24))
                if len(hravgdelay) == 1:
                    only1hr = True
                else:
                    only1hr = False

                for y in range(0, len(hravgdelay)):

                    hr = []

                    if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                        hr.append(Dictoftimes[int((hravgdelay[y]['hour']))])
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                        hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                        hourcomp.append(hr)

                maxhrvalue = "{0:.0f}".format(np.amax(hrs))
                minhrvalue = "{0:.0f}".format(np.amin(hrs))

                wsthr = findbstmth(hourcomp, maxhrvalue)

                bsthr = findwstmth(hourcomp, minhrvalue)

                return(maxhrvalue,minhrvalue,bsthr,wsthr,hourcomp,only1hr)

            except:
                db2=client.final.data3
                hravgdelay = list(
                    db2.find({'identifier': "h" + " " + str(Origin) + " " + str(Destination)},
                            {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}))

                if len(hravgdelay) == 1:
                    only1hr = True
                else:
                    only1hr = False

                for y in range(0, len(hravgdelay)):

                    hr = []

                    if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                        hr.append(Dictoftimes[int((hravgdelay[y]['hour']))])
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                        hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                        hourcomp.append(hr)

                maxhrvalue = "{0:.0f}".format(np.amax(hrs))
                minhrvalue = "{0:.0f}".format(np.amin(hrs))

                wsthr = findbstmth(hourcomp, maxhrvalue)

                bsthr = findwstmth(hourcomp, minhrvalue)

                return (maxhrvalue, minhrvalue, bsthr, wsthr, hourcomp,only1hr)


        if frequency=="d":
            try:
                daycomp = []
                dys = []

                dayavgdelay = list(db.find({'identifier': "d" +" "+ str(Origin) + " " + str(Destination) +  " "+str(Carrier)},
                                            {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))

                for y in range(0, len(dayavgdelay)):

                    day = []

                    if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                        day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                        day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                        day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                        dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                        daycomp.append(day)

                maxdyvalue = "{0:.0f}".format(np.amax(dys))
                mindyvalue = "{0:.0f}".format(np.amin(dys))

                wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

                bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]

                return (maxdyvalue,mindyvalue,bstdy,wstdy,daycomp)
            except:
                db2 = client.final.data3
                daycomp = []
                dys = []

                dayavgdelay = list(
                    db2.find({'identifier': "d" + " " + str(Origin) + " " + str(Destination)},
                            {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))

                for y in range(0, len(dayavgdelay)):

                    day = []

                    if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                        day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                        day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                        day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                        dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                        daycomp.append(day)

                maxdyvalue = "{0:.0f}".format(np.amax(dys))
                mindyvalue = "{0:.0f}".format(np.amin(dys))

                wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

                bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]

                return (maxdyvalue, mindyvalue, bstdy, wstdy, daycomp)



        if frequency == 'm':
            try:
                mthcomp = []
                mts = []

                hravgdelay = list(db.find({'identifier': "m" + " "+str(Origin) + " " + str(Destination) +  " "+str(Carrier)},
                                          {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}).limit(13))

                for y in range(0, len(hravgdelay)):

                    hr = []

                    if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                        hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                        mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                        mthcomp.append(hr)

                maxmthvalue = "{0:.0f}".format(np.amax(mts))
                minmthvalue = "{0:.0f}".format(np.amin(mts))

                wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

                bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]

                return (maxmthvalue, minmthvalue, bstmth, wstmth, mthcomp)
            except:
                db2 = client.final.data3
                mthcomp = []
                mts = []

                hravgdelay = list(db2.find({'identifier': "m" + " " + str(Origin) + " " + str(Destination)},
                                          {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}))

                for y in range(0, len(hravgdelay)):

                    hr = []

                    if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                        hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                        hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                        mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                        mthcomp.append(hr)

                maxmthvalue = "{0:.0f}".format(np.amax(mts))
                minmthvalue = "{0:.0f}".format(np.amin(mts))

                wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

                bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]

                return (maxmthvalue, minmthvalue, bstmth, wstmth, mthcomp)


    else:
        db = client.final.data2

        if frequency == "h":

            hourcomp = []
            hrs = []

            hravgdelay = list(db.find({'identifier':"h"+" "+str(Carrier)+" " +str(FL_NUM)+" " + str(Origin) + " " + str(Destination) },
                                      {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}).limit(24))

            if len(hravgdelay)==1:
                only1hr=True
            else:
                only1hr=False

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(Dictoftimes[(int(hravgdelay[y]['hour']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    hourcomp.append(hr)

            maxhrvalue = "{0:.0f}".format(np.amax(hrs))
            minhrvalue = "{0:.0f}".format(np.amin(hrs))

            wsthr = findbstmth(hourcomp, maxhrvalue)

            bsthr = findwstmth(hourcomp, minhrvalue)

            return (maxhrvalue, minhrvalue, bsthr, wsthr, hourcomp,only1hr)







        if frequency=='m':
            mthcomp = []
            mts = []

            hravgdelay = list(db.find({'identifier': "m"+" "+str(Carrier)+" " +str(FL_NUM)+" " + str(Origin) + " " + str(Destination)},
                                      {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}).limit(13))

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    mthcomp.append(hr)

            maxmthvalue = "{0:.0f}".format(np.amax(mts))
            minmthvalue = "{0:.0f}".format(np.amin(mts))

            wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

            bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]

            return(maxmthvalue,minmthvalue,bstmth,wstmth,mthcomp)

        if frequency == "d":
            daycomp = []
            dys = []

            dayavgdelay = list(
                db.find({'identifier': "d" + " " + str(Carrier) + " " + str(FL_NUM) + " " + str(Origin) + " " + str(
                    Destination)},
                        {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))
            print(dayavgdelay)

            for y in range(0, len(dayavgdelay)):

                day = []

                if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                    day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                    dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                    daycomp.append(day)

            maxdyvalue = "{0:.0f}".format(np.amax(dys))
            mindyvalue = "{0:.0f}".format(np.amin(dys))

            wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

            bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]

            return (maxdyvalue, mindyvalue, bstdy, wstdy, daycomp)


def getdata2(withid,Origin,Destination,Carrier,FL_NUM,client):
    Dictoftimes = {0: "12AM", 1: "1AM", 2: "2AM", 3: "3AM", 4: "4AM", 5: "5AM", 6: "6AM", 7: "7AM", 8: "8AM", 9: '9AM',
                   10: '10AM', 11: "11AM", 12: '12AM', 13: "1PM", 14: "2PM", 15: '3PM', 16: '4PM', 17: "5PM", 18: '6PM',
                   19: '7PM', 20: '8PM', 21: '9PM', 22: '10PM', 23: '11PM'}
    DictofMonths = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep",
                    10: "Oct", 11: "Nov", 12: "Dec"}
    DictofMonths2 = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May",
                     "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
                     "Oct": "October", "Nov": "November", "Dec": "December"}
    DictofDays = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thur', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
    DictofDays2 = {'Mon':'Monday','Tue':'Tuesday','Wed':"Wednesday",'Thur':'Thursday','Fri':'Friday','Sat':"Saturday",'Sun':"Sunday"}
    if withid==False:
        db=client.final.data







        hourcomp = []
        hrs = []

        try:

            hravgdelay = list(db.find({'identifier': "h" +" "+ str(Origin) + " " + str(Destination) + " "+str(Carrier)},
                                       {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}).limit(24))
            if len(hravgdelay) == 1:
                only1hr = True
            else:
                only1hr = False

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(Dictoftimes[int((hravgdelay[y]['hour']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    hourcomp.append(hr)

            maxhrvalue = "{0:.0f}".format(np.amax(hrs))
            minhrvalue = "{0:.0f}".format(np.amin(hrs))

            wsthr = findbstmth(hourcomp, maxhrvalue)

            bsthr = findwstmth(hourcomp, minhrvalue)



        except:
            db2=client.final.data3
            hravgdelay = list(
                db2.find({'identifier': "h" + " " + str(Origin) + " " + str(Destination)},
                        {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}))

            if len(hravgdelay) == 1:
                only1hr = True
            else:
                only1hr = False

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(Dictoftimes[int((hravgdelay[y]['hour']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    hourcomp.append(hr)

            maxhrvalue = "{0:.0f}".format(np.amax(hrs))
            minhrvalue = "{0:.0f}".format(np.amin(hrs))

            wsthr = findbstmth(hourcomp, maxhrvalue)

            bsthr = findwstmth(hourcomp, minhrvalue)

        daycomp = []
        dys = []

        try:


            dayavgdelay = list(db.find({'identifier': "d" +" "+ str(Origin) + " " + str(Destination) +  " "+str(Carrier)},
                                        {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))

            for y in range(0, len(dayavgdelay)):

                day = []

                if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                    day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                    dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                    daycomp.append(day)

            maxdyvalue = "{0:.0f}".format(np.amax(dys))
            mindyvalue = "{0:.0f}".format(np.amin(dys))

            wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

            bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]


        except:
            db2 = client.final.data3

            dayavgdelay = list(
                db2.find({'identifier': "d" + " " + str(Origin) + " " + str(Destination)},
                        {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))

            for y in range(0, len(dayavgdelay)):

                day = []

                if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                    day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                    day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                    dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                    daycomp.append(day)

            maxdyvalue = "{0:.0f}".format(np.amax(dys))
            mindyvalue = "{0:.0f}".format(np.amin(dys))

            wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

            bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]

        mthcomp = []
        mts = []


        try:


            hravgdelay = list(db.find({'identifier': "m" + " "+str(Origin) + " " + str(Destination) +  " "+str(Carrier)},
                                      {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}).limit(13))

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    mthcomp.append(hr)

            maxmthvalue = "{0:.0f}".format(np.amax(mts))
            minmthvalue = "{0:.0f}".format(np.amin(mts))

            wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

            bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]


        except:
            db2 = client.final.data3


            hravgdelay = list(db2.find({'identifier': "m" + " " + str(Origin) + " " + str(Destination)},
                                      {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}))

            for y in range(0, len(hravgdelay)):

                hr = []

                if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                    hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                    hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                    mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                    mthcomp.append(hr)

            maxmthvalue = "{0:.0f}".format(np.amax(mts))
            minmthvalue = "{0:.0f}".format(np.amin(mts))

            wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

            bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]

        return (
        maxhrvalue, minhrvalue, bsthr, wsthr, hourcomp, only1hr, maxdyvalue, mindyvalue, bstdy, wstdy, daycomp, maxmthvalue,
        minmthvalue, bstmth, wstmth, mthcomp)


    else:
        db = client.final.data2



        hourcomp = []
        hrs = []

        hravgdelay = list(db.find({'identifier':"h"+" "+str(Carrier)+" " +str(FL_NUM)+" " + str(Origin) + " " + str(Destination) },
                                  {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'hour': 1}).limit(24))

        if len(hravgdelay)==1:
            only1hr=True
        else:
            only1hr=False

        for y in range(0, len(hravgdelay)):

            hr = []

            if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                hr.append(Dictoftimes[(int(hravgdelay[y]['hour']))])
                hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                hrs.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                hourcomp.append(hr)

        maxhrvalue = "{0:.0f}".format(np.amax(hrs))
        minhrvalue = "{0:.0f}".format(np.amin(hrs))

        wsthr = findbstmth(hourcomp, maxhrvalue)

        bsthr = findwstmth(hourcomp, minhrvalue)









        mthcomp = []
        mts = []

        hravgdelay = list(db.find({'identifier': "m"+" "+str(Carrier)+" " +str(FL_NUM)+" " + str(Origin) + " " + str(Destination)},
                                  {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'month': 1}).limit(13))

        for y in range(0, len(hravgdelay)):

            hr = []

            if float(hravgdelay[y]['route_day_dep_pct']) > 0 and float(hravgdelay[y]['route_day_arr_pct']) > 0:
                hr.append(DictofMonths[int((hravgdelay[y]['month']))])
                hr.append("{0:.0f}".format(hravgdelay[y]['route_day_dep_pct'] * 100))
                hr.append("{0:.0f}".format(hravgdelay[y]['route_day_arr_pct'] * 100))
                mts.append(hravgdelay[y]['route_day_dep_pct'] * 100)
                mthcomp.append(hr)

        maxmthvalue = "{0:.0f}".format(np.amax(mts))
        minmthvalue = "{0:.0f}".format(np.amin(mts))

        wstmth = DictofMonths2[findbstmth(mthcomp, maxmthvalue)]

        bstmth = DictofMonths2[findwstmth(mthcomp, minmthvalue)]




        daycomp = []
        dys = []

        dayavgdelay = list(
            db.find({'identifier': "d" + " " + str(Carrier) + " " + str(FL_NUM) + " " + str(Origin) + " " + str(
                Destination)},
                    {'route_day_arr_pct': 1, 'route_day_dep_pct': 1, 'dayofweek': 1}).limit(8))
        print(dayavgdelay)

        for y in range(0, len(dayavgdelay)):

            day = []

            if float(dayavgdelay[y]['route_day_dep_pct']) > 0 and float(dayavgdelay[y]['route_day_arr_pct']) > 0:
                day.append(DictofDays[int(dayavgdelay[y]['dayofweek'])])
                day.append("{0:.0f}".format(dayavgdelay[y]['route_day_dep_pct'] * 100))
                day.append("{0:.0f}".format(dayavgdelay[y]['route_day_arr_pct'] * 100))
                dys.append(dayavgdelay[y]['route_day_dep_pct'] * 100)
                daycomp.append(day)

        maxdyvalue = "{0:.0f}".format(np.amax(dys))
        mindyvalue = "{0:.0f}".format(np.amin(dys))

        wstdy = DictofDays2[findbstmth(daycomp, maxdyvalue)]

        bstdy = DictofDays2[findwstmth(daycomp, mindyvalue)]

        return (
        maxhrvalue, minhrvalue, bsthr, wsthr, hourcomp, only1hr, maxdyvalue, mindyvalue, bstdy, wstdy, daycomp, maxmthvalue,
        minmthvalue, bstmth, wstmth, mthcomp)



def getotpct(Month,Dayofweek,hour,Origin,Destination,Carrier,Flightnumber,client):
    statsbad = False





    try:
        withid=True
        requestgood=True
        db = client.final.data4
        p = list(db.find(
            {'identifier': str(Carrier) + " " + str(Flightnumber) + " " + str(Origin) + " " + str(Destination)},{'route_day_arr_pct': 1, 'route_day_dep_pct': 1}).limit(2))
        percentarrival = p[0]['route_day_arr_pct']
        percentdeparture = p[0]['route_day_dep_pct']
        try:
            avgcarrierdelay = round(int(p[0]['avgcarrierdelay'], 2))
        except:
            avgcarrierdelay = ""
            pass


        if percentdeparture > 0.25:
            statsbad = True

        ontimepercentage = "{0:.0f}".format((1 - percentdeparture) * 100)
        percentarrival = "{0:.0f}".format((1 - percentarrival) * 100)
        return (requestgood,statsbad, ontimepercentage, percentarrival,withid)
    except:
        try:
            withid=False
            db = client.final.data6
            ot = list(db.find({'routeidentifier': str(Origin) + " " + str(Destination), 'carrier': str(Carrier),
                               }, {
                                  'route_day_arr_ot': 1, 'route_day_dep_ot': 1}).limit(1))
            percentdeparture = ot[0]['route_day_dep_ot']
            percentarrival = ot[0]['route_day_arr_ot']
            a = True
            if percentdeparture > 0.25:
                a = False

            ontimepercentage = "{0:.0f}".format((1 - percentdeparture) * 100)
            percentarrival = "{0:.0f}".format((1 - percentarrival) * 100)

            if percentdeparture > 0.25:
                statsbad = True
            requestgood = True
            return (requestgood, statsbad, ontimepercentage, percentarrival,withid)
        except:
            withid=False
            db = client.final.data7
            requestgood = False
            ot = list(db.find({'routeidentifier': str(Origin) + " " + str(Destination)
                               }, {
                                  'route_day_arr_ot': 1, 'route_day_dep_ot': 1}).limit(1))
            percentdeparture = ot[0]['route_day_dep_ot']
            percentarrival = ot[0]['route_day_arr_ot']
            a = True
            if percentdeparture > 0.25:
                a = False

            ontimepercentage = "{0:.0f}".format((1 - percentdeparture) * 100)
            percentarrival = "{0:.0f}".format((1 - percentarrival) * 100)

            if percentdeparture > 0.25:
                statsbad = True
            requestgood = True
            return (requestgood, statsbad, ontimepercentage, percentarrival, withid)

"""
y = float((float(Month) * 10000 + float(Dayofweek) * 1000 + float(hour)) / (float(1000)))

            ot = list(db.find({'routeidentifier': str(Origin) + " " + str(Destination), 'carrier': str(Carrier),
                          'time2': {"$near": [y, 0]}}, {
                             'route_day_arr_ot': 1, 'route_day_dep_ot': 1}).limit(1))
            percentdeparture = ot[0]['route_day_dep_ot']
            percentarrival = ot[0]['route_day_arr_ot']
            a = True
            if percentdeparture > 0.25:
                a = False

            ontimepercentage = "{0:.0f}".format((1 - percentdeparture) * 100)
            percentarrival = "{0:.0f}".format((1 - percentarrival) * 100)

            if percentdeparture > 0.25:
                statsbad = True
            requestgood=True
            return (requestgood,statsbad, ontimepercentage, percentarrival)
        except:
            requestgood=False
            return (requestgood,0,0,0)
"""


#simplelayout
@app.route('/')
def index():



    return render_template('mainindex2.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'),404
@app.errorhandler(403)
def page_not_found(e):
    return render_template('error.html'),403
@app.errorhandler(410)
def page_not_found(e):
    return render_template('error.html'),410
@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html'),500



@app.route('/error')
def problem():
    return render_template('error.html',link='/')



@app.route('/results', methods=['POST'])
def result():
    client=MongoClient()
    procdates=[]
    procdates2=[]
    if request.method=='POST':
        try:
            Date=request.form["Date"]
            dt=parser.parse(Date) #this is initalized from 0
            dt2=datetime.datetime.strptime(Date, '%m/%d/%Y %I:%M %p')
            Dayofweek=datetime.datetime.weekday(dt)+1
            Month=dt2.month
            Carrier=request.form["CARRIER"]
            Flightnumber=int(request.form["FL_NUM"])
            orig=request.form["ORIGIN"]
            orig=str(orig)
            origin1 = (orig.split(" - ")[-1])
            origin2 = (orig.split(" - ")[-2])+", "+(orig.split(" - ")[-0])
            Origin=dict[orig]
            desty=request.form["DEST"]
            desty=str(desty)
            Destination=dict[desty]
            desty2=(desty.split(" - ")[-2])+", "+(desty.split(" - ")[-0])
            desty1=(desty.split(" - ")[-1])
            hour=dt2.hour #returns a number from 1 to 24 #matches database format
            flnum=str(Carrier)+" "+str(Flightnumber)


            client=MongoClient() #needtospecifyspecificconnectionlater!!!
            db=client.final.data4
            #p=list(db.find({'identifier': str(Carrier)+" "+str(Flightnumber)+" "+str(Origin)+" "+str(Destination)},{'route_day_dep_pct':1,'route_day_arr_pct':1}).limit(1))
            gd4 = getotpct(Month, Dayofweek, hour, Origin, Destination, Carrier, Flightnumber, client)

            requestgood = gd4[0]

            statsbad = gd4[1]
            ontimepercentage = gd4[2]
            percentarrival = gd4[3]
            identifier=gd4[4]



            onecall=list(getdata2(identifier,Origin,Destination,Carrier,Flightnumber,client))

            """(
                maxhrvalue, minhrvalue, bsthr, wsthr, hourcomp, only1hr, maxdyvalue, mindyvalue, bstdy, wstdy, daycomp,
                maxmthvalue,
                minmthvalue, bstmth, wstmth, mthcomp)"""

            maxdyvalue = onecall[6]
            mindyvalue = onecall[7]
            bstdy = onecall[8]
            wstdy = onecall[9]
            daycomp = onecall[10]

            maxhrvalue = onecall[0]
            minhrvalue = onecall[1]
            bsthr = onecall[2]
            wsthr = onecall[3]
            hourcomp = onecall[4]
            only1hr = onecall[5]

            maxmthvalue = onecall[11]
            minmthvalue = onecall[12]
            bstmth = onecall[13]
            wstmth = onecall[14]
            monthcomp = onecall[15]






            """
                    gd1=getdata(identifier,'h',Origin,Destination,Carrier,Flightnumber,client)
            gd2=getdata(identifier, 'd',Origin,Destination,Carrier,Flightnumber,client)
            gd3=getdata(identifier,'m',Origin,Destination,Carrier,Flightnumber,client)



            maxdyvalue=gd2[0]
            mindyvalue=gd2[1]
            bstdy=gd2[2]
            wstdy=gd2[3]
            daycomp=gd2[4]



            maxhrvalue=gd1[0]
            minhrvalue=gd1[1]
            bsthr=gd1[2]
            wsthr=gd1[3]
            hourcomp=gd1[4]
            only1hr=gd1[5]



            maxmthvalue=gd3[0]
            minmthvalue=gd3[1]
            bstmth=gd3[2]
            wstmth=gd3[3]
            monthcomp=gd3[4]


            requestgood=gd4[0]

            statsbad=gd4[1]
            ontimepercentage=gd4[2]
            percentarrival=gd4[3]"""





                #dailyaverage
            #db1=client.FlightStats.dailyavgflightdelays

            #dayaveragedepdelaylist = []#thistoo
            #listoflabels=[] #needtoreturnthisforpiechart


            #dayaveragedepdelay = list(db1.find({'flightidentifier': str(Carrier) + " " + str(Flightnumber) + " " + str(Origin) + " " + str(Destination)},{'dailyavgflightdel':1, 'dayofweek':1}))

            #for x in range(0, len(dayaveragedepdelay)):

               #dayaveragedepdelaylist.append(format(dayaveragedepdelay[x]['dailyavgflightdel'], '.0f'))

                #listoflabels.append(DictofDays[(dayaveragedepdelay[x]['dayofweek'])])








            #monthlyavgflightdelay

            #gethourlydata(not identifier specific)



            # moduleforshowingnearestholiday
            curdate = dt2.date()
            tup = find_nearest(curdate, listofhols)
            closestholiday = tup[0]

            numberofdays = tup[1]
            numberofdaysfrom = tup[1]

            dateofholiday = "{:%B %d, %Y}".format(tup[2])

            daysnear = False
            if numberofdaysfrom < 10:
                daysnear = True










            #prediction

            #arrival_model=gl.load_model('models/RFC_30ITER_100DEPTH_ARR')
            #departure_model=gl.load_model('models/RFC_50ITER_110D_DEPDEL')
            #feature=gl.SFrame({'MONTH':[int(Month)],'DAY_OF_WEEK':[Dayofweek],'UNIQUE_CARRIER':[str(Carrier)],     'ORIGIN':[str(Origin)],'DEST':[str(Destination)],'DaysFrmNearest':[numberofdaysfrom],'hour':[hour]})''''''
            #arrivalprediction=arrival_model.predict(feature,output_type='class')[0]
            #arrivaldelprob=arrival_model.predict(feature,output_type='probability')[0]
            #departureprediction=departure_model.predict(feature,output_type='class')[0]
            #departuredelprob = departure_model.predict(feature, output_type='probability')[0]''''''




            #w=classify(Month,Dayofweek,Carrier,Origin,Destination,numberofdaysfrom,hour,type="arr")
            #arrivalprediction=w[0]
            #arrivaldelprob=w[1]
            #prob1 = float(arrivaldelprob.strip("%"))
            #t = classify(Month, Dayofweek, Carrier, Origin, Destination, numberofdaysfrom, hour, type="dep")
            #departureprediction=t[0]
            #departuredelprob=t[1]
            #prob2 = float(departuredelprob.strip("%"))






            #predictionprobability=probability(Month,Dayofweek,Carrier,Flightnumber,Origin,Destination)
            #prob=float(predictionprobability.strip("%"))

            listdates=generatelistofdates(dt,3)[0]

            firstdate=listdates[0].strftime("%Y-%m-%d")
            dateindex = generatelistofdates(dt,3)[-1]
            lastdate=listdates[-1].strftime("%Y-%m-%d")
            entry = []
            pdates = []
            pdates2 =[]
            alpha=[]
            c=ucc.transform(Carrier)
            o=origin.transform(Origin)
            d=dest.transform(Destination)
            #initialfeatures = [Month, Dayofweek, hour, o, d, c, numberofdaysfrom,str(dt2.date)]
            #alpha.append(initialfeatures)




            entry=listdates
            for dates in listdates:



                test=[]
                test2=[]
                dt3 = datetime.datetime.strptime(str(dates), '%Y-%m-%d %H:%M:%S')
                dt3=dt3.date()



                dow=(datetime.datetime.weekday(dates))+1
                mth=int(dates.month)
                tup=find_nearest(dt3,listofhols)
                ndf=tup[1]

                #dt6=str(dt3).split(" ")[0]
                dt6="{:%B %d, %Y}".format(dt3)

                feat=[mth,dow,hour,o,d,c,ndf,str(dt6)]
                alpha.append(feat)

            df=pd.DataFrame(alpha)
            df.columns=['month','dayofweek','hour','origin','destination','carrier','ndf','dates']
            #print(df, file=sys.stderr)
            features1=onehot.transform((df[['month','dayofweek','hour','origin','destination','carrier','ndf']]))
            df['dpred']=100*(clf.predict_proba(features1).T[1])
            prob2=df['dpred'].iloc[0]
            departureprediction="Not Delayed"
            if prob2>50:
                departureprediction="Delayed"
            departuredelprob="{0:.0f}%".format(prob2)


            df['dpred']=df['dpred'].round(decimals=1)
            df['apred']=100*(clf2.predict_proba(features1)).T[1]
            prob1=df['apred'].iloc[0]
            arrivalprediction="Not Delayed"
            if prob1>50:
                arrivalprediction="Delayed"
            arrivaldelprob="{0:.0f}%".format(prob1)

            df['apred']=df['apred'].round(decimals=1)

            #procdates=(df[['unixtime','dpred']]).values.tolist()
            #procdates2=(df[['unixtime','apred']]).values.tolist()
            df2=df[['dates','dpred','apred']]

            probgraph=(df2).values.tolist()


            #df2=df[['dpred','dates']]
            #df3=df[['apred','dates']]
            #df3.columns=['dpred','dates']

            #df4=pd.concat([df2,df3],axis=0)



            mx=df2['dpred'].values.max()
            mn=df2['dpred'].values.min()

            #mx=(df['dpred'].values.max())
            #mx1 = (df['apred'].values.max())
            #mx = max(mx, mx1)
            #mn=(df['dpred'].values.min())
            #mn1 = (df['apred'].values.min())
            #mn=min(mn,mn1)

            badday=df2[df2['dpred']==mx].dates.values[0]
            bestday = df2[df2['dpred'] == mn].dates.values[0]

            entry=str(entry)




            #moduleforshowinganalysisbyhours







            # listsforplotting

            #moduleforweather
            daysdiff=dt2-datetime.datetime.today()
            predictionavailable=False
            if daysdiff.days<6:
                predictionavailable=True


            olat = float(latdict[Origin])
            olng = float(lngdict[Origin])

            dlat = float(latdict[Destination])
            dlng = float(lngdict[Destination])

            weatherdays=[]
            searchdateconditions=[]

            if predictionavailable:

                dt10=listdates[0]
                forecast=forecastgps(olat, olng, start_date=datetime.datetime.today(), num_days=6, metric=False)
                for dys in forecast:
                    days=[]
                    date=dys.date
                    date="{:%B %d}".format(date)
                    mintemp=dys.min_temp.value
                    maxtemp=dys.max_temp.value
                    condition=dys.conditions
                    days=[date,mintemp,maxtemp,condition]
                    weatherdays.append(days)
                    if dys.date==dt2.date():
                        searchdateconditions=[date,mintemp,maxtemp,condition]





























            searchdate="{:%B %d, %Y}".format(dt2)

    #prob=prob,prediction=prediction,predictionprobability=predictionprobability
            client.close()
            return render_template('results.html',flnum=flnum,desty1=desty1,desty2=desty2,origin2=origin2,origin1=origin1,searchdateconditions=searchdateconditions,                        weatherdays=weatherdays,predictionavailable=predictionavailable,requestgood=requestgood,only1hr=only1hr,daysnear=daysnear,badday=badday,bestday=bestday,                            searchdate=searchdate,probgraph=probgraph,identifier=identifier,prob1=prob1,prob2=prob2,bstdy=bstdy,wstdy=wstdy,daycomp=daycomp,bsthr=bsthr,wsthr=wsthr,                            hourcomp=hourcomp,dateindex=dateindex,mn=mn,mx=mx,entry=entry,firstdate=firstdate,lastdate=lastdate, arrivaldelprob=arrivaldelprob,                                             departuredelprob=departuredelprob,arrivalprediction=arrivalprediction,departureprediction=departureprediction,closestholiday=closestholiday,                                numberofdaysfrom=numberofdaysfrom,dateofholiday=dateofholiday,bstmth=bstmth,wstmth=wstmth,monthcomp=monthcomp,statsbad=statsbad,                                        percentarrival=percentarrival,ontimepercentage=ontimepercentage,Month=Month,Dayofweek=Dayofweek,Carrier=Carrier,Flightnumber=Flightnumber,Origin=Origin,                            Destination=Destination,)

        except:
            return redirect('/error')

@app.route('/result')
def test():
    return render_template('predictedresults.html')






if __name__=='__main__':
    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
    app.run(debug=True, threaded=True)



