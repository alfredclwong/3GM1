from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import* #QTabWidget, QMainWindow, QPushButton, QCheckBox, QGridLayout, QHBoxLayout, QFormLayout, QAction, QApplication, QWidget,QLabel
from PyQt5.QtGui import QIcon, QPixmap

import pyqtgraph as pg
import random
import numpy as np
import time
import serial
import serial.tools.list_ports
import json
import time
import sys

#class Example(QWidget):
class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
        
    def initUI(self):
        
        #set up tabs object
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300,200)
        self.tabs.addTab(self.tab1,"Test")
        self.tabs.addTab(self.tab2,"File upload")
        
        self.tab1UI()
        self.tab2UI()
        
        self.setCentralWidget(self.tabs)
        
        ###add status bar###
        self.statusBar = self.statusBar()
        
        ###set window parameters###
        self.setGeometry(600, 500, 500, 500)
        self.setWindowTitle('Homepage')  
        self.show()
        
    def tab1UI(self):
        ###define dropdown menu to display images in directory###
        imagedrop=QtGui.QToolButton()
        dropdownSizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                               QtGui.QSizePolicy.Fixed)
        imagedrop.setSizePolicy(dropdownSizePolicy)
        imagedrop.setText('Select image')
        self.imagemenu = QtGui.QMenu()
        imagedrop.setMenu(self.imagemenu)
        imagedrop.setPopupMode(QtGui.QToolButton.InstantPopup)
        
        ###define pushbutton to intiate detection###
        detect=QPushButton("Detect")
        detect.clicked.connect(self.detectUSB)
        
        ###define top row###
        top=QHBoxLayout()
        top.addWidget(imagedrop)
        top.addWidget(detect)
        
        ###define image label###
        self.image = QLabel()
        self.pixmap = QPixmap('image_test.jpg')
        self.pixmap = self.pixmap.scaled(300, 300, QtCore.Qt.KeepAspectRatio)
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.image.setPixmap(self.pixmap)
        
        ###define middle row###
        mid=QHBoxLayout()
        mid.addWidget(self.image)
        
        ###define grid and layout###
        grid = QGridLayout()
        grid.addLayout(top,0,0)
        grid.addLayout(mid,1,0)
        #self.tab1.layout = QVBoxLayout(self)
        self.tab1.setLayout(grid)
        
    def tab2UI(self):
        layout = QVBoxLayout()
        detect2=QPushButton("Detect")
        layout.addWidget(detect2)
        self.tab2.setLayout(layout)
        
        
    def showimage(self):
        #sender=self.sender()
        action=self.sender()
        self.statusBar.showMessage(action.text() + ' selected')
        #print(type(action.text()))
        self.pixmap = QPixmap(action.text())
        self.pixmap = self.pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio)
        self.image.setPixmap(self.pixmap)
        
        
    def detectUSB(self):
        sender=self.sender()
        #self.statusBar.showMessage(sender.text() + ' was pressed')
        self.statusBar.showMessage(sender.text() + ' button pressed')
        self.imagemenu.clear()
        usb=['image_test.jpg', 'image_test2.jpg']
        for file in usb:
           self.imagemenu.addAction(file, self.showimage)
        
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        
    


if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)
    ex=Example()
    ex.show()
    sys.exit(app.exec_())