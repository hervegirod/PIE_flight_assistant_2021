import owlready2 as owl
import pyowm
import os
import numpy as np
import pandas as pd
from csv import reader
from .geo_utils import *
from geopy.geocoders import Nominatim
import operator
import requests
from datetime import datetime


filename_onto_individuals = "./ontology/final-archi-individuals.owl"

OWM_APIKEY = os.environ.get('OWM_APIKEY')
owm = pyowm.OWM(OWM_APIKEY)
mgr = owm.weather_manager()

location_manager = Nominatim(user_agent="GetLoc")

def fprint(*args, **kwargs):
    print(args, flush=True, **kwargs)


def init_ontology_individuals():
    """ Initializes the ontology instance from the file
    """
    fprint("Loading ontology...", end=" ")
    onto_individuals = owl.get_ontology(filename_onto_individuals).load()
    fprint("Ontology loaded !")
    return onto_individuals


df_all_airports = None
df_all_runways = None
df_all_frequencies = None
df_all_navaids = None
df_all_waypoints = None
df_all_checklists = None



def init_dataframes_individuals():
    """ Initializes dataframe objects containing Airport, Runway, Frequency, Navaid, Waypoint
    from ontology
    """
    global df_all_airports, df_all_runways, df_all_frequencies, df_all_navaids, df_all_waypoints, df_all_checklists
    fprint("Loading individuals", end=" ")
    df_all_airports = init_df_all_airports()
    df_all_runways = init_df_all_runways()
    df_all_frequencies = init_df_all_frequencies()
    df_all_navaids = init_df_all_navaids()
    df_all_waypoints = init_df_all_waypoints()
    df_all_checklists = init_df_all_checklists()
    fprint("Individuals loaded !")
    return



def init_df_all_airports():
    """ Initializes the airport dataframe from the Airport ontology's object
    """
    all_airports = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?name ?iata ?icao ?latitude ?longitude ?altitude ?country
            WHERE {{
                ?Airport pie:AirportName ?name .
                ?Airport pie:AirportIATA ?iata .
                ?Airport pie:AirportICAOCode ?icao .
                ?Airport pie:AirportGPSLatitude ?latitude .
                ?Airport pie:AirportGPSLongitude ?longitude .
                ?Airport pie:AirportAltitude ?altitude .
                ?Airport pie:AirportCountry ?country .
            }}
        """))
    fields = ['name', 'iata', 'icao', 'latitude', 'longitude', 'altitude', 'country']
    dict_all_airports = [dict(zip(fields, airport_tuple)) for airport_tuple in all_airports]
    return pd.DataFrame(dict_all_airports)


def init_df_all_runways():
    """ Initializes the runway dataframe from the Runway ontology's object
    """
    all_runways = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?icao ?couple ?ident ?altitude ?beg_latitude ?beg_longitude ?end_latitude ?end_longitude
                ?length ?lights ?orientation ?surface ?threshold ?width
            WHERE {{
                ?Airport pie:AirportICAOCode ?icao .
                ?Airport pie:HasRunway ?Runway .
                ?Runway pie:RunwayAltitude ?altitude .
                ?Runway pie:RunwayCouple ?couple .
                ?Runway pie:RunwayBeginGPSLatitude ?beg_latitude .
                ?Runway pie:RunwayBeginGPSLongitude ?beg_longitude .
                ?Runway pie:RunwayEndGPSLatitude ?end_latitude .
                ?Runway pie:RunwayEndGPSLongitude ?end_longitude .
                ?Runway pie:RunwayIdentifier ?ident .
                ?Runway pie:RunwayLength ?length .
                ?Runway pie:RunwayLights ?lights .
                ?Runway pie:RunwayIdentifier ?ident .
                ?Runway pie:RunwayOrientation ?orientation .
                ?Runway pie:RunwaySurface ?surface .
                ?Runway pie:RunwayThresholdLength ?threshold .
                ?Runway pie:RunwayWidth ?width .
            }}
        """))
    fields = ['airport', 'couple', 'ident', 'altitude', 'beg_latitude', 'beg_longitude', 'end_latitude', 'end_longitude', 
            'length', 'lights', 'orientation', 'surface', 'threshold', 'width']
    dict_all_runways = [dict(zip(fields, runway_tuple)) for runway_tuple in all_runways]
    return pd.DataFrame(dict_all_runways)


def init_df_all_frequencies():
    """ Initializes the frequency dataframe from the Frequency ontology's object
    """
    all_frequencies = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?frq_type ?desc ?frq_mhz ?icao
            WHERE {{
                ?Airport pie:AirportICAOCode ?icao .
                ?Airport pie:HasFrequency ?Frequency .
                ?Frequency pie:FrequencyDescription ?desc .
                ?Frequency pie:FrequencyMHz ?frq_mhz .
                ?Frequency pie:FrequencyType ?frq_type .
            }}
        """))
    fields = ['frq_type', 'desc', 'frq_mhz', 'icao']
    dict_all_frequencies = [dict(zip(fields, frq_tuple)) for frq_tuple in all_frequencies]
    return pd.DataFrame(dict_all_frequencies)


def init_df_all_navaids():
    """ Initializes the navaid dataframe from the Navaid ontology's object
    """
    all_navaids = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?ident ?name ?nav_type ?frequency ?latitude ?longitude ?altitude
            WHERE {{
                ?Navaid pie:NavaidIdentifier ?ident .
                ?Navaid pie:NavaidName ?name .
                ?Navaid pie:NavaidType ?nav_type .
                ?Navaid pie:NavaidFrequencyKHz ?frequency .
                ?Navaid pie:NavaidGPSLatitude ?latitude .
                ?Navaid pie:NavaidGPSLongitude ?longitude .
                ?Navaid pie:NavaidAltitude ?altitude .
            }}
        """))
    fields = ['ident', 'name', 'nav_type', 'frequency', 'latitude', 'longitude', 'altitude']
    dict_all_navaids = [dict(zip(fields, navaid_tuple)) for navaid_tuple in all_navaids]
    return pd.DataFrame(dict_all_navaids)


def init_df_all_waypoints():
    """ Initializes the waypoint dataframe from the Waypoint ontology's object
    """
    all_waypoints = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?ident ?country ?latitude ?longitude
            WHERE {{
                ?Waypoint pie:WaypointIdentifier ?ident .
                ?Waypoint pie:WaypointCountryCode ?country .
                ?Waypoint pie:WaypointGPSLatitude ?latitude .
                ?Waypoint pie:WaypointGPSLongitude ?longitude .
            }}
        """))
    fields = ['ident', 'country', 'latitude', 'longitude']
    dict_all_waypoints = [dict(zip(fields, waypoint_tuple)) for waypoint_tuple in all_waypoints]
    return pd.DataFrame(dict_all_waypoints)


def init_df_all_checklists():
    """ Initializes the checklist dataframe from the Checklist ontology's object
    """
    all_checklists = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?type ?model ?content
            WHERE {{
                ?Waypoint pie:ChecklistContent ?content .
                ?Waypoint pie:ChecklistModel ?model .
                ?Waypoint pie:ChecklistType ?type .
            }}
        """))
    fields = ['type', 'model', 'content']
    dict_all_checklists = [dict(zip(fields, checklist_tuple)) for checklist_tuple in all_checklists]
    return pd.DataFrame(dict_all_checklists)




# ======================================================================================
# ================ MAP QUERIES =========================================================
# ======================================================================================
# Queries to update the map on the GUI


def get_near_airports(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with airport data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client containing all the data
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_airports'] = query_map_near_airports(s, n, w, e)
    except Exception as e:
        print_error("Error querying airports", e)
        surrounding_data['list_airports'] = []


def get_near_runways(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with runway data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client containing all the data
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_runways'] = query_map_near_runways(s, n, w, e)
    except Exception as e:
        print_error("Error querying runways", e)
        surrounding_data['list_runways'] = []


def get_near_frequencies(surrounding_data):
    """ Updates the dictionary message sent to the client with frequency data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client containing all the data
    """    
    event_bug = ""
    for airport in surrounding_data['list_airports']:
        current_icao = airport['icao']
        try:
            airport['list_frequencies'] = query_map_near_frequencies(current_icao)
        except Exception as e:
            airport['list_frequencies'] = []
            event_bug = e
    
    if event_bug != "":
        print_error("Error querying frequencies", event_bug)


def get_near_navaids(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with navaid data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client containing all the data
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_navaids'] = query_map_near_navaids(s, n, w, e) 
    except Exception as e:
        print_error("Error querying navaids", e)
        surrounding_data['list_navaids'] = []


def get_near_waypoints(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with waypoint data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client containing all the data
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_waypoints'] = query_map_near_waypoints(s, n, w, e)
    except Exception as e:
        print_error("Error querying navaids", e)
        surrounding_data['list_waypoints'] = []




def query_map_near_airports(s, n, w, e):
    # Returns the airports within a box
    df_near_airports = df_all_airports.loc[
        df_all_airports['longitude'].between(w, e) & \
        df_all_airports['latitude'].between(s, n)
    ]
    return df_near_airports.to_dict('records')


def query_map_near_runways(s, n, w, e):
    # Returns the runways within a box
    df_near_runways = df_all_runways.loc[
        df_all_runways['beg_longitude'].between(w, e) & \
        df_all_runways['beg_latitude'].between(s, n)
    ]
    return df_near_runways.to_dict('records')


def query_map_near_frequencies(current_icao):
    # Returns the frequencies within a box
    df_associated_frequencies = df_all_frequencies.loc[
        df_all_frequencies['icao'] == current_icao
    ]
    return df_associated_frequencies.to_dict('records')


def query_map_near_navaids(s, n, w, e):
    # Returns the navaids within a box
    df_near_navaids = df_all_navaids.loc[
        df_all_navaids['longitude'].between(w, e) & \
        df_all_navaids['latitude'].between(s, n)
    ]
    return df_near_navaids.to_dict('records')


def query_map_near_waypoints(s, n, w, e):
    # Returns the waypoints within a box
    df_near_waypoints = df_all_waypoints.loc[
        df_all_waypoints['longitude'].between(w, e) & \
        df_all_waypoints['latitude'].between(s, n)
    ]
    return df_near_waypoints.to_dict('records')




# ======================================================================================
# ================ USER QUERIES ========================================================
# ======================================================================================

def process_query(query_type, arg1, arg2, flight_data):
    """
    flight_data : {
        'id', 'registration', 'callsign', 'model', 'model_text', 'origin', 'origin_icao', 'destination', 
        'latitude', 'longitude', 'heading', 'speed', 'vertical_speed', 'altitude', 'last_contact'
    }
    """
    
    response_str = "N/A"
    args = None

    # -------------------------------- TRAFIC STATIC ----------------------------------------
    if query_type == "departureAirport":
        response_str = f"The departure airport is {flight_data.get('origin')}."
    

    elif query_type == "arrivalAirport":
        response_str = f"The arrival airport is {flight_data.get('destination')}."

    # TO REMOVE
    # elif query_type == "runwaysAtArrival":
    #     response_dict = query_runways_at_airport(flight_data.get('destination_icao'))
    #     if response_dict.get('status'):
    #         list_runways_arrival = response_dict.get('list_runways')
    #         list_ident_runways = [runway_data[0] for runway_data in list_runways_arrival[:-1]]
    #         response_str = f"""Runways at {response_dict.get('name')} ({response_dict.get('icao')}) \
    #             are {", ".join(list_ident_runways)} and {list_runways_arrival[-1][0]}."""
    #     else:
    #         response_str = f"Arrival airport is not available."


    elif query_type == "runwaysAtAirport":
        if arg1 == "arrival":
            response_dict = query_runways_at_airport(flight_data.get('destination_icao'))
        elif arg1 == "departure":
            response_dict = query_runways_at_airport(flight_data.get('origin_icao'))
        else:
            response_dict = query_runways_at_airport(arg1)

        if response_dict.get('status'):
            list_runways_arrival = response_dict.get('list_runways')
            list_ident_runways = [runway_data[0] for runway_data in list_runways_arrival[:-1]]
            response_str = f"""Runways at {response_dict.get('name')} ({response_dict.get('icao')}) \
                are {", ".join(list_ident_runways)} and {list_runways_arrival[-1][0]}."""
        else:
            response_str = f"Runways for this airport are not available."


    # Je sais pas pourquoi ca fonctionne...
    elif query_type == "frequencyAtArrival":
        response_dict = query_frequency_at_airport(arg1.upper(), flight_data.get('destination_icao'))
        if response_dict.get('status'):
            response_str = f"The {response_dict.get('frq_name')} frequency at {response_dict.get('airport_name')} is {response_dict.get('frq_value')}."
        elif flight_data.get('destination_icao') == "N/A":
            response_str = f"Arrival airport is not available."
        else:
            response_str = f"This frequency is not available."


    elif query_type == "frequencyAtAirport":
        if arg1 == "arrival":
            response_dict = query_frequency_at_airport(arg1.upper(), flight_data.get('destination_icao'))
        elif arg1 == "departure":
            response_dict = query_frequency_at_airport(arg1.upper(), flight_data.get('origin_icao'))
        else:
            response_dict = query_frequency_at_airport(arg1.upper(), arg2)
        
        if response_dict.get('status'):
            response_str = f"The {response_dict.get('frq_name')} frequency at {response_dict.get('airport_name')} is {response_dict.get('frq_value')}."
        else:
            response_str = f"This frequency is not available."
    

    # -------------------------------- TRAFIC DYNAMIC ----------------------------------------
    elif query_type == "nearestAirport":
        response_dict = query_nearest_airport(flight_data.get('latitude'), flight_data.get('longitude'))
        response_str = f"The nearest airport is {response_dict.get('name')} ({response_dict.get('ICAO')}) at {response_dict.get('distance'):.2f} nm, \
            at heading {response_dict.get('heading'):.0f}°."


    elif query_type == "currentParam":
        response_dict = query_current_param(flight_data, arg1)
        if response_dict.get('status'):
            response_str = f"Your current {response_dict.get('param_name')} is {response_dict.get('param_format')}."
        else:
            response_str = f"This flight parameter is not available."


    elif query_type == "runwaysAtNearestAirport":
        nearest_airport_dict = query_nearest_airport(flight_data.get('latitude'), flight_data.get('longitude'))
        icao_nearest_airport = nearest_airport_dict.get('ICAO')
        response_dict = query_runways_at_airport(icao_nearest_airport)
        if response_dict.get('status'):
            list_runways_arrival = response_dict.get('list_runways')
            list_ident_runways = [runway_data[0] for runway_data in list_runways_arrival[:-1]]
            response_str = f"""Runways at {response_dict.get('name')} at {nearest_airport_dict.get('distance'):.2f} nm \
                are {", ".join(list_ident_runways)} and {list_runways_arrival[-1][0]}."""
        else:
            response_str = f"Runways for {response_dict.get('name')} are not available."

    
    elif query_type == "nearestTrafic":
        response_dict = query_nearest_flight(arg1, flight_data.get('latitude'), flight_data.get('longitude'), flight_data.get('callsign'))
        if response_dict.get('status'):
            response_str = f"The nearest trafic is {response_dict.get('nearest_callsign')} at {response_dict.get('distance_nearest'):.2f} nm, \
                at heading {response_dict.get('heading_nearest'):.0f}°."
        else:
            response_str = f"There is no trafic around you."


    elif query_type == "lengthNearestRunway":
        nearest_airport_dict = query_nearest_airport(flight_data.get('latitude'), flight_data.get('longitude'))
        icao_nearest_airport = nearest_airport_dict.get('ICAO')
        runway_data = query_runways_at_airport(icao_nearest_airport)
        response_dict = query_longest_runway(runway_data)
        if response_dict.get('status'):
            response_str = f"""The longest runways at {response_dict.get('airport_name')} are {", ".join(response_dict.get('runways_idents')[:-1])} and {response_dict.get('runways_idents')[-1]} of length {response_dict.get('max_length')} ft."""
        else:
            response_str = f"Runways for {response_dict.get('airport_name')} are not available."

    
    elif query_type == "eta":
        eta = arg1.get('arrival')
        if isinstance(eta, int):
            eta_str = datetime.utcfromtimestamp(eta).strftime('%H:%M')
        else:
            eta_str = 'N/A'
        response_str = f"Your estimated time of arrival is {eta_str}."


    # -------------------------------- WEATHER ----------------------------------------

    elif query_type == "weatherAtAirport":
        if arg2 == "arrival":
            response_dict = query_specific_weather_at_airport(arg1, flight_data.get('destination_icao'))
        elif arg2 == "departure":
            response_dict = query_specific_weather_at_airport(arg1, flight_data.get('origin_icao'))
        else:
            response_dict = query_specific_weather_at_airport(arg1, arg2)
        

        if response_dict.get('status'):
            response_str = f"The {response_dict.get('weather_name')} at {response_dict.get('airport_name')} is {response_dict.get('weather_value_format')}."
        else:
            # If it did not manage to find the airport
            return process_query("weatherAtLocation", arg1, arg2, flight_data)


    elif query_type == "metarAtAirport":
        if arg1 == "arrival":
            response_dict = query_metar_at_airport(flight_data.get('destination_icao'))
        elif arg1 == "departure":
            response_dict = query_metar_at_airport(flight_data.get('origin_icao'))
        else:
            response_dict = query_metar_at_airport(arg1)
        
        if response_dict.get('status'):
            response_str = 'METAR'
            args = response_dict.get('metar')
        else:
            response_str = response_dict.get('error')


    elif query_type == "weatherAtLocation":
        response_dict = query_specific_weather_at_location(arg1, arg2)
        if response_dict.get('status'):
            response_str = f"The {response_dict.get('weather_name')} at {response_dict.get('location')} is {response_dict.get('weather_value_format')}."
        else:
            response_str = f"This location is not available."


    elif query_type == "weatherAtWaypoint":
        response_dict = query_specific_weather_at_waypoint(arg1, arg2)
        if response_dict.get('status'):
            response_str = f"The {response_dict.get('weather_name')} at {response_dict.get('waypoint_name')} is {response_dict.get('weather_value_format')}."
        else:
            response_str = f"This waypoint is not available."

    # TO REMOVE

    # elif query_type == "weatherAtArrival":
    #     response_dict = query_specific_weather_at_airport(arg1, flight_data.get('destination_icao'))
    #     if response_dict.get('status'):
    #         response_str = f"The {response_dict.get('weather_name')} at {response_dict.get('airport_name')} is {response_dict.get('weather_value_format')}."
    #     else:
    #         response_str = f"Arrival airport is not available."


    # -------------------------------- CHECKLIST ----------------------------------------
    elif query_type == "checklist":
        response_dict = get_checklist(arg1, flight_data.get('model'))
        response_str = "CHECKLIST"
        args = {
            'name' : f'{arg1} checklist',
            'checklist' : response_dict.get('checklist')
        }


    # -----------------------------------------------------------------------------------
    
    elif query_type == "clear":
        response_str = "&nbsp;"

    return {'response_str' : response_str, 'args': args}



# ======================================================================================

# ============================== TRAFIC STATIC ========================================

def query_runways_at_airport(icao):
    response = list(owl.default_world.sparql(
        f"""
            PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
            SELECT ?name ?rw_id ?length
            WHERE {{
                ?Airport pie:AirportICAOCode ?airport_icao .
                ?Airport pie:AirportName ?name .
                ?Airport pie:HasRunway ?Runway .
                ?Runway pie:RunwayIdentifier ?rw_id .
                ?Runway pie:RunwayLength ?length .
                FILTER regex(?airport_icao, "{icao}", "i")
            }}
        """))

    if len(response) == 0:
        return {"status": False}

    list_runways = [(i[1], i[2]) for i in response]
    name = response[0][0]
    return {
        "status": True, 
        "icao": icao, 
        "name": name, 
        "list_runways": list_runways
    }


def query_frequency_at_airport(frq_sigle, icao):
    response = list(owl.default_world.sparql(
    f"""
        PREFIX pie:<http://www.semanticweb.org/clement/ontologies/2020/1/final-archi#>
        SELECT ?name ?mhz 
        WHERE {{
            ?Airport pie:AirportICAOCode ?ICAO .
            ?Airport pie:AirportName ?name .
            ?Airport pie:HasFrequency ?Frequency .
            ?Frequency pie:FrequencyDescription ?desc .
            ?Frequency pie:FrequencyMHz ?mhz .
            ?Frequency pie:FrequencyType ?type .
            FILTER regex(?ICAO, "{icao}", "i")
            FILTER regex(?type, "{frq_sigle}", "i")
            
        }}
    """))
    if len(response) == 0:
        return {"status": False}
    
    name_airport, value_mhz = response[0][0], response[0][1]
    return {
        "status": True,
        "frq_name": frq_sigle,
        "airport_name": name_airport,
        "frq_value": value_mhz
    }

# ============================== TRAFIC DYNAMIC ========================================
units = {
    'heading' : "°", 
    'speed' : " kt", 
    'vertical_speed' : " ft/min", 
    'altitude' : " ft"
}


def query_nearest_airport(lat, lng):
    """ Example : what is the nearest airport """

    df = pd.DataFrame({
        'name': df_all_airports['name'],
        'ICAO': df_all_airports['icao'],
        'lat': df_all_airports['latitude'],
        'lng': df_all_airports['longitude'],
    })

    df['distance'] = df.apply(lambda x: coord_to_dist(x["lat"], x["lng"], lat, lng), axis=1)

    response_dict = df.iloc[df['distance'].idxmin()].to_dict() # Contains ?name ?iata ?icao ?latitude ?longitude ?altitude ?country
    response_dict['heading'] = heading_to_point(lat, lng, response_dict['lat'], response_dict['lng'])
    return response_dict


def query_current_param(flight_data, param):
    """ Example : what is my current speed """

    param_value = flight_data.get(param)
    if param_value is None:
        return {"status": False}
    
    return {
        'status' : True,
        'param_name' : param.replace("_", " "),
        'param_format' : f"{param_value}{units.get(param,'')}"
    }


def compute_dist(dict_flight, latitude, longitude):
    """ Returns the distance between to flights """

    return dict_flight['icao24'], {
        "distance": coord_to_dist(latitude, longitude, dict_flight['latitude'], dict_flight['longitude']),
        "latitude": dict_flight['latitude'],
        "longitude": dict_flight['longitude'],
        "callsign" : dict_flight['icao24']
    }

def query_nearest_flight(list_flights, latitude, longitude, callsign):
    """ Example : what is the nearest traffic """

    if len(list_flights) == 1:
        return {"status": False}

    # Compute distance for each flight
    flight_to_dist = dict(map(lambda x: compute_dist(x, latitude, longitude), list_flights))
    flight_to_dist.pop(callsign, None)


    # Get the key of the minimum distance
    nearest_data = min(flight_to_dist.values(), key=operator.itemgetter('distance'))
    nearest_callsign = nearest_data['callsign']
    distance_nearest = nearest_data['distance']
    heading_nearest = heading_to_point(latitude, longitude, nearest_data['latitude'], nearest_data['longitude'])
    
    return {
        "status" : True,
        "nearest_callsign" : nearest_callsign,
        "distance_nearest" : distance_nearest,
        "heading_nearest" : heading_nearest
    }


def query_longest_runway(runways_data):
    """ Example : what is the length of the nearest runway """

    list_runways = runways_data.get('list_runways')

    # Get the maximum length
    max_length = max(list_runways, key=lambda x: x[1])[1]

    # Get all the runways with that length and retrieve only the idents
    runways_max = [r for r in list_runways if r[1] == max_length]
    runways_idents = list(list(zip(*runways_max))[0])
    return {
        'status': True,
        'airport_name' : runways_data['name'],
        'max_length': int(max_length),
        'runways_idents' : runways_idents
    }

# ============================== WEATHER ========================================

def get_weather_at_place(weather_sigle, current_weather):
    """ Process an OWM weather object and returns the useful weather parameter """

    weather_value_format = ""

    if weather_sigle == 'weather':
        weather_value_format = current_weather.detailed_status

    if weather_sigle == 'wind':
        wind_object = current_weather.wind()
        wind_speed = wind_object.get('speed')
        wind_orientation = wind_object.get('deg')
        weather_value_format = f"{wind_orientation}° {wind_speed} kt"

        if wind_object.get('gust'):
            weather_value_format += f" with gusts at {wind_object.get('gust')} kt"

    elif weather_sigle == 'gust':
        gust = current_weather.wind().get('gust', 0)
        weather_value_format = f"{gust} kt"

    elif weather_sigle == 'temperature':
        temperature = current_weather.temperature('celsius')['temp']
        weather_value_format = f"{temperature} celsius"

    elif weather_sigle == "pressure":
        pressure = current_weather.pressure.get('press')
        weather_value_format = f"{pressure} HPa"

    elif weather_sigle == "visibility":
        visibility = current_weather.visibility_distance
        weather_value_format = f"{visibility} m"

    elif weather_sigle == "clouds":
        clouds = current_weather.clouds
        weather_value_format = f"{clouds} % coverage"

    elif weather_sigle == "rain":
        amount = 0 if len(current_weather.rain) == 0 else current_weather.rain.get('1h')
        weather_value_format = f"{amount} mm"

    return weather_value_format


def query_specific_weather_at_airport(weather_sigle, icao):
    """ Example : what is the weather at Toulouse Blagnac """

    row = df_all_airports.loc[df_all_airports['icao'] == icao]
    if len(row) == 0:
        return {"status": False}
    
    airport_name = row['name'].values[0]
    coord = (float(row['latitude']), float(row['longitude']))
    current_weather = mgr.weather_at_coords(*coord).weather

    weather_value_format = get_weather_at_place(weather_sigle, current_weather)

    if len(weather_value_format) == 0:
        return {"status": False}
    else:
        return {
            "status": True,
            "weather_name" : weather_sigle,
            "airport_name" : airport_name,
            "weather_value_format" : weather_value_format
        }


def query_specific_weather_at_location(weather_sigle, location):
    """ Example : what is the weather at Toulouse """

    try: # if it PYOWM finds the location by itself
        current_weather = mgr.weather_at_place(location).weather
    except pyowm.commons.exceptions.NotFoundError: # Else, ask openstreetmap
        getLoc = location_manager.geocode(location)
        coord = (getLoc.latitude, getLoc.longitude)
        current_weather = mgr.weather_at_coords(*coord).weather
    except Exception:
        return {"status": False}
    
    weather_value_format = get_weather_at_place(weather_sigle, current_weather)

    return {
        "status": True,
        "weather_name" : weather_sigle,
        "location" : location,
        "weather_value_format" : weather_value_format
    }


def query_specific_weather_at_waypoint(weather_sigle, waypoint_ident):
    """ Example : what is the weather at MAKOX """

    row = df_all_waypoints.loc[df_all_waypoints['ident'] == waypoint_ident.upper()]
    if len(row) == 0:
        return {"status": False}
    
    waypoint_name = row['ident'].values[0]
    coord = (float(row['latitude']), float(row['longitude']))
    current_weather = mgr.weather_at_coords(*coord).weather

    weather_value_format = get_weather_at_place(weather_sigle, current_weather)

    return {
        "status": True,
        "weather_name" : weather_sigle,
        "waypoint_name" : waypoint_name,
        "weather_value_format" : weather_value_format
    }


def query_metar_at_airport(icao):
    """ Example : what is the metar at Toulouse Blagnac """

    r = requests.get(f'https://api.aviationapi.com/v1/weather/metar?apt={icao}')
    response = r.json()

    if response.get('status') == 'error':
        return {
            'status': False,
            'error' : response.get('message')
        }

    else:
        response = response.get(icao)
        response_format = ""

        time_metar = datetime.strptime(response.get('time_of_obs'), '%Y-%m-%dT%H:%M:%SZ')
        time_metar = time_metar.strftime("%H:%M")

        response_format += f"METAR at {icao} at {time_metar}; "
        if response.get('temp') != "": response_format += f"Temperature {int(float(response.get('temp')))}; "
        if response.get('dewpoint') != "": response_format += f"Dewpoint {int(float(response.get('dewpoint')))}; "
        if response.get('wind') != "": response_format += f"Wind {response.get('wind')}° {response.get('wind_vel')} kt; "
        if response.get('visibility') != "": 
            visibility = float(response.get('visibility')) * 1.625
            response_format += f"Visibility {round(visibility)} km; "
        if response.get('sky_conditions') != "":
            for condition in response.get('sky_conditions'):
                response_format += f"Clouds {condition['coverage']} at {condition['base_agl']} ft; "

        return {
            'status': True,
            'metar': response_format
        }



# ============================== CHECKLIST ========================================

# (Item, Response, ID) -- ID used for DOM, for example if there are many "ON" responses
def get_checklist(type_checklist, model):
    """ Example : landing checklist """
    
    model = 'a320' #### TO DELETE in the future

    row = df_all_checklists.loc[(df_all_checklists['type'] == type_checklist) & (df_all_checklists['model'] == model)]
    checklist_file = row['content'].iloc[0]

    with open(checklist_file, 'r') as read_obj:
        csv_reader = reader(read_obj)
        list_of_rows = list(csv_reader)

    checklist = [(item, response, i+1) for i, (item, response) in enumerate(list_of_rows)]
    return {"status": True, "checklist": checklist}


# ======================================================================================

