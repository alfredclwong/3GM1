import json
import time

class MedicalArduino:
    def __init__(self, ser, header_dict, plot_item):
        """
        
        """
        self.ser = ser
        
        self.name           = header_dict["name"]
        self.data_labels    = header_dict["labels"]
        #self.data_types     = header_dict["data_types"]
        #self.data_units     = header_dict["data_units"]
        self.data_ranges    = header_dict["data_range"]
        self.sampling_rate  = header_dict["sampling_rate"]
        self.data = {label: [] for label in self.data_labels}#["time"] + self.data_labels}
        self.start = time.time()
        
        self.curves = {}
        for label in self.data_labels:
            self.curves[label] = plot_item.plot(name=label)
    
    def sample(self):
        """
        Called by the GUI clock at regular intervals according to self.sampling_rate.        
        Send a data request signal to the Arduino and interpret the json output.
        """
        self.ser.write(b'B')
        time.sleep(0.1)
        self.ser.flush()
        while True:
            j = self.ser.readline()
            if j.endswith(b'\n'):
                break
        data = json.loads(j)
        if any(x == 0 for x in data.values()):
            return
        #self.data["time"].append(time.time() - self.start)
        for label in self.data_labels:
            self.data[label].append(data[label])
        print(data)
        
        for label in self.data_labels:
            self.curves[label].setData(self.data[label])
