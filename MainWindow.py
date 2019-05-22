from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QFormLayout
import pyqtgraph as pg

import random
import numpy as np
import time
import serial
import serial.tools.list_ports
import json
import time

from MedicalArduino import MedicalArduino

# The following lines of code were provided by the L2S2 employee:
# BEGIN
import asyncio
from datetime import datetime
import requests
import websockets
import inspect
import uuid
from pprint import pprint

# ARM dev server
API_URI = 'https://apicued2019.xenplate.com/internalapi'
API_KEY = 'hqQuiDT6rdh3dRJpEKXTXfunjMZCN5vG'
_cert = None
test_patient_username = 'TestPatient'
test_patient_password = 'Escape78BrightLight'
test_plate_template_name = 'Raw Medical'
# test_plate_template_name = 'Key Plate'

_user_api_key = API_KEY
_key_plate_template_id = None
_key_plate_data_id = None
_record_id = None
_user_id = None
LONG_TIME_EPOCH: datetime = datetime(1800, 1, 1)


def get_api_key_header(api_key):
    return {'Authorization': f'X-API-KEY {api_key}'}


def from_long_time(long_date_time: int) -> datetime:
    return LONG_TIME_EPOCH + timedelta(seconds=long_date_time)


def to_long_time(date_time: datetime) -> int:
    return int((date_time - LONG_TIME_EPOCH).total_seconds())


def print_status(resp) -> bool:
    if resp.status_code == 200: return False

    print(f"{inspect.stack()[1][0].f_code.co_name}  Status={resp.status_code}  Reason={resp.reason}")

    return True


def record_search(patient_ID):
    filters = [
        {'operator': 1, 'property': 'IdNumber', 'value': patient_ID}
    ]

    resp = requests.post(f'{API_URI}/record/search',
                         json={'filters': filters},
                         headers=get_api_key_header(API_KEY),
                         cert=_cert)

    if print_status(resp): return

    response_json = resp.json()

    # pprint(response_json)
    return response_json['RecordSearchResult']['records'][0]['id']


def data_create(record_id, template_id, control_values: list):
    payload = {'record_id': record_id,
               'plate_template_id': template_id,
               'control_values': control_values}

    resp = requests.post(f'{API_URI}/data/create',
                         json={'data': payload, 'ignore_conflicts': True},
                         headers=get_api_key_header(_user_api_key),
                         cert=_cert)

    if print_status(resp): return

    response_json = resp.json()

    status = response_json['PlateDataCreateResult']['status']

    print(f"data_create Status={status}")

    if status != 0:
        pprint(response_json['PlateDataCreateResult'], width=120)

def template_read_active_full(plate_template_name):
    resp = requests.get(f'{API_URI}/template/read/active/full?plate_name={plate_template_name}',
                        headers=get_api_key_header(_user_api_key),
                        cert=_cert)
    
    if print_status(resp): return

    response_json = resp.json()

    status = response_json['PlateTemplateReadActiveByIdNameResult']['status']

    if status != 0: 
        print(f"Failed, status={status}")
        return

    return response_json['PlateTemplateReadActiveByIdNameResult']['plate_template']['id']

# END


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        """
        The GUI design is split into three rows, organised as follows:
        Top row.    Contains input fields required for labelling the recorded data such
                    as patient ID and date/time. Also contains a settings button which
                    may later be used for viewing/changing Arduino properties.
        Middle row. Contains a graph capable of plotting data from multiple recordings.
        Bottom row. Contains functionality for controlling recordings (e.g. start/stop).
        """
        # Create the main window and a central widget which will hold all subcomponents
        super(MainWindow, self).__init__(parent)
        self.central = QtGui.QWidget()
        self.setCentralWidget(self.central)

        # Top row (horizontal box layout)
        self.top_row = QHBoxLayout()
        # Form layout is a nice way to contain multiple text input fields
        self.input_form = QFormLayout()
        self.id = QtGui.QLineEdit()
        self.input_form.addRow("Patient ID:", self.id)
        self.date = QtGui.QLineEdit()
        self.input_form.addRow("Date:", self.date)
        self.top_row.addLayout(self.input_form)
        self.top_row.addWidget(QtGui.QPushButton("Settings")) # dummy

        # Middle row (just graph)
        self.graph = pg.PlotWidget()

        # Bottom row (horizontal box layout)
        self.bottom_row = QHBoxLayout()
        self.dropdown = QtGui.QComboBox() # todo: add selection functionality?
        self.bottom_row.addWidget(self.dropdown, stretch=1)
        self.refresh = QtGui.QPushButton("Detect")
        self.bottom_row.addWidget(self.refresh)
        self.startstop = QtGui.QPushButton(">/=")
        self.bottom_row.addWidget(self.startstop)
        self.send = QtGui.QPushButton("Send")
        self.bottom_row.addWidget(self.send)

        # Add all 3 rows to self.layout and assign self.layout to self.central
        self.layout = QGridLayout()
        self.layout.addLayout(self.top_row, 0, 0)
        self.layout.addWidget(self.graph, 1, 0)
        self.layout.addLayout(self.bottom_row, 2, 0)
        self.central.setLayout(self.layout)

        # Now add functionality
        # Bottom row
        self.refresh.clicked.connect(self.refresh_ports)
        self.startstop.clicked.connect(self.plotter)
        self.send.clicked.connect(self.sender)

        # Other stuff - for keeping track of MedicalArduino instances and timing
        self.arduinos = []
        
        self.timer = QtCore.QTimer()
        self.prevs = []

    def refresh_ports(self):
        """
        Within refresh_ports():
        1. Detect connection
        2. Send header request ('A')
        3. Create MedicalArduino() using header
        
        Outside refresh_ports():
        4. Send data requests according to sample rate
        5. Update GUI?
        """
        # Close all currently open ports
        for arduino in self.arduinos:
            arduino.ser.close()
        
        # Reset graph
        self.graph.clear()
        self.graph.getPlotItem().addLegend()
        
        # Udpate self.dropdown using serial.tools.list_ports.comports()
        self.dropdown.clear()
        for p in serial.tools.list_ports.comports():
            print("Detected device at port", p.device)
            ser = serial.Serial(p.device, 115200, timeout=0)
            time.sleep(2) # temporary workaround
            ser.write(b'A')
            time.sleep(0.5) # temporary workaround
            while True: # read until endline ('\n') in case json is buffered
                j = ser.readline()
                if j.endswith(b'\n'):
                    break
            header = json.loads(j)
            print(header)

            # Create a new MedicalArduino using this information
            arduino = MedicalArduino(ser, header, self.graph.getPlotItem())
            self.arduinos.append(arduino)
            self.prevs.append(0) # such that data will be requested on '>/=' click
            self.dropdown.addItems([arduino.name])

    def plotter(self):  # called when the start/stop button is clicked
        """
        Set up graph according to selected arduinos and start timer
        TODO: legends not showing at the moment
        """
        if not self.timer.isActive():
            # Reset data plots
            for arduino in self.arduinos:
                for label in arduino.data_labels:
                    arduino.data[label] = []

            # Connect the updater() function to the clock and start it
            self.timer.timeout.connect(self.updater)
            self.timer.start(0)
            print("Recording started")
        else:
            self.timer.stop()
            print("Recording ended")

    def updater(self):  # called regularly by QTimer
        """
        Query arduinos for new data according to their sampling rates.
        Currently arduinos will also update the graph themselves.
        """
        for i in range(len(self.arduinos)):
            if time.time() - self.prevs[i] > 1.0 / self.arduinos[i].sampling_rate:
                self.arduinos[i].sample()
                self.prevs[i] = time.time()

    def sender(self):  # called when the send button is clicked
        """
        1. Read patient ID from GUI text field
        2. Extract data from MedicalArduino list
        """
        if not self.timer.isActive():
            print("Sending data to Xenplate...")

            # Read patient ID
            print("Patient ID:", self.id.text())
            patient_ID = self.id.text()
            if patient_ID == "":
                print("Error: no patient ID input!")
                return

            # Check for no data
            if not any(any(len(arduino.data[label]) > 0 for label in arduino.data_labels)
                       for arduino in self.arduinos):
                print("No data to send!")
                return
            
            # Extract data
            data = {}
            for arduino in self.arduinos:
                for label in arduino.data_labels:
                    data[label] = np.mean(arduino.data[label])
            print(data)

            # Convert to uploadable format
            values = [{'name': 'Date', 'value': to_long_time(datetime.now())},
                      {'name': 'Time', 'value': to_long_time(datetime.now())},
                      {'name': 'Pulse', 'value': data['Heart_rate']},
                      {'name': 'Oxygen', 'value': data['Oxygen']}]

            # Look up Xenplate patient record using patient ID and create an entry
            data_create(record_search(patient_ID),
                        template_read_active_full(arduino.name),
                        values)

            self.graph.getPlotItem().clear()
            print("Sent.")
        else:
            print("Recording still ongoing - end recording before sending data")


if __name__ == '__main__':
    app = QtGui.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
