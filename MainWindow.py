from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import* #(QApplication, QMainWindow, QWidget, QDesktopWidget, QSizePolicy,
                             #QGridLayout, QHBoxLayout, QFormLayout,
                             #QToolButton, QAction, QMenu, QPushButton, QLineEdit)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from bluetooth import *
import os
import sys
import random
import numpy as np
import time
import serial
import serial.tools.list_ports
import json
import time

from MedicalArduino import MedicalArduino
from BluetoothArduino import BluetoothArduino
from APICommands import *
#from imagelist_widget import imagelist

baudrate = 9600
hwids = [["1A86", "7523"]]
bluetooth_devices = ["HC-06"]

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

    def plot(self, data_dict, arduinos):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for label, data in data_dict.items():
            ax.plot(data, label=label)
        ax.legend(loc='upper left')
        lims = [arduino.data_range[0] for arduino in arduinos]
        lims += [arduino.data_range[1] for arduino in arduinos]
        ax.set_ylim(min(lims), max(lims))


        self.draw()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Other stuff - for keeping track of MedicalArduino instances and timing
        self.arduinos = []
        self.timer = QtCore.QTimer()
        self.prevs = []
        
        # UI stuff
        self.title = "title"
        self.tabname1 = "Devices"
        self.tabname2 = "USB Files"
        self.width = 640
        self.height = 480
        self.initUI()
        self.supportedfiles = ('.jpg','.png') #files supported by USB file detection

    def initUI(self):
        
        #setup main tabs Widget
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(self.width, self.height)
        self.tabs.addTab(self.tab1, self.tabname1)
        self.tabs.addTab(self.tab2, self.tabname2)
        self.tab1UI()
        self.tab2UI()
        
        #Set window title
        self.setWindowTitle(self.title)

        # Set size and centre the window in the desktop screen
        self.setGeometry(0, 0, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        
        # Create a central widget which will hold all subcomponents
        self.setCentralWidget(self.tabs)
        #self.statusBar().showMessage('')
        self.show()
        
    def tab1UI(self):
        """
        The GUI design is split into three rows, organised as follows:
        Interface row.  Used for controlling the Arduino-Pi interfaces - detecting/refreshing
                        connections and selecting which recordings to visualise/send.
        Visual row.     Contains a graph capable of plotting data from multiple recordings.
                        In the future could auto-toggle/format to visualise other data types.
        Data row.       Used for creating (>/=), tagging (ID) and sending (Send) data.
        """
        # INTERFACE ROW
        self.interface_row = QHBoxLayout()
        
        # Checkable dropdown menu for recording selection
        self.dropdown = QToolButton(self)
        self.dropdown.setMinimumHeight(50)
        dropdownSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dropdown.setSizePolicy(dropdownSizePolicy)
        self.dropdown.setText('Select recordings')
        self.dropdown.setPopupMode(QToolButton.InstantPopup)
        self.toolmenu = QMenu(self)
        self.plot = lambda: self.graph.plot({
            action.text(): arduino.data[action.text()]
            for arduino in self.arduinos
            for action in self.toolmenu.actions() if action.isChecked()},
            self.arduinos)
        self.toolmenu.triggered.connect(self.plot)
        self.dropdown.setMenu(self.toolmenu)
        self.interface_row.addWidget(self.dropdown)
        
        # Detect button
        self.detect = QPushButton("Detect")
        self.detect.setMinimumHeight(50)
        self.detect.clicked.connect(self.detect_ports)
        self.interface_row.addWidget(self.detect)

        # VISUAL ROW
        self.visual_row = QHBoxLayout()
        self.graph = PlotCanvas(self)
        self.visual_row.addWidget(self.graph)

        # DATA ROW
        self.data_row = QHBoxLayout()
        
        # Form layout is a nice way to contain multiple text input fields
        self.input_form = QFormLayout()
        self.id = QLineEdit()
        self.input_form.addRow("Patient ID:", self.id)
        self.data_row.addLayout(self.input_form)
        
        # Start stop button
        self.startstop = QPushButton("Start/Stop Recording")
        self.startstop.setMinimumHeight(50)
        self.startstop.clicked.connect(self.start_stop)
        self.data_row.addWidget(self.startstop)

        # Send button
        self.send = QPushButton("Send")
        self.send.setMinimumHeight(50)
        self.send.clicked.connect(self.sendData)
        self.data_row.addWidget(self.send)

        # Add all 3 rows to self.layout and set tab2 layout
        layout = QGridLayout()
        layout.addLayout(self.interface_row, 0, 0)
        layout.addLayout(self.data_row, 1, 0)
        layout.addLayout(self.visual_row, 2, 0)
        self.tab1.setLayout(layout)

    def tab2UI(self):
        """
        Tab split into 3 rows
        """
        
        #USER INTERFACE BUTTONS
        top=QHBoxLayout()
        
        #Drop down menu for selecting detected images
        imagedrop=QToolButton()
        imagedrop.setMinimumHeight(50)
        dropdownSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        imagedrop.setSizePolicy(dropdownSizePolicy)
        imagedrop.setText('Select image')
        self.imagemenu = QMenu(self)
        imagedrop.setMenu(self.imagemenu)
        imagedrop.setPopupMode(QToolButton.InstantPopup)
        top.addWidget(imagedrop)
        
        #Pushbutton for detecting images
        detect=QPushButton("Detect")
        detect.setMinimumHeight(50)
        detect.clicked.connect(self.detectUSB)
        top.addWidget(detect)       
        
        #DEFINE DATA ROW
        mid = QHBoxLayout()
        
        # Form layout is a nice way to contain multiple text input fields
        input_form = QFormLayout()
        self.id = QLineEdit()
        input_form.addRow("Patient ID:", self.id)
        mid.addLayout(input_form)

        # Send button
        self.sendimages = QPushButton("Send")
        self.sendimages.setMinimumHeight(50)
        #self.sendimages.clicked.connect(self.sendData)
        mid.addWidget(self.sendimages)
        
        #DEFINE BOTTOM ROW
        bottom = QHBoxLayout()
        
        #Image Widget
        self.image = QLabel()
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        bottom.addWidget(self.image)
        
        ###define grid and layout###
        layout = QGridLayout()
        layout.addLayout(top,0,0)
        layout.addLayout(mid,1,0)
        layout.addLayout(bottom,2,0, QtCore.Qt.AlignCenter)
        self.tab2.setLayout(layout)


    def display(self, msg):
        print(msg)
        self.statusBar().showMessage(str(msg))


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
        
        # Update self.dropdown (via self.toolmenu) and self.arduinos
        # TODO: submenus for each arduino and its data_labels in toolmenu
        self.toolmenu.clear()
        self.arduinos = []
        
        # Scan through USB connections: serial.tools.list_ports.comports()
        for p in serial.tools.list_ports.comports():
            self.display("detected device at port {}".format(p.device))
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
        
        # Scan through Bluetooth connections
        self.display("scanning for nearby bluetooth devices...")
        nearby_devices = discover_devices(lookup_names=True)
        print(nearby_devices)
        for i, (addr, name) in enumerate(nearby_devices):
            if name not in bluetooth_devices:
                continue
            self.display("detected bluetooth device at address {}".format(addr))
            sock = BluetoothSocket(RFCOMM)
            try:
                sock.connect((addr, i+1))  # open bluetooth socket on port i+1 (no port 0)
            except btcommon.BluetoothError as err:
                print(err)
                continue
            sock.send('A')
            data = b''
            while True:
                data += sock.recv(1024)
                if data.endswith(b'\n'):
                    break
            header = json.loads(data.decode())
            print(header)
            
            # Create a new BluetoothArduino
            arduino = BluetoothArduino(sock, header)
            self.arduinos.append(arduino)
            self.prevs.append(0) # such that data will be requested on '>/=' click
            for j, data_label in enumerate(arduino.data_labels):
                action = self.toolmenu.addAction(data_label)
                action.setCheckable(True)
                action.setShortcut("Ctrl+{}".format(j+1))
                action.setChecked(True)
        
        # Replot graph such that the legend updates
        data_dict = {action.text(): arduino.data[action.text()]
            for arduino in self.arduinos
            for action in self.toolmenu.actions() if action.isChecked()}
        print(data_dict)
        self.graph.plot(data_dict, self.arduinos)

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
            self.display("Recording started")
        else:
            #for action in self.toolmenu.actions():
            #    action.setCheckable(True)
            self.timer.stop()
            self.display("Recording ended")

    def updater(self):  # called regularly by QTimer
        """
        Query arduinos for new data according to their sampling rates.
        Update active curves (according to toolmenu selection) with the returned data.
        """
        for i in range(len(self.arduinos)):
            if time.time() - self.prevs[i] > 1.0 / self.arduinos[i].sampling_rate:
                self.arduinos[i].sample()
                self.plot
                self.prevs[i] = time.time()

    def sendData(self):  # called when the send button is clicked
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


    def showimage(self): #called when image from dropdown menu selected
        """
        Displays image in center of tab and displays "image_name selected"
        Then adds image to list of selected images
        """
        action=self.sender()
        path = action.text()
        self.display(path + ' selected')
        self.pixmap = QtGui.QPixmap(path)
        self.pixmap = self.pixmap.scaled(300, 300, QtCore.Qt.KeepAspectRatio)
        self.image.setPixmap(self.pixmap)
        
        
    def detectUSB(self): #called when "Detect" button clicked on Images tab
        """
        1. Clears image list arrays
        2. Searches directory assigned to usb devices for files of type specified by self.supportedfiles
        3. Adds file paths to a new array and updates dropdown menu
        """
        self.imagemenu.clear()
        self.imagelist=[]
        for root, dirs, files in os.walk(os.getcwd()): #temporary for PC
        #for root, dirs, files in os.walk('/media/pi'):
            for filename in files:
                if filename.endswith(self.supportedfiles): #edit this line for supported file formats
                    self.imagelist.append(os.path.join(root,filename))
        if self.imagelist: 
            group = QActionGroup(self.imagemenu)
            for image in self.imagelist:
                action = self.imagemenu.addAction(image, self.showimage)
                action.setCheckable(True)
                action.setChecked(False)
                group.addAction(action)
            self.display('Image found')
            group.setExclusive(True)
        elif not self.imagelist:
            self.display('No images found, please insert USB storage device')
        
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec_())
