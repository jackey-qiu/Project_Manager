import sys,os,qdarkstyle
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import uic, QtCore
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

class MyMainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MyMainWindow, self).__init__(parent)
        uic.loadUi(os.path.join(script_path,'project_manager.ui'),self)
        self.widget_terminal.update_name_space('main_gui',self)
        self.pushButton_start_server.clicked.connect(self.connect_mongo_server)
        self.pushButton_stop_server.clicked.connect(self.stop_mongo_server)
        self.pushButton_new_project.clicked.connect(self.new_project_dialog)
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

    def connect_mongo_server(self):
        #local server connection
        #for mongodb installed with brew on Mac OS
        #for windows the command is simply 'mongod'
        bashCommand = "brew services start mongodb-community@4.4"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        error_pop_up('\n'.join([str(output),str(error)]), ['Information','Error'][int(error=='')])
        try:
            self.start_mongo_client()
            self.comboBox_project_list.clear()
            self.comboBox_project_list.addItems(self.get_database_in_a_list())
        except Exception as e:
            error_pop_up('Fail to start mongo client.'+'\n{}'.format(str(e)),'Error')

    def stop_mongo_server(self):
        bashCommand = "brew services stop mongodb-community@4.4"
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        error_pop_up('\n'.join([str(output),str(error)]), ['Information','Error'][int(error=='')])

    def start_mongo_client(self):
        self.mongo_client = MongoClient('localhost:27017')

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
        return paper_id_list

    def update_paper_list_in_listwidget(self):
        papers = self.get_papers_in_a_list()
        papers = ['all'] + papers
        self.listWidget_papers.clear()
        self.listWidget_papers.addItems(papers)

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
        return tag_list

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
                        #print('I am here!')
                        #print(self.database.tag_info.find_one({'tag_name':tag_name}))
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
        return tag_list

    def update_tag_list_in_existing_input(self):
        collection = self.comboBox_section.currentText()
        paper_id = self.lineEdit_paper_id.text()
        tag_list = self.get_tag_list_by_paper_id_and_collection_name(paper_id, collection)
        self.comboBox_tag_list.clear()
        self.comboBox_tag_list.addItems(tag_list)

    def get_tag_list_by_paper_id_and_collection_name(self,paper_id,collection_name):
        tag_list = [each['tag_name'] for each in self.database[collection_name].find({'paper_id':paper_id})]
        return tag_list

    def update_tag_contents_slot(self):
        paper_id = self.lineEdit_paper_id.text()
        collection = self.comboBox_section.currentText()
        tag_name =  self.comboBox_tag_list.currentText()
        tag_content = self.textEdit_tag_conent.toPlainText()
        reply = QMessageBox.question(self, 'Message', 'Would you like to update your database with new input?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.update_tag_contents(paper_id, collection, tag_name, tag_content)
        else:
            pass

    def update_tag_contents(self,paper_id, collection, tag_name, tag_content_in_plain_text):
        #target = self.database[collection].find({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})
        self.database[collection].update_one({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]},{ "$set": { "tag_content": tag_content_in_plain_text.rsplit('\n')}})

    def extract_tag_contents_slot(self):
        paper_id = self.lineEdit_paper_id.text()
        collection = self.comboBox_section.currentText()
        tag_name =  self.comboBox_tag_list.currentText()
        self.textEdit_tag_conent.setPlainText(self.extract_tag_contents(paper_id, collection, tag_name))

    def extract_tag_contents(self, paper_id, collection, tag_name):
        contents = [each['tag_content'] for each in self.database[collection].find({"$and":[{'paper_id':paper_id},{'tag_name':tag_name}]})]
        if len(contents)!=0:
            return '\n'.join(contents[0])
        else:
            return ''

    def append_new_input(self):
        paper_id = self.lineEdit_paper_id_new_input.text()
        collection = self.comboBox_section_new_input.currentText()
        tag_name = self.lineEdit_tag_new_input.text()
        tag_content = self.textEdit_tag_content_new_input.toPlainText()
        location = self.lineEdit_location_new_input.text()
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

    def get_papers_by_tag(self, name_db, tag = {'first_author':'qiu'}):
        all_info = list(self.mongo_client[name_db].paper_info.find(tag,{'_id':0}))
        return all_info

    def add_paper_info(self):
        paper_info = {'first_author':self.lineEdit_1st_author.text(),
                      'journal':self.lineEdit_journal.text(),
                      'year':self.lineEdit_year.text(),
                      'title':self.lineEdit_title.text(),
                      'url':self.lineEdit_url.text(),
                      'doi':self.lineEdit_doi.text()
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
            # print(collection)
            target = self.database[collection].find({'paper_id':paper_id_list[0]})
            text_box.append('\n##{}##'.format(collection))
            for each in target:
                # print(each)
                text_box.append('  '+each['tag_name'])
                for i,each_tag_content in enumerate(each['tag_content']):
                    #print()
                    if i>=len(each['location']):
                        text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content))
                    else:
                        text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content))
            return text_box

        #extract tag conent from collection with tag_name for papers with paper_ids
        def make_text2(text_box, collection, tag_name, paper_id_list):
            text_box.append('\n##{}##'.format(collection))
            text_box.append('  '+tag_name)
            for paper_id in paper_id_list:
                text_box.append('    '+paper_id)
                target = self.database[collection].find({'$and':[{'paper_id':paper_id},{'tag_name':tag_name}]})
                for each in target:
                    #text_box.append('      '+each['tag_name'])
                    for i,each_tag_content in enumerate(each['tag_content']):
                        if i>=len(each['location']):
                            text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][-1],each_tag_content))
                        else:
                            text_box.append('      {}.@(page_{}):{}'.format(i+1,each['location'][i],each_tag_content))
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
                tag_names = [each_item['tag_name'] for each_item in self.database.tag_info.find({'collection_name':each})]
                for each_tag in tag_names:
                    text_box = make_text2(text_box, each, each_tag, paper_id_list)
        self.plainTextEdit_query_info.setPlainText('\n'.join(text_box))

    def extract_info_with_tag_for_one_paper(self,paper,tag):
        return list(self.database[paper].find({'tag_name':tag}))

    
    def open_url_in_webbrowser(self,url):
        webbrowser.open(url)

class NewProject(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the dialog's GUI
        uic.loadUi("new_project_dialog.ui", self)
        self.pushButton_ok.clicked.connect(lambda:parent.creat_a_new_project(name_db = self.lineEdit_name.text(), 
                                                                             db_info = self.textEdit_introduction.toPlainText(),
                                                                             type_db ='paper'))
        self.pushButton_cancel.clicked.connect(lambda:self.close())



if __name__ == "__main__":
    QApplication.setStyle("fusion")
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    myWin.show()
    sys.exit(app.exec_())