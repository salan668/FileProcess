"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""

import pyqtgraph as pg


class CustomViewBox(pg.ViewBox):
    def __init__(self, parent=None):
        pg.ViewBox.__init__(self)
        self._imgview = parent
        self.setMouseMode(self.PanMode)
        self._linkimgviewlist = None
        self.InitParam()

    def InitParam(self):
        self._roidraw_pos = []
        self._roidraw = self.CreateROIDraw()
        #         self._curve = pg.plot()
        #         self.addItem(self._curve)
        self._roilist = []
        self._line = []  # ROI line drawer, containing multiple ROIs

        self._roitype = None

    #         self._roidraw_start = None

    def CreateROIDraw(self):
        if hasattr(self, '_roidraw'):
            self.removeItem(self._roidraw)
        #         roidraw = myPolyLineROI([], pen=(0, 155, 155),  movable=False, closed=False)
        _pen = QtGui.QPen(QtGui.QColor(160, 160, 245))
        try:
            #             datasize = self._imgview._data.shape[0]
            #             penwidth = int(datasize / 100)
            #             if penwidth == 0: penwidth = 1
            #             _pen.setWidth(penwidth)
            # modified due to wide pen when zoom in
            _pen.setWidth(1)
        except:
            _pen.setWidth(1)
        roidraw = myPolyLineROI([], mypen=_pen, movable=False, closed=False)
        roidraw.setPoints(self._roidraw_pos, closed=False)
        self.addItem(roidraw)
        return roidraw

    def setLinkImageViewForViewBox(self, imgviewlist_orig):
        imgviewlist = imgviewlist_orig.copy()
        imgviewlist.pop(imgviewlist.index(self._imgview))
        self._linkimgviewlist = imgviewlist

    ## reimplement wheelEvent, slice rolling
    def wheelEvent(self, ev, axis=None):
        if ev.delta() > 0:
            sliceoffset = 1
        elif ev.delta() < 0:
            sliceoffset = -1
        else:
            return
        self.MoveSlice(sliceoffset)

    def MoveSlice(self, sliceoffset=0):
        try:
            if self._imgview.isDataLoaded():
                slicenum = self._imgview._data.shape[2]
                curslice_index = self._imgview.currentIndex + sliceoffset
                if (curslice_index >= slicenum) or (curslice_index < 0): return

                # move slice in current ImageView
                imgview = self._imgview
                imgview.jumpFrames(sliceoffset)
                self.SetROI2Draw()

                # move slice in linked ImageView
                if self._linkimgviewlist != None:
                    for limgview in self._linkimgviewlist:
                        slice_offset = imgview.currentIndex - limgview.currentIndex
                        if limgview.isDataLoaded():
                            limgview.jumpFrames(slice_offset)
                            limgview.getView().SetROI2Draw()
            else:  # update each imgview only, not move
                if self._linkimgviewlist != None:
                    for limgview in self._linkimgviewlist:
                        if limgview.isDataLoaded():
                            limgview.jumpFrames(0)
                            limgview.getView().SetROI2Draw()
        except:
            print('MoveSlice failed')

    def Move2Slice(self, sliceindex):
        slicenum = self._imgview._data.shape[2]
        if (sliceindex >= 0) and (sliceindex < slicenum):
            self._imgview.currentIndex = sliceindex
            self.MoveSlice(0)

    def mouseClickEvent(self, ev):
        if self._imgview.isROIDrawOn:
            if ev.button() == Qt.LeftButton:
                if self._roitype == 'Point':
                    autoNewROIOpt = self._imgview.parent()._roibar._checkbox_autoNewROI.isChecked()
                    roicontroller = self._imgview._roicontroller
                    if (
                            roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                        roicontroller.addNewEmptyROI()
                    self.createROIbyPointClick(ev.pos())
                    self._imgview.parent()._roibar.UpdateROI()
                else:
                    self.addROIPoint(ev.pos(), closed=False)
            #                 self._roidraw_start = True
            elif ev.button() == Qt.RightButton:
                self.closeROIPoint()
                self.createROI()
                #                 self.putROIinList()
                self.cancelROIDraw()
        elif self._imgview.isCurvePlotOn == True:
            self.PlotDataCurve(ev.pos())
        if ev.button() == Qt.RightButton:
            # disable right click menu display
            pass
        else:
            pg.ViewBox.mouseClickEvent(self, ev)
            self.showPosInfo(ev)

        self.SetCurAxe()

    def SetCurAxe(self):
        if self._imgview._parent._curAxe == self._imgview: return
        self.UpdateImgLevelView()

        if self._imgview._parent._isHideAxeFrame: return
        self.UpdateAxeBorder()

    def UpdateAxeBorder(self):
        for axe in self._imgview._parent._imgaxes:
            axe.setStyleSheet("border: 1px solid black;")
        self._imgview._parent._curAxe = self._imgview
        self._imgview._parent._curAxe.setStyleSheet("border: 1px solid blue;")

    def mouseDoubleClickEvent(self, ev):
        print('Double clicked')
        if ev.button() == Qt.LeftButton:
            self._imgview.SetInitGreyLevel()
        elif ev.button() == Qt.RightButton:
            self.autoRange()

        pg.ViewBox.mouseDoubleClickEvent(self, ev)

    def PlotDataCurve(self, evpos):
        pos = self.getPos(evpos)
        if hasattr(self._imgview.parent()._parent, 'PlotCurve'):
            self._imgview.parent()._parent.PlotCurve(pos)

    def showPosInfo(self, ev):
        if not isArrayData(self._imgview._data): return
        pos = ev.pos()
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.mapSceneToView(pos)
            pos3D = [int(mousePoint.y()), int(mousePoint.x()), int(self._imgview.currentIndex)]

            xsize, ysize = self._imgview._data.shape[:2]
            if (pos3D[0] >= xsize) or (pos3D[1] >= ysize) or (pos3D[0] < 0) or (pos3D[1] < 0): return
            posdata = self._imgview.getCurSlice()[pos3D[0], pos3D[1]]
            if posdata.dtype == int:
                posdata = str(posdata)
            else:
                posdata = str(round(posdata, 3))
            self._imgview.parent()._imgInfoView._imgPosView.setText(
                'X:' + str(pos3D[0]) + ',  Y:' + str(pos3D[1]) + ',  Z:' + str(pos3D[2])
                + ',  (' + posdata + ')')

    def mouseDragEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            if self._imgview.isMouseModeMoveOn:
                # print(ev.pos())
                pg.ViewBox.mouseDragEvent(self, ev)
            elif self._imgview.isROIDrawOn:  # and self._roidraw_start:
                ev.accept()
                self.addROIPoint(ev.pos(), closed=False)
            else:
                self.SetGrayLevel(ev)

        else:
            if self._imgview.isROIDrawOn: pass
            pg.ViewBox.mouseDragEvent(self, ev)
        self.SetCurAxe()

    def addROIPoint(self, pos, closed=False):
        if self.sceneBoundingRect().contains(pos):
            # first get pos when ROI handles was dragged
            #             self._roidraw_pos = self.getROIDrawPos()

            # add pos of the new click
            mousePoint = self.mapSceneToView(pos)
            pos = [int(mousePoint.x()), int(mousePoint.y())]
            lastpos = self._roidraw.getLastHandlePos()
            #             if self._roidraw_pos != []:
            #                 lastpos = self._roidraw_pos[-1]c
            #             if type(self._imgview._data)!= list:
            #                 datasize0 = self._imgview._data.shape[0]
            #             else:
            #                 datasize0 = self._imgview._data[0].shape[0]
            if lastpos != []:
                if (np.abs(lastpos[0] - pos[0]) + np.abs(lastpos[1] - pos[1])) > 2:  # int(datasize0/100):# 10:
                    self._roidraw_pos.append(pos)
                    # self._roidraw.setPoints(self._roidraw_pos,closed)
                    self._roidraw.addPoint(pos, closed)
            else:
                self._roidraw_pos.append(pos)
                # self._roidraw.setPoints(self._roidraw_pos,closed)
                self._roidraw.addPoint(pos, closed)

    def getROIDrawPos(self):
        pos_list = self._roidraw.getLocalHandlePositions()

        roidraw_pos = []
        for i in range(len(pos_list)):
            roidraw_pos.append([pos_list[i][1].x(), pos_list[i][1].y()])
        return roidraw_pos

    def closeROIPoint(self):
        self._roidraw.closePoint()
        self._roidraw_pos = self.getROIDrawPos()

    #         self._roidraw.addPoint(self._roidraw_pos,closed=True)

    def setDrawROIType(self, roitype):
        for limgview in self._linkimgviewlist:
            limgview.getView()._roitype = roitype
        self._roitype = roitype

    def createROIbyPointClick(self, evpos):
        roicontroller = self._imgview._roicontroller

        if roicontroller._curROIindex == None:  # when no roi is drawn, first create new ROI
            roicontroller.addNewEmptyROI()
        pad = int(self._imgview.parent()._roibar._commonUI._spinbox_roibypos_size.value())

        pos = self.getPos(evpos)
        # print(pos)
        self._imgview.parent()._curAxe.ROIbyPoint(pos, pad)
        self.MoveSlice(0)

    def getPos(self, evpos):
        curslice = self._imgview.currentIndex
        mousePoint = self.mapSceneToView(evpos)
        #         pos = np.array([int(mousePoint.y()),int(mousePoint.x()), curslice])
        return int(mousePoint.y()), int(mousePoint.x()), curslice

    def createROI(self):
        roitype = self._roitype
        verts = self._roidraw_pos

        if len(verts) < 2: return
        # last point set to the 1st point
        verts.append(verts[0])

        curslice = self._imgview.currentIndex
        roicontroller = self._imgview._roicontroller
        # temporal solution, autoNewROI option is set in ROI UI
        autoNewROIOpt = self._imgview.parent()._roibar._checkbox_autoNewROI.isChecked()

        if roitype == 'NewROI':
            roicontroller.addNewROIByVerts(verts, curslice)
        elif roitype == 'ManualROI':
            if (roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            roicontroller.combineROIByVerts(verts, curslice)
        elif roitype == 'DrawLine':
            if (roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            roicontroller.combineLineByVerts(verts, curslice)
        elif roitype == 'BreastDrawLine':
            if (roicontroller._curROIindex == None):  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            roicontroller.combineLineByVerts(verts, curslice)
        elif roitype == 'ExtendROI':
            roicontroller.combineROIByVerts(verts, curslice)
        elif roitype == 'ReduceROI':
            roicontroller.reduceROIByVerts(verts, curslice)
        #         elif roitype == 'AutoThres':
        #             roicontroller.AddAutoCalMask3D(verts, curslice,self._imgview.getCurImgVol(),isnew=True)
        elif roitype == 'AutoThres':
            if (roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            optionlist = self._imgview.parent()._roibar.getAutoROIoptionlist()
            optionlist += [False, False]  # high/low, isSingleROI, fillhole, convexborder
            Algoption = str(self._imgview.parent()._roibar._commonUI._combobox_autothresAlghOption.currentText())
            roicontroller.AddAutoCalMask3D(verts, curslice, self._imgview.getCurImgVol(),
                                           self._imgview.CalSliceBuffer(verts, curslice), optionlist, Algoption,
                                           isnew=False)
        elif roitype == 'AutoLine':
            if (roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            option = str(self._imgview.parent()._roibar._commonUI._combobox_autothresoption.currentText())
            Algoption = str(self._imgview.parent()._roibar._commonUI._combobox_autothresoption.currentText())
            roicontroller.AddAutoCalMask3DbyLine(verts, curslice, self._imgview.getCurImgVol(),
                                                 self._imgview.CalSliceBuffer(verts, curslice), option, Algoption)
        elif roitype == 'AutoProstate':
            if (roicontroller._curROIindex == None) or autoNewROIOpt:  # when no roi is drawn, first create new ROI
                roicontroller.addNewEmptyROI()
            # optionlist = self._imgview.parent()._roibar.getAutoROIoptionlist()
            optionlist = ['High', True, True, False]  # high/low, isSingleROI, fillhole, convexborder
            Algoption = str(self._imgview.parent()._roibar._commonUI._combobox_autothresAlghOption.currentText())
            roicontroller.AddAutoCalMask3D(verts, curslice, self._imgview.getCurImgVol(),
                                           self._imgview.CalSliceBuffer(verts, curslice), optionlist, Algoption,
                                           isnew=False)
            # roicontroller.AutoSegSubROI(self._imgview.getCurImgVol(),optionlist, Algoption)
        elif roitype == 'RegMask':
            roicontroller.addRegMaskROI(verts)
        elif roitype == 'RegGrow':
            roicontroller.AddRegionGrowMask3D(verts, curslice, self._imgview.getCurImgVol())
        else:
            return
        self.MoveSlice(0)
        # update ROI table and label info
        self._imgview.parent()._roibar.UpdateROI()

    def cancelROIDraw(self):
        #         self._roidraw.clearPoints()
        self._roidraw_pos = []
        self._roidraw = self.CreateROIDraw()

    #     def putROIinList(self):
    #         if len(self._roidraw_pos) > 1: # 2 point is a line, >3 points will be a region
    #             self._roilist.append(self._roidraw_pos)
    #             roipos = np.array(self._roidraw_pos)
    #             curve = pg.ScatterPlotItem(x=roipos[:,0].tolist(), y=roipos[:,1].tolist(),
    #                                    pen='g', brush='g')
    #             self.addItem(curve)

    def SetROI2Draw(self):
        if not self._imgview.isDataLoaded():
            return

        roicontroller = self._imgview._roicontroller
        curROIindex = roicontroller._curROIindex

        if len(roicontroller._ROIpointArray) != 0:
            # draw other ROI
            if len(roicontroller._ROIpointArray) > 0:  # bug here, could be == 1 when only 1 ROI
                for i, roipointarray in enumerate(roicontroller._ROIpointArray):
                    if i > (len(self._line) - 1):
                        self.AddLineDraw()
                    if (i == curROIindex):
                        self._line[i].setSymbol('o', update=False)
                    else:
                        self._line[i].setSymbol('x', update=False)
                    #                         self._line[i].setData(color='b')
                    roiindex = roipointarray[self._imgview.currentIndex]
                    #                     roiindex = self.rescaleRotateVerts(roiindex,inverse=True)
                    self._line[i].setData(roiindex[0], roiindex[1])
        #                 self._previousROInum = len(roicontroller._ROIpointArray)

        # donot show other empty ROI, check the next line if is left
        if len(self._line) > len(roicontroller._ROIpointArray):
            nextline = self._line[len(roicontroller._ROIpointArray)]
            if nextline.getData() != []:
                #         for i in range(len(roicontroller._ROIpointArray), self._previousROInum):
                nextline.setData([], [])

    def AddLineDraw(self):
        linecolor = self._imgview._roicolorlist[len(self._line) % len(self._imgview._roicolorlist)]
        # determine markersize
        if not isArrayData(self._imgview._data) == []:
            dsize = 4
        elif self._imgview._data.shape[0] > 250:
            dsize = 4
        elif self._imgview._data.shape[0] > 150:
            dsize = 5
        else:
            dsize = 6
        # bug fix: add scalex=False, scaley=False to avoid image size rescale after new ROI is drawn
        curve = pg.ScatterPlotItem([],
                                   pen=linecolor, brush=linecolor)
        curve.setSize(dsize)
        self.addItem(curve)
        self._line.append(curve)

    def RemoveLineDraw(self, index):
        if self._line == []: return
        if len(self._line) < index: return
        self.removeItem(self._line[index])
        self._line.pop(index)

    def RemoveAllLineDraw(self):
        for i in range(len(self._line) - 1, -1, -1):
            self.RemoveLineDraw(i)

    def SetGrayLevel(self, ev):
        ev.accept()  ## we accept all buttons
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        self.updateMaxMin(dif)

    def updateMaxMin(self, dif):
        dx = dif[1]
        dy = dif[0]

        if not hasattr(self._imgview, '_winlevel'): return
        winlevel = self._imgview._winlevel + dx * self._imgview._winstep
        winwidth = self._imgview._winwidth + dy * self._imgview._winstep
        #             print [dy, dx]
        if (winwidth > 0):  # & (winlevel > 0):
            self._imgview._winlevel = winlevel
            self._imgview._winwidth = winwidth

            winmin = winlevel - winwidth / 2
            winmax = winlevel + winwidth / 2
            #             if winmin < 0:
            #                 winmin = 0
            #             print([winmin,winmax])
            if (self._imgview._curwinmin != winmin) or (self._imgview._curwinmax != winmax):
                self._imgview.setLevels(winmin, winmax)
                self._imgview._curwinmin = winmin
                self._imgview._curwinmax = winmax
                self._imgview.parent()._imgInfoView._imgMinLevel.setText(str(round(winmin, 2)))
                self._imgview.parent()._imgInfoView._imgMaxLevel.setText(str(round(winmax, 2)))
                # Step: + str(round(self._imgview._winstep,2)))

    def UpdateImgLevelView(self):
        if not hasattr(self._imgview, '_curwinmin'): return
        winmin = self._imgview._curwinmin
        winmax = self._imgview._curwinmax
        self._imgview.parent()._imgInfoView._imgMinLevel.setText(str(round(winmin, 2)))
        self._imgview.parent()._imgInfoView._imgMaxLevel.setText(str(round(winmax, 2)))

    def SetWinMin(self, winmin):
        winmax = self._imgview.parent()._imgInfoView._imgMaxLevel.toPlainText()
        if winmax == '': return
        #         self._imgview._curwinmin = winmin
        winmax = float(winmax)

        self.setWinLevel(winmin, winmax)

    def SetWinMax(self, winmax):
        #         self._imgview._curwinmax = winmax
        winmin = float(self._imgview.parent()._imgInfoView._imgMinLevel.toPlainText())
        self.setWinLevel(winmin, winmax)

    def setWinLevel(self, winmin, winmax):
        self._imgview.setLevels(winmin, winmax)
        winlevel = (winmax + winmin) / 2
        winwidth = (winmax - winmin)
        self._imgview._winlevel = winlevel
        self._imgview._winwidth = winwidth
        self._imgview._curwinmax = winmax
        self._imgview._curwinmin = winmin


class Img2DObjPyQtGraphy(pg.ImageView):
    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, *args):
        if view == None:
            view = CustomViewBox(parent=self)
        pg.ImageView.__init__(self, parent, name, view, imageItem, *args)
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.ui.histogram.hide()
        self.show()

        self._roicolorlist = ['g', 'r', 'b', 'c', 'm', 'y']  # ['g']*10
        self._roicontroller = ROIControllerWithLabel(self)

        self.InitialParam()
        self._parent = parent

        self.setAcceptDrops(True)

    def InitialParam(self):
        # initialize parameter:
        self.isMouseModeMoveOn = False
        self.isCurvePlotOn = False
        self.isROIDrawOn = False

        self._data = []
        self._curdim4 = 0
        self._isColorData = False

        self._datareader = DataReader()


    def LoadFile(self, filepath):
        self.InitialParam()
        result = self._datareader.LoadAllTypeData(filepath)
        if (result == False) or (result == None): return False
        self.LoadDataFromDataReader(self._datareader)

        return True

    def LoadFileFast(self, filepath):
        self.InitialParam()
        result = self._datareader.LoadAllTypeDataFast(filepath)
        if (result == False) or (result == None): return False
        self.LoadDataFromDataReader(self._datareader)

        return True

    def LoadDataFromDataReader(self, datareader):
        self._datareader = datareader
        self.PrepareData(datareader._data, datatitle=datareader._filename, isColorData=datareader._isColorData)

    def LoadData(self, data, datatitle, refdatareader=[]):
        # load data both in self._data and datareader
        # temp modified, refdatareader if =[], not copy datareader
        # if (refdatareader == []) | (data == []): return
        if not isArrayData(data): return
        if refdatareader != []:
            self._datareader = refdatareader
        self._datareader.LoadData(data)
        self.PrepareData(data, datatitle, self._datareader._isColorData)

    def LoadDataNotChangeDataReader(self, data, datatitle):
        self.PrepareData(data, datatitle, self._datareader._isColorData)

    def LoadSitkData(self, sitkimg, datatitle=None, refdatareader=None):
        self._datareader.LoadSitkImg(sitkimg, refdatareader)
        if datatitle == None:
            datatitle = self._filename
        try:
            self.PrepareData(self._datareader._data, datatitle, self._datareader._isColorData)
        except:
            return

    def SetFilename(self, filename):
        self._filename = filename

    def GetFilename(self):
        return self._filename

    def GetImgData(self):
        return self._data

    def GetImgDataCopy(self):
        return self._data.copy()

    #     def SaveData(self):
    #         self._datareader.SaveDicomFolder(self._data)

    def PrepareData(self, data, datatitle, isColorData=False):
        self._data = data
        self._filename = datatitle
        datasize = np.array(self._data.shape)
        self._datasize = datasize
        self._isColorData = isColorData

        ## set image to display
        # if 4D data, select 1st vol
        if (len(data.shape) == 4) and (
        not ((data.shape[3] == 3) and isColorData)):  # color data should be shape[3]==3 and isColorData==True
            inputdata = data[..., 0]
        else:
            inputdata = data
        if len(inputdata.shape) >= 3:
            if inputdata.shape[2] == 1:
                inputdata = np.repeat(inputdata, 2, 2)
                print('Warning: 3D data contains only 1 slice, cannot be display')
                # return
            inputdata = inputdata.swapaxes(0, 2)
        elif len(inputdata.shape) == 2:
            inputdata = inputdata.swapaxes(0, 1)

        self.setImage(inputdata.astype(float),
                      autoRange=False)  # ,autoHistogramRange=True, autoLevels=True )#,levels=None, axes=None, xvals, pos, scale, transform, autoHistogramRange)
        #         self.autoRange()
        self.ui.roiPlot.hide()
        self.ui.histogram.hide()

        ## go to the middle slice
        initsliceind = self.getInitSliceIndex()
        self.currentIndex = initsliceind
        #         self.getView().MoveSlice(0)

        self.SetInitGreyLevel()
        #         self.autoLevels()
        # self.autoRange()

        self.ShowBvalueText()
        if len(self._filename) <= 27:
            self.text_topmid.setText(self._filename)
        else:
            #             self.text_topmid.setText(self._filename)
            self.text_topmid.setText(self._filename[:20] + '...' + self._filename[-10:])
        if not hasattr(self._roicontroller, '_datasize'):
            self.ResetROIController()

    def SetInitGreyLevel(self):
        ## set window level
        self._winlevel, self._winwidth, self._winstep = self._datareader.getWindowLevelwidth()
        self._winwidth_orig = self._winwidth
        self._winlevel_orig = self._winlevel

        # add 1 here to make update of window in draw
        self._curwinmin = self._winlevel - self._winwidth / 2 + 1
        self._curwinmax = self._winlevel + self._winwidth / 2 + 1
        self.setLevels(self._curwinmin, self._curwinmax)
        self.getView().updateMaxMin([0, 0])

    def getInitSliceIndex(self):
        datasize = self._data.shape
        if len(datasize) >= 3:
            if datasize[2] > 1:
                init_index = int(datasize[2] / 2 - 1)
                if init_index < 0: init_index = 0
                return init_index
            else:
                return 0
        #         self._curdim4 = 0
        #         self._curdim5 = 0

        if len(datasize) == 2:
            return 0

    def setLinkImageView(self, imgviewlist):
        viewbox = self.getView()
        viewbox.setLinkImageViewForViewBox(imgviewlist)

    def setROIDrawStatus(self, status):
        self.isROIDrawOn = status

    #         if self.isROIDrawOn:
    #             print('set ROIDrawOn')
    #         else: print('Cancel ROIDraw')
    def getROIDrawStatus(self):
        return self.isROIDrawOn

    def keyPressEvent(self, ev):
        key = ev.key()

        # move to the begining to remove ROIdraw when any button press
        if (self.isROIDrawOn) and (key != Qt.Key_Shift and key != Qt.Key_Control):
            self.getView().cancelROIDraw()

        if key == Qt.Key_Control:
            self.isMouseModeMoveOn = True
            print('set isMouseModeMoveOn')
        elif ev.key() == Qt.Key_Shift:
            self.isCurvePlotOn = True
            print('set isCurvePlotOn')
        elif key == Qt.Key_Delete:
            # add following 2 line to make sure if on drawing marker will be clean before roi deleted
            #             if self.isROIDrawOn:
            #                 self.getView().cancelROIDraw()
            self.parent()._roibar.RemoveROI()
        elif (key == Qt.Key_PageDown) or (key == Qt.Key_Enter) or (key == Qt.Key_Enter - 1) or (key == Qt.Key_Space):
            # two enter key, left and right one with different key number
            self._roicontroller.Move2NextROIindex()
            if not (key == Qt.Key_Space):
                self.parent()._roibar.LocateNewROI()
            self.getView().MoveSlice(0)
        elif key == Qt.Key_PageUp:
            self._roicontroller.Move2LastROIindex()
            self.parent()._roibar.LocateNewROI()
            self.getView().MoveSlice(0)
        elif key == Qt.Key_Home:
            self.currentIndex = 0
            self.getView().MoveSlice(0)
        elif key == Qt.Key_End:
            self.currentIndex = self._data.shape[2] - 1
            self.getView().MoveSlice(0)
        elif key == Qt.Key_Escape:
            self.parent()._roibar.ROIDrawOff()
        else:
            pg.ImageView.keyPressEvent(self, ev)

    def evalKeyState(self):
        if len(self.keysPressed) == 1:
            key = list(self.keysPressed.keys())[0]
            if key == Qt.Key_Up:
                self.getView().MoveSlice(1)
            elif key == Qt.Key_Down:
                self.getView().MoveSlice(-1)
            elif key == Qt.Key_Left:
                self.VolumeMove(-1)
            elif key == Qt.Key_Right:
                self.VolumeMove(1)
            else:
                pg.ImageView.evalKeyState(self)

    def keyReleaseEvent(self, ev):
        pg.ImageView.keyReleaseEvent(self, ev)
        if ev.key() == Qt.Key_Control:
            self.isMouseModeMoveOn = False
            print('cancel isMouseModeMoveOn')
        elif ev.key() == Qt.Key_Shift:
            self.isCurvePlotOn = False
            print('set isCurvePlotOff')

    def updateImage(self, autoHistogramRange=False):
        # rewrite this fun, to hide roiPlot
        ## Redraw image on screen
        if self.image is None:
            return

        image = self.getProcessedImage()

        if autoHistogramRange:
            self.ui.histogram.setHistogramRange(self.levelMin, self.levelMax)

        # Transpose image into order expected by ImageItem
        if self.imageItem.axisOrder == 'col-major':
            axorder = ['t', 'x', 'y', 'c']
        else:
            axorder = ['t', 'y', 'x', 'c']
        axorder = [self.axes[ax] for ax in axorder if self.axes[ax] is not None]
        image = image.transpose(axorder)

        # Select time index
        if self.axes['t'] is not None:
            #             self.ui.roiPlot.show()
            image = image[self.currentIndex]

        self.imageItem.updateImage(image)

    def setCurSliceIndex(self, sliceindex):
        self.currentIndex = sliceindex

    def getCurSliceIndex(self):
        return self.currentIndex

    def getCurDim4(self):
        return self._curdim4

    def setCurDim4(self, dimindex):
        self._curdim4 = dimindex

    def getCurSlice(self):
        return self.getCurSlicefromData(self._data)

    def getCurDataSliceNum(self):
        if hasattr(self, '_data'):
            if self._data != []:
                if self._datasize[2] >= 1:
                    return 1
        return 0

    def getCurSlicefromData(self, data):
        datadim = data.ndim
        if datadim == 2:
            slicedata = data
        elif datadim == 3:
            slicedata = data[:, :, self.currentIndex]
        elif datadim == 4:
            if (data.shape[3] < (self._curdim4 + 1)): self._curdim4 = 0
            slicedata = data[:, :, self.currentIndex, self._curdim4]
        elif datadim == 5:
            slicedata = data[:, :, self.currentIndex, self._curdim4, self._curdim5]
        else:
            return []
        return slicedata

    def VolumeMove(self, voloffset=0):
        try:
            if not self.isDataLoaded(): return
            datasize = self._data.shape
            if len(datasize) <= 2: return
            if self._isColorData: return

            if len(datasize) >= 4:
                if voloffset == 1:
                    if self._curdim4 < datasize[3] - 1:
                        self._curdim4 += 1
                        self.setDatabyVolume()
                elif voloffset == -1:
                    if self._curdim4 > 0:
                        self._curdim4 -= 1
                        self.setDatabyVolume()
                self.ShowBvalueText()
        except:
            print('ImageObjectPyQtGraphy.VolumeMove failed')

    def setDatabyVolume(self):
        curindex = self.currentIndex
        self.SimpleSetImage(self._data[:, :, :, self._curdim4].swapaxes(0, 2), autoRange=False,
                            autoHistogramRange=False,
                            autoLevels=False)  # ,levels=None, axes=None, xvals, pos, scale, transform, autoHistogramRange)
        #         self.ui.histogram.hide()
        #         self.ui.roiPlot.hide()
        self.currentIndex = curindex
        self.updateImage()
        # self.ShowBvalueText()

    def SimpleSetImage(self, img, autoRange=True, autoLevels=True, levels=None, axes=None, xvals=None, pos=None,
                       scale=None, transform=None, autoHistogramRange=True):
        # rewrite this fun, to hide roiPlot
        ## Redraw image on screen
        """
        Set the image to be displayed in the widget.

        ================== ===========================================================================
        **Arguments:**
        img                (numpy array) the image to be displayed. See :func:`ImageItem.setImage` and
                           *notes* below.
        xvals              (numpy array) 1D array of z-axis values corresponding to the third axis
                           in a 3D image. For video, this array should contain the time of each frame.
        autoRange          (bool) whether to scale/pan the view to fit the image.
        autoLevels         (bool) whether to update the white/black levels to fit the image.
        levels             (min, max); the white and black level values to use.
        axes               Dictionary indicating the interpretation for each axis.
                           This is only needed to override the default guess. Format is::

                               {'t':0, 'x':1, 'y':2, 'c':3};

        pos                Change the position of the displayed image
        scale              Change the scale of the displayed image
        transform          Set the transform of the displayed image. This option overrides *pos*
                           and *scale*.
        autoHistogramRange If True, the histogram y-range is automatically scaled to fit the
                           image data.
        ================== ===========================================================================

        **Notes:**

        For backward compatibility, image data is assumed to be in column-major order (column, row).
        However, most image data is stored in row-major order (row, column) and will need to be
        transposed before calling setImage()::

            imageview.setImage(imagedata.T)

        This requirement can be changed by the ``imageAxisOrder``
        :ref:`global configuration option <apiref_config>`.

        """
        from pyqtgraph import debug
        profiler = debug.Profiler()

        if hasattr(img, 'implements') and img.implements('MetaArray'):
            img = img.asarray()

        if not isinstance(img, np.ndarray):
            required = ['dtype', 'max', 'min', 'ndim', 'shape', 'size']
            if not all([hasattr(img, attr) for attr in required]):
                raise TypeError("Image must be NumPy array or any object "
                                "that provides compatible attributes/methods:\n"
                                "  %s" % str(required))

        self.image = img
        self.imageDisp = None

        profiler()

        if axes is None:
            x, y = (0, 1) if self.imageItem.axisOrder == 'col-major' else (1, 0)

            if img.ndim == 2:
                self.axes = {'t': None, 'x': x, 'y': y, 'c': None}
            elif img.ndim == 3:
                # Ambiguous case; make a guess
                if img.shape[2] <= 4:
                    self.axes = {'t': None, 'x': x, 'y': y, 'c': 2}
                else:
                    self.axes = {'t': 0, 'x': x + 1, 'y': y + 1, 'c': None}
            elif img.ndim == 4:
                # Even more ambiguous; just assume the default
                self.axes = {'t': 0, 'x': x + 1, 'y': y + 1, 'c': 3}
            else:
                raise Exception("Can not interpret image with dimensions %s" % (str(img.shape)))
        elif isinstance(axes, dict):
            self.axes = axes.copy()
        elif isinstance(axes, list) or isinstance(axes, tuple):
            self.axes = {}
            for i in range(len(axes)):
                self.axes[axes[i]] = i
        else:
            raise Exception(
                "Can not interpret axis specification %s. Must be like {'t': 2, 'x': 0, 'y': 1} or ('t', 'x', 'y', 'c')" % (
                    str(axes)))

        for x in ['t', 'x', 'y', 'c']:
            self.axes[x] = self.axes.get(x, None)
        axes = self.axes

        if xvals is not None:
            self.tVals = xvals
        elif axes['t'] is not None:
            if hasattr(img, 'xvals'):
                try:
                    self.tVals = img.xvals(axes['t'])
                except:
                    self.tVals = np.arange(img.shape[axes['t']])
            else:
                self.tVals = np.arange(img.shape[axes['t']])

        profiler()

        self.currentIndex = 0
        self.updateImage(autoHistogramRange=autoHistogramRange)
        if levels is None and autoLevels:
            self.autoLevels()
        if levels is not None:  ## this does nothing since getProcessedImage sets these values again.
            self.setLevels(*levels)

        #         if self.ui.roiBtn.isChecked():
        #             self.roiChanged()

        profiler()

        if self.axes['t'] is not None:
            # self.ui.roiPlot.show()
            self.ui.roiPlot.setXRange(self.tVals.min(), self.tVals.max())
            self.timeLine.setValue(0)
            # self.ui.roiPlot.setMouseEnabled(False, False)
            if len(self.tVals) > 1:
                start = self.tVals.min()
                stop = self.tVals.max() + abs(self.tVals[-1] - self.tVals[0]) * 0.02
            elif len(self.tVals) == 1:
                start = self.tVals[0] - 0.5
                stop = self.tVals[0] + 0.5
            else:
                start = 0
                stop = 1
            for s in [self.timeLine, self.normRgn]:
                s.setBounds([start, stop])
        # else:
        # self.ui.roiPlot.hide()
        profiler()

        self.imageItem.resetTransform()
        if scale is not None:
            self.imageItem.scale(*scale)
        if pos is not None:
            self.imageItem.setPos(*pos)
        if transform is not None:
            self.imageItem.setTransform(transform)

        profiler()

        if autoRange:
            self.autoRange()
        # self.roiClicked()

        profiler()

    def isDataLoaded(self):
        if not isArrayData(self._data):
            return False
        else:
            return True

    def ResetROIController(self):
        datasize = self._data.shape
        if len(datasize) >= 3:
            self._roicontroller.ResetROIdata(datasize[:3])
            # self.setROIController(ROIController(data.shape[:3]))
        elif len(datasize) == 2:
            self._roicontroller.ResetROIdata(datasize[:2])
            # self.setROIController(ROIControllerWithLabel(datasize[:2]))
        else:
            print('wrong data size: ' + datasize)

    def setROIController(self, roicontroller):
        self._roicontroller = roicontroller

    def getROIController(self):
        return self._roicontroller

    def ClearAxe(self):
        self.setImage(np.zeros([1, 1]), autoRange=False)
        self.getView().RemoveAllLineDraw()
        if hasattr(self, 'text_topmid') and hasattr(self, 'text_bottom'):
            self.text_topmid.setText('')
            self.text_bottom.setText('')
            self.text_bottom.setWordWrap(True)

    def ClearData(self):
        self.InitialParam()
        #         # bug fix: img window scale change when DWI model is calculated. The reason is the datasize of previous loaded data is not clear, then imshow with wrong size lead to scale change
        #         if hasattr(self,'_datasize'): del self._datasize
        self.ClearAxe()

    #         self.LinkedAxesAutoRange()

    def LinkedAxesAutoRange(self):
        if self.getView()._linkimgviewlist != None:
            for limgview in self.getView()._linkimgviewlist:
                if limgview.isDataLoaded():
                    limgview.autoRange()
                    return

    def getCurImgVol(self):
        return self.getCur3DVolume(self._data)

    def getCurImgVolAsSitkimg(self):
        data = self.getCurImgVol()
        return self._datareader.createSingleSitkImg(data)

    def getCur3DVolume(self, data):
        datadim = data.ndim
        if datadim == 3:
            voldata = data
        elif datadim == 4:
            voldata = data[:, :, :, self._curdim4]
        elif datadim == 5:
            voldata = data[:, :, :, self._curdim4, self._curdim5]
        else:
            return []
        return voldata

    def saveMaskAsNii(self, filepath, isOnlyCurROI=False):
        print("save Mask as nii:" + filepath)
        if not isOnlyCurROI:
            mask3Dlist = self.getAllMaskdata()
        else:
            mask3Dlist = [self.getCurMaskdata()]

        for i in range(len(mask3Dlist)):
            filebase = getBasepath(filepath)
            if len(mask3Dlist) > 1:
                savefilepath = filebase + str(i) + '.nii.gz'
            else:
                savefilepath = filebase + '0' + '.nii.gz'

            if self._datareader._dataFormat == 'Nifty':
                self._datareader.SaveNiftyFilebyData(mask3Dlist[i].astype(np.uint8), savefilepath, refpath=None)
            else:
                self._datareader.SaveEmptyNiftyFilebyData(
                    self._datareader.NiftyImgRotateBack(mask3Dlist[i].astype(np.uint8)), savefilepath)

    def getCurMaskdata(self):
        # curROIindex == None, maybe no ROI was drawn
        if self._roicontroller._curROIindex == None: return []
        mask3D = self._roicontroller.calMask4CurROI()
        #         mask3D = self.rotateBackMaskImg4Save(mask3D)
        return mask3D

    def getCurMaskdataAsSitkimg(self):
        # curROIindex == None, maybe no ROI was drawn
        if self._roicontroller._curROIindex == None: return []
        mask3D = self.getCurMaskdata()
        return self._datareader.createSingleSitkImg(mask3D)

    def getAllMaskdata(self):
        if self._roicontroller._ROIdataArray == []: return []
        mask3Dlist = self._roicontroller.calMask4AllROI()
        #         mask3D = self.rotateBackMaskImg4Save(mask3D)
        return mask3Dlist

    def getAllMaskdataAsSitkimg(self):
        if self._roicontroller._ROIdataArray == []: return []
        return self._datareader.createSingleSitkImg(self.getAllMaskdata())

    def saveMaskdata(self, filepath):
        self._roicontroller.saveMaskdata(filepath)

    def loadMaskdata(self, filepath):
        return self._roicontroller.loadMaskdata(filepath)

    def loadMaskdataFromMask(self, filepath):
        ## resample implement: to ensure ROI matched img data with different dcm2nii tool
        # bug fix for sitk readimage error when chinese in filepath
        try:
            maskimg = sitk.ReadImage(filepath)
        except:
            temppath = 'temp' + getExtension(filepath)
            shutil.copyfile(filepath, temppath)
            maskimg = sitk.ReadImage(temppath)
            os.remove(temppath)
        # refimg = self._datareader.GetSitkImgObj()
        # bugfix for resample position error with ref to img0
        refimg = self._parent._imgaxes[0]._datareader.GetSitkImgObj()
        if type(refimg) == list: refimg = refimg[0]

        # bug fix, even when ref and mask be the same img, the datareader._isorien could be different
        maskimg_resample, dummy = ResampleImage2Ref(refimg, maskimg)  # ,outputpixeltype=sitk.sitkFloat32)
        # datareader._isorien should be from axe[0]
        mask = self._parent._imgaxes[0]._datareader.GetDataFromSitkImg(maskimg_resample)
        mask[mask <= 0.5] = 0
        roiinds = np.unique(mask.ravel())
        roisize = roiinds.size - 1
        if roiinds.size >= 10: roisize = 1
        if roisize <= 1:
            mask[mask > 0.5] = 1
            roiinds = np.unique(mask.ravel())

        if mask.sum() == 0:
            print('## Error: no info in ROI')
            return False
        # bug: self._datareader._datasize not match to data real size (may due to resample)
        if self._datareader._data.shape[:3] == mask.shape[:3]:
            for roii in roiinds:
                if roii == 0:
                    continue
                else:
                    self._roicontroller.loadMaskdataFromMask(mask == roii)
            return True
        else:
            QMessageBox.about(self, 'Error', 'Not matched ROI file (image size may be different)')
            print('## Error:not matched ROI file (image size may be different)')
            return False

    def ROIInfoRealTimeUpdate(self):
        if not hasattr(self._parent, '_roibar'): return
        roibar = self._parent._roibar
        if hasattr(roibar, '_combobox_DLROIMethod'):
            roimethod = roibar._combobox_DLROIMethod.currentText()
        else:
            roimethod = ''

        if roimethod == 'PCaPredRT':
            roibar.ProstateAICal()
        else:
            curroi = self.getCurMaskdata()
            if not isArrayData(curroi):
                result = ''
            else:
                result = '->ROI ' + str(self._roicontroller._curROIindex + 1) + ' size:' + str(np.sum(curroi > 0))
                self.HighlightCurROIinTable()
            roibar._label_status.setText(result)

    def HighlightCurROIinTable(self):
        is_singleROI = self._parent._parent._roiInfoUI._checkbox_singleroi.isChecked()
        if not is_singleROI:
            x = self._roicontroller._curROIindex
            self._parent._parent._itemsTable.clearSelection()
            colnum = self._parent._parent._itemsTable.columnCount()
            self._parent._parent._itemsTable.setRangeSelected(QTableWidgetSelectionRange(x, colnum - 1, x, 0), True)

    def NewROIbyPos(self, pos, pad=1):
        mask = np.zeros(self._datasize[:3])
        mask[(pos[0] - pad):(pos[0] + pad + 1), (pos[1] - pad):(pos[1] + pad + 1), pos[2]] = 1
        self._roicontroller.loadMaskdataFromMask(mask)

    def ROIbyPoint(self, pos, pad=1):
        if self.isDataLoaded() == False: return
        mask = np.zeros(self._datasize[:3])
        pad1 = int(pad / 2)
        pad2 = pad - pad1
        mask[(pos[0] - pad1):(pos[0] + pad2), (pos[1] - pad1):(pos[1] + pad2), pos[2]] = 1
        self._roicontroller.addMaskdataFromMask(mask)

    def singleDicomDir2Nii(self, dicomdirpath):
        output_file = dicomdirpath + '.nii'
        dicom2nifti.dicom_series_to_nifti(dicomdirpath, output_file, reorient_nifti=False)

    def multipleDicomDirs2Nii(self, dicomdirpath):
        dicom2nifti.convert_directory(dicomdirpath, dicomdirpath)

    def CalSliceBuffer(self, verts, curslice):
        verts_np = np.array(verts)
        roibar = self.parent()._roibar
        method = self.parent()._roibar._cur_manualROIOption
        if hasattr(roibar, '_commonUI'):
            is_autoslicebuffer = roibar._commonUI._checkbox_autoslicebuffer.isChecked()
            slicebuffer = roibar._commonUI._spinbox_slicebuffer.value()
            if is_autoslicebuffer:
                pixdim = self._datareader._pixel_spacing
                if method == 'AutoLine':
                    center, halfrad = calCenterRadbyPoints(verts_np)
                elif (method == 'AutoThres') or (method == 'AutoProstate'):
                    slicemask = self._roicontroller.calMask2D(verts)
                    halfrad = np.sqrt(np.sum(slicemask > 0)) / 2
                slicebuffer = int(round(pixdim[0] / pixdim[2] * halfrad))
        slicebuffer = np.min([slicebuffer, (curslice - 0), (self._data.shape[2] - curslice - 1)])
        print('slice buffer:' + str(slicebuffer))
        return slicebuffer

    def SetImageColor(self, color):
        if self.isDataLoaded():
            lut = getLookupTableFromMatplotlab(color)
            self.getImageItem().setLookupTable(lut, update=True)

    def SetAndShowBvalueText(self, bvallist):
        self._datareader._bval = bvallist
        self.ShowBvalueText()

    def ShowBvalueText(self):
        txt = ''
        if hasattr(self._datareader, '_dinfo') and (self._datareader._dinfo != []):
            # get curindex
            if len(self._datareader._dinfo['tr']) <= self._curdim4:
                curindex = 0
            else:
                curindex = self._curdim4

            if (self._datareader._dinfo != []) & (len(self._data.shape) > 3):
                #                 txt = txt + ('TR:' + str(self._datareader._dinfo['tr'][curindex]) + '\n' +
                #                              'TE:' + str(self._datareader._dinfo['te'][curindex]) + '\n' +
                #                              'FA:' + str(self._datareader._dinfo['fa'][curindex]) )
                dinfo = self._datareader._dinfo
                for k in ['tr', 'te', 'fa', 'ir']:
                    if k in dinfo.keys():
                        if dinfo[k] == []: continue
                        if k == 'fa': txt = txt + '\n'
                        txt = txt + (str(k) + ':' + str(round(float(dinfo[k][curindex]), 2)) + '   ')
                #                 for k in self._datareader._dinfo.keys():
                #                     if self._datareader._dinfo[k] == []: continue
                #                     if k in ['tr','te','fa','ir']:
                #                         if k == 'fa': txt=txt+'\n'
                #                         txt = txt + (str(k)+':' + str(round(float(self._datareader._dinfo[k][curindex]),2)) + '   ')

                txt = txt[:-1] + '\n'
                self.text_bottom.setAlignment(Qt.AlignLeft)
        if hasattr(self._datareader, '_bval') & (len(self._data.shape) > 3):
            # get curindex
            if len(self._datareader._bval) <= self._curdim4:
                curindex = 0
            else:
                curindex = self._curdim4
            if self._datareader._bval != []:
                txt += 'b: ' + str(self._datareader._bval[curindex])
                self.text_bottom.setAlignment(Qt.AlignLeft)
        commentxt = ''
        if hasattr(self._datareader, '_comment'):
            if (self._datareader._comment != []):
                if (type(self._datareader._comment) == list):
                    commentxt = self._datareader._comment[self._curdim4]
                else:
                    commentxt = self._datareader._comment
                self.text_bottom.setAlignment(Qt.AlignCenter)
        self.text_bottom.setText(txt + commentxt)