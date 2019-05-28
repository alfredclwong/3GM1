from PyQt5 import QtWidgets
from MainWindow import MainWindow
import sys
import serial
import time

# This dictionary shows admin and user cards
ValidCards = {'admin':b'78 , 242 , 84 , 78\r\n'}

class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        
        # Set up login gui
        self.notification = QtWidgets.QLabel('Press "Scan" and then present your Security Card')
        self.buttonScan = QtWidgets.QPushButton('Scan', self)
        self.buttonScan.clicked.connect(self.scanAndCheck)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.notification)
        layout.addWidget(self.buttonScan)

    def checkForCards(self):
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
        return card_id
        
    # Pressing 'scan' links here, it finds the correct arduino
    # and then waits for a card number and checks it
    def scanAndCheck(self):
        # Call checkForCards
        card_id = self.checkForCards()
        
        # Optional troubleshooting data
        #print(card_id)
        #print(ValidCards.values())
        
        # Check if card is valid
        if card_id in ValidCards.values():
            self.accept()            
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Invalid card, press "ok" to try again')

    # This scans ports and sends 'A' to find out what they are
    # If the arduino returns 'card' we set that port as 'ser
    def connectArduino(self):
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