import sys,os,qdarkstyle
from dotenv import load_dotenv
import ntpath
import fitz
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import clipboard
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog, QMenu
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtGui import QCursor, QImage
import PyQt5
import pyqtgraph as pg
import random,copy
import numpy as np
from numpy.linalg import inv
import matplotlib.pyplot as plt
try:
    from . import locate_path
except:
    import locate_path
script_path = locate_path.module_path_locator()
import pandas as pd
import time, datetime
import matplotlib
#matplotlib.use("TkAgg")
os.environ["QT_MAC_WANTS_LAYER"] = "1"
try:
    import ConfigParser
except:
    import configparser as ConfigParser
import sys,os
import subprocess
from pymongo import MongoClient
import certifi
import webbrowser
import qpageview.viewactions
import base64
from gridfs import GridFS
from PIL import ImageGrab
import io
import codecs

# import ray
# ray.init()

def error_pop_up(msg_text = 'error', window_title = ['Error','Information','Warning'][0]):
    msg = QMessageBox()
    if window_title == 'Error':
        msg.setIcon(QMessageBox.Critical)
    elif window_title == 'Warning':
        msg.setIcon(QMessageBox.Warning)
    else:
        msg.setIcon(QMessageBox.Information)

    msg.setText(msg_text)
    # msg.setInformativeText('More information')
    msg.setWindowTitle(window_title)
    msg.exec_()

def image_to_64base_string(image_path):
    with open(image_path, "rb") as img_file:
         my_string = base64.b64encode(img_file.read())
    return my_string

def image_string_to_qimage(my_string, img_format = 'PNG'):
    QByteArr = PyQt5.QtCore.QByteArray.fromBase64(my_string)
    QImage = PyQt5.QtGui.QImage()
    QImage.loadFromData(QByteArr, img_format)
    return QImage

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, data, tableviewer, main_gui, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.tableviewer = tableviewer
        self.main_gui = main_gui

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role):
        if index.isValid():
            if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole] and index.column()!=0:
                return str(self._data.iloc[index.row(), index.column()])
            if role == QtCore.Qt.BackgroundRole and index.row()%2 == 0:
                return QtGui.QColor('green')
                # return QtGui.QColor('DeepSkyBlue')
                # return QtGui.QColor('green')
            if role == QtCore.Qt.BackgroundRole and index.row()%2 == 1:
                return QtGui.QColor('white')
                # return QtGui.QColor('aqua')
                # return QtGui.QColor('lightGreen')
            if role == QtCore.Qt.ForegroundRole and index.row()%2 == 1:
                return QtGui.QColor('black')
            if role == QtCore.Qt.CheckStateRole and index.column()==0:
                if self._data.iloc[index.row(),index.column()]:
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            if value == QtCore.Qt.Checked:
                self._data.iloc[index.row(),index.column()] = True
            else:
                self._data.iloc[index.row(),index.column()] = False
        else:
            if str(value)!='':
                self._data.iloc[index.row(),index.column()] = str(value)
        if self._data.columns.tolist()[index.column()] in ['select','archive_date','user_label','read_level']:
            self.main_gui.update_meta_info_paper(paper_id = self._data['paper_id'][index.row()])
        self.dataChanged.emit(index, index)
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()
        self.tableviewer.resizeColumnsToContents() 
        return True

    def update_view(self):
        self.layoutAboutToBeChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def headerData(self, rowcol, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[rowcol]         
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self._data.index[rowcol]         
        return None

    def flags(self, index):
        if not index.isValid():
           return QtCore.Qt.NoItemFlags
        else:
            if index.column()==0:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
            else:
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)

    def sort(self, Ncol, order):
        """Sort table by given column number."""
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(self._data.columns.tolist()[Ncol],
                                        ascending=order == QtCore.Qt.AscendingOrder, ignore_index = True)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        uic.loadUi(os.path.join(script_path,'project_manager_new.ui'),self)
        self.widget_terminal.update_name_space('main_gui',self)
        #set plaintext style
        self.plainTextEdit_pdf_text.setStyleSheet(
                """QPlainTextEdit {background-color: #FFFFFF;
                    color: #6600CC;}""")
        self.setWindowTitle('Scientific Project Manager')
        #binary string for temp figures from clipboard buffer
        self.base64_string_temp = ''
        self.base64_string_new_input_temp = ''
        self.meta_figure_base_strings = []
        #menu bar
        self.action = qpageview.viewactions.ViewActions(self)
        self.action.setView(self.widget_view)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&View')
        fileMenu.addAction(self.action.fit_both)
        fileMenu.addAction(self.action.fit_height)
        fileMenu.addAction(self.action.fit_width)
        fileMenu.addAction(self.action.zoom_in)
        fileMenu.addAction(self.action.zoom_out)
        fileMenu.addAction(self.action.next_page)
        fileMenu.addAction(self.action.previous_page)
        #show or hide
        # self.pushButton_hide_show.clicked.connect(lambda:self.frame_3.setVisible(not self.frame_3.isVisible()))
        #toolbar action slot functions
        self.actionFitWidth.triggered.connect(lambda:self.action.fit_width.trigger())
        self.actionFitHeight.triggered.connect(lambda:self.action.fit_height.trigger())
        self.actionFitBoth.triggered.connect(lambda:self.action.fit_both.trigger())
        self.actionzoomin.triggered.connect(lambda:self.action.zoom_in.trigger())
        self.actionzoomout.triggered.connect(lambda:self.action.zoom_out.trigger())
        self.actionExportBiTex.triggered.connect(self.export_bibtex)
        self.actionImportBiTex.triggered.connect(self.import_bibtex)
        self.actionDatabaseInfo.triggered.connect(self.get_database_info)
        self.actionDatabaseCloud.triggered.connect(self.start_mongo_client_cloud)
        self.actionLocalServerOn.triggered.connect(self.connect_mongo_server)
        self.actionLocalServerOff.triggered.connect(self.stop_mongo_server)
        self.actionLocalClient.triggered.connect(self.start_mongo_client)
        self.actionSearchDB.triggered.connect(self.search_database)
        #control of pdf viewer (image render)
        self.action_pdf = qpageview.viewactions.ViewActions(self)
        self.action_pdf.setView(self.widget_pdf_viewer)
        self.pushButton_fit_width.clicked.connect(lambda:self.action_pdf.fit_width.trigger())
        self.pushButton_fit_height.clicked.connect(lambda:self.action_pdf.fit_height.trigger())
        self.pushButton_fit_page.clicked.connect(lambda:self.action_pdf.fit_both.trigger())
        self.pushButton_next.clicked.connect(lambda:self.action_pdf.next_page.trigger())
        self.pushButton_previous.clicked.connect(lambda:self.action_pdf.previous_page.trigger())
        self.pushButton_zoomin.clicked.connect(lambda:self.action_pdf.zoom_in.trigger())
        self.pushButton_zoomout.clicked.connect(lambda:self.action_pdf.zoom_out.trigger())
        self.pushButton_extract_pdf_text.clicked.connect(lambda:self.plainTextEdit_pdf_text.setPlainText(self.doc_pdf[self.widget_pdf_viewer.currentPageNumber()-1].getText()))
        #control of projects
        self.pushButton_new_project.clicked.connect(self.new_project_dialog)
        self.pushButton_update_project_info.clicked.connect(self.update_project_info)
        self.pushButton_load.clicked.connect(self.load_project)
        #controls of paper_info
        # self.listWidget_papers.itemDoubleClicked.connect(lambda:self.comboBox_papers.setCurrentText(self.listWidget_papers.selectedItems()[0].text()))
        self.comboBox_papers.activated.connect(self.extract_paper_info)
        self.comboBox_papers.currentIndexChanged.connect(self.extract_paper_info)
        self.pushButton_add_new_paper.clicked.connect(lambda:self.add_paper_info(parser=None))
        self.pushButton_add_paper_clipboard.clicked.connect(self.fill_input_fields_from_clipboard_buffer)
        self.pushButton_new_paper.clicked.connect(self.new_paper)
        self.comboBox_tags.activated.connect(self.display_tag_info)
        self.comboBox_tags.currentIndexChanged.connect(self.display_tag_info)
        self.comboBox_section_tag_info.activated.connect(self.update_tag_list_in_combo)
        self.comboBox_section_tag_info.currentIndexChanged.connect(self.update_tag_list_in_combo)
        self.pushButton_update_tag_info.clicked.connect(self.update_tag_info_slot)
        self.pushButton_append_info_new_input.clicked.connect(self.append_new_input)
        self.pushButton_parse_row.clicked.connect(self.parse_selected_row_info)
        # self.comboBox_pick_paper.activated.connect(lambda:self.lineEdit_paper_id_figure.setText(self.comboBox_pick_paper.currentText()))
        # self.comboBox_pick_paper.currentIndexChanged.connect(lambda:self.lineEdit_paper_id_figure.setText(self.comboBox_pick_paper.currentText()))
        self.pushButton_update_paper.clicked.connect(self.update_paper_info)
        self.pushButton_remove_paper.clicked.connect(self.delete_one_paper)
        self.pushButton_remove_pdf.clicked.connect(self.delete_pdf_file)
        #controls of tags
        self.comboBox_tag_list.activated.connect(self.extract_tag_contents_slot)
        self.comboBox_tag_list.currentIndexChanged.connect(self.extract_tag_contents_slot)
        self.pushButton_update_info.clicked.connect(self.update_tag_contents_slot)
        self.comboBox_section.activated.connect(self.update_tag_list_in_existing_input)
        self.comboBox_section.currentIndexChanged.connect(self.update_tag_list_in_existing_input)
        self.comboBox_section_new_input.activated.connect(self.update_tag_list_in_new_input)
        self.comboBox_section_new_input.currentIndexChanged.connect(self.update_tag_list_in_new_input)
        self.comboBox_tag_list_new_input.activated.connect(self.update_tag_in_new_input)
        self.comboBox_tag_list_new_input.currentIndexChanged.connect(self.update_tag_in_new_input)
        # self.comboBox_section_figure.activated.connect(self.get_figure_tag_list_by_paper_id_and_collection_name)
        # self.comboBox_section_figure.currentIndexChanged.connect(self.get_figure_tag_list_by_paper_id_and_collection_name)
        # self.comboBox_fig_tags.activated.connect(lambda:self.lineEdit_tag_name_figure.setText(self.comboBox_fig_tags.currentText()))
        # self.comboBox_fig_tags.currentIndexChanged.connect(lambda:self.lineEdit_tag_name_figure.setText(self.comboBox_fig_tags.currentText()))
        self.pushButton_rename.clicked.connect(self.rename_tag)
        self.pushButton_delete_tag.clicked.connect(self.delete_tag)
        #extract info
        self.pushButton_extract_selected.clicked.connect(self.extract_all_info)
        #open link or pdf 
        # self.pushButton_open_url.clicked.connect(self.open_url_in_webbrowser)
        self.pushButton_open_pdf.clicked.connect(lambda:self.open_pdf_file(use_external_app=False))
        self.pushButton_pdf_to_image.clicked.connect(lambda:self.open_pdf_file(use_external_app=False))
        self.pushButton_pdf_to_image.clicked.connect(lambda:self.action_pdf.fit_width.trigger())
        #controls of figures
        self.pushButton_paste_image.clicked.connect(lambda:self.paste_image_to_viewer_from_clipboard(self.widget_view,'base64_string_temp'))
        self.pushButton_open_image.clicked.connect(lambda:self.open_image_file(self.widget_view,'base64_string_temp'))
        self.pushButton_paste_figure.clicked.connect(lambda:self.paste_image_to_viewer_from_clipboard(self.widget_figure_input,'base64_string_new_input_temp'))
        self.pushButton_load_figure.clicked.connect(lambda:self.open_image_file(self.widget_figure_input,'base64_string_new_input_temp'))
        # self.pushButton_extract_figure.clicked.connect(self.load_figure_from_database)
        # self.pushButton_save_figure.clicked.connect(self.save_figure_to_filesystem)
        self.pushButton_select_all.clicked.connect(self.select_all)
        self.pushButton_select_none.clicked.connect(self.select_none)

    def parse_selected_row_info(self):
        self.comboBox_papers.setCurrentText(self.pandas_model_paper_info._data['paper_id'].tolist()[self.tableView_paper_info.selectionModel().selectedRows()[0].row()])

    def select_all(self):
        self.pandas_model_paper_info._data['select'] = True
        self.pandas_model_paper_info.update_view()

    def select_none(self):
        self.pandas_model_paper_info._data['select'] = False
        self.pandas_model_paper_info.update_view()

    #get the info of basic setting of mongodb, e.g. locatin of database storage, config file 
    def get_database_info(self):
        if hasattr(self, 'mongo_client'):
            return_str = self.mongo_client.admin.command((({'getCmdLineOpts': 1})))
            return_str_list = []
            for key, item in return_str.items():
                return_str_list.append('{}:{}'.format(key,item))
            error_pop_up('\n'.join(return_str_list),'Information')
        else:
            pass

    def open_image_file(self, widget_view, base64_string = 'base64_string_temp'):
        self.action.setView(widget_view)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","image file (*.*)", options=options)
        if fileName:
            base64_data = image_to_64base_string(fileName)
            #self.base64_string_temp = base64_data
            setattr(self, base64_string, base64_data)
            widget_view.clear()
            widget_view.loadImages([image_string_to_qimage(base64_data, img_format = 'PNG')])
            widget_view.show()

    def paste_image_to_viewer_from_clipboard(self, widget_view, base64_string = 'base64_string_temp'):
        self.action.setView(widget_view)
        # Pull image from clibpoard
        img = ImageGrab.grabclipboard()
        # Get raw bytes
        img_bytes = io.BytesIO()
        try:
            img.save(img_bytes, format='PNG')
            # Convert bytes to base64
            base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
            setattr(self, base64_string, base64_data)
            #self.base64_string_temp = base64_data
            widget_view.clear()
            widget_view.loadImages([image_string_to_qimage(base64_data, img_format = 'PNG')])
            widget_view.show()
        except:
            error_pop_up('Fail to paste image from clipboard.','Error')
            return

    def convert_clipboard_buffer_to_base64_string(self):
        # Pull image from clibpoard
        img = ImageGrab.grabclipboard()
        # Get raw bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        # Convert bytes to base64
        base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
        return base64_data, 'PNG'

    def load_graphical_abstract(self,base64_string):
        self.base64_string_temp = base64_string
        qimage = image_string_to_qimage(base64_string, 'PNG')
        self.widget_view.clear()
        self.widget_view.loadImages([qimage])
        self.widget_view.show()

    def load_figure_from_database(self):
        self.action.setView(self.widget_figure_existing)
        paper_id = self.lineEdit_paper_id_figure.text()
        section = self.comboBox_section_figure.currentText()
        tag_name = self.lineEdit_tag_name_figure.text()
        target = self.database[section].find_one({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})
        tag_contents = target['tag_content']
        try:
            figures_strings = [each for each in tag_contents if type(each)==type(b'')]
            figures_qimages = [image_string_to_qimage(each, 'PNG') for each in figures_strings]
            self.widget_figure_existing.clear()
            self.widget_figure_existing.loadImages(figures_qimages)
            self.widget_figure_existing.show()
        except Exception as e:
            error_pop_up('Fail to load figure from database,\n{}'.format(str(e)),'Error')

    def save_figure_to_filesystem(self):
        paper_id = self.lineEdit_paper_id_figure.text()
        section = self.comboBox_section_figure.currentText()
        tag_name = self.lineEdit_tag_name_figure.text()
        target = self.database[section].find_one({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})
        tag_contents = target['tag_content']
        try:
            figures_strings = [base64.decodebytes(each) for each in tag_contents if type(each)==type(b'')]
            if len(figures_strings)!=0:
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                fileName, _ = QFileDialog.getSaveFileName(self, "Save file as", "", "image file (*.png);;all files (*.*)")
                if fileName:
                    for i, each in enumerate(figures_strings):
                        with open(fileName.replace('.','_{}.'.format(i+1)), "wb") as fh:
                            fh.write(each)
                    self.statusbar.showMessage('The figure was saved on local disk successfully!')
        except Exception as e:
            error_pop_up('Fail to save figure to filesystem,\n{}'.format(str(e)),'Error')

    def connect_mongo_server(self):
        #local server connection
        #for mongodb installed with brew on Mac OS
        #for windows the command is simply 'mongod'
        bashCommand = "brew services start mongodb-community@4.4"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        error_pop_up('\n'.join([str(output),str(error)]), ['Information','Error'][int(error=='')])

    def stop_mongo_server(self):
        bashCommand = "brew services stop mongodb-community@4.4"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        error_pop_up('\n'.join([str(output),str(error)]), ['Information','Error'][int(error=='')])

    def start_mongo_client(self):
        try:
            self.mongo_client = MongoClient('localhost:27017')
            self.comboBox_project_list.clear()
            self.comboBox_project_list.addItems(self.get_database_in_a_list())
        except Exception as e:
            error_pop_up('Fail to start mongo client.'+'\n{}'.format(str(e)),'Error')

    def start_mongo_client_cloud(self):
        try:
            if not os.path.exists(os.path.join(script_path,'private','atlas_password')):
                error_pop_up('You should create a file named atlas_password under Project_Manager/private folder, \
                                where you save the atlas url link for your MongoDB atlas cloud account. \
                                please use the format ATLAS_URL="URL LINK"')
            else:
                env = load_dotenv(os.path.join(script_path,'private','atlas_password'))
                if env:
                    url = os.getenv('ATLAS_URL') 
                    self.mongo_client = MongoClient(url,tlsCAFile=certifi.where())
                    self.comboBox_project_list.clear()
                    self.comboBox_project_list.addItems(self.get_database_in_a_list())
                else:
                    url = ''
                    print('something is wrong')
        except Exception as e:
            error_pop_up('Fail to start mongo client.'+'\n{}'.format(str(e)),'Error')

    def get_database_in_a_list(self):
        return self.mongo_client.list_database_names()

    def extract_project_info(self):
        all = self.database.project_info.find()
        self.plainTextEdit_project_info.setPlainText('\n'.join([each['project_info'] for each in all]))

    def load_project(self):
        self.database = self.mongo_client[self.comboBox_project_list.currentText()]
        self.extract_project_info()
        #self.update_paper_list_in_listwidget()
        self.init_pandas_model_from_db()
        self.update_paper_list_in_combobox()
        self.update_tag_list_in_listwidget()
        self.create_instance_for_file_storage()

    def update_project_info(self):
        try:
            self.database.project_info.drop()
            self.database.project_info.insert_many([{'project_info':self.plainTextEdit_project_info.toPlainText()}])
            error_pop_up('Project information has been updated successfully!','Information')
        except Exception as e:
            error_pop_up('Failure to update Project information!','Error')

    def new_project_dialog(self):
        dlg = NewProject(self)
        dlg.exec()

    def creat_a_new_project(self,name_db, db_info,type_db ='paper'):
        self.database = self.mongo_client[name_db]
        if type_db == 'paper':
            self.database.project_info.insert_many([{'project_info':db_info}])
        self.comboBox_project_list.clear()
        self.comboBox_project_list.addItems(self.get_database_in_a_list())
        self.comboBox_project_list.setCurrentText(name_db)
        self.extract_project_info()
        self.create_instance_for_file_storage()

    def create_instance_for_file_storage(self, file_type = 'pdf_file'):
        if not hasattr(self, 'file_worker'):
            self.file_worker = GFS(self.database, file_type)
        else:
            self.file_worker.update_database(self.database)

    def get_papers_in_a_list(self):
        all_info = list(self.database.paper_info.find({},{'_id':0}))
        paper_id_list = [each['paper_id'] for each in all_info]
        return sorted(paper_id_list)

    def update_tag_list_after_delete(self):
        paper_id_list = self.get_papers_in_a_list()
        tags = []
        for each in paper_id_list:
            #collections = ['methods']
            collections = ['questions','methods','results','discussions','terminology','grammer']
            for collection in collections:
                tags += [each_item['tag_name'] for each_item in self.database[collection].find()]
        tags = list(set(tags))
        tags_before = self.get_tags_in_a_list()
        for each in tags_before:
            if each not in tags:
                self.database.tag_info.delete_one({'tag_name':each})
        self.update_tag_list_in_listwidget()

    def update_paper_list_in_listwidget(self):
        papers = self.get_papers_in_a_list()
        papers = ['all'] + papers
        self.listWidget_papers.clear()
        self.listWidget_papers.addItems(papers)
        #also update the paper list in the combobox
        self.update_paper_list_in_combobox()

    def update_paper_list_in_combobox(self):
        papers = self.get_papers_in_a_list()
        self.comboBox_paper_ids_new_input.clear()
        self.comboBox_paper_ids_new_input.addItems(papers)
        self.comboBox_paper_ids.clear()
        self.comboBox_paper_ids.addItems(papers)
        self.comboBox_papers.clear()
        self.comboBox_papers.addItems(papers)
        # self.comboBox_pick_paper.clear()
        # self.comboBox_pick_paper.addItems(papers)

    def rename_tag(self):
        new_tag_name = self.lineEdit_renamed_tag.text()
        original_tag_name = self.comboBox_tags.currentText()
        reply = QMessageBox.question(self, 'Message', 'Sure to rename the tag?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            for collection in self.database.list_collection_names():
                self.database[collection].update_one({'tag_name':original_tag_name},{"$set": {"tag_name":new_tag_name}})
            self.update_tag_list_in_listwidget()
            self.update_tag_list_in_combo()
            self.update_tag_list_in_existing_input()
            self.statusbar.clearMessage()
            self.statusbar.showMessage('The tag was renamed sucessfully!')

    def update_tag_list_in_listwidget(self):
        tags = self.get_tags_in_a_list()
        tags = ['all'] + tags
        self.listWidget_tags.clear()
        self.listWidget_tags.addItems(tags)

    def get_tags_in_a_list(self):
        all_info = [list(self.database['tag_info'].find({},{'_id':0}))]
        tag_list = []
        for each in all_info:
            for each_item in each:
                tag_list.append(each_item['tag_name'])
        return sorted(list(set(tag_list)))

    def update_tag_info_slot(self):
        collection_name = self.comboBox_section_tag_info.currentText()
        tag_name = self.comboBox_tags.currentText() 
        tag_doc = self.textEdit_tag_info.toPlainText()
        self.update_tag_info(tag_name, tag_doc, collection_name, force = True)

    def update_tag_info(self,tag_name, tag_doc, collection_name, force = False):
        try:
            if self.database.tag_info.find_one({'tag_name':tag_name})==None:
                self.database.tag_info.insert_one({'tag_name':tag_name,'tag_content':tag_doc, 'collection_name':collection_name})
                self.statusbar.clearMessage()
                self.statusbar.showMessage('Append tag document info sucessfully!')
            else:
                if force:
                    self.database.tag_info.update_one({'tag_name':tag_name},{"$set": {"tag_content":tag_doc}})
                    self.statusbar.clearMessage()
                    self.statusbar.showMessage('Update tag document info sucessfully!')
                else:
                    if self.database.tag_info.find_one({'tag_name':tag_name})['tag_content']=='':
                        self.database.tag_info.update_one({'tag_name':tag_name},{"$set": {"tag_content":tag_doc}})
                        self.statusbar.clearMessage()
                        self.statusbar.showMessage('Update tag document info sucessfully!')
                    else:
                        pass
        except Exception as e:
            error_pop_up('Fail to append tag document info.\n{}'.format(str(e)),'Error')

    def display_tag_info(self):
        tag_name = self.comboBox_tags.currentText()
        self.textEdit_tag_info.setPlainText(self.database.tag_info.find_one({'tag_name':tag_name})['tag_content'])

    def update_tag_list_in_combo(self):
        collection_name = self.comboBox_section_tag_info.currentText()
        items = self.get_tag_list_by_collection_name(collection_name)
        self.comboBox_tags.clear()
        self.comboBox_tags.addItems(items)

    def get_tag_list_by_collection_name(self, collection_name):
        tag_list = [each['tag_name'] for each in self.database.tag_info.find({'collection_name':collection_name})]
        return sorted(tag_list)

    def update_tag_list_in_existing_input(self):
        collection = self.comboBox_section.currentText()
        paper_id = self.comboBox_paper_ids.currentText()
        tag_list = self.get_tag_list_by_paper_id_and_collection_name(paper_id, collection)
        self.comboBox_tag_list.clear()
        self.comboBox_tag_list.addItems(tag_list)

    def update_tag_list_in_new_input(self):
        collection = self.comboBox_section_new_input.currentText()
        paper_id = self.comboBox_paper_ids_new_input.currentText()
        tag_list = self.get_tag_list_by_paper_id_and_collection_name(paper_id, collection)
        self.comboBox_tag_list_new_input.clear()
        self.comboBox_tag_list_new_input.addItems(tag_list)

    def update_tag_in_new_input(self):
        # self.checkBox_check_tag.setChecked(False)
        self.lineEdit_tag_new_input.setText(self.comboBox_tag_list_new_input.currentText())

    def get_tag_list_by_paper_id_and_collection_name(self,paper_id,collection_name):
        tag_list = [each['tag_name'] for each in self.database[collection_name].find({'paper_id':paper_id})]
        return sorted(tag_list)

    def get_figure_tag_list_by_paper_id_and_collection_name(self):
        paper_id = self.lineEdit_paper_id_figure.text()
        collection_name = self.comboBox_section_figure.currentText()
        tag_list = [each['tag_name'] for each in self.database[collection_name].find({'paper_id':paper_id}) if type(each['tag_content'][0])==type(b'')]
        self.comboBox_fig_tags.clear()
        self.comboBox_fig_tags.addItems(sorted(tag_list))
        #return sorted(tag_list)

    def update_tag_contents_slot(self):
        #paper_id = self.lineEdit_paper_id.text()
        paper_id = self.comboBox_paper_ids.currentText()
        collection = self.comboBox_section.currentText()
        tag_name =  self.comboBox_tag_list.currentText()
        tag_content = self.textEdit_tag_conent.toPlainText()
        location = self.lineEdit_location.text()
        reply = QMessageBox.question(self, 'Message', 'Would you like to update your database with new input?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.update_tag_contents(paper_id, collection, tag_name, tag_content,location)
        else:
            pass

    def delete_tag(self):
        #paper_id = self.lineEdit_paper_id.text()
        paper_id = self.comboBox_paper_ids.currentText()
        collection = self.comboBox_section.currentText()
        tag_name =  self.comboBox_tag_list.currentText()
        #tag_content = self.textEdit_tag_conent.toPlainText()
        #location = self.lineEdit_location.text()
        reply = QMessageBox.question(self, 'Message', 'Are you sure to delete this tag (no way to have the deleted tag content back)?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                self.database[collection].delete_one({'$and':[{'paper_id':paper_id},{'tag_name':tag_name}]})
                self.update_tag_list_after_delete()
                self.update_tag_list_in_listwidget()
                self.statusbar.showMessage('tag {} was deleted!'.format(tag_name))
            except Exception as e:
                error_pop_up('Could not delete the tag {}, since {}'.format(tag_name, str(e)))

    def update_tag_contents(self,paper_id, collection, tag_name, tag_content_in_plain_text,location):
        tag_content_list = tag_content_in_plain_text.rsplit('\n')
        for i, each in enumerate(self.meta_figure_base_strings):
            if each!='':
                tag_content_list[i] = each
            else:
                pass
        self.database[collection].update_one({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]},{ "$set": { "tag_content": tag_content_list}})
        self.database[collection].update_one({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]},{ "$set": { "location": location.rstrip().rsplit(',')}})

    def extract_tag_contents_slot(self):
        #paper_id = self.lineEdit_paper_id.text()
        paper_id = self.comboBox_paper_ids.currentText()
        collection = self.comboBox_section.currentText()
        tag_name =  self.comboBox_tag_list.currentText()
        self.textEdit_tag_conent.setPlainText(self.extract_tag_contents(paper_id, collection, tag_name))
        locations = [each['location'] for each in self.database[collection].find({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})]
        # print(locations)
        if len(locations)!=0:
            self.lineEdit_location.setText(','.join(locations[0]))

    def extract_tag_contents(self, paper_id, collection, tag_name):
        contents = [each['tag_content'] for each in self.database[collection].find({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})]
        self.meta_figure_base_strings = []
        #identify figure string
        if len(contents)!=0:
            for i,each in enumerate(contents[0]):
                if type(each)==type(b''):
                    self.meta_figure_base_strings.append(each)
                    contents[0][i] = '<<figure string>>NOT SHOWING HERE!'
                else:
                    self.meta_figure_base_strings.append('')
        if len(contents)!=0:
            return '\n'.join(contents[0])
        else:
            return ''

    def append_new_input(self):
        #paper_id = self.lineEdit_paper_id_new_input.text()
        paper_id = self.comboBox_paper_ids_new_input.currentText()
        collection = self.comboBox_section_new_input.currentText()
        tag_name = self.lineEdit_tag_new_input.text()
        tag_content = self.textEdit_tag_content_new_input.toPlainText()
        location = self.lineEdit_location_new_input.text()
        if self.checkBox_figure.isChecked():
            if self.base64_string_new_input_temp == '':
                error_pop_up('This is supposed to be a figure tag, please load a figure or paste a figure first!','Error')
                return 
            else:
                #set tag_content to the figure string
                tag_content = self.base64_string_new_input_temp
        if collection in self.database.list_collection_names():
            if self.database[collection].find_one({'$and':[{'tag_name':tag_name},{'paper_id':paper_id}]})==None:
                self.database[collection].insert_one({'paper_id':paper_id,'tag_name':tag_name,'tag_content':[tag_content],'location':[location]})
                self.statusbar.clearMessage()
                self.statusbar.showMessage('New tag content of tag_name {} is inserted!'.format(tag_name))
            else:
                newvalues_tag_content = { "$set": { "tag_content": self.database[collection].find_one({'$and':[{'tag_name':tag_name},{'paper_id':paper_id}]})['tag_content']+[tag_content]}}
                newvalues_tag_location = { "$set": { "location": self.database[collection].find_one({'$and':[{'tag_name':tag_name},{'paper_id':paper_id}]})['location']+[location]}}
                self.database[collection].update_one({'$and':[{'tag_name':tag_name},{'paper_id':paper_id}]},newvalues_tag_content)
                self.database[collection].update_one({'$and':[{'tag_name':tag_name},{'paper_id':paper_id}]},newvalues_tag_location)
                self.statusbar.clearMessage()
                self.statusbar.showMessage('New tag content of tag_name {} is appended!'.format(tag_name))
        else:
            self.database[collection].insert_one({'paper_id':paper_id,'tag_name':tag_name,'tag_content':[tag_content],'location':[location]})
            self.statusbar.clearMessage()
            self.statusbar.showMessage('New tag content of tag_name {} is inserted!'.format(tag_name))
        if self.database.tag_info.find_one({'tag_name':tag_name})==None:
            self.update_tag_info(tag_name,'To be edited!',collection, force = False)
            self.update_tag_list_in_listwidget()
        else:
            pass
        #set this back to ''
        self.base64_string_new_input_temp = ''

    def search_database(self):
        dlg = QueryDialog(self)
        dlg.exec()

    def _and_opt(self, list_1, list_2):
        return_list = []
        if len(list_1)<len(list_2):
            list_1, list_2 = list_2, list_1
        for each in list_1:
            if each in list_2:
                return_list.append(each)
        return return_list

    def _or_opt(self,list_1, list_2):
        return list(set(list_1+list_2))

    def query_by_field(self, field, query_string):
        """[return the paper_ids according the query_string w.r.t the specified field]

        Args:
            field ([string]): in ['full_authors','journal','year','abstract','title']
            query_string ([string]): [the query string you want to perform, e.g. 1999 for field = 'year']

        Returns:
            [list]: [paper_id list]
        """
        index_name = self.database.paper_info.create_index([(field,'text')])
        targets = self.database.paper_info.find({"$text": {"$search": "\"{}\"".format(query_string)}})
        #drop the index afterwards
        return_list = [each['paper_id'] for each in targets]
        self.database.paper_info.drop_index(index_name)
        # print(field, return_list)

        return return_list
        
    def query_info(self):
        fields = ['title','abstract','full_authors','journal','year']
        query_strings = [self.query_string_title, self.query_string_abstract, self.query_string_author, self.query_string_journal, self.query_string_year]
        compound_operators = [self.query_opt_title,self.query_opt_abstract, self.query_opt_author, self.query_opt_journal, self.query_opt_year]
        kept_index = [i for i in range(len(compound_operators)) if (compound_operators[i]!='na' and query_strings[i]!='')]
        def _update(container):
            new = []
            for i,item in enumerate(container):
                if i in kept_index:
                    new.append(item)
            return new
        fields, query_strings, compound_operators = _update(fields), _update(query_strings), _update(compound_operators)
        return_paper_ids = []
        compound_operators[0] = 'or'
        for i, field in enumerate(fields):
            temp_paper_list = self.query_by_field(field, query_strings[i])
            if compound_operators[i]=='and':
                return_paper_ids = self._and_opt(return_paper_ids, temp_paper_list)
            elif compound_operators[i]=='or':
                return_paper_ids = self._or_opt(return_paper_ids, temp_paper_list)
        return return_paper_ids

    def get_papers_by_tag(self, name_db, tag = {'first_author':'qiu'}):
        all_info = list(self.mongo_client[name_db].paper_info.find(tag,{'_id':0}))
        return all_info

    def extract_paper_info(self):
        paper_id = self.comboBox_papers.currentText()
        target = self.database.paper_info.find_one({'paper_id':paper_id})
        #set the pdf block to '' first
        self.lineEdit_pdf.setText('')
        paper_info = {'first_author':self.lineEdit_1st_author.setText,
                      'full_authors':self.lineEdit_full_author.setText,
                      'paper_type':self.lineEdit_paper_type.setText,
                      'journal':self.lineEdit_journal.setText,
                      'volume':self.lineEdit_volume.setText,
                      'issue':self.lineEdit_issue.setText,
                      'page':self.lineEdit_page.setText,
                      'year':self.lineEdit_year.setText,
                      'title':self.lineEdit_title.setText,
                      'url':self.lineEdit_url.setText,
                      'doi':self.lineEdit_doi.setText,
                      'abstract':self.textEdit_abstract.setHtml,
                      'graphical_abstract':self.load_graphical_abstract
                      }
        for key, item in paper_info.items():
            if key in target:
                if key == 'abstract':
                    format_ = '<p style="color:gold;margin-left:20px;">{}</p>'.format
                    item(format_(target[key]))
                else:
                    item(target[key])
            else:
                if key == 'graphical_abstract':
                    pass
                else:
                    item('')
        if not hasattr(self,'file_worker'):
            return
        pdf = self.file_worker._getID(query = {'paper_id':paper_id})
        if pdf!=None:
            self.lineEdit_pdf.setText(str(pdf))
        else:
            self.lineEdit_pdf.setText('Not existing!')

    def new_paper(self):
        """clear input fields and get ready to create a new paper
        """
        self.lineEdit_1st_author.setText('')
        self.lineEdit_full_author.setText('')
        self.lineEdit_paper_type.setText('')
        self.lineEdit_journal.setText('')
        self.lineEdit_volume.setText('')
        self.lineEdit_issue.setText('')
        self.lineEdit_page.setText('')
        self.lineEdit_year.setText('')
        self.lineEdit_title.setText('')
        self.lineEdit_url.setText('')
        self.lineEdit_doi.setText('')
        self.lineEdit_pdf.setText('')
        self.textEdit_abstract.setPlainText('')
        self.widget_view.clear()

    def delete_one_paper(self):
        paper_id = self.comboBox_papers.currentText()
        reply = QMessageBox.question(self, 'Message', 'Are you sure to delete this paper?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                for collection in self.database.list_collection_names():
                    self.database[collection].delete_many({'paper_id':paper_id})
                self.update_tag_list_after_delete()
                self.delete_pdf_file()
                self.statusbar.clearMessage()
                self.statusbar.showMessage('Update the paper info successfully:-)')
                # self.update_paper_list_in_listwidget()
                self.update_paper_list_in_combobox()
            except:
                error_pop_up('Fail to delete the paper info!','Error')

    def delete_pdf_file(self):
        try:
            self.file_worker.remove(self.comboBox_papers.currentText())
        except Exception as e:
            error_pop_up('Fail to delete the pdf file.\n{}'.format(str(e)),'Error')

    def _form_qimage(self,pix):
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        return QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)

    #if use_external_app = True, then open pdf file using system wide default pdf viewer
    #otherwise the pdf pages will be converted to images and be rendered in the app
    def open_pdf_file(self, use_external_app = True):
        # paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
        #paper_id_list = self.pandas_model_paper_info._data[self.pandas_model_paper_info._data['select']]['paper_id'].tolist()
        paper_id_list = [self.comboBox_papers.currentText()]
        if len(paper_id_list)>0:
            paper_id = paper_id_list[0]
            try:
                full_path = self.file_worker.write_2_disk(paper_id, os.path.join(script_path,'temp_pdf_files'))
                if use_external_app:
                    webbrowser.open_new(r'file://{}'.format(full_path))
                else:
                    doc = fitz.open(full_path)
                    qimages = [self._form_qimage(each.getPixmap(matrix = fitz.Matrix(3,3))) for each in doc]
                    self.doc_pdf = doc
                    self.widget_pdf_viewer.loadImages(qimages)
            except Exception as e:
                error_pop_up('Fail to open the pdf file.\n{}'.format(str(e)),'Error')
        else:
            pass

    def update_paper_info(self):
        paper_id = self.comboBox_papers.currentText()
        original = self.database.paper_info.find_one({'paper_id':paper_id})
        paper_info_new = {
                      'paper_id':paper_id,
                      'first_author':self.lineEdit_1st_author.text(),
                      'full_authors':self.lineEdit_full_author.text(),
                      'paper_type':self.lineEdit_paper_type.text(),
                      'journal':self.lineEdit_journal.text(),
                      'volume':self.lineEdit_volume.text(),
                      'issue':self.lineEdit_issue.text(),
                      'page':self.lineEdit_page.text(),
                      'year':self.lineEdit_year.text(),
                      'title':self.lineEdit_title.text(),
                      'url':self.lineEdit_url.text(),
                      'doi':self.lineEdit_doi.text(),
                      'abstract':self.textEdit_abstract.toPlainText().replace('\n',' '),
                      'graphical_abstract':self.base64_string_temp
                    }
        paper_info_new['select'] = original['select']
        paper_info_new['archive_date'] = original['archive_date']
        paper_info_new['user_label'] = original['user_label']
        paper_info_new['read_level'] = original['read_level']
        try:        
            reply = QMessageBox.question(self, 'Message', 'Would you like to update your database with new input?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.database.paper_info.replace_one(original,paper_info_new)
                #also update the pdf file
                if os.path.exists(self.lineEdit_pdf.text()):
                    self.file_worker.remove(paper_id)
                    self.file_worker.insertFile(filePath = self.lineEdit_pdf.text(),paper_id = paper_id)
            self.statusbar.clearMessage()
            self.statusbar.showMessage('Update the paper info successfully:-)')
        except Exception as e:
            error_pop_up('Fail to update the paper info :-(\n{}'.format(str(e)),'Error')

    #the buffer must be a complete string of bibtex record including paranthesis
    def fill_input_fields_from_clipboard_buffer(self):
        bib_database = bibtexparser.loads(clipboard.paste())
        if len(bib_database.entries)==0:
            return
        record_list = bib_database.get_entry_list()
        for each_record in record_list:
            paper_info = {'first_author':'',
                        'full_authors':each_record.get('author','Author'),
                        'paper_type':each_record.get('ENTRYTYPE','research article'),
                        'journal':each_record.get('journal',''),
                        'volume':each_record.get('volume',''),
                        'issue':each_record.get('number',''),
                        'page':each_record.get('pages',''),
                        'year':each_record.get('year',''),
                        'title':each_record.get('title',''),
                        'url':each_record.get('url',''),
                        'doi':each_record.get('doi',''),
                        'abstract':each_record.get('abstract',''),
                        'graphical_abstract':image_to_64base_string(os.path.join(script_path,'icons','no_graphical_abstract.png'))
                        }
            paper_info['first_author'] = paper_info['full_authors'].rstrip().rsplit(',')[0]
            #remove space in url link
            paper_info['url'] = paper_info['url'].rstrip().replace('\n','').replace(' ','')
            self.add_paper_info(parser = paper_info)

    #import bibtex file
    def import_bibtex(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","bibtex file (*.bib);;all Files (*.*)", options=options)
        if fileName:
            with open(fileName) as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)
        else:
            return
        record_list = bib_database.get_entry_list()
        for each_record in record_list:
            paper_info = {'first_author':each_record.get('first_author',''),
                        'full_authors':each_record.get('author','Author'),
                        'paper_type':each_record.get('paper_type','research article'),
                        'journal':each_record.get('journal',''),
                        'volume':each_record.get('volume',''),
                        'issue':each_record.get('number',''),
                        'page':each_record.get('pages',''),
                        'year':each_record.get('year',''),
                        'title':each_record.get('title',''),
                        'url':each_record.get('url',''),
                        'doi':each_record.get('doi',''),
                        'abstract':each_record.get('abstract',''),
                        'graphical_abstract':image_to_64base_string(os.path.join(script_path,'icons','no_graphical_abstract.png'))
                        }
            if paper_info['first_author'] == '':
                paper_info['first_author'] = paper_info['full_authors'].rstrip().rsplit(',')[0]
            #remove space in url link
            paper_info['url'] = paper_info['url'].rstrip().replace('\n','').replace(' ','')
            self.add_paper_info(parser = paper_info)

    def export_bibtex(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName,_ = QFileDialog.getSaveFileName(self,"QFileDialog.getOpenFileName()", "","bibtex file (*.bib);;all Files (*.*)", options=options)
        if fileName:
            # paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
            paper_id_list = self.pandas_model_paper_info._data[self.pandas_model_paper_info._data['select']]['paper_id'].tolist()
            if len(paper_id_list)==0:
                paper_id_list = ['all']
            if 'all' in paper_id_list:
                paper_id_list = self.get_papers_in_a_list()
            record_list = []
            bibtex_list = []
            record_list = list(self.database.paper_info.find({'paper_id':{'$in':paper_id_list}}))
            keys_map = {'author':'full_authors',
                        'ID':'paper_id',
                        'first_author':'first_author',
                        'journal':'journal',
                        'volume':'volume',
                        'number':'issue',
                        'pages':'page',
                        'year':'year',
                        'title':'title',
                        'url':'url',
                        'doi':'doi',
                        'abstract':'abstract',
                        'paper_type':'paper_type'
                        }
            for record in record_list:
                temp_info = {}
                for key_bibtex, key_database in keys_map.items():
                    temp_info[key_bibtex] = record.get(key_database,'')
                temp_info['ENTRYTYPE'] = 'article'
                bibtex_list.append(temp_info)
            db = BibDatabase()
            db.entries = bibtex_list
            writer = BibTexWriter()
            writer.indent = '    '     # indent entries with 4 spaces instead of one
            writer.comma_first = True  # place the comma at the beginning of the line
            with open(fileName, 'w') as bibfile:
                bibfile.write(writer.write(db))
                self.statusbar.showMessage('Bibtex file is exported successfully!')

    #create a new paper record in database
    def add_paper_info(self, parser = None):
        paper_info = {'first_author':self.lineEdit_1st_author.text(),
                      'full_authors':self.lineEdit_full_author.text(),
                      'paper_type':self.lineEdit_paper_type.text(),
                      'journal':self.lineEdit_journal.text(),
                      'volume':self.lineEdit_volume.text(),
                      'issue':self.lineEdit_issue.text(),
                      'page':self.lineEdit_page.text(),
                      'year':self.lineEdit_year.text(),
                      'title':self.lineEdit_title.text(),
                      'url':self.lineEdit_url.text(),
                      'doi':self.lineEdit_doi.text(),
                      'abstract':self.textEdit_abstract.toPlainText().replace('\n',' '),
                      'graphical_abstract':self.base64_string_temp
                      }
        if parser!=None:
            paper_info = parser
        paper_id_temp = paper_info['first_author']+'_'+paper_info['year']+'_'
        papers = self.get_papers_in_a_list()
        i = 1
        while True:
            if paper_id_temp + str(i) in papers:
                i = i + 1
            else:
                paper_id_temp = paper_id_temp + str(i)
                break
        paper_info['paper_id'] = paper_id_temp
        paper_info['select'] = False
        paper_info['archive_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
        paper_info['user_label'] = 'user_label'
        paper_info['read_level'] = 0

        # if os.path.exists(self.lineEdit_pdf.text()):
            # self.file_worker.insertFile(filePath = self.lineEdit_pdf.text(),paper_id = paper_id_temp)
        try:
            self.database.paper_info.insert_one(paper_info)
            self.statusbar.clearMessage()
            self.statusbar.showMessage('Append the paper info sucessfully!')
            #also store the pdf file
            if parser==None:
                if os.path.exists(self.lineEdit_pdf.text()):
                    self.file_worker.insertFile(filePath = self.lineEdit_pdf.text(),paper_id = paper_id_temp)
                    self.statusbar.showMessage('Archive PDF file sucessfully!')
            else:
                pass
            #self.update_paper_list_in_listwidget()
            self.init_pandas_model_from_db()
            self.update_paper_list_in_combobox()
            self.comboBox_papers.setCurrentText(paper_id_temp)
        except Exception as e:
            error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error')



    def extract_all_info(self):
        #extract tag content from collection
        def make_text(text_box, collection):
            target = self.database[collection].find({'paper_id':paper_id_list[0]})
            # text_box.append('\n##{}##'.format(collection))
            text_box.append('<br><h3 style="color:Magenta;margin-left:0px;">{}</h3>'.format('{}'.format(collection)))
            ii = 0
            for each in target:
                ii += 1
                # text_box.append('  '+each['tag_name'])
                text_box.append('<h3 style="color:yellow;margin-left:40px;">{}</h3>'.format(each['tag_name']))
                for i,each_tag_content in enumerate(each['tag_content']):
                    if type(each_tag_content)==type(b''):
                        each_tag_content = '<p style="margin-left:60px;"><img src="data:image/png;base64,{}" max-height="600px"/></p>'.format(each_tag_content.decode('utf-8'))
                        if i>=len(each['location']):
                            text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>{}'.format('{}.@(page_{}):'.format(i+1,each['location'][-1]),each_tag_content))
                        else:
                            text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>{}'.format('{}.@(page_{}):'.format(i+1,each['location'][i]),each_tag_content))
                    else:
                        if i>=len(each['location']):
                            text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>'.format('{}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content)))
                        else:
                            text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>'.format('{}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content)))
            if ii == 0:
                text_box.pop()
            return text_box

        #extract tag conent from collection with tag_name for papers with paper_ids
        #@ray.remote
        def make_text2(text_box, collection, tag_name, paper_id_list):
        #def make_text2(text_box, collection, tag_name, paper_id_list):
            # text_box.append('\n##{}##'.format(collection))
            if collection not in self.database.list_collection_names():
                return text_box
            paper_id_list = list(set([each['paper_id'] for each in self.database[collection].find({})]))
            append_times = 1
            collection_text = '<br><h2 style="color:Magenta;margin-left:0px;">{}</h2>'.format('{}'.format(collection))
            if collection_text not in text_box:
                text_box.append(collection_text)
                append_times = 2
            # text_box.append('  '+tag_name)
            text_box.append('<h3 style="color:yellow;margin-left:40px;">{}</h3>'.format(tag_name))
            jj = 0
            print('Working on {}'.format(tag_name))
            for paper_id in paper_id_list:
                print('  Working on {}'.format(paper_id))
                # text_box.append('    '+paper_id)
                text_box.append('<h3 style="color:green;margin-left:60px;">{}</h3>'.format(paper_id))
                target = self.database[collection].find({'$and':[{'paper_id':paper_id},{'tag_name':tag_name}]})
                # target = database[collection].find({'$and':[{'paper_id':paper_id},{'tag_name':tag_name}]})
                ii = 0
                for each in target:
                    ii += 1
                    for i,each_tag_content in enumerate(each['tag_content']):
                        if type(each_tag_content)==type(b''):
                            each_tag_content = '<p style="margin-left:60px;"><img src="data:image/png;base64,{}" max-height="600px"/></p>'.format(each_tag_content.decode('utf-8'))
                            # jj+=1
                            if i>=len(each['location']):
                                text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>{}'.format('{}.@(page_{}):'.format(i+1,each['location'][-1]),each_tag_content))
                                jj+=1
                            else:
                                text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>{}'.format('{}.@(page_{}):'.format(i+1,each['location'][i]),each_tag_content))
                                jj+=1
                        else:
                            if i>=len(each['location']):
                                text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>'.format('{}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content)))
                                jj+=1
                            else:
                                text_box.append('<p style="color:white;margin-left:60px;background-color: gray;">{}</p>'.format('{}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content)))
                                jj+=1
                if ii == 0:
                    text_box.pop()
            if jj==0:#if not record is found then delete the header info
                for i in range(append_times):
                    text_box.pop()
            return text_box

        text_box = []
        #paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
        paper_id_list = self.pandas_model_paper_info._data[self.pandas_model_paper_info._data['select']]['paper_id'].tolist()
        tag_list = [item.text() for item in self.listWidget_tags.selectedItems()]
        if 'all' in paper_id_list:
            paper_id_list = self.get_papers_in_a_list()
        if 'all' in tag_list:
            tag_list = self.get_tags_in_a_list()
        if len(paper_id_list)==1:
            # text_box.append(paper_id_list[0])
            text_box.append('<h1 style="color:Magenta;margin-left:0px;">{}</h1>'.format(paper_id_list[0]))
            #extract paper info
            # text_box.append('##paper_info##')
            text_box.append('<h2 style="color:Magenta;margin-left:0px;">{}</h2>'.format('paper_info'))
            #text_box.append('##paper_info##')
            target = self.database.paper_info.find_one({'paper_id':paper_id_list[0]})
            keys = ['first_author','journal','year','title','url','doi']
            for each_key in keys:
                # text_box.append('{}:  {}'.format('  '+each_key,target[each_key]))
                text_box.append('<p style="color:white;margin-left:20px;background-color: gray;">{}</p>'.format('{}:  {}'.format('  '+each_key,target[each_key])))
            collections = ['questions','methods','results','discussions','terminology','grammer']
            for each in collections:
                text_box = make_text(text_box, each)
        elif len(paper_id_list)>1:
            collections = ['questions','methods','results','discussions','terminology','grammer']
            collections = [each for each in collections if each in self.database.list_collection_names()]
            for each in collections:
                # tag_names = [each_item['tag_name'] for each_item in self.database.tag_info.find({'collection_name':each})]
                # tag_names = [each_item['tag_name'] for each_item in self.database.tag_info.find({'collection_name':each})]
                # text_makers = [make_text_ray.remote(each, each_tag, paper_id_list, self.database) for each_tag in tag_list]
                # [maker.make_text.remote() for maker in text_makers]
                # results = [maker.get_text_box.remote() for maker in text_makers]
                # text_box = sum(ray.get(results),[])
                for each_tag in tag_list:
                    text_box = make_text2(text_box, each, each_tag, paper_id_list)
        # self.plainTextEdit_query_info.setPlainText('\n'.join(text_box))
        self.plainTextEdit_query_info.setHtml(''.join(text_box))
        self.tabWidget.setCurrentIndex(1)

    def extract_info_with_tag_for_one_paper(self,paper,tag):
        return list(self.database[paper].find({'tag_name':tag}))
    
    def open_url_in_webbrowser(self):
        # paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
        paper_id_list = self.pandas_model_paper_info._data[self.pandas_model_paper_info._data['select']]['paper_id'].tolist()
        if 'all' in paper_id_list:
            paper_id_list = self.get_papers_in_a_list()
        if len(paper_id_list) != 0:
            for paper_id in paper_id_list:
                url = self.database.paper_info.find_one({'paper_id':paper_id})['url']
                if url!='':
                    webbrowser.open(url)

    def update_paper_info_once(self):
        myquery = { "paper_id": { "$regex": ".*?"}}
        newvalues = { "$set": { "select": 'False', "archive_date":'2020-04-20','user_label':'user_label','read_level':'0'}}
        self.database.paper_info.update_many(myquery, newvalues)

    def update_meta_info_paper(self, paper_id):
        myquery = { "paper_id": paper_id}
        sub_data = self.pandas_model_paper_info._data[self.pandas_model_paper_info._data['paper_id'] == paper_id]
        # print(sub_data)
        newvalues = { "$set": { "select": str(sub_data['select'].tolist()[0]), "archive_date":str(sub_data['archive_date'].tolist()[0]),'user_label':str(sub_data['user_label'].tolist()[0]),'read_level':str(sub_data['read_level'].tolist()[0])}}
        self.database.paper_info.update_one(myquery, newvalues)

    def init_pandas_model_from_db(self):
        data = {'select':[],'paper_id':[],'year':[],'journal':[],'archive_date':[],'user_label':[],'read_level':[]}
        for each in self.database.paper_info.find():
            data['select'].append(each.get('select','True'))
            data['paper_id'].append(each['paper_id'])
            # data['title'].append(each['title'])
            data['year'].append(each['year'])
            data['journal'].append(each['journal'])
            data['archive_date'].append(each.get('archive_date','2020-04-20'))
            data['user_label'].append(each.get('user_label','user_label'))
            data['read_level'].append(each.get('read_level','0'))
        data = pd.DataFrame(data)
        data['select'] = data['select'].astype(bool)
        self.pandas_model_paper_info = PandasModel(data = data, tableviewer = self.tableView_paper_info, main_gui = self)
        self.tableView_paper_info.setModel(self.pandas_model_paper_info)
        self.tableView_paper_info.resizeColumnsToContents()
        self.tableView_paper_info.setSelectionBehavior(PyQt5.QtWidgets.QAbstractItemView.SelectRows)

class NewProject(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(script_path,"new_project_dialog.ui"), self)
        self.pushButton_ok.clicked.connect(lambda:parent.creat_a_new_project(name_db = self.lineEdit_name.text(), 
                                                                             db_info = self.textEdit_introduction.toPlainText(),
                                                                             type_db ='paper'))
        self.pushButton_cancel.clicked.connect(lambda:self.close())

class QueryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Load the dialog's GUI
        uic.loadUi(os.path.join(script_path,"query_dialog.ui"), self)
        self.pushButton_clear.clicked.connect(self.clear_fields)
        self.pushButton_search.clicked.connect(self.search)
        self.pushButton_exit.clicked.connect(lambda:self.close())
    
    def clear_fields(self):
        self.lineEdit_title.setText('')
        self.lineEdit_abstract.setText('')
        self.lineEdit_author.setText('')
        self.lineEdit_journal.setText('')
        self.lineEdit_year.setText('')

    def search(self):
        self.parent.query_string_title = self.lineEdit_title.text()
        self.parent.query_string_abstract = self.lineEdit_abstract.text()
        self.parent.query_string_author = self.lineEdit_author.text()
        self.parent.query_string_journal = self.lineEdit_journal.text()
        self.parent.query_string_year = self.lineEdit_year.text()

        self.parent.query_opt_title = self.comboBox_title.currentText()
        self.parent.query_opt_abstract = self.comboBox_abstract.currentText()
        self.parent.query_opt_author = self.comboBox_author.currentText()
        self.parent.query_opt_journal = self.comboBox_journal.currentText()
        self.parent.query_opt_year = self.comboBox_year.currentText()

        self.parent.database.paper_info.drop_indexes()

        paper_ids = self.parent.query_info()
        text_box = []

        #self.textEdit_query_info.setText('\n'.join(self.parent.query_info()))
        for each in paper_ids:
            text_box.append(each)
            #extract paper info
            text_box.append('##paper_info##')
            target = self.parent.database.paper_info.find_one({'paper_id':each})
            keys = ['full_authors','journal','year','title','url','doi','abstract']
            for each_key in keys:
                text_box.append('{}:  {}'.format('  '+each_key,target[each_key]))
            text_box.append('\n')
        self.textEdit_query_info.setText('\n'.join(text_box))

#class to store to and rechieve file from database
class GFS(object):
    def __init__(self, db, file_table = 'pdf_file'):
        self.db = db
        self.file_table = file_table
        self.fs = GridFS(db, file_table)
 
    def update_database(self, new_db):
        self.db = new_db
        #the collection name will be '{}.files'.format(self.file_table)
        self.fs = GridFS(new_db, self.file_table)

    def insertFile(self,filePath,paper_id): #将文件存入数据表
        if self.fs.exists({'paper_id':paper_id}):
            error_pop_up('The file is existent already.','Error')
        else:
            with open(filePath,'rb') as fileObj:
                data = fileObj.read()
                ObjectId = self.fs.put(data,filename = ntpath.basename(filePath),paper_id = paper_id)
                #print(ObjectId)
                #fileObj.close()
            return ObjectId
 
    def _getID(self,query): #通过文件属性获取文件ID，ID为文件删除、文件读取做准备
        target = self.db['{}.{}'.format(self.file_table,'files')].find_one(query)
        if target!=None:
            return target['_id']
        else:
            return None
 
    def getFile(self,paper_id): #获取文件属性，并读出二进制数据至内存
        id = self._getID({'paper_id':paper_id})
        if id==None:
            error_pop_up('No record with paper_id of {}'.format(paper_id),'Error')
            return None
        gf = self.fs.get(id)
        bdata=gf.read() #二进制数据
        attri={} #文件属性信息
        attri['chunk_size']=gf.chunk_size
        attri['length']=gf.length
        attri["upload_date"] = gf.upload_date
        attri["filename"] = gf.filename
        attri['md5']=gf.md5
        # error_pop_up(str('success to get file with attri of {}'.format(attri)),'Information')
        return (bdata, attri)

    def write_2_disk(self, paper_id, path = None): #将二进制数据存入磁盘
        # id = self._getID({'paper_id':paper_id})
        results = self.getFile(paper_id)
        if results == None:
            return
        bdata, attri = results
        #name = attri['filename']
        name = '{}.pdf'.format(paper_id)
        if path!=None:
            name = os.path.join(path, name)
        if not os.path.exists(name):
            output = open(name, 'wb')
            output.write(bdata)
            output.close()
        else:
            pass
        # error_pop_up("Success to fetch and save file with filename of {}!".format(name),'Information')
        return name
 
    def remove(self,paper_id): #文件数据库中数据的删除
        id = self._getID({'paper_id':paper_id})
        if id == None:
            error_pop_up('No record with paper_id of {}'.format(paper_id),'Error')
            return
        self.fs.delete(id) #只能是id       
        # error_pop_up('success to delete the file of id {}'.format(id))

if __name__ == "__main__":
    QApplication.setStyle("windows")
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())