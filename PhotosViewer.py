# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImportPhotos
                                 A QGIS plugin
 Import photos jpegs
                              -------------------
        begin                : 2018-08-27
        git sha              : $Format:%H$
        copyright            : (C) 2018 by KIOS Research Center
        email                : mariosmsk@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QVBoxLayout, QHBoxLayout, QWidget, \
    QLineEdit, QLabel, QSizePolicy, QPushButton, QFrame)
from PyQt5.QtCore import (Qt, pyqtSignal, QRectF, QRect, QSize)
from PyQt5.QtGui import (QPainterPath, QIcon, QPixmap, QImage)
import os.path

try:
    # qgis 3
    from qgis.utils import Qgis
except:
    pass


class PhotosViewer(QGraphicsView):
    afterLeftClick = pyqtSignal(float, float)
    afterLeftClickReleased = pyqtSignal(float, float)
    afterDoubleClick = pyqtSignal(float, float)
    keyPressed = pyqtSignal(int)

    def __init__(self, selfwindow):
        QGraphicsView.__init__(self)

        self.selfwindow = selfwindow
        self.panSelect = False
        self.zoomSelect = False
        self.rotate_value = 0
        self.rotate_azimuth_value = 0

        self.zoom_data = []
        size = 36
        self.scene = QGraphicsScene()
        self.leftClick = QPushButton(self)
        self.leftClick.setIcon(QIcon(self.selfwindow.path+'//svg//arrowLeft.png'))
        self.leftClick.clicked.connect(self.selfwindow.leftClickButton)
        self.leftClick.setToolTip('Show previous photo')
        self.leftClick.setStyleSheet("QPushButton{background: transparent;}")
        self.leftClick.setIconSize(QSize(size, size))
        self.leftClick.setFocusPolicy(Qt.NoFocus)

        self.rightClick = QPushButton(self)
        self.rightClick.setIcon(QIcon(self.selfwindow.path+'//svg//arrowRight.png'))
        self.rightClick.clicked.connect(self.selfwindow.rightClickButton)
        self.rightClick.setToolTip('Show next photo')
        self.rightClick.setStyleSheet("QPushButton{background: transparent;}")
        self.rightClick.setIconSize(QSize(size, size))
        self.rightClick.setFocusPolicy(Qt.NoFocus)

        self.setScene(self.scene)
        self.setMouseTracking(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)

    def mousePressEvent(self, event):
        sc_pos = self.mapToScene(event.pos())
        if self.panSelect:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        if self.zoomSelect:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        self.afterLeftClick.emit(sc_pos.x(), sc_pos.y())
        QGraphicsView.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        sc_pos = self.mapToScene(event.pos())
        if self.zoomSelect or self.panSelect:
            self.zoom_data = []
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.afterDoubleClick.emit(sc_pos.x(), sc_pos.y())
        QGraphicsView.mouseDoubleClickEvent(self, event)

    def mouseReleaseEvent(self, event):
        QGraphicsView.mouseReleaseEvent(self, event)
        sc_pos = self.mapToScene(event.pos())
        if self.zoomSelect:
            view_bb = self.sceneRect()
            if self.zoom_data:
                view_bb = self.zoom_data
            selection_bb = self.scene.selectionArea().boundingRect().intersected(view_bb)
            self.scene.setSelectionArea(QPainterPath())
            if selection_bb.isValid() and (selection_bb != view_bb):
                self.zoom_data = selection_bb
                self.fitInView(self.zoom_data, Qt.KeepAspectRatio)
        self.setDragMode(QGraphicsView.NoDrag)
        self.afterLeftClickReleased.emit(sc_pos.x(), sc_pos.y())

    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        loc = self.viewport().geometry()
        newloc =  list(loc.getRect())
        newloc[0] = newloc[0] # x
        newloc[1] = newloc[3]/2.2 # y
        newloc[2] = newloc[2]/5 # width
        newloc[3] = newloc[3]/5 # height
        self.leftClick.setGeometry(QRect(newloc[0], newloc[1], newloc[2], newloc[3]))
        newloc =  list(loc.getRect())
        newloc[0] = newloc[2] - newloc[2]/5 # x
        newloc[1] = newloc[3]/2.2 # y
        newloc[2] = newloc[2]/5 # width
        newloc[3] = newloc[3]/5 # height
        self.rightClick.setGeometry(QRect(newloc[0], newloc[1], newloc[2], newloc[3]))

        # Fix rotate for the next photo
        self.rotate(-self.rotate_value)
        self.rotate_value = 0

        # Fix azimuth rotate for the next photo
        self.rotate(-self.rotate_azimuth_value)
        self.rotate_azimuth_value = 0

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Right:
            self.selfwindow.drawSelf.featureIndex = self.selfwindow.drawSelf.featureIndex+1

            if self.selfwindow.drawSelf.featureIndex > len(self.selfwindow.allpictures)-1:
                self.selfwindow.drawSelf.featureIndex = 0
            self.selfwindow.updateWindow()

        if e.key() == Qt.Key_Left:
            self.selfwindow.drawSelf.featureIndex = self.selfwindow.drawSelf.featureIndex - 1

            if self.selfwindow.drawSelf.featureIndex < 0:
                self.selfwindow.drawSelf.featureIndex = len(self.selfwindow.allpictures)-1
            self.selfwindow.updateWindow()

        if e.key() == Qt.Key_Escape:
            if self.selfwindow.isFullScreen():
                self.selfwindow.showMaximized()
                return

        if e.key() == Qt.Key_F11:
            if self.selfwindow.isFullScreen():
                self.selfwindow.showMaximized()
            else:
                self.selfwindow.showFullScreen()

        if e.key() == Qt.Key_Escape:
            self.selfwindow.close()


class PhotoWindow(QWidget):
    def __init__(self, drawSelf):
        super(PhotoWindow, self).__init__()
        self.drawSelf = drawSelf
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.viewer = PhotosViewer(self)

        ## Update for photo
        self.allpictures = []
        self.allpicturesdates = []
        self.allpicturestimes = []
        self.allpicturesImpath= []
        self.allpicturesAzimuth=[]
        for i, f in enumerate(self.drawSelf.layerActive.getFeatures()):
            if 'PATH' in self.drawSelf.fields:
                imPath = f.attributes()[f.fieldNameIndex('Path')]
            elif 'PHOTO' in self.drawSelf.fields :
                imPath = f.attributes()[f.fieldNameIndex('photo')]
            else:
                imPath = ''
            try:
                dateTrue = str(f.attributes()[f.fieldNameIndex('Date')].toString('yyyy-MM-dd'))
            except:
                dateTrue = str(f.attributes()[f.fieldNameIndex('Date')])
            try:
                timeTrue = str(f.attributes()[f.fieldNameIndex('Time')].toString('hh:mm:ss'))
            except:
                timeTrue = str(f.attributes()[f.fieldNameIndex('Time')])

            Azimuth = f.attributes()[f.fieldNameIndex('Azimuth')]
            self.allpictures.append(f.attributes()[f.fieldNameIndex('Name')])
            self.allpicturesdates.append(dateTrue)
            self.allpicturestimes.append(timeTrue)
            self.allpicturesImpath.append(imPath)
            self.allpicturesAzimuth.append(Azimuth)

        ######################################################################################

        self.setWindowTitle('Photo')
        #self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(self.path + "//icon.png"))

        self.infoPhoto1 = QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.infoPhoto1.setSizePolicy(sizePolicy)
        self.infoPhoto1.setFrameShape(QFrame.Box)

        self.infoPhoto2 = QLabel(self)
        self.infoPhoto2.setSizePolicy(sizePolicy)
        self.infoPhoto2.setFrameShape(QFrame.Box)

        self.infoPhoto3 = QLabel(self)
        self.infoPhoto3.setSizePolicy(sizePolicy)
        self.infoPhoto3.setFrameShape(QFrame.Box)

        self.extent = QPushButton(self)
        self.extent.setSizePolicy(sizePolicy)
        self.extent.setIcon(QIcon(self.path + '//svg//mActionZoomFullExtent.svg'))
        self.extent.clicked.connect(self.extentbutton)

        self.zoom = QPushButton(self)
        self.zoom.setSizePolicy(sizePolicy)
        self.zoom.setIcon(QIcon(self.path + '//svg//method-draw-image.svg'))
        self.zoom.clicked.connect(self.zoombutton)

        self.pan = QPushButton(self)
        self.pan.setSizePolicy(sizePolicy)
        self.pan.setIcon(QIcon(self.path + '//svg//mActionPan.svg'))
        self.pan.clicked.connect(self.panbutton)

        self.zoom_to_select = QPushButton(self)
        self.zoom_to_select.setSizePolicy(sizePolicy)
        self.zoom_to_select.setIcon(QIcon(self.path + '//svg//mActionZoomToSelected.svg'))
        self.zoom_to_select.clicked.connect(self.zoom_to_selectbutton)

        self.rotate_option = QPushButton(self)
        self.rotate_option.setSizePolicy(sizePolicy)
        self.rotate_option.setIcon(QIcon(self.path + '//svg//rotate.png'))
        self.rotate_option.clicked.connect(self.rotatebutton)

        self.rotate_azimuth = QPushButton(self)
        self.rotate_azimuth.setSizePolicy(sizePolicy)
        self.rotate_azimuth.setIcon(QIcon(self.path + '//svg//tonorth.png'))
        self.rotate_azimuth.clicked.connect(self.rotate_azimuthbutton)

        # Add tips on buttons
        self.extent.setToolTip('Extent photo')
        self.zoom.setToolTip('Select area to zoom')
        self.pan.setToolTip('Pan')
        self.zoom_to_select.setToolTip('Zoom to selected photo')
        self.rotate_option.setToolTip('Rotate 45°')
        self.rotate_azimuth.setToolTip('Rotate to azimuth')

        # Arrange layout
        VBlayout = QVBoxLayout(self)
        HBlayout = QHBoxLayout()
        HBlayout2 = QHBoxLayout()
        HBlayout2.addWidget(self.viewer)
        HBlayout.setAlignment(Qt.AlignCenter)
        HBlayout.addWidget(self.infoPhoto1)
        HBlayout.addWidget(self.infoPhoto2)
        HBlayout.addWidget(self.infoPhoto3)
        HBlayout.addWidget(self.extent)
        HBlayout.addWidget(self.zoom)
        HBlayout.addWidget(self.pan)
        HBlayout.addWidget(self.rotate_option)
        HBlayout.addWidget(self.rotate_azimuth)
        HBlayout.addWidget(self.zoom_to_select)

        VBlayout.addLayout(HBlayout2)
        VBlayout.addLayout(HBlayout)

    def leftClickButton(self):
        self.drawSelf.featureIndex = self.drawSelf.featureIndex - 1
        if self.drawSelf.featureIndex < 0:
            self.drawSelf.featureIndex = len(self.allpictures) - 1
        self.updateWindow()

    def rightClickButton(self):
        self.drawSelf.featureIndex = self.drawSelf.featureIndex + 1
        if self.drawSelf.featureIndex > len(self.allpictures) - 1:
            self.drawSelf.featureIndex = 0
        self.updateWindow()

    def updateWindow(self):
        imPath = self.allpicturesImpath[self.drawSelf.featureIndex]
        self.viewer.scene.clear()
        pixmap = QPixmap.fromImage(QImage(imPath))
        self.viewer.scene.addPixmap(pixmap)
        self.viewer.setSceneRect(QRectF(pixmap.rect()))
        if Qgis.QGIS_VERSION >= '3.0':
            self.drawSelf.layerActive.selectByIds([self.drawSelf.featureIndex])
        else:
            self.drawSelf.layerActive.setSelectedFeatures([self.drawSelf.featureIndex])

        self.viewer.resizeEvent([])
        self.extentbutton()
        self.infoPhoto1.setText(
            'Date: ' + self.allpicturesdates[self.drawSelf.featureIndex])
        self.infoPhoto2.setText(
            'Time: ' + self.allpicturestimes[self.drawSelf.featureIndex])
        self.infoPhoto3.setText('Layer: ' + self.drawSelf.layerActiveName)

        value = self.allpicturesAzimuth[self.drawSelf.featureIndex]
        if type(value) is float:
            if value > 0:
                self.rotate_azimuth.setEnabled(True)
                return
        self.rotate_azimuth.setEnabled(False)

    def rotatebutton(self):
        self.viewer.rotate(90)
        self.viewer.rotate_value = self.viewer.rotate_value + 90
        if self.viewer.rotate_value == 360:
            self.viewer.rotate_value = 0

    def rotate_azimuthbutton(self):
        self.viewer.rotate(self.allpicturesAzimuth[self.drawSelf.featureIndex])
        self.viewer.rotate_azimuth_value = self.allpicturesAzimuth[self.drawSelf.featureIndex]

    def zoom_to_selectbutton(self):
        self.drawSelf.iface.actionZoomToSelected().trigger()

    def panbutton(self):
        self.viewer.panSelect = True
        self.viewer.zoomSelect = False
        self.viewer.setCursor(Qt.OpenHandCursor)
        self.viewer.setDragMode(QGraphicsView.ScrollHandDrag)

    def zoombutton(self):
        self.viewer.panSelect = False
        self.viewer.zoomSelect = True
        self.viewer.setCursor(Qt.CrossCursor)
        self.viewer.setDragMode(QGraphicsView.RubberBandDrag)

    def extentbutton(self):
        self.viewer.zoom_data = []
        self.viewer.fitInView(self.viewer.sceneRect(), Qt.KeepAspectRatio)
        self.viewer.panSelect = False
        self.viewer.zoomSelect = False
        self.viewer.setCursor(Qt.ArrowCursor)
        self.viewer.setDragMode(QGraphicsView.NoDrag)