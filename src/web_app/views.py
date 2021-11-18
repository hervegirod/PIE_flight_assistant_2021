"""
Web app views

"""
# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context, request, jsonify
from random import random
from time import sleep
import os
from threading import Thread, Event

from .flight_data_handler import *

import logging
from .query_ontology import *


# =======================================================================
# ===================== FLASK APP INIT ==================================
# =======================================================================
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True


log = logging.getLogger('werkzeug')
log.disabled = True
sio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)
# ====================================

airspace_worker = None
flight_follower_worker = None
thread = Thread()
USE_RADAR = True
SLEEP_TIME = .5

autocomplete_query_handler = AutocompleteQueryHandler()

# =======================================================================
# ===================== BACKGROUND TASKS ================================
# =======================================================================

def get_near_airports(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with airport data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_airports'] = query_map_near_airports(s, n, w, e)
    except Exception as e:
        fprint("Error querying airports", e)
        surrounding_data['list_airports'] = []


def get_near_runways(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with runway data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_runways'] = query_map_near_runways(s, n, w, e)
    except Exception as e:
        fprint("Error querying runways", e)
        surrounding_data['list_runways'] = []


def get_near_frequencies(surrounding_data):
    """ Updates the dictionary message sent to the client with frequency data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client
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
        fprint("Error querying frequencies", event_bug)


def get_near_navaids(surrounding_data, center, RADIUS=100):
    """ Updates the dictionary message sent to the client with navaid data

    Parameters
    ----------
    surrounding_data : dict
        Dictionary sent to the client
    center : (float, float)
        Center of the radar
    RADIUS : float, optional
        Radius of the radar
    """    
    try:
        s, n, w, e = get_box_from_center(center, RADIUS)
        surrounding_data['list_navaids'] = query_map_near_navaids(s, n, w, e) 
    except Exception as e:
        fprint("Error querying navaids", e)
        surrounding_data['list_navaids'] = []





class AirspaceBackgroundWorker:
    """
    Thread handling periodic queries and calls to the traffic data API
    """
    switch = False

    def __init__(self, sio, box=None, center=None):
        self.sio = sio
        self.switch = True
        self.box = box
        self.center = center
        self.surrounding_data = {}
        self.flight_data_process = FlightRadar24Handler()
        self.update_static_data()


        fprint("----- Background airspace worker initialized -----")

    def do_work(self):
        while self.switch:
            try:
                # Handle traffic
                if USE_RADAR:
                    self.flight_data_process.get_current_airspace(self.surrounding_data, center=self.center)
                else:
                    self.flight_data_process.get_current_airspace(self.surrounding_data, box=self.box)
        

                self.sio.emit('airspace', self.surrounding_data)

                fprint(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), 
                    f"# Flights : {self.surrounding_data['number_flights']}", 
                    f"# Airports : {len(self.surrounding_data['list_airports'])}",
                    f"# Runways : {len(self.surrounding_data['list_runways'])}",
                    )

                self.sio.sleep(.5)

            except Exception as e:
                fprint(f"Error : {str(e)}")
    


    def update_static_data(self):
        try:
            self.surrounding_data['center'] = self.center
            self.surrounding_data['box'] = self.box

            # Handle airports
            self.surrounding_data['list_airports'] = []
            get_near_airports(self.surrounding_data, self.center)

            # # Handle frequencies
            get_near_frequencies(self.surrounding_data)

            # # Handle runways
            self.surrounding_data['list_runways'] = []
            get_near_runways(self.surrounding_data, self.center)
            
            # # Handle navaids
            self.surrounding_data['list_navaids'] = []
            get_near_navaids(self.surrounding_data, self.center)
        
        except Exception as e:
                fprint(f"Error : {str(e)}")


    def update_box(self, box):
        self.box = box
        self.update_static_data()

    
    def update_center(self, center):
        self.center = center
        self.update_static_data()

    def stop(self):
        self.switch = False



class FlightFollowerWorker:

    def __init__(self, sio):
        self.sio = sio
        self.flight_id = ""
        self.switch = True
        self.is_following = False
        # To search near this position
        self.latitude = 0
        self.longitude = 0
        self.static_info = {
            'id' : "",
            'registration' : "",
            'callsign' : "",
            'origin' : "",
            'destination' : ""
        }

    def do_work(self):
        while self.switch:
            try:
                if self.is_following:
                    dynamic_data = autocomplete_query_handler.query_proximity_to_flight(self.latitude, self.longitude, self.flight_id)
                    # Move box around the current followed flight
                    self.latitude = dynamic_data['lat']
                    self.longitude = dynamic_data['lon']

                    flight_data = self.static_info
                    for k in dynamic_data:
                        flight_data[k] = dynamic_data[k]
                else:
                    flight_data = {}
                
                fprint(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    f"Following {self.flight_id}")

                flight_data['is_following'] = self.is_following
                
                self.sio.emit('follow_flight_info', flight_data)
                self.sio.sleep(SLEEP_TIME)

            except Exception as e:
                fprint(f"Error : {str(e)}")


    def update_flight_static_info(self, flight_id):
        self.is_following = True
        self.flight_id = flight_id
        current_flight_data = autocomplete_query_handler.query_complete_flight(self.flight_id)
        self.latitude = current_flight_data['lat']
        self.longitude = current_flight_data['lon']

        for k in self.static_info:
            self.static_info[k] = current_flight_data[k]




def start_work(sid):
    global thread, airspace_worker, flight_follower_worker
    toulouse_lat, toulouse_long = 43.59972466458162, 1.4492797572165728
    min_lat, max_lat = toulouse_lat - 1, toulouse_lat + 1
    min_long, max_long = toulouse_long - 2, toulouse_long + 2
    box = (min_lat, max_lat, min_long, max_long)
    center = (toulouse_lat, toulouse_long)

    if not thread.is_alive():
        if airspace_worker is not None:
            if USE_RADAR: airspace_worker.update_center(center)
            else: airspace_worker.update_box(box)
        else:
            airspace_worker = AirspaceBackgroundWorker(sio, box=box, center=center)
            sio.start_background_task(airspace_worker.do_work)

        if flight_follower_worker is not None:
            flight_follower_worker.update_flight_id('')
        else:
            flight_follower_worker = FlightFollowerWorker(sio)
            sio.start_background_task(flight_follower_worker.do_work)



# =======================================================================
# ===================== FLASK APP VIEWS =================================
# =======================================================================

# =============== ROUTE ==========================
@app.route('/')
def index():
    print(request)
    return render_template('index.html')

@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    results = autocomplete_query_handler.query_partial_flight(query=search)
    fprint(f"Follow flight query : {search} , {results}")
    return jsonify(matching_results=results)


# =============== SOCKET =======================
init_ontology_individuals()

@sio.on('init_worker')
def init_worker():
    start_work("start")


@sio.on('change_focus')
def get_change_focus(data):
    fprint(f"Change focus : {data}")
    if USE_RADAR:
        center = (data['latitude'], data['longitude'])
        airspace_worker.update_center(center)
    else:
        min_lat, max_lat = data['latitude'] - 1, data['latitude'] + 1
        min_long, max_long = data['longitude'] - 2, data['longitude'] + 2
        box = (min_lat, max_lat, min_long, max_long)
        airspace_worker.update_box(box)


@sio.on('new_follow')
def new_follow_flight(data):
    flight_id = data['flight_id']
    fprint(f"New follow flight : {data['label']}")
    # Update a thread that moves center
    flight_follower_worker.update_flight_static_info(flight_id)





@sio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
