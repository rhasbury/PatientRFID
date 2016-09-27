import tkinter as tk
import tkinter.ttk as ttk
import threading
import time
import queue
import serial
import glob

import sys
#from tkinter.constants import VERTICAL
#from test.test_tcl import TkinterTest
#from tkinter.tix import COLUMN

import pymysql.cursors





dbhost='localhost'
dbuser='rfid'
dbpassword='rfid'
dbDB='patientdat',
dbcharset='utf8mb4'

editlocked = True


serialPort = None
baud = 115200

class Application(tk.Frame):
    
    
    def __init__(self, master, cmdqueue, tagqueue, endCommand, serialmgr):
        self.cmdqueue = cmdqueue
        self.tagqueue = tagqueue
        tk.Frame.__init__(self, master)
        self.pack()        
        self.createWidgets()
        self.serialmgr = serialmgr
    
    
    def busy(self):
        self.config(cursor="wait")

    def notbusy(self):
        self.config(cursor="")
        

    def createWidgets(self):
        #ttk.Style().configure("TButton", padding=(0, 5, 0, 5), font='serif 10')
                
        # Create notebook and read & write frames
        self.notebook = ttk.Notebook(self, width=500, height=400)
        self.frame1 = ttk.Frame(self.notebook)
        self.frame2 = ttk.Frame(self.notebook)
        self.frame3 = ttk.Frame(self.notebook)
        
        #self.frame1.rowconfigure(0, weight=1)        
        #self.frame1.columnconfigure(0, weight=1)
        #self.frame2.rowconfigure(0, weight=1)
        #self.frame2.columnconfigure(0, weight=1)
        self.notebook.add(self.frame1, text='Read')
        self.notebook.add(self.frame2, text='Write')
        self.notebook.add(self.frame3, text='Admin')        
        self.notebook.bind_all("<<NotebookTabChanged>>", self.ActivateReading)
        self.notebook.grid(row=0, column=0)
       
        # Add widgets for write frame
        self.namelab = ttk.Label(self.frame2, text="Patient Name :  ")        
        self.namelab.grid(row=0, column=0)
        self.name = ttk.Entry(self.frame2, text="bbbb")
        self.name.grid(row=0, column=1)
        self.writetag = tk.Button(self.frame2)
        self.writetag["text"] = "Write Name to Card"
        self.writetag["command"] = self.WritePatientToCard
        self.writetag.grid(row=3, column=1)

        
        
        # Add quit button to main display.
        #self.QUIT = tk.Button(self, text="QUIT", fg="red", command=client.endApplication)
        #self.QUIT.pack(side="bottom")
        
        # Add widgets for read frame
        self.uuidlab = ttk.Label(self.frame1, text="Name On Card  :  ")        
        self.uuidlab.grid(row=0, column=0)
        self.uuid = ttk.Label(self.frame1, text="----", width=75)
        self.uuid.grid(row=0, column=1, columnspan=3)
        self.pendingreglist = tk.Listbox(self.frame1)
        self.pendingreglist.grid(row=1, column=0)
        self.registeredlist = tk.Listbox(self.frame1)
        self.registeredlist.grid(row=1, column=2)
        self.registerpatient = tk.Button(self.frame1)
        self.registerpatient["text"] = "Register Patient"
        self.registerpatient["command"] = self.RegisterPatient
        self.registerpatient.grid(row=1, column=1)
        
        
        # Add widgets for admin frame
        self.editframe = ttk.Frame(self.frame3, borderwidth=5, relief="raised")
        self.editframe.grid(row=1, column=0, columnspan=2, sticky="W")        
        self.searchframe = ttk.Frame(self.frame3)
        self.searchframe.grid(row=0, column=0)
    
        self.searchentry = tk.Entry(self.searchframe)
        self.searchentry.grid(row=0, column=0, pady=5 )
        
        self.searchbutton = tk.Button(self.searchframe, text="Search", command=self.SearchForPatient)
        self.searchbutton.grid(row=0, column=1, padx=5, pady=5) 
        
        self.searchbox = tk.Listbox(self.searchframe)
        self.searchbox.bind("<<ListboxSelect>>", self.ListBoxSelect) 
        self.searchbox.grid(row=1, column=0, columnspan=2, sticky="w")
    
        self.statuslab = ttk.Label(self.searchframe, text=" Idle  ")        
        self.statuslab.grid(row=2, column=1)
    
              

        self.namelab_edit = ttk.Label(self.editframe, text="Patient Name :  ")
        self.emaillab_edit = ttk.Label(self.editframe, text="Patient Email :  ")
        self.pidab_edit = ttk.Label(self.editframe, text="Patient ID :  ")         
        self.firstnamebox = tk.Entry(self.editframe, state="disabled")
        self.lastnamebox = tk.Entry(self.editframe, state="disabled")
        self.pidbox = tk.Entry(self.editframe, state="readonly")
        self.emailbox = tk.Entry(self.editframe, state="disabled", width=45)
        
        self.firstnamebox.grid(row=0, column=1, padx=5, pady=5)
        self.lastnamebox.grid(row=0, column=2, padx=5, pady=5)
        self.pidbox.grid(row=2, column=1, padx=5, pady=5)
        self.emailbox.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        self.namelab_edit.grid(row=0, column=0)
        self.emaillab_edit.grid(row=1, column=0)
        self.pidab_edit.grid(row=2, column=0)
        
        self.createnewbutton = tk.Button(self.editframe, text="Create New", command=self.CreateNewEntry)
        self.lockunlockbutton = tk.Button(self.editframe, text="Lock/Unlock", command=self.LockUnlock)
        self.savebutton = tk.Button(self.editframe, text="Save", command=self.SaveEntry)
        self.deletebutton = tk.Button(self.editframe, text="Delete", command=self.DeleteEntry)
        self.writetagbutton = tk.Button(self.editframe, text="Write Tag", command=self.WriteTag)
        
        self.createnewbutton.grid(row=2, column=2, padx=5, pady=5)
        self.lockunlockbutton.grid(row=3, column=0, padx=5, pady=5)
        self.savebutton.grid(row=3, column=1, padx=5, pady=5)
        self.deletebutton.grid(row=3, column=2, padx=5, pady=5)
        self.writetagbutton.grid(row=3, column=3, padx=5, pady=5)
        
        
        self.PopluateListBox()
        
        
    def PopluateListBox(self, searchstring=None):
                
            
        connection = pymysql.connect(host='localhost',
                 user='rfid',
                 password='rfid',
                 db='patientdat',
                 charset='utf8mb4',
                 cursorclass=pymysql.cursors.DictCursor)
            
        if(searchstring == None):        
            try:
                self.searchbox.delete(0, tk.END)
            
                with connection.cursor() as cursor: #
                    # Read a single record
                    sql = "SELECT * FROM patients ORDER by id DESC LIMIT 20"
                    cursor.execute(sql)
                    for key in cursor:
                        if(key['firstname'] != "blank"):
                            self.searchbox.insert(tk.END, "{}, {}   ID:{}".format(key['lastname'], key['firstname'], key['id']))
                    
            finally:
                connection.close()
        else:
            try:
                self.searchbox.delete(0, tk.END)
            
                with connection.cursor() as cursor: #
                    # Read a single record
                    sql = "SELECT * FROM patients WHERE (firstname LIKE '%{}%') OR (lastname LIKE '%{}%') ORDER by id DESC LIMIT 200".format(searchstring, searchstring)
                    cursor.execute(sql)
                    for key in cursor:
                        if(key['firstname'] != "blank"):
                            self.searchbox.insert(tk.END, "{}, {}   ID:{}".format(key['lastname'], key['firstname'], key['id']))
                    
            finally:
                connection.close()                
        
    
    def ListBoxSelect(self, evt):
        box = evt.widget
        index = int(box.curselection()[0])
        text = box.get(index)
        idLoc = text.find("ID:") + 3\
        
        if (idLoc != -1):
            pid = int(text[idLoc:])
            connection = pymysql.connect(host='localhost',
                     user='rfid',
                     password='rfid',
                     db='patientdat',
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)
            
            try:  
                with connection.cursor() as cursor: #
                    # Read a single record
                    sql = "SELECT * FROM patients WHERE id = {}".format(pid)
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    #print(result)         
                    self.pidbox.configure(state="normal")                    
                    self.pidbox.delete(0, tk.END)
                    self.pidbox.insert(0, result['id'])       
                    self.pidbox.configure(state="readonly")
                    self.firstnamebox.configure(state="normal")
                    self.firstnamebox .delete(0, tk.END)
                    self.firstnamebox.insert(0, result['firstname'])       
                    self.firstnamebox.configure(state="readonly")
                    self.lastnamebox.configure(state="normal")
                    self.lastnamebox.delete(0, tk.END)
                    self.lastnamebox.insert(0, result['lastname'])       
                    self.lastnamebox.configure(state="readonly")
                    self.emailbox.configure(state="normal")
                    self.emailbox.delete(0, tk.END)
                    self.emailbox.insert(0, result['email'])       
                    self.emailbox.configure(state="readonly")                    
                    
            finally:
                connection.close()
        
    
    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.tagqueue.qsize( ):
            
            try: 
                msg = self.tagqueue.get(0)
                found = False
                #print("mesgreceived  {}".format(msg))               
                #self.uuid.config(text=msg) #, width=100)
                if(msg.isdigit()):
                    pid = int(msg)
                    connection = pymysql.connect(host='localhost',
                             user='rfid',
                             password='rfid',
                             db='patientdat',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
                    
                    try:  
                        with connection.cursor() as cursor: #                            
                            for listbox_entry in enumerate(self.pendingreglist.get(0, tk.END)):                                
                                if(listbox_entry[1].find("ID: {} ".format(pid)) >= 0):
                                    found = True
                                    print("found1")
                                    break

                            for listbox_entry in enumerate(self.registeredlist.get(0, tk.END)):
                                if(listbox_entry[1].find("ID: {} ".format(pid)) >= 0):
                                    found = True
                                    print("found2")
                                    break
                            
                            if(found == False):
                                sql = "SELECT * FROM patients WHERE id = {}".format(pid)
                                cursor.execute(sql)
                                result = cursor.fetchone()
                                self.pendingreglist.insert(tk.END, "{}, {} ID: {} ".format(result['firstname'], result['lastname'], pid))
                                #print(result)
                        
                    except:
                        # just on general principles, although we don't
                        # expect this branch to be taken in this case                
                        raise
            except ValueError:
                pass
    
    def ActivateReading(self, event):
        if(event.widget.tab(event.widget.index("current"), "text") == "Read"):
            #self.frame1.uuid.configure(text="thread started")
            self.cmdqueue.put("Read Enabled")
            
        else:            
            self.cmdqueue.put("Read Disabled")

    def WriteTag(self):
        self.busy()
        result = self.serialmgr.WriteTag(self.pidbox.get().encode('utf-8'))        
        print("wrote: {}".format(self.pidbox.get().encode('utf-8')))
        if(result.find("Write Successful") >= 0):                                        
            self.statuslab["text"] = "Write Successful"
            self.statuslab["foreground"] = "green"
        else:
            self.statuslab["text"] = "Write failed"
            self.statuslab["foreground"] = "red"
        self.notbusy()
        
            
    def WritePatientToCard(self):
        
        print(self.name.get())
        result = self.serialmgr.WriteTag(self.name.get().encode('utf-8'))        
        
        if(result.find("Write Successful") >= 0):                                        
            self.statuslab["text"] = "Write Successful"
            self.statuslab["fg"] = "green"
        else:
            self.statuslab["text"] = "Write failed"
            self.statuslab["fg"] = "red"
            
    def RegisterPatient(self):
            self.registeredlist.insert(0, self.pendingreglist.get(tk.ACTIVE))
            self.pendingreglist.delete(self.pendingreglist.index(tk.ACTIVE))
            

    def SearchForPatient(self):
        self.PopluateListBox(self.searchentry.get())
        
        
        
        
    def LockUnlock(self):
        global editlocked
        
        if(editlocked == True):
            self.firstnamebox.configure(state="normal")
            self.lastnamebox.configure(state="normal")        
            self.emailbox.configure(state="normal")       
            editlocked = False
        else:
            self.firstnamebox.configure(state="readonly")
            self.lastnamebox.configure(state="readonly")        
            self.emailbox.configure(state="readonly") 
            editlocked = True           
        
        
        
        
    def SaveEntry(self):
        global editlocked
        connection = pymysql.connect(host='localhost',
                     user='rfid',
                     password='rfid',
                     db='patientdat',
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)

        try:
            with connection.cursor() as cursor:
                
                sql = "UPDATE patients SET firstname='{}', lastname='{}', email='{}', last_updated=NOW() WHERE id={}".format(self.firstnamebox.get(),
                                                                                                   self.lastnamebox.get(),
                                                                                                   self.emailbox.get(),
                                                                                                   self.pidbox.get())
                cursor.execute(sql)                
               
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()        

        finally:
            connection.close()
        
        self.firstnamebox.configure(state="readonly")
        self.lastnamebox.configure(state="readonly")        
        self.emailbox.configure(state="readonly")     
        self.writetagbutton.configure(state="normal")      
        editlocked = True        
        self.PopluateListBox()
        
        
        
    
    def DeleteEntry(self):
        return("done")
        
    def CreateNewEntry(self):
        global editlocked
        self.firstnamebox.configure(state="normal")
        self.lastnamebox.configure(state="normal")        
        self.emailbox.configure(state="normal")
        self.writetagbutton.configure(state="disabled")       
        editlocked = False
        
        connection = pymysql.connect(host='localhost',
                             user='rfid',
                             password='rfid',
                             db='patientdat',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
        
        try:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO patients (firstname, lastname, email, last_updated) VALUES ('blank', 'blank', 'blank', NOW())"
                cursor.execute(sql)                
                sql = "SELECT LAST_INSERT_ID();"
                cursor.execute(sql)
                result = cursor.fetchone()
                #print(result['LAST_INSERT_ID()'])
                #self.pidbox.delete(0, END)
                self.pidbox.configure(state="normal")
                self.pidbox.delete(0, tk.END)
                self.pidbox.insert(0, result['LAST_INSERT_ID()'])       
                self.pidbox.configure(state="readonly")
                self.firstnamebox.delete(0, tk.END)
                self.lastnamebox.delete(0, tk.END)        
                self.emailbox.delete(0, tk.END)  
                
                
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()        

        finally:
            connection.close()
        
        
        # might do a new patient creation popup box at some point. 
        
        
class ThreadedClient:
    def __init__(self, master):
  
        self.master = master

        # Create the queue
        self.tagqueue = queue.Queue( )
        self.cmdqueue = queue.Queue( )
    
        self.serialmgr = SerialManager()

        # Set up the GUI part
        self.gui = Application(master, self.cmdqueue, self.tagqueue, self.endApplication, self.serialmgr)       
        
        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall(  )

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        #self.gui.processIncoming( )
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            sys.exit(1)
        self.master.after(200, self.periodicCall)



    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        readenabled = 0
        
        while self.running:

            if(self.cmdqueue.qsize()):
                msg = self.cmdqueue.get(0)         

                if(msg == "Read Enabled"):
                    readenabled = 1                                          
                else:
                    readenabled = 0
                                        
                
            if (readenabled == 1):
                # do stuff to read tags from the reader and put them in the queue                
                self.tagqueue.put(self.serialmgr.ReadTag())
                            
            self.gui.processIncoming( )
            time.sleep(0.2)
        
        
    
    
    
    def endApplication(self):
        #self.serialmgr.Close()
        self.running = 0




class SerialManager:
    def __init__(self):
        try:
            self.ser = serial.Serial(serialPort, baud, bytesize=8, parity='N', stopbits=1, timeout=1, rtscts=False, dsrdtr=False)
            time.sleep(3) # creating connection will reset arduino, need to wait for reset complete.
        except serial.SerialException as e:
            sys.stderr.write('Could not open serial port : {}\n'.format(e))
            raise
   
    
    
    def ReadTag(self):
        # do stuff to read tags from the reader and put them in the queue         
        if (self.ConnectionTest()):            
            self.ser.flushInput()
            self.ser.write(b'read_tag\n') 
            time.sleep(0.2)
            result = self.ser.readline()
            #print(result)
            if(result.find(b'Sucess:') >= 0):  
                temp = result.lstrip(b'Sucess:')            
                return temp.rstrip(b'\n')
            elif(result.find(b'no tag') >= 0):
                return(b'No Card Detected')
            else:
                return (b'read failed')
        else:
            return(b'Reader not connected')
    

    def WriteTag(self, texttowrite):       
        if (self.ConnectionTest()):        
            self.ser.flushInput()
            print(b'write_tag:' + texttowrite + b'\n')
            self.ser.write(b'write_tag:' + texttowrite + b'\n')       
            time.sleep(5)
            result = self.ser.readline()
            print(result)
            if(result.find(b'Success') >= 0):              
                return "Write Successful"
            else:              
                return "Write failed"
        else:
            return(b'Reader not connected')
                           
    def ConnectionTest(self):
        self.ser.flushInput()
        self.ser.write(b'connection_test\n')
        time.sleep(0.1)
        result = self.ser.readline()
        print(result)
        if(result.find(b'ok') >= 0):              
            return 1
        else:              
            return 0
        
    def Close(self):
        print("closing serial")
        self.ser.close()


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def on_closing():    
    client.endApplication()
    root.destroy()


if __name__ == "__main__":


    availableports = serial_ports()
    
    print(availableports)
    
    for port in availableports:
        try:
            ser = serial.Serial(port, baud, bytesize=8, parity='N', stopbits=1, timeout=1, rtscts=False, dsrdtr=False, write_timeout=2)
            ser.dtr = True
            ser.rts = True
            time.sleep(2)
            ser.flushInput()               
            ser.write(b'whatis\n')                   
            time.sleep(0.5)
            result = ser.readline()
            print("Testing port {}".format(port))
            if(result.find(b'rfid_read') >= 0):
                serialPort = port
                print("Found rfid reader on serial port {}".format(serialPort))
                ser.close()
                break
            
            ser.close()
        except serial.SerialException:
            print("Reader not found on port {}".format(port))
            ser.close()
        
        except:            
            ser.close()
            raise

    if(serialPort == None):
        print("No reader found. Exiting")
        exit()
        
    
    
    # insert check for Mysql connectivity
      
    root = tk.Tk()
    client = ThreadedClient(root)
    
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop(  )
    #app = Application(master=root)
    #app.mainloop()
