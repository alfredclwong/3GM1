from MedicalArduino import MedicalArduino

import json
import time

class BluetoothArduino(MedicalArduino):
    def __init__(self, sock, header_dict):
        """
        Interpret and store the decoded json dictionary from the handshake header file.
        Start an empty data tracking dictionary, according to data_labels.
        """
        super().__init__(header_dict)
        self.sock = sock
    
    def sample(self):
        """
        Called by the GUI clock at regular intervals according to self.sampling_rate.        
        Send a data request signal to the Arduino and interpret the json output.
        Return the entire history of all recorded data (regardless of whether or not a
        null value was read or if the data series are not 'checked' in the GUI).
        """
        print("sampling bluetooth arduino")
        self.sock.send(b'B')
        data = b''
        '''while True:
            data += self.sock.recv(1024)
            if data.endswith(b'\n'):
                break
        '''
        #self.sock.settimeout(2)
        try:
            while True:
                d = self.sock.recv(255)
                data += d
                if d.find(b'\n') != -1:
                    break
        except Exception as err:
            print(err)
            pass
        print(data)
        data = json.loads(data.decode())
        if not any(x == 0 for x in data.values()):
            for label in self.data_labels:
                self.data[label].append(data[label])
            #self.data["time"].append(time.time() - self.start)
        print(data)
        #print(self.data)
        #return self.data

    def close(self):
        self.sock.close()
