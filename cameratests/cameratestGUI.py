import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication
from models import Camera    
from pyqtgraph import ImageView
import numpy as np


class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):  
        
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Camera')    
        self.show()
        
        
        self.camera = Camera(1)
        self.camera.initialize()

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        
        #define data capture button
        self.button_frame = QPushButton('Capture', self.central_widget)
        self.button_frame.clicked.connect(self.update_image)
        self.layout.addWidget(self.button_frame) 
        
        #define image view widget
        self.image_view = ImageView()
        self.layout.addWidget(self.image_view)
        
        #add central widget
        self.setCentralWidget(self.central_widget)

        
    def update_image(self):
        frame = self.camera.get_frame()
        self.image_view.setImage(frame.T)
        print('Maximum in frame: {}, Minimum in frame: {}'.format(np.max(frame), np.min(frame)))
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
