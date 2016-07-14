import tkinter as tk
import tkinter.ttk as ttk
import threading
import time
import queue
import serial
#import string

import sys
#from tkinter.tix import COLUMN


serialPort = 'COM5'
baud = 115200

class Application(tk.Frame):
    
    
    def __init__(self, master, cmdqueue, tagqueue, endCommand, serialmgr):
        self.cmdqueue = cmdqueue
        self.tagqueue = tagqueue
        tk.Frame.__init__(self, master)
        self.pack()        
        self.createWidgets()
        self.serialmgr = serialmgr
        

    def createWidgets(self):
        # Create notebook and read & write frames
        self.notebook = ttk.Notebook(self, width=300, height=150)
        self.frame1 = ttk.Frame(self.notebook)
        self.frame2 = ttk.Frame(self.notebook)
        self.notebook.add(self.frame1, text='Read')
        self.notebook.add(self.frame2, text='Write')
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
        self.statuslab = ttk.Label(self.frame2, text=" Idle  ")        
        self.statuslab.grid(row=2, column=1)
        
        
        # Add quit button to main display.
        #self.QUIT = tk.Button(self, text="QUIT", fg="red", command=client.endApplication)
        #self.QUIT.pack(side="bottom")
        
        # Add widgets for read frame
        self.uuidlab = ttk.Label(self.frame1, text="Name On Card  :  ")        
        self.uuidlab.grid(row=0, column=0)
        self.uuid = ttk.Label(self.frame1, text="----")
        self.uuid.grid(row=0, column=1)

    
    
    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.tagqueue.qsize( ):
            
            try: 
                msg = self.tagqueue.get(0)
                #print("mesgreceived  {}".format(msg))               
                self.uuid.config(text=msg, width=100)

                
            except:
                # just on general principles, although we don't
                # expect this branch to be taken in this case                
                raise
            
    
    def ActivateReading(self, event):
        if(event.widget.tab(event.widget.index("current"), "text") == "Read"):
            #self.frame1.uuid.configure(text="thread started")
            self.cmdqueue.put("Read Enabled")
            
        else:            
            self.cmdqueue.put("Read Disabled")
            
    def WritePatientToCard(self):
        
        print(self.name.get())
        result = self.serialmgr.WriteTag(self.name.get().encode('utf-8'))        
        
        if(result.find("Write Successful") >= 0):                                        
            self.statuslab["text"] = "Write Successful"
            self.statuslab["fg"] = "green"
        else:
            self.statuslab["text"] = "Write failed"
            self.statuslab["fg"] = "red"    
        
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
            import sys
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



root = tk.Tk()
client = ThreadedClient(root)

def on_closing():    
    client.endApplication()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop(  )
#app = Application(master=root)
#app.mainloop()
