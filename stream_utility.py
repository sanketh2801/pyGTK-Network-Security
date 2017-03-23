import gtk, pango
import string, random, operator, os
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None

#Constants to determine number of elements
MIN_N_LENGTHS = 1
MAX_N_LENGTHS = 2

#Constants to customize allowable stream length
MIN_SIZE_STREAM = 4*8
MAX_SIZE_STREAM = 130*8
DISTANCE_CONSECUTIVE = 0

ALLOWABLE_CHARS = string.ascii_letters + string.digits #+ string.punctuation

DEBUG_MODE = 1

class StreamApp:
    def generate(self, widget, Spin_Btn, Btn, entry):
        signature_length = []
        size_index = {}
        for i in range(1):
            if(Btn[i]!=None and Btn[i].state):
                signature_length.append(Spin_Btn[i].get_value_as_int())
                size_index[Spin_Btn[i].get_value_as_int()]=0
        
        retVal, textVal = verify_size(size_index)
        if (retVal):
            self.message_display("Stream has the following error(s):\n"+textVal+'\nFile not created. Please try again!')
            return 0
        
        save_filename = entry.get_text()
        if save_filename.endswith('.txt'):
            try:
                patternGenerator(file_name=save_filename, size_arr=signature_length)
                self.message_display(message_text="Successfully created "+save_filename, type=gtk.MESSAGE_INFO)
            #Exception Handling in case file save fails
            except:
                print "Failed to create file. Please debug!"
                self.message_display(message_text="Failed to create file. Please debug!")
        else:
            self.message_display(message_text="File extension must be '.txt'. Please try again!")
        
    
    def read_from_csv(self, widget, data):
        """Callback function to initiate reading CSV file"""
        dialog = gtk.FileChooserDialog("Open Stream CSV",
                           None,
                           gtk.FILE_CHOOSER_ACTION_OPEN,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        #Add Filter to view only CSV Files
        _filter = gtk.FileFilter()
        dialog.set_current_folder(os.getcwd())
        _filter.set_name("CSV Only")
        _filter.add_pattern("*.csv")
        dialog.add_filter(_filter)            
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            #Update GUI to new CSV file
            file_location=dialog.get_filename()
            dialog.destroy()
            self.window.destroy()
            loop_call(read_csv=True, file_location=file_location)
        elif response == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            
    def display_original_text(self, widget, data):
        """Callback function to Display Original Text Signature"""
        dialog = gtk.Dialog(title="Original Stream", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(400,300)
        
        frame = gtk.Frame()
    
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        
        tableD = gtk.Table(rows=5, columns=2, homogeneous=False) #len(self.df)+1
        tableD.set_col_spacings(10)       
        title_bar = ['SID', 'Original']
        for i in range(2):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 15"))
            tableD.attach(label, i, i+1, 0, 1)
        
        for i in range(2):
            for j in range(1, len(self.df)+1):
                if(i==1):
                    text = str(self.df[title_bar[i]][j-1])
                    flag=0
                    color = ["red", "blue", "green", "yellow", "orange"]
                    for k in self.si:
                        start = int(k) + 25*flag
                        end = start + int(self.si[k])
                        text = text[:start]+'<span color="'+color[(flag)%5]+'">'+text[start:end]+'</span>'+text[end:]
                        flag = flag + 1                   
                
                    #print text
                    label = gtk.Label()
                    label.set_markup(text)
                    
                else:
                    label = gtk.Label(str(self.df[title_bar[i]][j-1]))
                
                label.modify_font(pango.FontDescription("Sans 10"))
                label.set_alignment(0, 0)
                tableD.attach(label, i, i+1, j, j+1)
        tableD.show()
        scrolledWin.add_with_viewport(tableD)
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dialog.vbox.pack_start(frame, expand = False, fill = True, padding = 5)
        dialog.vbox.show_all()
        #dialog.vbox.pack_start(label)
        #label.show()
        
         
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
            
    def generate_pattern(self, widget, data):
        """Callback function to Generate random patterns"""
        dialog = gtk.Dialog(title="Generate Random Text for Stream", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(400,300)        
        
        #Display_Order = [0, 4, 3, 2, 1]
        HBox = [None]*5
        VBox = [None]*5
        Label = [None]*5
        Adj = [None]*5
        Spin_Btn = [None]*5
        Btn = [None]*5
        for i in range(0, 1):
            HBox[i] = gtk.HBox()
            VBox[i] = gtk.VBox()
            Label[i] = gtk.Label("Stream length")
            if(i==0):
                Adj[i] = gtk.Adjustment(value=3*8, lower=3*8, upper=130*8, step_incr=1*8)
            else:
                Adj[i] = gtk.Adjustment(value=4*8, lower=4*8, upper=130*8, step_incr=1*8)
            
            Spin_Btn[i] = gtk.SpinButton(adjustment=Adj[i], climb_rate=0.0, digits=0)
            HBox[i].pack_start(Label[i])
            HBox[i].pack_start(Spin_Btn[i])
            Btn[i] = gtk.CheckButton()
            HBox[i].pack_start(Btn[i], False, False)
            VBox[i].pack_start(HBox[i])
            dialog.vbox.pack_start(VBox[i])
        
        VBoxL = gtk.VBox()
        HBoxL = gtk.HBox()
        button = gtk.Button("Generate!")
        entry = gtk.Entry()
        entry.set_text("RandomStream.txt")
        tooltips = gtk.Tooltips()
        tooltips.set_tip(entry, "Enter a valid *.txt filename")
        button.connect("clicked", self.generate, Spin_Btn, Btn, entry)        
        HBoxL.pack_start(button, False, True)
        HBoxL.pack_start(entry, False, True)
        VBoxL.pack_start(HBoxL, False, True)
        dialog.vbox.pack_start(VBoxL)
        
        dialog.vbox.show_all()
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def message_display(self, message_text, _type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK):
        message = gtk.MessageDialog(type=_type, buttons=buttons)
        message.set_markup(message_text)
        message.run()
        message.destroy()
    
    def destroy(self, widget, data=None):
        """Destroys the GUI instance"""
        gtk.main_quit()
    
    def get_main_menu(self, window):
        accel_group = gtk.AccelGroup()

        # This function initializes the item factory.
        # Param 1: The type of menu - can be MenuBar, Menu,
        #          or OptionMenu.
        # Param 2: The path of the menu.
        # Param 3: A reference to an AccelGroup. The item factory sets up
        #          the accelerator table while generating menus.
        item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)

        # This method generates the menu items. Pass to the item factory
        #  the list of menu items
        item_factory.create_items(self.menu_items)

        # Attach the new accelerator group to the window.
        window.add_accel_group(accel_group)

        # need to keep a reference to item_factory to prevent its destruction
        self.item_factory = item_factory
        # Finally, return the actual menu bar created by the item factory.
        return item_factory.get_widget("<main>")
   
    def __init__(self, df, si, file_location):
        #Retrieve Dataframe and Size dictionary
        self.df = df
        self.si = si
        
        self.showSize = 1
        
        self.menu_items = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Read HEX Stream with IDs, Size and Index(.csv)",     "<control>O", self.read_from_csv, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Quit",     "<control>Q", self.destroy, 0, None ),
            ( "/_Display",      None,         None, 0, "<Branch>" ),
            ( "/Display/_Display Original Text Stream",  "<control>D", self.display_original_text, 0, None ),
            ( "/_Generate",         None,         None, 0, "<Branch>" ),
            ( "/Generate/Generate Random Text Stream",   None, self.generate_pattern, 0, None ),
            )
        
        #Create new GTK Window instance
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", lambda w: gtk.main_quit())
        self.window.set_title("Stream Utility | File: "+str(file_location))
        self.window.set_default_size(640, 480)
        
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        #self.window.add(main_vbox)
        main_vbox.show()

        menubar = self.get_main_menu(self.window)

        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        
        #Create partition for Data display
        dataBox = gtk.VBox(spacing=30)
        frame = gtk.Frame("Stream Values")
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        
        #Create Table to display values
        self.table = gtk.Table(rows=len(df)+1, columns=4, homogeneous=False) 
        self.table.set_col_spacings(10)       
        title_bar = ['SID', 'Size', 'HEX']
        for i in range(3):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 15"))
            self.table.attach(label, i, i+1, 0, 1)
        
        #Loop through table to display values
        for i in range(3):
            for j in range(1, len(df)+1):    
                label = gtk.Label(str(df[title_bar[i]][j-1]))
                label.modify_font(pango.FontDescription("Sans 10"))
                #label.set_use_markup(gtk.TRUE)
                #label.set_markup('<span size="20000">'+str(df[title_bar[i]][j-1])+'</span>')
                label.set_alignment(0, 0)
                self.table.attach(label, i, i+1, j, j+1)
        
        scrolledWin.add_with_viewport(self.table)
        self.table.show()
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dataBox.pack_start(frame,  expand = False, fill = True, padding = 5)
        dataBox.set_border_width(1)
        
        #Create Partition for displaying size information
        sizeBox = gtk.VBox()
        frame = gtk.Frame("Signature information")
        
        sorted_size = sorted(self.si.items(), key=operator.itemgetter(0))
        
        #Initialize table for size information
        table2 = gtk.Table(rows=len(sorted_size)+1, columns=2, homogeneous=False)
        table2.attach(gtk.Label("Starting Index"), 0, 1, 0, 1)
        table2.attach(gtk.Label("Size"), 1, 2, 0, 1)
        
        for i in range(2):
            for j in range(1, len(sorted_size)+1):
                label = gtk.Label(str(sorted_size[j-1][i]))
                table2.attach(label, i, i+1, j, j+1)
        frame.add(table2)            
        
        sizeBox.pack_start(frame,  expand = False, fill = True, padding = 0)
        
        #Arrange all the elements legibly
        self.window.add(main_vbox)
        main_vbox.add(dataBox)
        dataBox.add(sizeBox)
        #sizeBox.add(buttonBox)
        
        self.window.show_all()
        
        #Verification utility
        """
        retVal, textVal = verify_size(self.si)
        if (retVal):
            self.message_display("Streams have the following error(s):\n"+textVal)
        """

def verify_size(size_index):
    """Verifies if constraints are met for size of signatures.
        Returns True, None if constraints are met
        Returns False, ErrorMessage if contrains aren't met
    """
    
    sorted_size = sorted(size_index.items(), key=operator.itemgetter(0))
    flag=0;
    ErrorMessage = ""
    
    if(len(sorted_size)>MAX_N_LENGTHS):
        flag=1
        ErrorMessage = "Count of lengths greater than: "+str(MAX_N_LENGTHS)+"\n"
    elif(len(sorted_size)<MIN_N_LENGTHS):
        flag=1
        ErrorMessage += "Count of lengths less than: "+str(MIN_N_LENGTHS)+"\n"
    
    for i in range(len(sorted_size)):
        if len(sorted_size)==1:
            min_check = MIN_SIZE_STREAM - 1
        else:
            min_check = MIN_SIZE_STREAM
        
        if sorted_size[i][0]>MAX_SIZE_STREAM:
            flag=1
            ErrorMessage+= "Stream length greater than: "+str(MAX_SIZE_STREAM)+"\n"
        elif sorted_size[i][0]<min_check:
            flag=1
            ErrorMessage+= "Stream length less than: "+str(MIN_SIZE_STREAM)+"\n"
    
    if(flag):
        return 1, ErrorMessage
    else:
        return 0, None
        
def id_generator(size=MIN_SIZE_STREAM, chars=ALLOWABLE_CHARS):
    """Generates a random ID of specified size and characters
        Inputs:
        size: Size of random string
        chars: Characters to be included
    """
    return ''.join(random.choice(chars) for _ in range(size))

def patternGenerator(file_name="stream.txt", size_arr = [], min_n_lengths=MIN_N_LENGTHS, 
                     max_n_lengths=MAX_N_LENGTHS, min_size_stream=MIN_SIZE_STREAM,
                     max_size_stream=MIN_SIZE_STREAM, distance_consecutive=DISTANCE_CONSECUTIVE):
    """Generates a file in the local directory with a set of random patterns.
        Constraints:
        Length is between MIN_SIZE_STREAM, MIN_SIZE_STREAM
        Count is between MIN_N_LENGTHS, MAX_N_LENGTHS
        Distance between lengths is greater than or equal to DISTANCE_CONSECUTIVE
        
        Inputs:
        file_name: Name of the file
    """
    try:
        fo = open(file_name, "wb")
        if(len(size_arr)==0):
            n = random.randint(min_n_lengths-1, max_n_lengths)
            #Hardcoding n to 5 temporarily
            #n=5
            #Generate array of random numbers, such that difference is greater than or equal to DISTANCE_CONSECUTIVE
            while len(size_arr)!=n:
                tmp = random.randint(min_size_stream, max_size_stream)
                
                #Ensure byte condition is satisfied
                if(tmp%8!=0):
                    break
                
                if(len(size_arr)==0):
                    size_arr.append(tmp)
                    continue
                #Check for sizes of other elements
                flag=True
                for j in size_arr:
                    if(abs(tmp-j)<distance_consecutive):
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

def interpretPattern(read_csv=True, file_location="test3.csv"):
    """Reads the pattern file and generates ID, HEX and Size paramters. 
        Returns None, None on failure and a dataframe, dictionary on success
        Inputs:
        file_name: Name of the file
    """
    if(read_csv):
        try:
            csv_data = pd.read_csv(file_location, header=0)
        except Exception,e:
            print "Failed to read file with exception" + str(e)
            return None, 1
    
    signature_index = csv_data['Start_byte_index'][0].split('|')
    signature_data = {}
    for i in signature_index:
        if(i!=''):
            tmp=i.split(':')
            signature_data[tmp[0]]=tmp[1]
    return csv_data, signature_data, 0

def loop_call(read_csv=True, file_location="test3.csv"):
    """Function to generate new patterns and display it on the GUI
    """
    if not(read_csv):
        patternGenerator()
    df, si, retVal = interpretPattern(read_csv=read_csv, file_location=file_location)
    #GTK object
    if(~retVal):
        StreamApp(df, si, file_location)
        gtk.main()
    else:
        print "Debug the exception!"
if __name__ == "__main__":
    loop_call()