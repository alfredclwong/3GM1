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

from USBArduino import USBArduino
from BluetoothArduino import BluetoothArduino
from APICommands import *
from camera_widget import camWidget, Camera

baudrate = 9600
blacklist = ["20:15:03:03:08:43"]
hwids = [["1A86", "7523"]]
bluetooth_devices = ["HC-06"]
usb_dir = "/media/pi"
bluetooth_port = 1

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

    def plot(self, arduinos):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        for i, arduino in enumerate(arduinos):
            for label, data in arduino.data.items():
                if arduino.active_data[label]:
                    ax.plot(data, label="{}. {} [{}]".format(i, label, arduino.data_units[label]))
                    for x,y in zip((len(data)-1), data):
                        ax.annotate(str(y), xy=(5,y), xytext=(0,0), textcoords='offset points')

        ax.legend(loc='upper left')
        lims = [data_range[:][0] for data_range in arduino.data_ranges for arduino in arduinos]
        lims += [data_range[:][1] for data_range in arduino.data_ranges for arduino in arduinos]
        ax.set_ylim(min(lims), max(lims))
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # Other stuff - for keeping track of MedicalArduino instances and timing
        self.arduinos = []
        self.timer = QtCore.QTimer()
        self.prevs = []
        
        # UI Titles and size constants
        self.title = "Data Aqcuisition"
        self.tabname1 = "Devices"
        self.tabname2 = "File Upload"
        self.tabname3 = "Camera"
        self.width = 640
        self.height = 480
        self.initUI()
        self.supportedfiles = ('.jpg','.png','pdf') #files supported by USB file detection

    def initUI(self):
        #self.showFullScreen()
        
        #INTERFACE BUTTONS
        self.interface_row = QHBoxLayout()
        
        # Patient ID form -single patient ID form to avoid overwriting problem
        self.id = QLineEdit()
        self.input_form = QFormLayout()
        self.input_form.addRow("Patient ID:", self.id)
        self.interface_row.addLayout(self.input_form)
        
        # Detect button -single detect button to act as switch based on current tab
        self.detect = QPushButton("Detect",self)
        self.detect.setMinimumHeight(50)
        self.detect.clicked.connect(self.detectswitch)
        self.interface_row.addWidget(self.detect)

        # Send button - single send button to act as switch based on current tab
        self.send = QPushButton("Send")
        self.send.setMinimumHeight(50)
        self.send.clicked.connect(self.sendData)
        self.interface_row.addWidget(self.send)
        
        #TABS WIDGET
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(self.width, self.height)
        self.tabs.addTab(self.tab1, self.tabname1)
        self.tabs.addTab(self.tab2, self.tabname2)
        self.tabs.addTab(self.tab3, self.tabname3)
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        
        #Set window title
        self.setWindowTitle(self.title)

        # Set size and centre the window in the desktop screen
        self.setGeometry(0, 0, self.width, self.height)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        
        # Create a central widget which will hold all subcomponents
        layout = QGridLayout()
        layout.addLayout(self.interface_row,0,0)
        layout.addWidget(self.tabs,1,0)
        self.central=QWidget()
        self.central.setLayout(layout)
        self.setCentralWidget(self.central)
        self.statusBar()
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
        top_row1 = QHBoxLayout()
        
        # Checkable dropdown menu for recording selection
        self.dropdown = QToolButton(self)
        self.dropdown.setMinimumHeight(50)
        dropdownSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dropdown.setSizePolicy(dropdownSizePolicy)
        self.dropdown.setText('Select recordings')
        self.dropdown.setPopupMode(QToolButton.InstantPopup)
        self.toolmenu = QMenu(self)
        self.toolmenu.triggered.connect(self.onChecked)
        self.dropdown.setMenu(self.toolmenu)
        top_row1.addWidget(self.dropdown)
        
        # Start stop button
        self.startstop = QPushButton("Start/Stop Recording")
        self.startstop.setMinimumHeight(50)
        self.startstop.clicked.connect(self.start_stop)
        top_row1.addWidget(self.startstop)

        # VISUAL ROW (PLOTTING WIDGET)
        visual_row1 = QHBoxLayout()
        self.graph = PlotCanvas(self)
        visual_row1.addWidget(self.graph)

        #DEFINE GRID LAYOUT AND ADD INTERFACE/VISUAL ROWS
        self.layout = QGridLayout()
        self.layout.addLayout(top_row1, 0, 0)
        self.layout.addLayout(visual_row1, 1, 0)
        self.tab1.setLayout(self.layout)
        
    def onChecked(self):
        """
        """
        for i, arduino in enumerate(self.arduinos):
            for action in self.toolmenu.actions():
                suffix = " ({})".format(i)
                if action.text().endswith(suffix):
                    arduino.active_data[action.text().strip(suffix)] = action.isChecked()
        
        self.graph.plot(self.arduinos)

    def tab2UI(self):
        """
        Tab split into 2 rows
        """
        
        #INTERFACE ROW
        top_row2=QHBoxLayout()
        
        #Drop down menu for selecting detected images
        dropdownSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.imagemenu = QMenu(self)
        self.imagedrop=QToolButton()
        self.imagedrop.setMinimumHeight(50)
        self.imagedrop.setSizePolicy(dropdownSizePolicy)
        self.imagedrop.setText('Select File')
        self.imagedrop.setMenu(self.imagemenu)
        self.imagedrop.setPopupMode(QToolButton.InstantPopup)
        top_row2.addWidget(self.imagedrop)
             
        #DEFINE VISUAL ROW (IMAGE WIDGET)
        visual_row2 = QHBoxLayout()
        self.image = QLabel()
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        visual_row2.addWidget(self.image)
        
        #DEFINE GRID LAYOUT AND ADD INTERFACE/VISUAL ROWS
        self.layout2 = QGridLayout()
        self.layout2.addLayout(top_row2,0,0)
        self.layout2.addLayout(visual_row2,1,0, QtCore.Qt.AlignCenter)
        self.tab2.setLayout(self.layout2)
        
    def tab3UI(self):
        """
        """
        self.layout3 = QVBoxLayout()
        #initialise custom webcam widget
        self.webcam = camWidget()
        self.layout3.addWidget(self.webcam)
        self.tab3.setLayout(self.layout3)
        
        
    
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
            arduino.close()

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

            # Create a new USBArduino using this information
            arduino = USBArduino(ser, header)
            self.arduinos.append(arduino)
            self.prevs.append(0) # such that data will be requested on '>/=' click
            for i, data_label in enumerate(arduino.data_labels):
                action = self.toolmenu.addAction(data_label)
                action.setCheckable(True)
                action.setChecked(True)
        self.graph.plot(self.arduinos)
        
        # Scan through Bluetooth connections
        self.display("scanning for nearby bluetooth devices...")
        nearby_devices = discover_devices(lookup_names=True)
        print(nearby_devices)
        for i, (addr, name) in enumerate(nearby_devices):
            if name not in bluetooth_devices or addr in blacklist:
                continue
            self.display("detected bluetooth device at address {}".format(addr))
            sock = BluetoothSocket(RFCOMM)
            try:
                sock.connect((addr, bluetooth_port))
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
                action.setChecked(True)
        
        # Replot graph such that the legend updates
        self.graph.plot(self.arduinos)

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
                self.graph.plot(self.arduinos)
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
            if not any(any(len(medicaldata) > 0 for medicaldata in arduino.data)
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
        if path.endswith('pdf'):
            path='pdf_logo.jpg'
        self.display(path + ' selected')
        self.pixmap = QtGui.QPixmap(path)
        self.pixmap = self.pixmap.scaled(230, 500, QtCore.Qt.KeepAspectRatio)
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
        #for root, dirs, files in os.walk(usb_dir):
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
            self.display('Files found')
            group.setExclusive(True)
        elif not self.imagelist:
            self.display('No images found, please insert USB storage device')
        
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
    def detectswitch(self):
        current_tab = self.tabs.currentIndex() + 1 #add 1 to be consistent with tab numbers
        if current_tab == 1:
            self.detect_ports()
        elif current_tab == 2:
            self.detectUSB()
        elif current_tab == 3:
            self.display('Detecting Webcam...')
            self.webcam.setup()
            
            
        
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec_())
