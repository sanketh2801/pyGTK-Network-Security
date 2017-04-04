import gtk, pango
import string, random, operator, os, fileinput
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None

#Constant to change utility name
TOOL_NAME = "Signatures"

#Constants to determine number of elements
MIN_N_LENGTHS = 1
MAX_N_LENGTHS = 5

#Constants to customize allowable signature length
MIN_SIZE_SIGNATURE = 4*8
MAX_SIZE_SIGNATURE = 130*8
DISTANCE_CONSECUTIVE = 2*8

ALLOWABLE_CHARS = string.ascii_letters + string.digits + string.punctuation

DEBUG_MODE = 1

class PyApp:
    def generate(self, widget, Spin_Btn, Btn, entry):
        signature_length = []
        size_index = {}
        for i in range(5):
            if(Btn[i]!=None and Btn[i].state):
                signature_length.append(Spin_Btn[i].get_value_as_int())
                size_index[Spin_Btn[i].get_value_as_int()]=0
        
        if(len(size_index)>0):
            retVal, textVal = verify_size(size_index)
            if (retVal):
                self.message_display("Signatures have the following error(s):\n"+textVal+'\nFile not created. Please try again!')
                return 0
            
        save_filename = entry.get_text()
        if save_filename.endswith('.txt'):
            try:
                patternGenerator(file_name=save_filename, size_arr=signature_length)
                self.message_display(message_text="Successfully created "+save_filename, _type=gtk.MESSAGE_INFO)
            #Exception Handling in case file save fails
            except Exception, e:
                print "Failed to create file. Please debug: "+str(e)
                self.message_display(message_text="Failed to create file. Please debug!")
        else:
            self.message_display(message_text="File extension must be '.txt'. Please try again!")
        
    
    def read_from_csv(self, widget, data):
        """Callback function to initiate reading CSV file"""
        file_location = self.read_from_file(widget, data, message="Open Signature CSV", file_type="csv")
        if(len(file_location)>0):
            self.window.destroy()
            loop_call(read_csv=True, file_location=file_location)
            
    def read_from_text(self, widget, data):
        """Callback function to initiate reading txt file"""
        file_location = self.read_from_file(widget, data, message="Open Signature Text", file_type="txt")
        if(len(file_location)>0):
            self.window.destroy()
            loop_call(read_csv=False, file_location=file_location)
        
    
    def read_from_file(self, widget, data, message, file_type):
        """Callback function to initiate reading a generic file"""
        dialog = gtk.FileChooserDialog(message,
                           None,
                           gtk.FILE_CHOOSER_ACTION_OPEN,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        #Add Filter to view only Txt Files
        _filter = gtk.FileFilter()
        dialog.set_current_folder(os.getcwd())
        if file_type=="txt":
            _filter.set_name("Text Only")
            _filter.add_pattern("*.txt")
        elif file_type=="csv":
            _filter.set_name("CSV Only")
            _filter.add_pattern("*.csv")
        else:
            _filter.set_name(file_type+" Only")
            _filter.add_pattern("*."+file_type)
            
        dialog.add_filter(_filter)            
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            file_location=dialog.get_filename()
            dialog.destroy()
            return file_location
        elif response == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            return ''
        
    
    def display_original_text(self, widget, data):
        """Callback function to Display Original Text Signature"""
        dialog = gtk.Dialog(title="Original Signatures", parent=None, 
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
        title_bar = ['ID', 'Original']
        for i in range(2):
            label = gtk.Label(title_bar[i])
            label.set_alignment(0, 0)
            label.modify_font(pango.FontDescription("Sans bold 12"))
            tableD.attach(label, i, i+1, 0, 1, xpadding=5)
        
        for i in range(2):
            for j in range(1, len(self.df)+1):
                if(i<3):
                    label = gtk.Label(str(self.df[title_bar[i]][j-1]))
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_alignment(0, 0)
                    tableD.attach(label, i, i+1, j, j+1, xpadding=10)
        
        tableD.show()
        tableD.set_col_spacings(15)
        scrolledWin.add_with_viewport(tableD)
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dialog.vbox.pack_start(frame, expand = False, fill = True, padding = 15)
        dialog.vbox.show_all()
        #dialog.vbox.pack_start(label)
        #label.show()
        
         
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def save_signature(self, widget, data, save_default_df=True, df=None):
        """Callback function to Save the Signature"""
        dialog = gtk.FileChooserDialog("Save File",
                           None,
                           gtk.FILE_CHOOSER_ACTION_SAVE,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)   
        dialog.set_current_folder(os.getcwd())
        
        #Create a filter to show only csv files
        _filter = gtk.FileFilter()
        _filter.set_name("CSV Only")
        _filter.add_pattern("*.csv")
        dialog.add_filter(_filter)  
        
        response = dialog.run()
        
        if save_default_df:
            save_df = self.df
        else:
            save_df = df
        
        #Run a basic check to ensure user has provided CSV file name
        if response == gtk.RESPONSE_OK:
            save_filename = dialog.get_filename()
            if save_filename.endswith('.csv'):
                try:
                    save_df.to_csv(save_filename, index=False)
                    self.message_display(message_text="Successfully created "+save_filename, _type=gtk.MESSAGE_INFO)
                    dialog.destroy()
                    return save_filename
                #Exception Handling in case file save fails
                except:
                    print "Failed to create file. Please debug!"
                    self.message_display(message_text="Failed to create file. Please debug!")
            else:
                self.message_display(message_text="File extension must be '.csv'. Please try again!")
            dialog.destroy()
        
        elif response == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            
    def generate_pattern(self, widget, data):
        """Callback function to Generate random patterns"""
        dialog = gtk.Dialog(title="Generate Random Text for Signatures", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(400,300)        
        
        Display_Order = [0, 4, 3, 2, 1]
        HBox = [None]*5
        VBox = [None]*5
        Label = [None]*5
        Adj = [None]*5
        Spin_Btn = [None]*5
        Btn = [None]*5
        for i in range(0, 5):
            HBox[i] = gtk.HBox()
            VBox[i] = gtk.VBox()
            Label[i] = gtk.Label("SLR "+str(Display_Order[i]))
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
        entry.set_text("RandomPatterns.txt")
        tooltips = gtk.Tooltips()
        tooltips.set_tip(entry, "Enter a valid *.txt filename")
        button.connect("clicked", self.generate, Spin_Btn, Btn, entry)        
        HBoxL.pack_start(button)
        HBoxL.pack_start(entry)
        VBoxL.pack_start(HBoxL)
        dialog.vbox.pack_start(VBoxL)
        
        dialog.vbox.show_all()
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def display_insertion_options(self, widget, data):
        """Callback funtion to allow options to inject signatures"""
        
        df=self.df
        #Insert table options for Enable and Start Index
        #Dummy values to make table insertion more readable
        title_bar = [None, None, 'Enable', 'Start Index', None]
        for i in range(2,4):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            label.set_alignment(0, 0)
            self.table.attach(label, i, i+1, 0, 1, xpadding=5)
        
        #Loop through table to display values
        ctr = 0
        self.button = [None]*5
        self.entry = [None]*5
        for i in range(2,4):
            ctr = 0
            for j in range(1, len(df)+1):
                if(i==2):
                    self.button[ctr] = gtk.CheckButton()
                    self.button[ctr].set_alignment(0, 0)
                    self.table.attach(self.button[ctr], i, i+1, j, j+1, xpadding=5)
                    ctr = ctr + 1
                elif(i==3):
                    self.entry[ctr] = gtk.Entry()
                    self.entry[ctr].set_alignment(0)
                    self.entry[ctr].set_width_chars(3)
                    self.table.attach(self.entry[ctr], i, i+1, j, j+1, xpadding=5)
                    ctr = ctr + 1
        
        self.table.show()
            
    def save_signature_pattern(self, widget, data):
        """Callback function to save signature patterns"""
        stream_data = pd.DataFrame(0, index=np.arange(0, len(self.entry)), columns = ['ID', 'Start_byte_index', 'End_byte_index'])
        ctr = 0
        for i in range(len(self.entry)):
            if(self.button[i]!=None and self.button[i].state):
                start_index = int(self.entry[i].get_text())
                stream_data['ID'][ctr]=self.df['ID'][i]
                stream_data['Start_byte_index'][ctr]=start_index
                stream_data['End_byte_index'][ctr]=start_index + self.df['Size'][i]
                ctr=ctr+1              
        
        stream_data = stream_data[(stream_data.T != 0).any()]
        self.message_display("Please choose a location to save the Signature insertion data", _type=gtk.MESSAGE_INFO)    
        self.save_signature(widget, data, save_default_df=False, df=stream_data)
    
    def validate_signature_pattern_for_stream(self, signature_pattern_data, stream_data):
        """Validates if signature pattern can be used for the given stream"""
        ErrorMessage = ''
        ErrorFlag = 0
        for i in range(0, len(signature_pattern_data)):
            for j in range(0, len((signature_pattern_data))):
                if(i!=j and signature_pattern_data['Start_byte_index'][i]==signature_pattern_data['Start_byte_index'][j]):
                    ErrorMessage+="SID #"+str(signature_pattern_data['ID'][j])+" will overlap SID #"+str(signature_pattern_data['ID'][i]) +"\n"
                elif(i!=j and signature_pattern_data['End_byte_index'][i]<=signature_pattern_data['Start_byte_index'][j]):
                    ErrorFlag=1
                    ErrorMessage+="SID #"+str(signature_pattern_data['ID'][i])+" will overlap starting index of SID #"+str(signature_pattern_data['ID'][j]) +"\n"

        for i in range(0,len(stream_data)):
            for j in range(0, len((signature_pattern_data))):
                if(stream_data['Size'][i]<signature_pattern_data['End_byte_index'][j]):
                    ErrorMessage+="SID #"+str(signature_pattern_data['ID'][j])+" exceeds size of Stream #"+str(stream_data['SID'][i])  +"\n"
                    ErrorFlag=1
        
        return ErrorFlag, ErrorMessage
                
    def inject(self, widget, data):
        """Callback function to Inject signature patterns into streams"""
        self.message_display(message_text="Open Signature Patterns File(.csv)", _type=gtk.MESSAGE_INFO)
        signature_pattern_location = self.read_from_file(widget, data, message="Open Signature Pattern File(.csv)", file_type="csv")
        signature_pattern_data = pd.read_csv(signature_pattern_location, header=0)
        
        self.message_display(message_text="Open Streams File(.txt)", _type=gtk.MESSAGE_INFO)
        stream_file_location = self.read_from_file(widget, data, message="Open Streams File(.txt)", file_type="txt")
        stream_data = pd.DataFrame(0, index=np.arange(MIN_N_LENGTHS-1, MAX_N_LENGTHS), columns = ['SID', 'Size', 'Hex'])
        fo = open(stream_file_location, "r")
        i=0
        for line in fo:
            line = line.strip('\n')
            size_line = len(line)       
            
            stream_data['SID'][i] = i
            stream_data['Hex'][i] = line.encode("Hex")
            stream_data['Size'][i] = size_line
            i=i+1
        
        retVal, retMessage = self.validate_signature_pattern_for_stream(signature_pattern_data, stream_data)        
        if(retVal):
            self.message_display(message_text="Cannot use the signature pattern file:\n"+retMessage+"Please try a different combination!")
            return 1
        elif(retVal==0 and len(retMessage)>0):
            self.message_display(message_text=retMessage, _type=gtk.MESSAGE_WARNING)
        
        for i in range(0,len(stream_data)):
            for j in range(0, len((signature_pattern_data))):
                stream_val = stream_data['Hex'][i].decode("Hex")
                start_index = signature_pattern_data['Start_byte_index'][j]
                end_index = signature_pattern_data['End_byte_index'][j]
                #Lookup signature data from original file based on matching ID
                search_val = self.df[self.df['ID']==signature_pattern_data['ID'][j]]
                search_val.reset_index(drop=True, inplace=True)
                signature_val = search_val['Original'][0]
                stream_val = stream_val[0:start_index] + signature_val + stream_val[end_index]
            
            #Update the stream value
            stream_data['Hex'][i]=stream_val.encode("Hex")
        
        size_arr = []
        for i in range(0,len(signature_pattern_data)):
            size_arr.append(int(signature_pattern_data['End_byte_index'][i])-int(signature_pattern_data['Start_byte_index'][i]))
        size_arr = sorted(size_arr, reverse=True)
        
        if(size_arr==1):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,0,0'
        elif(size_arr==2):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,0,'+str(size_arr[1])
        elif(size_arr==3):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,'+str(size_arr[1])+','+str(size_arr[2])
        elif(size_arr==4):
            Load_Line = 'L,'+str(size_arr[0])+',0,'+str(size_arr[1])+','+str(size_arr[2])+','+str(size_arr[3])
        else:
            Load_Line = 'L,'+str(size_arr[0])+','+str(size_arr[1])+','+str(size_arr[2])+','+str(size_arr[3])+','+str(size_arr[4])
            
        self.message_display("Please choose a location to save the Stream Input file(.csv)", _type=gtk.MESSAGE_INFO)    
        file_location = self.save_signature(widget, data, save_default_df=False, df=stream_data)
        
        for line in fileinput.input(file_location, inplace=True):
            if 'SID' in line:
                print Load_Line
            else:
                print line.strip('\n')
        """
        fo = open(file_location, "r+")
        for line in fo:
            if 'SID' in line:
                fo.write(Load_Line)
                break
        """
        
    def stream_view(self, widget, data):
        """Callback function to Inject signatures into the stream"""
        filename = 'stream_utility.py'
        os.system("start "+filename)
    
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
        self.file_location = file_location
        
        self.showSize = 1
        
        self.menu_items = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Read Hex Signatures with IDs & Size(.csv)",     "<control>O", self.read_from_csv, 0, None ),
            ( "/File/_Read Text Signatures(.txt)",    "<control>T", self.read_from_text, 0, None ),
            ( "/File/_Save As..",    "<control>S", self.save_signature, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Quit",     "<control>Q", self.destroy, 0, None ),
            ( "/_Display",      None,         None, 0, "<Branch>" ),
            ( "/Display/_Display Text View of Signatures",  "<control>D", self.display_original_text, 0, None ),
            ( "/_Generate",         None,         None, 0, "<Branch>" ),
            ( "/Generate/Generate Random Text Signatures",   None, self.generate_pattern, 0, None ),
            ( "/_Inject",         None,         None, 0, "<Branch>" ),
            ("/_Inject/Save Signature Injection pattern file(.csv)",   None, self.save_signature_pattern, 0, None ),
            ("/_Inject/Inject Signature pattern into streams",   None, self.inject, 0, None ),
            ( "/_View",         None,         None, 0, "<Branch>" ),
            ("/_View/Stream View",   None, self.stream_view, 0, None ),
            )
        
        #Create new GTK Window instance
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", lambda w: gtk.main_quit())
        self.window.set_title(TOOL_NAME+" | File: "+str(self.file_location))
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
        frame = gtk.Frame("Pattern Values")
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        
        #Create Table to display values
        self.table = gtk.Table(rows=len(df)+1, columns=5, homogeneous=False) 
        self.table.set_col_spacings(10)       
        title_bar = ['ID', 'Size', 'Enable', 'Start Index', 'Hex']
        for i in range(5):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            label.set_alignment(0, 0)
            self.table.attach(label, i, i+1, 0, 1, xpadding=5)
        
        #Loop through table to display values
        ctr = 0
        self.button = [None]*5
        self.entry = [None]*5
        for i in range(5):
            ctr = 0
            for j in range(1, len(df)+1):
                if(i!=2 and i!=3):
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_alignment(0, 0)
                    self.table.attach(label, i, i+1, j, j+1, xpadding=5)
                
                elif(i==2):
                    self.button[ctr] = gtk.CheckButton()
                    self.button[ctr].set_alignment(0, 0)
                    self.table.attach(self.button[ctr], i, i+1, j, j+1, xpadding=5)
                    ctr = ctr + 1
                elif(i==3):
                    self.entry[ctr] = gtk.Entry()
                    self.entry[ctr].set_alignment(0)
                    self.entry[ctr].set_width_chars(3)
                    self.table.attach(self.entry[ctr], i, i+1, j, j+1, xpadding=5)
                    ctr = ctr + 1
                

        scrolledWin.add_with_viewport(self.table)
        self.table.set_col_spacings(15)
        self.table.show()
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dataBox.pack_start(frame,  expand = False, fill = True, padding = 15)
        dataBox.set_border_width(1)
        #Create Partition for displaying size information
        sizeBox = gtk.VBox()
        frame = gtk.Frame("Size information")
        sorted_size = sorted(self.si.items(), key=operator.itemgetter(0))
        
        #Initialize table for size information
        table2 = gtk.Table(rows=len(sorted_size)+1, columns=2, homogeneous=False)
        table2.attach(gtk.Label("Size"), 0, 1, 0, 1)
        table2.attach(gtk.Label("Count"), 1, 2, 0, 1)
        
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
        retVal, textVal = verify_size(self.si)
        if (retVal):
            self.message_display("Signatures have the following error(s):\n"+textVal)


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
            min_check = MIN_SIZE_SIGNATURE - 1
        else:
            min_check = MIN_SIZE_SIGNATURE
        
        if sorted_size[i][0]%8!=0:
            flag=1
            ErrorMessage+= "Signature is not a multiple of 8. It's not a valid byte.\n"
        
        if sorted_size[i][0]>MAX_SIZE_SIGNATURE:
            flag=1
            ErrorMessage+= "Signature length greater than: "+str(MAX_SIZE_SIGNATURE)+"\n"
        elif sorted_size[i][0]<min_check:
            flag=1
            ErrorMessage+= "Signature length less than: "+str(MIN_SIZE_SIGNATURE)+"\n"
        
        if(i==0):
            previous_val=sorted_size[0][0]
            continue
        
        if(sorted_size[i][0]-previous_val<DISTANCE_CONSECUTIVE):
            flag=1
            ErrorMessage+= "Distance between consecutive signatures less than: "+str(DISTANCE_CONSECUTIVE)+"\n"
        
        previous_val=sorted_size[i][0]
    
    if(flag):
        return 1, ErrorMessage
    else:
        return 0, None
        
def id_generator(size=MIN_SIZE_SIGNATURE, chars=ALLOWABLE_CHARS):
    """Generates a random ID of specified size and characters
        Inputs:
        size: Size of random string
        chars: Characters to be included
    """
    return ''.join(random.choice(chars) for _ in range(size))

def patternGenerator(file_name="patterns.txt", size_arr = [], min_n_lengths=MIN_N_LENGTHS, 
                     max_n_lengths=MAX_N_LENGTHS, min_size_signature=MIN_SIZE_SIGNATURE,
                     max_size_signature=MAX_SIZE_SIGNATURE, distance_consecutive=DISTANCE_CONSECUTIVE):
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
        if(len(size_arr)==0):
            n = random.randint(min_n_lengths-1, max_n_lengths)
            #Hardcoding n to 5 temporarily
            #n=5
            #Generate array of random numbers, such that difference is greater than or equal to DISTANCE_CONSECUTIVE
            while len(size_arr)!=n:
                tmp = random.randint(min_size_signature, max_size_signature)
                
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

def generateBitStream(ID, Size_val, Hex_val, SLR_val, SLR_index):
    ID = "{0:016b}".format(ID)
    Size_val = "{0:016b}".format(Size_val)
    #Hex_val = ''.join('{0:04b}'.format(int(c, 16)) for c in Hex_val)
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
    
    return ID+str_pad+Size_val+str_pad+SLR_final+str_pad+Hex_val

def interpretPattern(read_csv=False, file_location="patterns.txt"):
    """Reads the pattern file and generates ID, Hex and Size paramters. 
        Returns None, None on failure and a dataframe, dictionary on success
        Inputs:
        file_name: Name of the file
    """
    if(read_csv):
        try:
            csv_data = pd.read_csv(file_location, header=0)
        except Exception,e:
            print "Failed to read file with exception" + str(e)
            return None, None, 1
        
    proc_data = pd.DataFrame(0, index=np.arange(MIN_N_LENGTHS-1, MAX_N_LENGTHS), columns = ['ID', 'Size', 'Hex', 'Original'])
    size_index = {}
    if not(read_csv):
        try:
            fo = open(file_location, "r")
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
                proc_data['Hex'][i] = line.encode("Hex")
                proc_data['Original'][i] = line
                proc_data['Size'][i] = size_line
                
                #Generate bitstream
                #stream_data = ''.join('{0:04b}'.format(int(c, 16)) for c in proc_data['Hex'][i])
                
                i=i+1
        except Exception,e:
            print "Failed to open file with exception" + str(e)
            return None, None, 1
    
    else:
        proc_data['ID'] = csv_data['ID']
        proc_data['Size'] = csv_data['Size']
        proc_data['Hex'] = csv_data['Hex']
        for i in range(len(proc_data)):
            proc_data['Original'][i] = proc_data['Hex'][i].decode("Hex")
            size_line = proc_data['Size'][i]
            if(size_index.has_key(size_line)):
                    size_index[size_line] += 1
            else:
                size_index[size_line] = 1
    
    #Commenting out block for Vector Generation
    """                
    #Sort the dataframe from lowest to highest based on size
    proc_data = proc_data.sort_values(by='Size', ascending=True)
    proc_data.reset_index(drop=True, inplace=True)
    
    #Prepare Python to store strings
    proc_data['Vector']=''
    
    #Fill the largest element in SLR 0
    l=len(proc_data)-1
    val=generateBitStream(proc_data['ID'][l], proc_data['Size'][l], proc_data['Hex'][l], 130-proc_data['Size'][l]-1, 0)
    proc_data['Vector'][l]=str(val)
    
    previous_Val = 0
    SLR_index=4
    #Fill the smallest elements in SLRs 4 to 1
    for i in range(0, len(proc_data)-1):
        SLR_val = 130 - (proc_data['Size'][i] - previous_Val) - 1
        val=generateBitStream(proc_data['ID'][i], proc_data['Size'][i], proc_data['Hex'][i], SLR_val, SLR_index)
        proc_data['Vector'][i] = val
        previous_Val = proc_data['Size'][i]
        SLR_index=SLR_index-1
    
    
    #Write as CSV
    proc_data.to_csv("InterpretPatterns.csv", index=False)
    """
    proc_data = proc_data[(proc_data.T != 0).any()]
    return proc_data, size_index, 0

def loop_call(read_csv=True, file_location="TemplateCSV.csv"):
    """Function to generate new patterns and display it on the GUI
    """
    if not(read_csv):
        patternGenerator()
    df, si, retVal = interpretPattern(read_csv=read_csv, file_location=file_location)
    #GTK object
    if(~retVal):
        PyApp(df, si, file_location)
        gtk.main()
    else:
        print "Debug the exception!"
if __name__ == "__main__":
    loop_call()