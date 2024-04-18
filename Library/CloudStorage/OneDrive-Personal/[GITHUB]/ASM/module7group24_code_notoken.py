
import time
import requests
import json
import spacy
from spacy import Language
from typing import List

# load language model
nlp = spacy.load("en_core_web_md")
WEATHER_API_KEY = ""
CURR_API_KEY = ""
TRIP_TOKEN = ""
class Weather:
    
    def __init__(self):
        self.city_name = None
        self.weather = None
    
    def get_weather(self, city_name):
        api_url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city_name}&days=1&aqi=no&alerts=no"
        response = requests.get(api_url)
        result = response.json()
        response_text = result['current']['condition']['text'] +" : "+str(result['current']['temp_c']) + " degree Celcius.\n"
        if response.status_code == 200:
            return response_text      
        return None
    
    def fill_sentence(self, sentence):
        for ent in sentence.ents:
            if ent.label_ == "GPE":
                self.city_name = ent.text      
    
    def check_sentence(self):
        if self.city_name == None:
            city = input("It seems like you haven't input the city name or it is incorrect. Please give me a correct city name.\n>")
            sentence = nlp(city)
            self.fill_sentence(sentence)
            self.weather = self.get_weather(self.city_name)
            print(str(self.weather))
        else:
            self.weather = self.get_weather(self.city_name)
            print(str(self.weather))
        
class Currency:
    
    def __init__(self):
        self.basecurr = None
        self.destcurr = None
        self.conversion = None
    
    def get_currency(self, base_currency, currencies):
        
        base_currency = base_currency.upper()
        currencies = currencies.upper()
        api_url = "https://api.freecurrencyapi.com/v1/latest"
        headers =  {"Content-Type":"application/json"}
        params = {
            'apikey': CURR_API_KEY,
            'base_currency': base_currency,
            'currencies': currencies,
        }
        response = requests.get(api_url, headers=headers, params=params)
        data = response.json()
        response_text = f"1 {base_currency} = {data['data'][currencies]} {currencies}.\n"
    
        if response.status_code == 200:
            return response_text            
        return None
    
    def fill_sentence(self, sentence):
        splitsentence = str(sentence)
        words = splitsentence.split()
        for i in range(1,len(words)):
            if words[i-1] == 'from':
                self.basecurr = words[i]
            if words[i-1] ==  'to':
                self.destcurr = words[i]

    def check_sentence(self):
        if self.basecurr == None or self.destcurr == None:
            baseanddestcurr = input("It seems like you haven't input the currency or it is incorrect. \
                                    Please give me those information in this format 'from USD to SEK'.\n>")
            sentence = nlp(baseanddestcurr)
            self.fill_sentence(sentence)
            self.conversion = self.get_currency(self.basecurr, self.destcurr)
            print(str(self.conversion))
        else:
            self.conversion = self.get_currency(self.basecurr, self.destcurr)
            print(str(self.conversion))

class Trip:
    
    def __init__(self):
        self.originstation = None
        self.destinationstation = None
        self.transportmode = None
        self.route = None
        
    def get_gid(self, stationname):
        gid = None
        with open('stationdict.json') as json_file:
            data = json.load(json_file)
        key_list = list(data.keys())
        val_list = list(data.values())
        if stationname.capitalize() in data.values() :
            position = val_list.index(stationname.capitalize())
            gid = key_list[position]
        return gid
                
    
    def get_trip(self, originGid, destinationGid, transportModes):
        api_url = "https://ext-api.vasttrafik.se/pr/v4/journeys"
        headers =  {"Content-Type":"application/json", "Authorization": f"Bearer {TRIP_TOKEN}"}
        params = {
            'originGid': originGid,
            'destinationGid': destinationGid,
            'dateTime': '',  # current time
            'dateTimeRelatesTo': 'departure',
            'limit': 1,
            'transportModes': transportModes,
            'onlyDirectConnections': True,
            'includeNearbyStopAreas': False,
            'includeOccupancy': False
        }
        
        response = requests.get(api_url, headers=headers, params=params)
        data = response.json()
        #print(data)
        if "results" in data:
            if transportModes == 'bike':
                originname = data['results'][0]['destinationLink']['origin']['name']
                destinationname = data['results'][0]['destinationLink']['destination']['name']
                distance = data['results'][0]['destinationLink']['distanceInMeters']
                duration = data['results'][0]['destinationLink']['plannedDurationInMinutes']
                response_text = f"Bike trip from {originname} to {destinationname} took {duration} mins for {distance} meters."
            else:
                originname = data['results'][0]['tripLegs'][0]['origin']['stopPoint']['name']
                originplatform = data['results'][0]['tripLegs'][0]['origin']['stopPoint']['platform']
                destinationname = data['results'][0]['tripLegs'][0]['destination']['stopPoint']['name']
                destinationplatform = data['results'][0]['tripLegs'][0]['destination']['stopPoint']['platform']
                line =  data['results'][0]['tripLegs'][0]['serviceJourney']['line']['name']
                duration = data['results'][0]['tripLegs'][0]['plannedDurationInMinutes']
                response_text = f"{transportModes} trip from {originname} platform {originplatform} to {destinationname} \
                                platform {destinationplatform} via line {line} will take {duration} mins."
            
        else:
            response_text = originGid#data#"location not found"
        
        if response.status_code == 200:
            return response_text            
        else:
            return response_text #None
    
    def fill_sentence(self, sentence):
        splitsentence = str(sentence)
        words = splitsentence.split()
        for i in range(1,len(words)):
            if words[i-1] == 'from':
                self.originstation = self.get_gid(words[i])
            if words[i-1] ==  'to':
                self.destinationstation = self.get_gid(words[i])
            if words[i-1] ==  'by':
                self.transportmode = words[i]

    def check_sentence(self):             
        if self.originstation == None or self.destinationstation == None or self.transportmode == None:
            originanddesttrip = input("It seems like your input is missing some information or incorrect.\
                                      Example 'from Chalmers to Nordstan by tram/bus/bike'.\n>")
            sentence = nlp(originanddesttrip)
            self.fill_sentence(sentence)
            self.route = self.get_trip(self.originstation, self.destinationstation, self.transportmode)
            print(str(self.route))
        else:
            self.route = self.get_trip(self.originstation, self.destinationstation, self.transportmode)
            print(str(self.route))

def calc_similarities(tasks: List[Language], statement: Language):
    res = []
    # calc all similarities for the nlp tasks
    for key, lang in tasks:
        sim = lang.similarity(statement)
        res.append((key, sim))
    # sort by similarity ascending
    res.sort(key=lambda y: y[1])
    return res

#Method to extract context from intitial question
def extract_context(sentence):
    weather = ("weather", nlp("Current weather in a city"))
    currency = ("currency", nlp("I want to convert a currency"))
    trip = ("trip", nlp("Plan a trip"))
    tasks = [weather, currency, trip]
    context = ''
    while context == '':
        
        sentence = nlp(sentence)
        min_similarity = 0.5
        # calc similarities
        sims = calc_similarities(tasks, sentence)
        intent_name, intent_sim = sims[-1]
        print(f"I feel like you ask about {intent_name} with {intent_sim} similarity\n")
        if intent_sim >= min_similarity:
            if intent_name == 'weather':            
                context = Weather()
            if intent_name == 'currency':            
                context = Currency()
            if intent_name == 'trip':            
                context = Trip()

        if context == '':
            sentence = input("Sorry, I cannot understand. Please try again.\n>")
    return context, sentence

#Main chatbot method
def get_help():
    inputString = input("Hej! I can give you information about \n \
                        1)Current weather (eg. Current weather in Gothenburg) \n\
                        2)Currency converter (eg. Convert a currency from USD to SEK)\n\
                        3)Plan your trip in Gothenburg(eg. Plan a trip)\n>").lower()
    while 'no' not in inputString.split():
        #SinputString = input("What can I help you with?").lower()
        context, inputString = extract_context(inputString)
        context.fill_sentence(inputString)
        context.check_sentence()
        inputString = input("Anything else?\n>").lower()
    print("Goodbye!")

get_help()

