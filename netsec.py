import gtk, pango
import string, random, operator, os
import pandas as pd
import numpy as np
from test import SLR_final

pd.options.mode.chained_assignment = None

#Constants to determine number of elements
MIN_N_LENGTHS = 1
MAX_N_LENGTHS = 5

#Constants to customize allowable signature length
MIN_SIZE_SIGNATURE = 4
MAX_SIZE_SIGNATURE = 130
DISTANCE_CONSECUTIVE = 2

ALLOWABLE_CHARS = string.ascii_letters + string.digits + string.punctuation

DEBUG_MODE = 1

class PyApp:
    def callback(self, widget, data=None):
        """Callback function customized based on what buttons are pressed"""
        if data == "Read from CSV":
            dialog = gtk.FileChooserDialog("Open..",
                           None,
                           gtk.FILE_CHOOSER_ACTION_OPEN,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            dialog.set_default_response(gtk.RESPONSE_OK)
            filter = gtk.FileFilter()
            dialog.set_current_folder("C:/Users/sanke/workspace/PythonDev")
            filter.set_name("CSV Only")
            filter.add_pattern("*.csv")
            dialog.add_filter(filter)            
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                file_location=dialog.get_filename()
                dialog.destroy()
                loop_call(read_csv=True, csv_location=file_location)
            elif response == gtk.RESPONSE_CANCEL:
                dialog.destroy()
                print 'Closed, no files selected'
                   
        elif data == "Open Results":
            #Hardcoded filename to default for now. Can be taken as input in the future.
            filename = r'C:/Users/sanke/workspace/PythonDev/InterpretPatterns.csv'
            os.system("start "+filename)
    
    def destroy(self, widget, data=None):
        """Destroys the GUI instance"""
        gtk.main_quit()
   
    def __init__(self, df, si):
        #Retrieve Dataframe and Size dictionary
        self.df = df
        self.si = si
        
        self.showSize = 1
        
        #Create new GTK Window instance
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", lambda w: gtk.main_quit())
        self.window.set_title("Dictionary Utility")
        self.window.set_default_size(800, 600)
        
        #Create partition for Data display
        dataBox = gtk.VBox()
        frame = gtk.Frame("Pattern Values")
        frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=65535))
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        
        #Create Table to display values
        self.table = gtk.Table(rows=len(df)+1, columns=7, homogeneous=False) 
        self.table.set_col_spacings(10)       
        title_bar = ['ID', 'Size', 'HEX', 'Original', 'Vector', 'Enable', 'Index']
        for i in range(7):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 15"))
            self.table.attach(label, i, i+1, 0, 1)
        
        #Loop through table to display values
        ctr = 0
        button = [None]*5
        entry = [None]*5
        for i in range(7):
            ctr = 0
            for j in range(1, len(df)+1):
                if(i<5):
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.modify_font(pango.FontDescription("Sans 10"))
                    #label.set_use_markup(gtk.TRUE)
                    #label.set_markup('<span size="20000">'+str(df[title_bar[i]][j-1])+'</span>')
                    label.set_alignment(0, 0)
                    self.table.attach(label, i, i+1, j, j+1)
                elif(i==5):
                    button[ctr] = gtk.CheckButton()
                    button[ctr].set_alignment(0, 0)
                    self.table.attach(button[ctr], i, i+1, j, j+1)
                    ctr = ctr + 1
                else:
                    entry[ctr] = gtk.Entry()
                    entry[ctr].set_alignment(0)
                    entry[ctr].set_width_chars(3)
                    self.table.attach(entry[ctr], i, i+1, j, j+1)

        scrolledWin.add_with_viewport(self.table)
        self.table.show()
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dataBox.pack_start(frame,  expand = True, fill = True, padding = 0)
        
        #Create Partition for displaying size information
        sizeBox = gtk.VBox()
        frame = gtk.Frame("Size information")
        sorted_size = sorted(self.si.items(), key=operator.itemgetter(0))
        
        #Initialize table for size information
        self.table2 = gtk.Table(rows=len(sorted_size)+1, columns=2, homogeneous=False)
        self.table2.attach(gtk.Label("Size"), 0, 1, 0, 1)
        self.table2.attach(gtk.Label("Count"), 1, 2, 0, 1)
        
        for i in range(2):
            for j in range(1, len(sorted_size)+1):
                label = gtk.Label(str(sorted_size[j-1][i]))
                self.table2.attach(label, i, i+1, j, j+1)
        frame.add(self.table2)
            
        
        sizeBox.pack_start(frame,  expand = True, fill = False, padding = 0)
        
        
        #Create buttons for creating New instance, Opening the file and quitting the app
        buttonBox = gtk.HBox()
        button1 = gtk.Button("Read from CSV")
        button1.connect("clicked", self.callback, "Read from CSV")
        buttonBox.pack_start(button1,  expand = True, fill = True, padding = 0)
        button1.show()
        
        buttonBox3 = gtk.HBox()
        button3 = gtk.Button("Open Results")
        button3.connect("clicked", self.callback, "Open Results")
        buttonBox3.pack_start(button3,  expand = True, fill = True, padding = 0)
        button3.show()
        
        buttonBox2 = gtk.VBox()
        button2 = gtk.Button("Quit")
        button2.connect("clicked", self.destroy, "Quit")
        buttonBox2.pack_start(button2,  expand = True, fill = True, padding = 0)
        button2.show()
        
        #Arrange all the elements legibly
        self.window.add(dataBox)
        dataBox.add(sizeBox)
        sizeBox.add(buttonBox)
        buttonBox.add(buttonBox3)
        buttonBox3.add(buttonBox2)
        
        self.window.show_all()

def id_generator(size=MIN_SIZE_SIGNATURE, chars=ALLOWABLE_CHARS):
    """Generates a random ID of specified size and characters
        Inputs:
        size: Size of random string
        chars: Characters to be included
    """
    return ''.join(random.choice(chars) for _ in range(size))

def patternGenerator(file_name="patterns.txt"):
    """Generates a file in the local directory with a set of random patterns.
        Constraints:
        Length is between MIN_SIZE_SIGNATURE, MAX_SIZE_SIGNATURE
        Count is between MIN_N_LENGTHS, MAX_N_LENGTHS
        Distance between lengths is greater than or equal to DISTANCE_CONSECUTIVE
        
        Inputs:
        file_name: Name of the file
    """
    try:
        fo = open(file_name, "wb")
        n = random.randint(MIN_N_LENGTHS-1, MAX_N_LENGTHS)
        #Hardcoding n to 5 temporarily
        n=5
        size_arr = []
        #Generate array of random numbers, such that difference is greater than or equal to DISTANCE_CONSECUTIVE
        while len(size_arr)!=n:
            tmp = random.randint(MIN_SIZE_SIGNATURE, MAX_SIZE_SIGNATURE)
            if(len(size_arr)==0):
                size_arr.append(tmp)
                continue
            #Check for sizes of other elements
            flag=True
            for j in size_arr:
                if(abs(tmp-j)<DISTANCE_CONSECUTIVE):
                    flag=False
                    break
            if(flag):
                size_arr.append(tmp)
                    
        for i in size_arr:
            #Call Random string generator
            fo.write(id_generator(i)+"\n")
        fo.close()
        return 0
    
    except:
        print "Failed to open file"
        return 1

def generateBitStream(ID, Size_val, HEX_val, SLR_val, SLR_index):
    ID = "{0:016b}".format(ID)
    Size_val = "{0:016b}".format(Size_val)
    #HEX_val = ''.join('{0:04b}'.format(int(c, 16)) for c in HEX_val)
    SLR_val = "{0:07b}".format(SLR_val)
    if SLR_index>0:
        SLR_val = SLR_val + '1'
    else:
        SLR_index=5
        
    SLR_arr = ['0']*39
    ctr=0
    for i in range((SLR_index-1)*8, (SLR_index-1)*8+len(SLR_val)):
        SLR_arr[i]=SLR_val[ctr]
        ctr+=1
    if(DEBUG_MODE):
        str_pad="__"
        SLR_arr.insert(8, str_pad)
        SLR_arr.insert(17, str_pad)
        SLR_arr.insert(26, str_pad)
        SLR_arr.insert(35, str_pad)
    else:
        str_pad=""
    SLR_final = ''.join(SLR_arr)    
    
    return ID+str_pad+Size_val+str_pad+SLR_final+str_pad+HEX_val

def interpretPattern(file_name="patterns.txt", read_csv=False):
    """Reads the pattern file and generates ID, HEX and Size paramters. 
        Returns None, None on failure and a dataframe, dictionary on success
        Inputs:
        file_name: Name of the file
    """
    if(read_csv):
        try:
            csv_data = pd.read_csv(file_name, header=0)
        except Exception,e:
            print "Failed to read file with exception" + str(e)
            return None, None, 1
        
    proc_data = pd.DataFrame(0, index=np.arange(MIN_N_LENGTHS-1, MAX_N_LENGTHS), columns = ['ID', 'Size', 'HEX', 'Original', 'Vector'])
    size_index = {}
    if not(read_csv):
        try:
            fo = open(file_name, "r")
            i=0
            for line in fo:
                #Strip the newline character
                line = line.strip('\n')
                size_line = len(line)
                
                #Create an entry in the dictionary for size
                if(size_index.has_key(size_line)):
                    size_index[size_line] += 1
                else:
                    size_index[size_line] = 1
                
                
                proc_data['ID'][i] = i
                proc_data['HEX'][i] = line.encode("hex")
                proc_data['Original'][i] = line
                proc_data['Size'][i] = size_line
                
                #Generate bitstream
                #stream_data = ''.join('{0:04b}'.format(int(c, 16)) for c in proc_data['HEX'][i])
                
                i=i+1
        except Exception,e:
            print "Failed to open file with exception" + str(e)
            return None, None, 1
    
    else:
        proc_data['ID'] = csv_data['ID']
        proc_data['Size'] = csv_data['Size']
        proc_data['HEX'] = csv_data['HEX']
        for i in range(len(proc_data)):
            proc_data['Original'][i] = proc_data['HEX'][i].decode("hex")
            size_line = proc_data['Size'][i]
            if(size_index.has_key(size_line)):
                    size_index[size_line] += 1
            else:
                size_index[size_line] = 1
                    
    #Sort the dataframe from lowest to highest based on size
    proc_data = proc_data.sort_values(by='Size', ascending=True)
    proc_data.reset_index(drop=True, inplace=True)
    
    #Prepare Python to store strings
    proc_data['Vector']=''
    
    #Fill the largest element in SLR 0
    l=len(proc_data)-1
    val=generateBitStream(proc_data['ID'][l], proc_data['Size'][l], proc_data['HEX'][l], 130-proc_data['Size'][l]-1, 0)
    proc_data['Vector'][l]=str(val)
    
    previous_Val = 0
    SLR_index=4
    #Fill the smallest elements in SLRs 4 to 1
    for i in range(0, len(proc_data)-1):
        SLR_val = 130 - (proc_data['Size'][i] - previous_Val) - 1
        val=generateBitStream(proc_data['ID'][i], proc_data['Size'][i], proc_data['HEX'][i], SLR_val, SLR_index)
        proc_data['Vector'][i] = val
        previous_Val = proc_data['Size'][i]
        SLR_index=SLR_index-1
    
    
    #Write as CSV
    proc_data.to_csv("InterpretPatterns.csv", index=False)
    
    return proc_data, size_index, 0

def loop_call(read_csv=False, csv_location="patterns.txt"):
    """Function to generate new patterns and display it on the GUI
    """
    if not(read_csv):
        patternGenerator()
    df, si, retVal = interpretPattern(csv_location, read_csv)
    #GTK object
    if(~retVal):
        PyApp(df, si)
        gtk.main()
    else:
        print "Debug the exception!"
if __name__ == "__main__":
    loop_call()