#UI is based on http://code.activestate.com/recipes/578665-a-wxpython-gui-to-create-sqlite3-databases/

#sh database_editor.sh(DO NOT set password for mysql database）
#
#run topology
#python pyretic.py -m p0 pyretic.modules.netassay.test.test_assay_as
#sudo python database_editor.py

import mysql.connector
from mysql.connector import errorcode
from client import Client
import wx
import wx.grid
import gettext
import threading
import asyncore, socket

class DatabaseConnector:

    def connect(self):
        db = mysql.connector.connect(user='root')
        try:
            db.database = "NETASSAY_DB" 
            self.db = db
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                sql = 'CREATE DATABASE NETASSAY_DB'
                cursor.execute(sql)
                db.database = "NETASSAY_DB"
                self.db = db
            else:
                print(err)
        return db
       

    def cursor(self):
        return self.db.cursor()       

    def close(self):
        self.db.close()


def single_quote_remover(text):# to remove single quotes from entry to prevent SQL crash
    return text.replace ("'","/")

class MyFrame(wx.Frame):# this is the parent frame
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.frame_1_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(1, _("Index"), "", wx.ITEM_NORMAL)
        self.frame_1_menubar.Append(wxglade_tmp_menu,_("AS Record"))
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(2, _("Message"), "", wx.ITEM_NORMAL)
        self.frame_1_menubar.Append(wxglade_tmp_menu,_("About"))
        self.SetMenuBar(self.frame_1_menubar)
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_MENU, self.open_dialog, id=1)
        self.Bind(wx.EVT_MENU,self.open_dialog1,id =2)

 
    def __set_properties(self):
        self.SetTitle(_("AS Record Editor"))
        self.SetSize((555, 444))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer_1)
        self.Layout()

    def open_dialog(self, event):
        MyDialog1(self).Show()

    def open_dialog1(self,event):
        wx.MessageBox("A simple editor that resumes basic graphical database configuration\n\n!")

class MyDialog1(wx.Dialog):# this is the PhoneBook dialog box...
    def __init__(self, *args, **kwds):
        #connect to database
        self.database_connector = DatabaseConnector()
        self.database_connector.connect()

        #UI layout
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_10 = wx.StaticText(self, -1, _(" ID"))
        self.txtID = wx.TextCtrl(self, -1, "")
        self.label_11 = wx.StaticText(self, -1, _(" Network"))
        self.txtNETWORK = wx.TextCtrl(self, -1, "")
        self.label_12 = wx.StaticText(self, -1, _(" Next Hop"))
        self.txtNEXTHOP = wx.TextCtrl(self, -1, "")
        self.label_13 = wx.StaticText(self, -1, _(" AS Path"))
        self.txtASPATH = wx.TextCtrl(self, -1, "")
        self.button_6 = wx.Button(self, -1, _("UPDATE"))
        self.button_5 = wx.Button(self, -1, _("ADD"))
        self.button_7 = wx.Button(self, -1, _("DELETE"))
        self.button_8 = wx.Button(self, -1, _("LOAD"))
        self.grid_1 = wx.grid.Grid(self, -1, size=(1, 1))
        self.txtNETWORK.SetFocus()
        self.button_6.Enabled=False
        self.txtID.Enabled=False
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.clk_add, self.button_5)
        self.Bind(wx.EVT_BUTTON, self.clk_update, self.button_6)
        self.Bind(wx.EVT_BUTTON, self.clk_delete, self.button_7)
        self.Bind(wx.EVT_BUTTON, self.clk_load, self.button_8)
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        #setup client to connect netassay engine
        self.client = Client('', 8080)
        client_thread = threading.Thread(target= asyncore.loop)
        client_thread.start()

    def OnCloseFrame(self, event):
        self.Close()
        self.database_connector.close()

    #count number of rows in database
    def data_rows_count(self):
        #con = connect()
        cur=self.database_connector.cursor()
        cur.execute("SELECT * FROM AS_RECORD")
        rows=cur.fetchall()
        num=0
        for r in rows:
            num+=1
        return num

    #retrieve data from database and refresh its display in UI
    def refresh_data(self):
        #cnn =connect()
        cur = self.database_connector.cursor()
        cur.execute("SELECT * FROM AS_RECORD")
        rows=cur.fetchall()
        for i in range (0,len(rows)):
            for j in range(0,4):
                cell = rows[i]
                self.grid_1.SetCellValue(i,j,str(cell[j]))

    def __set_properties(self):
        self.SetTitle(_("AS Record"))
        self.SetSize((600, 550))
        self.txtID.SetMinSize((120, 27))
        self.txtNETWORK.SetMinSize((120, 27))
        self.txtNEXTHOP.SetMinSize((120, 27))
        self.txtASPATH.SetMinSize((120, 27))
        self.grid_1.CreateGrid(self.data_rows_count(), 4)
        self.grid_1.SetColLabelValue(0, _("ID"))
        self.grid_1.SetColSize(0, 12)
        self.grid_1.SetColLabelValue(1, _("Network"))
        self.grid_1.SetColSize(1, 150)
        self.grid_1.SetColLabelValue(2, _("Next Hop"))
        self.grid_1.SetColSize(2, 150)
        self.grid_1.SetColLabelValue(3, _("AS Path"))
        self.grid_1.SetColSize(3, 150)
        self.grid_1.EnableEditing(False)
        self.grid_1.SetFocus()
        self.refresh_data()

    def __do_layout(self):
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.GridSizer(4, 3, 0, 0)
        sizer_4.Add((20, 20), 0, 0, 0)
        grid_sizer_3.Add(self.label_10, 0, 0, 0)
        grid_sizer_3.Add(self.txtID, 0, 0, 0)
        grid_sizer_3.Add(self.button_5, 0, 0, 0)
        grid_sizer_3.Add(self.label_11, 0, 0, 0)
        grid_sizer_3.Add(self.txtNETWORK, 0, 0, 0)
        grid_sizer_3.Add(self.button_6, 0, 0, 0)
        grid_sizer_3.Add(self.label_12, 0, 0, 0)
        grid_sizer_3.Add(self.txtNEXTHOP, 0, 0, 0)
        grid_sizer_3.Add(self.button_7, 0, 0, 0)
        grid_sizer_3.Add(self.label_13, 0, 0, 0)
        grid_sizer_3.Add(self.txtASPATH, 0, 0, 0)
        grid_sizer_3.Add(self.button_8, 0, 0, 0)
        sizer_4.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        sizer_4.Add(self.grid_1, 1, wx.EXPAND, 0)
        sizer_4.Add((20, 20), 0, 0, 0)
       
        self.SetSizer(sizer_4)
        self.Layout()

    def clear_grid(self):
        self.txtID.Value=""
        self.txtNETWORK.Value=""
        self.txtNEXTHOP.Value=""
        self.txtASPATH.Value=""

    def auto_number(self):
        j=self.data_rows_count()
        return j+1  

    def clk_add(self, event):
        if self.txtNETWORK.Value == "" or self.txtNEXTHOP.Value == "" or self.txtASPATH.Value == "":
            wx.MessageBox("Some Fields Are Empty!")
        else:
            network=single_quote_remover(str(self.txtNETWORK.Value))
            nexthop=single_quote_remover(str(self.txtNEXTHOP.Value))
            aspath=(str(self.txtASPATH.Value))#set the format here to the country u want
            self.grid_1.AppendRows(1)

            cursor = self.database_connector.cursor()
            sql = "INSERT INTO AS_RECORD(network,next_hop,path) VALUES('"+(network)+"','"+(nexthop)+"','"+(aspath)+"')"
            cursor.execute(sql)
            self.database_connector.db.commit()
            
            self.refresh_data()
            self.clear_grid()
            self.txtNETWORK.SetFocus()

            self.client.send_msg("ADD##"+network+"@@"+aspath)

        event.Skip()

    def clk_update(self, event):
        try:           
            row_index = self.grid_1. GetSelectedRows()[0]
            c=self.grid_1.GetCellValue(row_index,0)

            cur=self.database_connector.cursor()
            cur.execute("SELECT * FROM AS_RECORD WHERE as_no="+"'"+ str(c)+"'")
            rows = cur.fetchall()
            for row in rows:
                old_network = row[1]
                old_aspath = row[3]

            network=single_quote_remover(str(self.txtNETWORK.Value))
            nexthop=single_quote_remover(str(self.txtNEXTHOP.Value))
            aspath=(str(self.txtASPATH.Value))#set the format here to the country u want
            cur.execute("UPDATE AS_RECORD SET network = "+ "'"+(network)+"'" + " ,next_hop="+ "'"+(nexthop)+"'" +",path=" + "'" +(aspath) + "'" + "WHERE as_no="+"'" + str(c) + "'")
            self.database_connector.db.commit()

            self.refresh_data()
            self.clear_grid()
            self.button_6.Enabled=False
            self.button_5.Enabled=True
            self.txtNETWORK.SetFocus()

            self.client.send_msg("UPDATE##"+old_network + "@@"+old_aspath+"&&"+network+"@@"+aspath)
            event.Skip()

        except IndexError:
            wx.MessageBox("you have lost focus on the row you wanted to edit")

    def clk_delete(self, event):
        try:
            lst = self.grid_1. GetSelectedRows()[0]
            c=self.grid_1.GetCellValue(lst,0)
            #cnn=connect()
            cur=self.database_connector.cursor()
            cur.execute("SELECT * FROM AS_RECORD WHERE as_no="+"'"+ str(c)+"'")
            rows = cur.fetchall()
            for row in rows:
                network = row[1]
                aspath = row[3]

            cur.execute("DELETE FROM AS_RECORD WHERE as_no="+"'" + str(c) + "'")
            self.database_connector.db.commit()

            self.grid_1.DeleteRows(lst,1)
            self.refresh_data()
            self.clear_grid()
            self.button_6.Enabled=False
            self.button_5.Enabled=True
            self.txtNETWORK.SetFocus()

            self.client.send_msg("DELETE##"+network+"@@"+aspath)
        except IndexError:
            wx.MessageBox("You Did Not Select Any Row To Delete!")
        event.Skip()

    def clk_load(self, event):
        try:
            row_index = self.grid_1.GetSelectedRows()[0]
            cell_value=[]
            for i in range(0,4):
                cell_value.append(self.grid_1.GetCellValue(row_index,i))
            self.txtID.Value= str(cell_value[0])
            self.txtNETWORK.Value=str(cell_value[1])
            self.txtNEXTHOP.Value=str(cell_value[2])
            self.txtASPATH.Value=str(cell_value[3])
            self.button_6.Enabled=True
            self.button_5.Enabled=False
            self.txtNETWORK.SetFocus()
            event.Skip()
        except IndexError:
            wx.MessageBox("You Did Not Select Any Row To Load")
            

  
if __name__ == "__main__":

    gettext.install("app")
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, wx.ID_ANY, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

