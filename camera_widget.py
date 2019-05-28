import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
#from models import Camera
import pyqtgraph
from pyqtgraph import ImageItem, ImageView
from PyQt5.QtCore import Qt, QThread, QTimer
import numpy as np
import cv2


class Camera:
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
        self.last_frame = np.zeros((1,1))

    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)

    def get_frame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame

    def acquire_movie(self, num_frames):
        movie = []
        for _ in range(num_frames):
            movie.append(self.get_frame())
        return movie

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
        
        self.setGeometry(300, 300, 600, 480)
        self.setWindowTitle('Camera')    
        self.show()
        
        self.camera = Camera(1)
        self.camera.initialize()
        self.framerate = 30
        self.captured_frame = None 

        #temporarily align images in vertical format
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self)
        
        #define start feed button
        self.start_temp = QPushButton('Start Feed', self.central_widget)
        self.start_temp.clicked.connect(self.start_feed)
        self.layout.addWidget(self.start_temp) 
        
        #define data capture button
        self.capturebutton = QPushButton('Capture', self.central_widget)
        self.capturebutton.clicked.connect(self.capture_frame)
        self.layout.addWidget(self.capturebutton)
        
        #define image view widget
        self.image_view = ImageView()
        self.image_view.ui.histogram.hide()
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        self.layout.addWidget(self.image_view)
        
        #Definie timer
        self.update_timer=QTimer()
        self.update_timer.timeout.connect(self.update_image)
        
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
        frame = self.camera.get_frame()
        self.image_view.setImage(frame.T)
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
