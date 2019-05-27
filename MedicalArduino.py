from abc import ABC, abstractmethod

import json
import time

class MedicalArduino(ABC):
    def __init__(self, header_dict):
        """
        Interpret and store the decoded json dictionary from the handshake header file.
        Start an empty data tracking dictionary, according to data_labels.
        """
        self.name           = header_dict["name"]
        self.data_labels    = header_dict["labels"]
        #self.data_types     = header_dict["data_types"]
        self.data_units     = {label: header_dict["data_units"][i] for i, label in enumerate(self.data_labels)}
        self.data_ranges    = header_dict["data_range"]
        self.sampling_rate  = header_dict["sampling_rate"]
        self.active_data    = {label: True for label in self.data_labels}
        self.data = {label: [] for label in self.data_labels}#["time"] + self.data_labels}
        self.start = time.time()
    
    @abstractmethod
    def sample(self):
        """
        Called by the GUI clock at regular intervals according to self.sampling_rate.
        Send a data request signal to the Arduino and interpret the json output.
        Return the entire history of all recorded data (regardless of whether or not a
        null value was read or if the data series are not 'checked' in the GUI).
        """
        pass

    @abstractmethod
    def close(self):
        pass
