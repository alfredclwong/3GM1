from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from MainWindow import MainWindow
import sys
import serial
import time

# This dictionary shows admin and user cards
ValidCards = {'admin':b'78 , 242 , 84 , 78\r\n'}

class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """
        Set up GUI add buttons, layout and button click links
        """
        super(Login, self).__init__(parent)
        
        # Set icon and title
        self.setWindowIcon(QIcon('icon_logo.png'))
        self.setWindowTitle("Login Window")
        
        # Initialise scan button and logo image
        self.buttonScan = QtWidgets.QPushButton('Tap here and then present your Security Card', self)
        self.buttonScan.clicked.connect(self.scanAndCheck)
        self.buttonScan.setMinimumHeight(50)
        self.logo = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap('main_logo.png')
        self.logo.setPixmap(pixmap)
        self.logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logo.setAlignment(Qt.AlignCenter)

        # Optional, resize window to image size
        # self.logo.resize(pixmap.width(),pixmap.height())
        
        # Initialise layout and add widgets
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.logo)
        layout.addWidget(self.buttonScan)

    def checkForCards(self):
        """
        Check for cards:
        1. Call 'connectArduino' to find the correct serial port
        2. Wait till we read a card
        3. Return card number of the first card read
        """
        # First find which port has the card reader attached and set it as ser
        ser = self.connectArduino()
        
        # i optionally used for debugging
        i = 0
        
        # Wait to read a card
        while True: 
            
            # Send 'B' so the Arduino sends card data
            ser.write(b'B')
            time.sleep(0.5)
            
            # Read the Arduino data
            j = ser.readline()
            
            print('Checking for card num...', i , j)
            i += 1
            
            # if we don't get a blank reading record it as the card_id
            if j != b'':
                card_id = j    
                ser.close()
                print('found card', card_id)
                break
        
        # record the card ID
        return card_id
        
    def scanAndCheck(self):
        """
        Scan button links here:
        1. Call 'checkForCards'
        2. Check if card is in ValidCards dictionary
        3. accept or send error message accordingly
        """
        # Call checkForCards
        card_id = self.checkForCards()
        
        # Optional troubleshooting data
        #print(card_id)
        #print(ValidCards.values())
        
        # Check if card is valid and react accordingly
        if card_id in ValidCards.values():
            self.accept()            
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Invalid card, press "ok" to try again')

    def connectArduino(self):
        """
        1. Send 'A' to each port with a connection
        2. Set whichever one returns 'card' as the card reader port
        3. Return card reader serial port or error message if there is no card reader
        """
        
        #k = 0
        # Open each port
        for p in serial.tools.list_ports.comports():
            #print("detected device at port", p.device)
        
            # Set up connection and send 'A'
            i = serial.Serial(p.device, 9600, timeout=0.5)
            time.sleep(2) # temporary workaround
            i.write(b'A')
            
            # Read reply
            time.sleep(0.5) # temporary workaround
            j = i.readline()
            
            #print(k, j)
            #k += 1
        
            # Check if reply is 'card' if so this is our card reader
            if j == b'card\r\n':
                # Therefore set ser to this port
                ser = i
                print('found card reader')
                break
            else:
                i.close()
        try:
            return ser
        except:
            raise Exception('Card Reader not plugged in')

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    login = Login()

    if login.exec_() == QtWidgets.QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())