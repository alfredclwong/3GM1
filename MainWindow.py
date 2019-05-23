from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QFormLayout, QAction
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
from APICommands import *

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

        ###################################
        # Top row (horizontal box layout) #
        ###################################
        self.top_row = QHBoxLayout()
        
        # Checkable dropdown menu for recording selection
        self.dropdown = QtGui.QToolButton(self)
        self.top_row.addWidget(self.dropdown)
        # set size to expand horizontally, stay fixed vertically
        dropdownSizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                               QtGui.QSizePolicy.Fixed)
        self.dropdown.setSizePolicy(dropdownSizePolicy)
        # set text to show when not expanded
        self.dropdown.setText('Select recordings')
        # set the menu to show when expanded
        self.toolmenu = QtGui.QMenu(self)
        self.dropdown.setMenu(self.toolmenu)
        # functionality: expansion and checking
        self.toolmenu.triggered.connect(self.update_legends)
        self.dropdown.setPopupMode(QtGui.QToolButton.InstantPopup)
        
        # Detect button
        self.detect = QtGui.QPushButton("Detect")
        self.top_row.addWidget(self.detect)
        self.detect.clicked.connect(self.detect_ports)

        ###########################
        # Middle row (just graph) #
        ###########################
        self.graph = pg.PlotWidget()

        ######################################
        # Bottom row (horizontal box layout) #
        ######################################
        self.bottom_row = QHBoxLayout()
        
        # Form layout is a nice way to contain multiple text input fields
        self.input_form = QFormLayout()
        self.bottom_row.addLayout(self.input_form)
        self.id = QtGui.QLineEdit()
        self.input_form.addRow("Patient ID:", self.id)
        #self.date = QtGui.QLineEdit()
        #self.input_form.addRow("Date:", self.date)
        #self.bottom_row.addWidget(QtGui.QPushButton("Settings")) # dummy
        
        # Start stop button
        self.startstop = QtGui.QPushButton(">/=")
        self.bottom_row.addWidget(self.startstop)
        self.startstop.clicked.connect(self.start_stop)

        # Send button
        self.send = QtGui.QPushButton("Send")
        self.bottom_row.addWidget(self.send)
        self.send.clicked.connect(self.sender)

        # Add all 3 rows to self.layout and assign self.layout to self.central
        self.layout = QGridLayout()
        self.layout.addLayout(self.top_row, 0, 0)
        self.layout.addWidget(self.graph, 1, 0)
        self.layout.addLayout(self.bottom_row, 2, 0)
        self.central.setLayout(self.layout)

        # Other stuff - for keeping track of MedicalArduino instances and timing
        self.arduinos = []
        self.timer = QtCore.QTimer()
        self.prevs = []

    def update_legends(self):
        """
        Clear the graph, add in an empty legend box (which tracks the plotted curves),
        and plot empty data for each recording type that is selected in the dropdown menu.
        """
        self.graph.clear()
        try:
            self.legend.scene().removeItem(self.legend)
        except:
            pass
        self.legend = self.graph.getPlotItem().addLegend()
        self.curves = {action.text(): self.graph.getPlotItem().plot(name=action.text())
                       for action in self.toolmenu.actions() if action.isChecked()}

    def detect_ports(self):
        """
        Within detect_ports():
        1. detect_ports connection
        2. Send header request ('A')
        3. Create MedicalArduino() using header
        
        Outside detect_ports():
        4. Send data requests according to sample rate
        5. Update GUI?
        """
        # Close all currently open ports
        for arduino in self.arduinos:
            arduino.ser.close()
        
        # Reset graph
        self.graph.clear()
        
        # Udpate self.dropdown using serial.tools.list_ports.comports()
        self.toolmenu.clear()
        for p in serial.tools.list_ports.comports():
            print("detected device at port", p.device)
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
            for i, data_label in enumerate(arduino.data_labels):
                action = self.toolmenu.addAction(data_label)
                action.setCheckable(True)
                action.setShortcut(f"Ctrl+{i+1}")
                action.setChecked(True)
            self.update_legends()

    def start_stop(self):  # called when the start/stop button is clicked
        """
        Set up graph according to selected arduinos and start timer
        """
        if not self.timer.isActive():
            #for action in self.toolmenu.actions():
            #    action.setCheckable(False)
            
            # Reset data plots
            for arduino in self.arduinos:
                for label in arduino.data_labels:
                    arduino.data[label] = []

            # Connect the updater() function to the clock and start it
            self.timer.timeout.connect(self.updater)
            self.timer.start(0)
            print("Recording started")
        else:
            #for action in self.toolmenu.actions():
            #    action.setCheckable(True)
            self.timer.stop()
            print("Recording ended")

    def updater(self):  # called regularly by QTimer
        """
        Query arduinos for new data according to their sampling rates.
        Update active curves (according to toolmenu selection) with the returned data.
        """
        for i in range(len(self.arduinos)):
            if time.time() - self.prevs[i] > 1.0 / self.arduinos[i].sampling_rate:
                data = self.arduinos[i].sample()
                for label in data.keys():
                    if label in [action.text() for action in self.toolmenu.actions() if action.isChecked()]:
                        self.curves[label].setData(data[label])
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
