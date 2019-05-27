class MedicalData(object):
    def __init__(self, label, active=True):
        self._label = label
        self._active = active
        self._data = []

    @property
    def label(self):
        return label

    @property
    def active(self):
        return active

    @property
    def data(self):
        return data

    def setActive(self, active):
        self.active = active

    def appendData(self, data):
        self.data.append(data)

    def clearData(self):
        self.data = []
