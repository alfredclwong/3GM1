from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDesktopWidget, QSizePolicy,
                             QGridLayout, QHBoxLayout, QFormLayout,
                             QToolButton, QAction, QMenu, QPushButton, QLineEdit)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import sys
import random
import numpy as np
import time
import serial
import serial.tools.list_ports
import json
import time

from MedicalArduino import MedicalArduino
from APICommands import *

baudrate = 9600
hwids = [["1A86", "7523"]]

class PlotCanvas(FigureCanvas):
    """
    
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self, data_dict):
        ax = self.figure.add_subplot(111)
        for label, data in data_dict.items():
            ax.plot(data, label=label)
        plt.legend(loc='upper left')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Other stuff - for keeping track of MedicalArduino instances and timing
        self.arduinos = []
        self.timer = QtCore.QTimer()
        self.prevs = []
        
        # UI stuff
        self.title = "title"
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        """
        The GUI design is split into three rows, organised as follows:
        Top row.    Contains input fields required for labelling the recorded data such
                    as patient ID and date/time. Also contains a settings button which
                    may later be used for viewing/changing Arduino properties.
        Middle row. Contains a graph capable of plotting data from multiple recordings.
        Bottom row. Contains functionality for controlling recordings (e.g. start/stop).
        """
        self.setWindowTitle(self.title)

        # Set size and centre window
        self.setGeometry(0, 0, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        
        # Create a central widget which will hold all subcomponents
        self.central = QWidget()
        self.setCentralWidget(self.central)

        # TOP ROW (horizontal box layout)
        self.top_row = QHBoxLayout()
        
        # Checkable dropdown menu for recording selection
        self.dropdown = QToolButton(self)
        self.top_row.addWidget(self.dropdown)
        dropdownSizePolicy = QSizePolicy(QSizePolicy.Expanding,
                                         QSizePolicy.Fixed)
        self.dropdown.setSizePolicy(dropdownSizePolicy)
        self.dropdown.setText('Select recordings')
        self.toolmenu = QMenu(self)
        self.dropdown.setMenu(self.toolmenu)
        self.toolmenu.triggered.connect(lambda: self.graph.plot({
            action.text(): arduino.data[action.text()]
            for arduino in self.arduinos
            for action in self.toolmenu.actions() if action.isChecked()}))
        self.dropdown.setPopupMode(QToolButton.InstantPopup)
        
        # Detect button
        self.detect = QPushButton("Detect")
        self.top_row.addWidget(self.detect)
        self.detect.clicked.connect(self.detect_ports)

        # MIDDLE ROW (just graph)
        self.graph = PlotCanvas(self)

        # BOTTOM ROW (horizontal box layout)
        self.bottom_row = QHBoxLayout()
        
        # Form layout is a nice way to contain multiple text input fields
        self.input_form = QFormLayout()
        self.bottom_row.addLayout(self.input_form)
        self.id = QLineEdit()
        self.input_form.addRow("Patient ID:", self.id)
        
        # Start stop button
        self.startstop = QPushButton(">/=")
        self.bottom_row.addWidget(self.startstop)
        self.startstop.clicked.connect(self.start_stop)

        # Send button
        self.send = QPushButton("Send")
        self.bottom_row.addWidget(self.send)
        self.send.clicked.connect(self.sender)

        # Add all 3 rows to self.layout and assign self.layout to self.central
        self.layout = QGridLayout()
        self.layout.addLayout(self.top_row, 0, 0)
        self.layout.addWidget(self.graph, 2, 0)
        self.layout.addLayout(self.bottom_row, 1, 0)
        self.central.setLayout(self.layout)
        
        self.statusBar().showMessage('status bar message')
        self.show()

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
        
        # Udpate self.dropdown using serial.tools.list_ports.comports()
        self.toolmenu.clear()
        for p in serial.tools.list_ports.comports():
            print("detected device at port", p.device)
            if not any(all(id in p.hwid for id in hwid) for hwid in hwids):
                print("hwid mismatch")
                continue
            ser = serial.Serial(p.device, baudrate, timeout=0)
            time.sleep(2) # temporary workaround
            ser.write(b'A')
            time.sleep(0.5) # temporary workaround
            while True: # read until endline ('\n') in case json is buffered
                j = ser.readline()
                if j.endswith(b'\n'):
                    break
            header = json.loads(j.decode())
            print(header)

            # Create a new MedicalArduino using this information
            arduino = MedicalArduino(ser, header)
            self.arduinos.append(arduino)
            self.prevs.append(0) # such that data will be requested on '>/=' click
            for i, data_label in enumerate(arduino.data_labels):
                action = self.toolmenu.addAction(data_label)
                action.setCheckable(True)
                action.setShortcut("Ctrl+{}".format(i+1))
                action.setChecked(True)
        data_dict = {action.text(): arduino.data[action.text()]
            for arduino in self.arduinos
            for action in self.toolmenu.actions() if action.isChecked()}
        print(data_dict)
        self.graph.plot(data_dict)

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
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec_())
