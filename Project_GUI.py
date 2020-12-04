import sys,os,qdarkstyle
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog, QMenu
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QCursor
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
import time
import matplotlib
matplotlib.use("TkAgg")
try:
    import ConfigParser
except:
    import configparser as ConfigParser
import sys,os
import subprocess
from pymongo import MongoClient
import webbrowser
import qpageview.viewactions
import base64
from PIL import ImageGrab
import io
import codecs

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

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        uic.loadUi(os.path.join(script_path,'project_manager.ui'),self)
        self.setWindowTitle('Scientific Project Manager')
        self.base64_string_temp = ''
        self.base64_string_new_input_temp = ''
        self.meta_figure_base_strings = []
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
        self.widget_terminal.update_name_space('main_gui',self)
        self.pushButton_start_server.clicked.connect(self.connect_mongo_server)
        self.pushButton_stop_server.clicked.connect(self.stop_mongo_server)
        self.pushButton_start_client.clicked.connect(self.start_mongo_client)
        self.pushButton_new_project.clicked.connect(self.new_project_dialog)
        self.pushButton_update_project_info.clicked.connect(self.update_project_info)
        self.pushButton_load.clicked.connect(self.load_project)
        self.pushButton_add_new_paper.clicked.connect(self.add_paper_info)
        self.comboBox_tags.currentIndexChanged.connect(self.display_tag_info)
        self.comboBox_section_tag_info.currentIndexChanged.connect(self.update_tag_list_in_combo)
        self.pushButton_update_tag_info.clicked.connect(self.update_tag_info_slot)
        self.pushButton_append_info_new_input.clicked.connect(self.append_new_input)
        self.comboBox_tag_list.currentIndexChanged.connect(self.extract_tag_contents_slot)
        self.pushButton_update_info.clicked.connect(self.update_tag_contents_slot)
        self.comboBox_section.currentIndexChanged.connect(self.update_tag_list_in_existing_input)
        self.pushButton_hide_show.clicked.connect(lambda:self.frame_3.setVisible(not self.frame_3.isVisible()))
        self.pushButton_extract_selected.clicked.connect(self.extract_all_info)
        self.comboBox_papers.currentIndexChanged.connect(self.extract_paper_info)
        self.pushButton_update_paper.clicked.connect(self.update_paper_info)
        self.pushButton_remove_paper.clicked.connect(self.delete_one_paper)
        self.pushButton_rename.clicked.connect(self.rename_tag)
        self.pushButton_open_url.clicked.connect(self.open_url_in_webbrowser)
        self.pushButton_paste_image.clicked.connect(lambda:self.paste_image_to_viewer_from_clipboard(self.widget_view,'base64_string_temp'))
        self.pushButton_open_image.clicked.connect(lambda:self.open_image_file(self.widget_view,'base64_string_temp'))
        self.pushButton_paste_figure.clicked.connect(lambda:self.paste_image_to_viewer_from_clipboard(self.widget_figure_input,'base64_string_new_input_temp'))
        self.pushButton_load_figure.clicked.connect(lambda:self.open_image_file(self.widget_figure_input,'base64_string_new_input_temp'))
        self.pushButton_extract_figure.clicked.connect(self.load_figure_from_database)

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

    def get_database_in_a_list(self):
        return self.mongo_client.list_database_names()

    def extract_project_info(self):
        all = self.database.project_info.find()
        self.plainTextEdit_project_info.setPlainText('\n'.join([each['project_info'] for each in all]))

    def load_project(self):
        self.database = self.mongo_client[self.comboBox_project_list.currentText()]
        self.extract_project_info()
        self.update_paper_list_in_listwidget()
        self.update_tag_list_in_listwidget()

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

    def get_papers_in_a_list(self):
        all_info = list(self.database.paper_info.find({},{'_id':0}))
        paper_id_list = [each['paper_id'] for each in all_info]
        return sorted(paper_id_list)

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
        return sorted(tag_list)

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

    def get_tag_list_by_paper_id_and_collection_name(self,paper_id,collection_name):
        tag_list = [each['tag_name'] for each in self.database[collection_name].find({'paper_id':paper_id})]
        return sorted(tag_list)

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
        if self.checkBox_check_tag.isChecked():
            if tag_name in self.get_tags_in_a_list():
                error_pop_up('This is supposed to be a new tag, but the tag you provided is already existed. \nPick a different one please! If it is supposed to be an existed tag, check off the newtag checkbox! And do again!','Error')
                return
        if self.checkBox_figure.isChecked():
            if self.base64_string_new_input_temp == '':
                error_pop_up('This is supposed to be a figure tag, please load a figure or paste a figure first!','Error')
                return 
            else:
                #set tag_content to the figure string
                tag_content = self.base64_string_new_input_temp
        if collection in self.database.list_collection_names():
            if self.database[collection].find_one({'tag_name':tag_name})==None:
                self.database[collection].insert_one({'paper_id':paper_id,'tag_name':tag_name,'tag_content':[tag_content],'location':[location]})
                # self.update_tag_info(tag_name,'To be edited!',collection, force = False)
            else:
                newvalues_tag_content = { "$set": { "tag_content": self.database[collection].find_one({'tag_name':tag_name})['tag_content']+[tag_content]}}
                newvalues_tag_location = { "$set": { "location": self.database[collection].find_one({'tag_name':tag_name})['location']+[location]}}
                self.database[collection].update_one({'tag_name':tag_name},newvalues_tag_content)
                self.database[collection].update_one({'tag_name':tag_name},newvalues_tag_location)
        else:
            self.database[collection].insert_one({'paper_id':paper_id,'tag_name':tag_name,'tag_content':[tag_content],'location':[location]})
        if self.database.tag_info.find_one({'tag_name':tag_name})==None:
            self.update_tag_info(tag_name,'To be edited!',collection, force = False)
            self.update_tag_list_in_listwidget()
        else:
            pass
        #set this back to ''
        self.base64_string_new_input_temp = ''

    def get_papers_by_tag(self, name_db, tag = {'first_author':'qiu'}):
        all_info = list(self.mongo_client[name_db].paper_info.find(tag,{'_id':0}))
        return all_info

    def extract_paper_info(self):
        paper_id = self.comboBox_papers.currentText()
        target = self.database.paper_info.find_one({'paper_id':paper_id})
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
                      'abstract':self.textEdit_abstract.setPlainText,
                      'graphical_abstract':self.load_graphical_abstract
                      }
        for key, item in paper_info.items():
            if key in target:
                item(target[key])
            else:
                if key == 'graphical_abstract':
                    pass
                else:
                    item('')

    def delete_one_paper(self):
        paper_id = self.comboBox_papers.currentText()
        reply = QMessageBox.question(self, 'Message', 'Are you sure to delete this paper?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                for collection in self.database.list_collection_names():
                    self.database[collection].delete_many({'paper_id':paper_id})
                self.statusbar.clearMessage()
                self.statusbar.showMessage('Update the paper info successfully:-)')
                self.update_paper_list_in_listwidget()
            except:
                error_pop_up('Fail to delete the paper info!','Error')

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
        try:        
            reply = QMessageBox.question(self, 'Message', 'Would you like to update your database with new input?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.database.paper_info.replace_one(original,paper_info_new)
            self.statusbar.clearMessage()
            self.statusbar.showMessage('Update the paper info successfully:-)')
        except Exception as e:
            error_pop_up('Fail to update the paper info :-(\n{}'.format(str(e)),'Error')

    #create a new paper record in database
    def add_paper_info(self):
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
        try:
            self.database.paper_info.insert_one(paper_info)
            self.statusbar.clearMessage()
            self.statusbar.showMessage('Append the paper info sucessfully!')
            self.update_paper_list_in_listwidget()
        except Exception as e:
            error_pop_up('Failure to append paper info!\n{}'.format(str(e)),'Error')

    def extract_all_info(self):
        text_box = []
        paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
        tag_list = [item.text() for item in self.listWidget_tags.selectedItems()]

        #extract tag content from collection
        def make_text(text_box, collection):
            target = self.database[collection].find({'paper_id':paper_id_list[0]})
            text_box.append('\n##{}##'.format(collection))
            ii = 0
            for each in target:
                ii += 1
                text_box.append('  '+each['tag_name'])
                for i,each_tag_content in enumerate(each['tag_content']):
                    if type(each_tag_content)==type(b''):
                        each_tag_content = '<<figure string>>NOT SHOWING HERE!'
                    if i>=len(each['location']):
                        text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content))
                    else:
                        text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content))
            if ii == 0:
                text_box.pop()
            return text_box

        #extract tag conent from collection with tag_name for papers with paper_ids
        def make_text2(text_box, collection, tag_name, paper_id_list):
            text_box.append('\n##{}##'.format(collection))
            text_box.append('  '+tag_name)
            jj = 0
            for paper_id in paper_id_list:
                text_box.append('    '+paper_id)
                target = self.database[collection].find({'$and':[{'paper_id':paper_id},{'tag_name':tag_name}]})
                ii = 0
                for each in target:
                    ii += 1
                    for i,each_tag_content in enumerate(each['tag_content']):
                        if type(each_tag_content)==type(b''):
                            each_tag_content = '<<figure string>>NOT SHOWING HERE!'
                            jj+=1
                        if i>=len(each['location']):
                            text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content))
                            jj+=1
                        else:
                            text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content))
                            jj+=1
                if ii == 0:
                    text_box.pop()
            if jj==0:#if not record is found then delete the header info
                text_box.pop()
                text_box.pop()
            return text_box

        if 'all' in paper_id_list:
            paper_id_list = self.get_papers_in_a_list()
        if 'all' in tag_list:
            tag_list = self.get_tags_in_a_list()
        if len(paper_id_list)==1:
            text_box.append(paper_id_list[0])
            #extract paper info
            text_box.append('##paper_info##')
            target = self.database.paper_info.find_one({'paper_id':paper_id_list[0]})
            keys = ['first_author','journal','year','title','url','doi']
            for each_key in keys:
                text_box.append('{}:  {}'.format('  '+each_key,target[each_key]))
            collections = ['questions','methods','results','discussions','terminology','grammer']
            for each in collections:
                text_box = make_text(text_box, each)
        elif len(paper_id_list)>1:
            collections = ['questions','methods','results','discussions','terminology','grammer']
            for each in collections:
                # tag_names = [each_item['tag_name'] for each_item in self.database.tag_info.find({'collection_name':each})]
                # tag_names = [each_item['tag_name'] for each_item in self.database.tag_info.find({'collection_name':each})]
                for each_tag in tag_list:
                    text_box = make_text2(text_box, each, each_tag, paper_id_list)
        self.plainTextEdit_query_info.setPlainText('\n'.join(text_box))

    def extract_info_with_tag_for_one_paper(self,paper,tag):
        return list(self.database[paper].find({'tag_name':tag}))
    
    def open_url_in_webbrowser(self):
        paper_id_list = [item.text() for item in self.listWidget_papers.selectedItems()]
        if 'all' in paper_id_list:
            paper_id_list = self.get_papers_in_a_list()
        if len(paper_id_list) != 0:
            for paper_id in paper_id_list:
                url = self.database.paper_info.find_one({'paper_id':paper_id})['url']
                if url!='':
                    webbrowser.open(url)
                

class NewProject(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi(os.path.join(script_path,"new_project_dialog.ui"), self)
        self.pushButton_ok.clicked.connect(lambda:parent.creat_a_new_project(name_db = self.lineEdit_name.text(), 
                                                                             db_info = self.textEdit_introduction.toPlainText(),
                                                                             type_db ='paper'))
        self.pushButton_cancel.clicked.connect(lambda:self.close())

if __name__ == "__main__":
    QApplication.setStyle("windows")
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())