import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QLabel, QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
#from models import Camera
from PyQt5.QtCore import Qt, QThread, QTimer
import numpy as np
import cv2
import time


class Camera:
    
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
        self.last_frame = np.zeros((1,1))

    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)
        self.initialized = True

    def get_frame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame

    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def get_brightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    def close_camera(self):
        self.cap.release()

    def __str__(self):
        return 'OpenCV Camera {}'.format(self.cam_num)
    
    

class camWidget(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
        
    def initUI(self):  
        """
        Sets up camera and Capture button objects and puts them in layout
        Also sets up timer
        """
        
        self.setGeometry(300, 300, 600, 300)
        
        self.camera = Camera(0)
        self.framerate = 30
        self.captured_frame = None 
        
        #temporarily align images in vertical format
        self.central_widget = QWidget()
        self.layout = QHBoxLayout(self)
        
        self.label = QLabel(self)
        self.layout.addWidget(self.label)
        self.buttonlayout = QVBoxLayout()

        
        #define data capture button
        self.capturebutton = QPushButton('Capture', self.central_widget)
        self.capturebutton.clicked.connect(self.capture_frame)
        self.capturebutton.setMinimumHeight(50)
        self.capturebutton.setMaximumWidth(100)
        self.buttonlayout.addWidget(self.capturebutton)
        
        self.buttonlayout.addStretch(1) #shift buttons to top
        self.layout.addLayout(self.buttonlayout)
        
        #Definie timer
        self.update_timer=QTimer()
        self.update_timer.timeout.connect(self.update_image)
    
    def setup(self):
        """
        initialises sensor and starts timer
        """
        self.camera.initialize()
        self.start_feed()
        
    
    def start_feed(self):
        """
        Called upon loading camera or when image retaken
        Starts timer with specified framerate parameter
        """
        self.update_timer.start(self.framerate)
        
    def capture_frame(self):
        """
        Called by 'Capture' button
        1. Resets text on capture button to 'Retake', stops timer and stores frame
        2. OR if 'Retake' - restarts timer and changes text back
        
        """
        if (self.sender().text() == 'Capture') and (self.update_timer.isActive()):
            self.capturebutton.setText('Retake')
            self.update_timer.stop()
            self.captured_frame = self.camera.last_frame.T  #<class 'numpy.ndarray'>
            cv2.imwrite('captured_frame.jpg',self.captured_frame.T)
        elif self.sender().text() == 'Retake':
            self.start_feed()
            self.capturebutton.setText('Capture')
    
    def update_image(self):
        """
        Called by QTimer at regular timeout signals
        """
        try:
            frame = self.camera.get_frame()
            rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except: #catches error of crashing when camera disconnected
            print("Camera not detected")
            self.update_timer.stop()
            self.camera.close_camera()
            self.camera.cap = None
            self.captured_frame = None
            print("Camera closed")
            return
        #self.image_view.setImage(frame.T)
        convertToQtFormat = QtGui.QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0],
                                         QtGui.QImage.Format_RGB888)
        convertToQtFormat = QtGui.QPixmap.fromImage(convertToQtFormat)
        pixmap = QtGui.QPixmap(convertToQtFormat)
        resizeImage = pixmap.scaled(400, 300, QtCore.Qt.KeepAspectRatio)
        QApplication.processEvents()
        self.label.setPixmap(resizeImage)
            
            
        

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
