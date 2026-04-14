import Metashape
from gui3 import *
import os


application: Metashape.Application = Metashape.app
WGS_84 = Metashape.CoordinateSystem("EPSG::4326")
DEFAUT_CRS = Metashape.CoordinateSystem("EPSG::2180")
U_2000 = Metashape.CoordinateSystem("EPSG::2178")
def find_files(folder, types):
    return [entry.path for entry in os.scandir(folder) if (entry.is_file() and os.path.splitext(entry.name)[1].lower() in types)]

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.dcloud = False
        self.mmodel = False
        self.texture = False

        self.DCQuality = None
        self.MMQuality = None

        self.ui.photodirButton.clicked.connect(self.photosdirfun)
        self.ui.cpdirbutton.clicked.connect(self.cpdirfun)
        self.ui.cpepsgButton.clicked.connect(self.cpepsgfun)
        self.ui.projepsgButton.clicked.connect(self.projepsgfun)
        self.ui.densecloud.stateChanged.connect(self.showdensecloud)
        self.ui.meshModel.stateChanged.connect(self.showmeshmodel)
        self.ui.RunButton.clicked.connect(self.runauto)

       

    def photosdirfun(self):
        photos_directory = QtWidgets.QFileDialog.getExistingDirectory(self,"Otwórz zdjęcia")
        if photos_directory == "":
            return
        self.photos_path = photos_directory
        self.ui.photodir.setText(photos_directory)

    def cpdirfun(self):
        osn_dir = QtWidgets.QFileDialog.getOpenFileName( self, "Otwórz plik osnowy")
        self.cp_path = osn_dir
        self.ui.cpdir.setText(str(osn_dir))


    def projepsgfun(self): 
        destination_crs = Metashape.app.getCoordinateSystem("Select Coordinate System", DEFAUT_CRS)
        self.destepsg = destination_crs
        self.ui.projepsg.setText(str(destination_crs))
        self.raise_()
    
    def cpepsgfun(self):
        markerscrs = Metashape.app.getCoordinateSystem("Select Markers' Coordinate System", U_2000)
        self.cpepsg = markerscrs
        self.ui.cpepsg.setText(str(markerscrs))
        self.raise_()

    def showdensecloud(self, state):
        enabled = state == QtCore.Qt.Checked
        self.ui.labelCloudQual.setEnabled(enabled)
        self.ui.comboBox_2.setEnabled(enabled)
        # self.dcloud = enabled
        # if enabled:
        #     self.DCQuality = str(self.ui.comboBox_2.currentText())

    def showmeshmodel(self, state):
        enabled = state == QtCore.Qt.Checked
        self.ui.labelModelQual.setEnabled(enabled)
        self.ui.comboBox_4.setEnabled(enabled)
        self.ui.textutre.setEnabled(enabled)

        # if enabled:
        #     self.MMQuality = str(self.ui.comboBox_4.currentText())


    def runauto(self):
        self.orientation = str(self.ui.comboBoxOrient.currentText())
        doc = Metashape.app.document

        for chunk in doc.chunks: 
            doc.remove(chunk)

        chunk = doc.addChunk()

        #uklad docelowy
        destination_crs = self.destepsg
        doc.chunk.crs = destination_crs
        
        photosdir = self.photos_path
        photos_to_load = find_files(photosdir, [".jpg", ".jpeg", ".tif", ".tiff"])
        chunk.addPhotos(photos_to_load)

        #transformacja zdjęc do ukladu docelowego
        for camera in chunk.cameras:
            location_wgs84 = camera.reference.location
            location_destination_crs = Metashape.CoordinateSystem.transform(
              location_wgs84, WGS_84, destination_crs)
            camera.reference.location = location_destination_crs

        #wczytywanie markerów:
        markerscrs = self.cpepsg
        osn_dir = str(self.cp_path[0])

        with open(osn_dir, "r") as f:
            for line in f:
                parts = line.strip().split()
                print(f"parts: {parts}")
                m_id, x, y, z = parts

                transformed = [float(y),float(x),float(z)]
                if markerscrs != destination_crs:
                    transformed = Metashape.CoordinateSystem.transform(transformed, markerscrs, destination_crs)

                print("g")
                
                print(f"transformed: {transformed}")
                marker = chunk.addMarker()
                marker.label=str(m_id)
                marker.reference.location = [transformed[0], transformed[1], transformed[2]]

        chunk.crs=destination_crs

        dwnscaledict = {"Highest":0 ,"High":1,"Medium":2,"Low":4,"Lowest":8}
        dwnscale = dwnscaledict[self.orientation]
        print(f"tutaj downscale:{dwnscale}")
        chunk.matchPhotos(downscale = dwnscale) #szuka wspólnych punktów między zdjęciami (tworzy tiepoints)
        #chunk.matchPhotos(keypoint_limit = 40000, tiepoint_limit = 10000, generic_preselection = True, reference_preselection = True)
        chunk.alignCameras() # liczy pozycje i orientacje kamer
    
        targettype = Metashape.TargetType.CrossTarget
        #detect markers:
        chunk.detectMarkers(targettype, tolerance=20)

        controlpoints={} #te z 20X
        checkpoints={} #te wtkryte z detectmarkers

        for point in chunk.markers:
            if point.label.startswith("point"):
                transformed = Metashape.Vector(point.position)
                mtx=Metashape.ChunkTransform.matrix
                ecef = chunk.transform.matrix.mulp(transformed)
                transformed=chunk.crs.project(ecef)
                checkpoints[point.label] =transformed
            if point.label.startswith("2"):
                controlpoints[point.label] = point.reference.location

        def dist(v, u):
            x1, y1, z1 = v
            x0, y0, z0 = u

            a = (x1 - x0)**2
            b = (y1 - y0)**2
            #c = (z1 - z0)**2

            return (a + b)**(1/2)
        
        final_controlpts = controlpoints.copy()

        for i0, v0 in controlpoints.items():
            candidates={}
            for i1, v1 in checkpoints.items():
                d = dist(v1,v0)
                if d < 4:
                    candidates[i1] = d

            if not candidates:
                continue
            id_min = min(candidates, key = candidates.get)
            #changes[i0] = checkpoints[id_min]
            final_controlpts[i0] = checkpoints[id_min]

        for p in chunk.markers:
            if p.label in final_controlpts:
                p.reference.location = final_controlpts[p.label]

        path = os.path.join(photosdir, "OrientacjaZewnetrzna")
        
        build_densecloud = self.ui.densecloud.isChecked()       
        build_mesh = self.ui.meshModel.isChecked()
        build_texture = self.ui.textutre.isChecked()

        if build_densecloud: 
            DMscaledict = {"UltraHigh":1 ,"High":2,"Medium":4,"Low":8,"Lowest":16}
            DMdwscale = DMscaledict[str(self.ui.comboBox_2.currentText())]
            chunk.buildDepthMaps(downscale=DMdwscale)
            chunk.buildPointCloud()

        if build_mesh:
            DMscaledict = {"UltraHigh":1 ,"High":2,"Medium":4,"Low":8,"Lowest":16}
            DMdwscale = DMscaledict[str(self.ui.comboBox_4.currentText())]
            chunk.buildDepthMaps(downscale=DMdwscale)
            chunk.buildModel()
            if build_texture:
                chunk.buildUV()
                chunk.buildTexture()
        
        finalpath = os.path.join(photosdir, "ModelKoncowy.psx")  
        doc.save(finalpath)
      




main_window = None

def viewmeta():
    global main_window 
    if main_window is None:
        # main_window = QtWidgets.QMainWindow()
        # ui = MyWindow()
        # ui.setupUi(main_window)
        main_window =MyWindow()
    main_window.show()


application.removeMenuItem("FTP")
application.addMenuItem("FTP/Automatyczna orientacja", viewmeta)


