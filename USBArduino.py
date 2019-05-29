from MedicalArduino import MedicalArduino

import json
import time

class USBArduino(MedicalArduino):
    def __init__(self, ser, header_dict):
        """
        Interpret and store the decoded json dictionary from the handshake header file.
        Start an empty data tracking dictionary, according to data_labels.
        """
        super().__init__(header_dict)
        self.ser = ser
    
    def sample(self):
        """
        Called by the GUI clock at regular intervals according to self.sampling_rate.
        Send a data request signal to the Arduino and interpret the json output.
        Return the entire history of all recorded data (regardless of whether or not a
        null value was read or if the data series are not 'checked' in the GUI).
        """
        print("sampling USB arduino")
        self.ser.write(b'B')
        time.sleep(0.01)
        self.ser.flush()
        while True:
            j = self.ser.readline()
            if j.endswith(b'\n'):
                break
        data = json.loads(j.decode())
        if not any(x == 0 for x in data.values()):
            for label in self.data_labels:
                self.data[label].append(data[label])
            #self.data["time"].append(time.time() - self.start)
        print(data)
        #print(self.data)
        #return self.data

    def close(self):
        self.ser.close()
