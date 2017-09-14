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

MAX_COUNT_STREAMS = 15

ALLOWABLE_CHARS = string.ascii_letters + string.digits + string.punctuation


class PyApp:
    
    def read_from_csv(self, widget, data):
        """Callback function to initiate reading CSV file"""
        file_location = self.read_from_file(widget, data, message="Open Signature CSV", file_type="csv")
        try:
            if(file_location!=None and len(file_location)>0):
                self.window.destroy()
                df, si, retVal = interpretPattern(read_csv=True, file_location=file_location)
                if(~retVal):
                    self.create_signature_window(widget, df, si, file_location)
                else:
                    self.message_display("Failed to read file. Please verify the file contents.")
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
            
    def read_from_text(self, widget, data):
        """Callback function to initiate reading txt file"""
        file_location = self.read_from_file(widget, data, message="Open Signature Text", file_type="txt")
        try:
            if(file_location!=None and len(file_location)>0):
                self.window.destroy()
                df, si, retVal = interpretPattern(read_csv=False, file_location=file_location)
                if(~retVal):
                    self.create_signature_window(widget, df, si, file_location)
                else:
                    self.message_display("Failed to read file. Please verify the file contents.")
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
        
    def read_csv_stats(self, widget, data):
        """Callback function to initiate reading CSV file"""
        file_location = self.read_from_file(widget, data, message="Open Stream Stats CSV", file_type="csv")
        try:
            if(file_location!=None and len(file_location)>0):
                self.window3.destroy()
                ver_df, retVal = interpretStats(file_location=file_location)
                if(~retVal):
                    retValueMsg = self.message_display(message_text="Proceed checking with default file(STREAMS_IN.csv)?", _type=gtk.MESSAGE_INFO, buttons=(gtk.BUTTONS_YES_NO))
                    #Stop if user presses cancel
                    if retValueMsg!=-8:
                        stream_bin_file_location = self.read_from_file(widget, data, message="Open Stream Binary File", file_type="csv")
                    else:
                        stream_bin_file_location =  os.path.join(os.getcwd(), 'STREAMS_IN.csv')
                    
                    if(os.path.isfile(stream_bin_file_location)):
                        ver_df_updated, stats = verifyStats(ver_df, stream_bin_file_location)
                        self.create_verification_window(ver_df_updated, stats)
                    else:
                        self.message_display("Failed to locate: "+str(stream_bin_file_location)+"\nPlease try again!")
                else:
                    self.message_display("Failed to read file. Please verify the file contents.")               
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
        
    def read_csv_processed_stats(self, widget, data):
        """Callback function to initiate reading CSV file"""
        file_location = self.read_from_file(widget, data, message="Open processed Stream Stats CSV", file_type="csv")
        try:
            if(file_location!=None and len(file_location)>0):
                self.window3.destroy()
                ver_df, retVal = interpretStats(file_location=file_location, processed=1)
                if(~retVal):
                    ver_stats, retVal2 = interpretStatsSummary(file_location=file_location)
                    if(~retVal2):
                        self.create_verification_window(ver_df, ver_stats)
                    else:
                        self.message_display("Failed to read file. Please verify the file contents.")
                        return 1
                else:
                    self.message_display("Failed to read file. Please verify the file contents.")
                    return 1
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
            
    def load_stream_binary_file(self, widget, data):
        """Callback function to initiate reading stream map file"""
        #Clear old values
        for i in range(self.current_index):
            self.update_Stream_GUI(SID='', Size_Stream='', Select_Stream=False, SgnPosition='', History='', index=i)
        self.stream_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Original'])
        self.current_index = 0
        self.history_index = [[[-1, -1, -1, -1]]] * MAX_COUNT_STREAMS
        self.size_history = {}
        self.current_index = 0
        self.close_insertion_dialog()
        if(hasattr(self,'undo_button')):
            self.undo_button.set_sensitive(False)
        
        file_location = self.read_from_file(widget, data, message="Open Binary Stream output File", file_type="csv")
        self.window2.set_title("Stream Construction Window | "+str(file_location))
        try:
            if(file_location!=None and len(file_location)>0):    
                stream_df_map = pd.read_csv(file_location, skiprows=[0], header=None)
                #stream_df_map.fillna(-1, inplace=True)
                for i in range(len(stream_df_map)):
                    SID = int(stream_df_map[0][i])
                    Size_stream = int(stream_df_map[1][i])
                    Hex = str(stream_df_map[2][i])
                    Original = Hex.decode("hex")
                    self.stream_df.loc[self.current_index]=[SID, Size_stream, Hex, Original]
                    count = int(float(stream_df_map[3][i]))
                    pattern_val = ''
                    SgnPosition = ''
                    if(count>0):
                        for p in range(4, 4+(count*3)):
                            pattern_val+=str(stream_df_map[p][i])+","
                        pattern_val = pattern_val[:-1]
                        pattern_val = pattern_val.split(',')
                        #Typecast string to float
                        for i in range(len(pattern_val)):
                            pattern_val[i] = float(pattern_val[i])
                            
                        ctr=0
                        for _ in range(count):
                            ID = int(pattern_val[ctr])
                            S_Index = int(pattern_val[ctr+1])
                            E_Index = int(pattern_val[ctr+2])
                            SgnPosition+='('+str(ID)+':'+str(S_Index)+'-'+str(E_Index)+') '
                            ctr += 3
                            
                            if(self.history_index[i][0]==[-1, -1, -1, -1]):
                                self.history_index[i] = [[ID, S_Index, E_Index, 0]]
                            else:
                                self.history_index[i].append([id, S_Index, E_Index, 0])
                            #Create an entry in the dictionary for size
                            sign_size = E_Index - S_Index + 1
                            if(self.size_history.has_key(sign_size)):
                                self.size_history[sign_size] += 1
                            else:
                                self.size_history[sign_size] = 1
                    
                    self.update_Stream_GUI(SID=SID, Size_Stream=Size_stream/8, Select_Stream=True, SgnPosition=SgnPosition, History=None, index=self.current_index)
                    self.current_index += 1
                    
                #Make a copy of the stream to have an option to undo later
                self.stream_df_copy = self.stream_df.copy()
                
                self.create_insertion_dialog(widget, data, undoButton=False)
        except Exception, e:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
        
    def load_stream_map(self, widget, data):
        """Loads Stream map into stream construction GUI"""
        #Clear old values
        for i in range(self.current_index):
            self.update_Stream_GUI(SID='', Size_Stream='', Select_Stream=False, SgnPosition='', History='', index=i)
        self.stream_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Original'])
        self.current_index = 0
        self.history_index = [[[-1, -1, -1, -1]]] * MAX_COUNT_STREAMS
        self.size_history = {}
        self.current_index = 0
        self.close_insertion_dialog()
        
        if(hasattr(self,'undo_button')):
            self.undo_button.set_sensitive(True)
        
        file_location = self.read_from_file(widget, data, message="Open Stream Map", file_type="csv")
        self.window2.set_title("Stream Construction Window | "+str(file_location))
        try:
            if(file_location!=None and len(file_location)>0):
                stream_df_map = pd.read_csv(file_location, header=None, names=['SID', 'Stream_Size', 'ID', 'Start_index', 'End_Index', 'Full_Signature'])
                i=0
                while i < len(stream_df_map):
                    SID = int(stream_df_map['SID'][i])
                    Size_stream = int(stream_df_map['Stream_Size'][i])
                    Stream = id_generator(size=Size_stream/8)
                    Hex = Stream.encode("hex")
                    self.stream_df.loc[self.current_index]=[SID, Size_stream, Hex, Stream]
                    
                    search_val = stream_df_map[stream_df_map['SID']==SID]
                    search_val.reset_index(drop=True, inplace=True)
                    sign_count = len(search_val)
                    SgnPosition = ''
                    for j in range(i, i+sign_count):
                        if(stream_df_map['ID'][j]>-1):
                            ID = int(stream_df_map['ID'][j])
                            S_Index = int(stream_df_map['Start_index'][j])
                            E_Index = int(stream_df_map['End_Index'][j])
                            Full_Signature = int(stream_df_map['Full_Signature'][j])
                            if Full_Signature:
                                SgnPosition+='('+str(ID)+':'+str(S_Index)+'-'+str(E_Index)+') '
                            else:
                                SgnPosition +='<span color="red">('+str(ID)+':'+str(S_Index)+'-'+str(E_Index)+') </span>'
                            Full_Signature = 0 if Full_Signature==1 else 1
                            if(self.history_index[self.current_index][0]==[-1, -1, -1, -1]):
                                    self.history_index[self.current_index] = [[ID, S_Index, E_Index, Full_Signature]]
                            else:
                                self.history_index[self.current_index].append([ID, S_Index, E_Index, Full_Signature])
                                
                            #Create an entry in the dictionary for size
                            sign_size = E_Index - S_Index + 1
                            if(self.size_history.has_key(sign_size)):
                                self.size_history[sign_size] += 1
                            else:
                                self.size_history[sign_size] = 1
                            
                    self.update_Stream_GUI(SID=SID, Size_Stream=Size_stream/8, Select_Stream=True, SgnPosition=SgnPosition, History=None, index=self.current_index)
                    self.current_index += 1
                    i = i + sign_count                
                self.create_insertion_dialog(widget, data)
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1        
            
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
        if(len(self.df)<15):
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        else:
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
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
        
        if(len(self.df)<15):
            dialog.vbox.pack_start(frame,  expand = False, fill = False, padding = 15)
        else:
            dialog.vbox.pack_start(frame,  expand = True, fill = True, padding = 15)   
            
        #dialog.vbox.pack_start(frame, expand = False, fill = True, padding = 15)
        dialog.vbox.show_all()
         
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def save_signature(self, widget, data, save_default_df=True, df=None, header=False):
        """Callback function to Save the Signature.
            Doubles as functio to save a dataframe based on customizable paramters."""
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
        
        #Run a basic check to ensure user has provided CSV file name
        if response == gtk.RESPONSE_OK:
            if save_default_df:
                save_df = self.df.copy()
                save_df.drop('Original', axis=1, inplace=True)
            else:
                save_df = df.copy()
            save_filename = dialog.get_filename()
            if save_filename.endswith('.csv'):
                try:
                    save_df.to_csv(save_filename, index=False, header=header)
                    self.message_display(message_text="Successfully created "+save_filename, _type=gtk.MESSAGE_INFO)
                    dialog.destroy()
                    return save_filename
                #Exception Handling in case file save fails
                except:
                    print "Failed to create file. Please debug!"
                    self.message_display(message_text="Failed to create file. Please debug!")
                    return ''
            else:
                self.message_display(message_text="File extension must be '.csv'. Please try again!")
                return ''
            dialog.destroy()
        
        elif response == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            
    def generate(self, widget, Spin_Btn, Btn, Spin_Btn_Count ,entry):
        """Callback function to parse signature random patterns"""
        #Generate array for various sizes
        signature_length = []
        
        #Record sizes to perform verification
        size_index = {}
        for i in range(5):
            if(Btn[i]!=None and Btn[i].state):
                #Get number of times a particular length should be repeated
                count = Spin_Btn_Count[i].get_value_as_int()
                while count!=0:
                    #Append Byte size of Signature length
                    signature_length.append(Spin_Btn[i].get_value_as_int()/8)
                    
                    #Dummy Size index for verification dictionary
                    size_index[Spin_Btn[i].get_value_as_int()]=0
                    count=count-1
        
        #Verify the sizes entered in the dialog box
        if(len(size_index)>0):
            retVal, textVal = verify_size(size_index)
            if (retVal):
                self.message_display("Signatures have the following error(s):\n"+textVal+'\nFile not created. Please try again!')
                return 0
        else:
            self.message_display("None of the check-boxes were enabled. Please choose at least one signature length.")
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
        
    
    def generate_pattern(self, widget, data):
        """Callback function to create dialog to generate random patterns"""
        dialog = gtk.Dialog(title="Generate Random Text for Signatures", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR)
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(400,300)        
        
        HBox = [None]*5
        VBox = [None]*5
        Label = [None]*5
        Adj = [None]*5
        Spin_Btn = [None]*5
        Btn = [None]*5
        Spin_Btn_Count = [None]*5
        Adj_Count = [None]*5
        tooltips = gtk.Tooltips()
        
        for i in range(0, 5):
            HBox[i] = gtk.HBox()
            VBox[i] = gtk.VBox()
            Label[i] = gtk.Label("Size "+str(i+1))
            if(i==0):
                Adj[i] = gtk.Adjustment(value=3*8, lower=3*8, upper=130*8, step_incr=1*8)
            else:
                Adj[i] = gtk.Adjustment(value=4*8, lower=4*8, upper=130*8, step_incr=1*8)
            
            Spin_Btn[i] = gtk.SpinButton(adjustment=Adj[i], climb_rate=0.0, digits=0)
            Adj_Count[i] = gtk.Adjustment(value=1, lower=1, upper=100, step_incr=1)
            Spin_Btn_Count[i] = gtk.SpinButton(adjustment=Adj_Count[i], climb_rate=0.0, digits=0)
            
            
            HBox[i].pack_start(Label[i])
            HBox[i].pack_start(Spin_Btn[i])
            HBox[i].pack_start(Spin_Btn_Count[i])
            Btn[i] = gtk.CheckButton()
            
            tooltips.set_tip(Spin_Btn[i], "Choose the signature size in bits")
            tooltips.set_tip(Spin_Btn_Count[i], "Choose the number of signatures")
            tooltips.set_tip(Btn[i], "Check to enable creation")
            
            HBox[i].pack_start(Btn[i], False, False)
            VBox[i].pack_start(HBox[i])
            dialog.vbox.pack_start(VBox[i])
        
        VBoxL = gtk.VBox()
        HBoxL = gtk.HBox()
        button = gtk.Button("Generate!")
        entry = gtk.Entry()
        entry.set_text("RandomPatterns.txt")
        tooltips.set_tip(entry, "Enter a valid *.txt filename")
        button.connect("clicked", self.generate, Spin_Btn, Btn, Spin_Btn_Count, entry)        
        HBoxL.pack_start(button, padding=10)
        HBoxL.pack_start(entry, padding=10)
        VBoxL.pack_start(HBoxL)
        dialog.vbox.pack_start(VBoxL)
        
        dialog.vbox.show_all()
        response = dialog.run()
        
        dialog.destroy()
    
    
    def active_signature(self, widget, data):
        """Updates active signature"""
        if widget.get_active():
            if(data!=''):
                self.current_signature = int(data)
            try:
                self.current_signature_label.set_text(data)
            except:
                return
    
    def active_stream(self, widget, data):
        """Updates active stream"""
        if widget.get_active():
            if(data!=''):
                self.current_stream = int(data)
            try:
                self.current_stream_label.set_text(data)
            except:
                return
    
    def update_Stream_GUI(self, SID, Size_Stream, Select_Stream, SgnPosition, History, index):
        """Updates the GUI based on input parameters. Send None if you don't want to update"""
        if SID!=None:
            self.SID[index].set_text(str(SID))
        if Size_Stream!=None:
            self.Size_Stream[index].set_text(str(Size_Stream))
        if Select_Stream!=None:
            self.Select_Stream[index].set_sensitive(Select_Stream)
            self.Select_Stream[index].connect("clicked", self.active_stream, self.SID[index].get_label())
            self.Select_Stream[index].set_active(Select_Stream)
            data = self.SID[index].get_label()
            if data!='':
                self.current_stream = int(data)
            try:
                self.current_stream_label.set_text(data)
            except:
                pass
            
        if SgnPosition!=None:
            #self.SgnPosition[index].set_text(SgnPosition)
            self.SgnPosition[index].set_markup(SgnPosition)
        if History!=None:
            self.History.set_text(History)
        
        self.table_stream.show()
        
        #Update copy with new df
        #self.stream_df_copy = self.stream_df.copy()
    
    
    def display_text_view(self, widget, data):
        """Display original text of current stream"""
        dialog = gtk.Dialog(title="Text View of Stream", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(400,300)
        
        frame = gtk.Frame()
    
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        
        tableD = gtk.Table(rows=2, columns=2, homogeneous=False)
        tableD.set_col_spacings(10)       
        title_bar = ['SID', 'Original']
        for i in range(2):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            tableD.attach(label, i, i+1, 0, 1, xpadding=5)
        
        stream_index = self.stream_df[self.stream_df['SID']==self.current_stream].index[0]
        
        SID = gtk.Label(str(self.current_stream))
        
        text = self.stream_df['Original'][stream_index]
        """
        color = ["red", "blue", "green", "yellow", "orange"]
        flag = 0
        for i in self.history_index:
            start = i[1] + 25*flag
            end = i[2]
            text = text[:start]+'<span color="'+color[(flag)%5]+'">'+text[start:end]+'</span>'+text[end:]
            flag = flag + 1
        """
        TextView = gtk.Label(text)
        TextView.set_selectable(True)
        #TextView.set_markup(glib.markup_escape_text(text))
        #TextView.set_markup(text)
        
        val=[SID, TextView]
        for i in range(2):
            tableD.attach(val[i], i, i+1, 1, 2, xpadding=5)
        
        tableD.show()
        scrolledWin.add_with_viewport(tableD)
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        dialog.vbox.pack_start(frame, expand = False, fill = True, padding = 5)
        dialog.vbox.show_all()
        
         
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
            
    def create_stream_table(self):
        """Create Table to display stream values"""
        self.table_stream = gtk.Table(rows=1+MAX_COUNT_STREAMS, columns=4, homogeneous=False) 
        self.table_stream.set_col_spacings(10)
        title_bar = ['SID', 'Size(bytes)', 'Select', 'Signature (ID: Start-End)']
        for i in range(4):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            label.set_alignment(0, 0)
            self.table_stream.attach(label, i, i+1, 0, 1, xpadding=5)
        
        self.SID = [None] * MAX_COUNT_STREAMS        
        self.Select_Stream = [None] * MAX_COUNT_STREAMS        
        self.Size_Stream = [None] * MAX_COUNT_STREAMS        
        self.SgnPosition = [None] * MAX_COUNT_STREAMS
        
        
        
        #Load dummy values into the table
        for i in range(4):
            for j in range(1, MAX_COUNT_STREAMS+1):
                if(i==0):
                    label = gtk.Label("")
                    label.set_alignment(0, 0)
                    self.SID[j-1] = label
                    self.table_stream.attach(self.SID[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==1):
                    label = gtk.Label("")
                    label.set_alignment(0, 0)
                    self.Size_Stream[j-1] = label
                    self.table_stream.attach(self.Size_Stream[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==2): 
                    if(j==1):
                        self.Select_Stream[j-1] = gtk.RadioButton(None)
                        self.Select_Stream[j-1].set_active(True)
                    else:
                        self.Select_Stream[j-1] = gtk.RadioButton(self.Select_Stream[0])
                        self.Select_Stream[j-1].set_alignment(0.5, 0.5)
                    
                    self.Select_Stream[j-1].set_sensitive(False)
                    self.table_stream.attach(self.Select_Stream[j-1], i, i+1, j, j+1, xpadding=5)
                    
                else:
                    label = gtk.Label("")
                    label.set_alignment(0, 0)
                    self.SgnPosition[j-1] = label
                    self.table_stream.attach(self.SgnPosition[j-1], i, i+1, j, j+1, xpadding=5)                        
                                    
        self.table_stream.set_col_spacings(15)
        self.table_stream.show()
    
    def delete_verify_window(self, widget, data=None):
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==8:
            self.save_stats(widget, data)
        else:
            self.window3.destroy()
            
    def delete_stream_window(self, widget, data=None):
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==8:
            self.save_stream_map(widget, data)    
        else:
            self.window2.destroy()        
        self.change_signature_select_line_state(state=False)
    
    def delete_signature_window(self, widget, data=None):
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==8:
            self.save_signature(widget, data)
        else:
            self.window.destroy()
    
    def delete_load_window(self, widget, data=None):
        retValue = self.message_display("Are you sure you want to quit?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue!=gtk.RESPONSE_YES:
            return True
        return False
            
    def create_verification_table(self):
        """Create Table to display verification values"""
        df=self.ver_df
        self.table_verification = gtk.Table(rows=len(df)+1, columns=6, homogeneous=False) 
        self.table_verification.set_col_spacings(10)
        title_bar = ['SID', 'Time', 'Query Op', 'Start Index', 'End Index', 'Verification Result', 'Signature ID']
        for i in range(7):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            label.set_alignment(0, 0)
            self.table_verification.attach(label, i, i+1, 0, 1, xpadding=5)
        
        #Loop through table to display values
        title_bar = ['SID', 'Time', 'Query_Op', 'Start_Index', 'End_Index', 'Verification_Result', 'ID']
        for i in range(7):
            for j in range(1, len(df)+1):                       
                if(i<3 or i>4):                    
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_selectable(True)
                    label.set_alignment(0, 0)
                    self.table_verification.attach(label, i, i+1, j, j+1, xpadding=5)
                elif(i>2 and i<5):
                    #Check if its Q_START
                    if('START' in str(df['Query_Op'][j-1])):
                        label = gtk.Label("")
                    else:
                        label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_selectable(True)
                    label.set_alignment(0, 0)
                    self.table_verification.attach(label, i, i+1, j, j+1, xpadding=5)
                    
        self.table_verification.show()
    
    def create_stats_table(self):
        """Create table to display stats"""
        self.table_stats = gtk.Table(rows=2, columns=7, homogeneous=True)
        ctr=0
        for i in self.ver_stats:
            label = gtk.Label(str(i[0]))
            label.modify_font(pango.FontDescription("Sans bold 11"))
            label.set_alignment(0.5, 0.5)
            self.table_stats.attach(label, ctr, ctr+1, 0, 1, xpadding=5)
            ctr+=1
        
        ctr=0
        for i in self.ver_stats:
            label = gtk.Label(str(i[1]))
            label.modify_font(pango.FontDescription("Sans 10"))
            label.set_alignment(0.5, 0.5)
            self.table_stats.attach(label, ctr, ctr+1, 1, 2)
            ctr+=1
        
        self.table_stats.show()
        
    def create_verification_window(self, ver_df, stats):
        """Creates Window 3 for Stream verification"""
        self.window3 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window3.connect("destroy", lambda w: self.window3.destroy())
        self.window3.connect("delete_event", self.delete_verify_window)
        self.window3.set_title("Stream Verification Window")
        self.window3.set_default_size(640, 480)
        
        self.ver_df = ver_df
        self.ver_stats = stats
        
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        main_vbox.show()
        menu_items3 = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Load Stream Stats",     "<control>O", self.read_csv_stats, 0, None ),
            ( "/File/_Load processed Stream Stats",     "<control>T", self.read_csv_processed_stats, 0, None ),
            ( "/File/_Save processed Stream Stats",     "<control>S", self.save_stats, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_stream_window, 0, None ),
            )
        
        menubar = self.get_main_menu(self.window3, menu_items3)

        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        
        dataBox = gtk.VBox(spacing=30)
        frame = gtk.Frame("Stream Results")
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        if(len(ver_df)<15):
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        else:
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            
        self.create_verification_table()        
        scrolledWin.add_with_viewport(self.table_verification)      
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        if(len(ver_df)<15):
            dataBox.pack_start(frame,  expand = False, fill = False, padding = 15)
        else:
            dataBox.pack_start(frame,  expand = True, fill = True, padding = 15)
        
        statBox = gtk.VBox()
        frame = gtk.Frame("Statistics")
        self.create_stats_table()
        #label = gtk.Label(stats)
        #label.set_use_markup(True)
        frame.add(self.table_stats)                    
        statBox.pack_start(frame,  expand = False, fill = True, padding = 20)        
        
        main_vbox.pack_start(dataBox, False, False)
        main_vbox.pack_start(statBox, False, False)
        
        self.window3.add(main_vbox)
        self.window3.show_all()    
        
        
    def create_stream_window(self):
        """Creates Window 2 for Stream viewing and editing"""
        self.window2 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window2.connect("destroy", lambda w: self.window2.destroy())
        self.window2.connect("delete_event", self.delete_stream_window)
        self.window2.set_title("Stream Construction Window")
        self.window2.set_default_size(640, 480)
        
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        main_vbox.show()
        
        self.menu_items2 = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Load Stream Binary file",     "<control>O", self.load_stream_binary_file, 0, None ),
            ( "/File/_Load Stream Map",    "<control>T", self.load_stream_map, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_stream_window, 0, None ),
            ( "/_Display",         None,         None, 0, "<Branch>" ),
            ( "/_Display/_Display Text view of Current Stream (without signatures)",    "<control>D", self.display_text_view, 0, None ),
            ( "/_Create",         None,         None, 0, "<Branch>" ),
            ( "/_Create/_Open Stream Construction Dialog",    "<control>N", self.create_insertion_dialog, 0, None ),
            )
        
        menubar = self.get_main_menu(self.window2, self.menu_items2)

        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        
        #Create partition for Data display
        dataBox = gtk.VBox(spacing=30)
        frame = gtk.Frame("Stream Information")
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)        
        self.create_stream_table()        
        scrolledWin.add_with_viewport(self.table_stream)        
        
        frame.add(scrolledWin)
        scrolledWin.show()
        dataBox.pack_start(frame,  expand = True, fill = True, padding = 15)
        
        
        #Create Partition for displaying size information
        historyBox = gtk.VBox()
        frame = gtk.Frame("History(StreamID: Signature ID-->Start Index, End Index)")
        self.History = gtk.Label(" ")
        self.History.set_alignment(0.5, 0.5)
        frame.add(self.History)            
        historyBox.pack_start(frame,  expand = False, fill = True, padding = 20)        
        
        main_vbox.pack_start(dataBox, True, True)
        main_vbox.pack_start(historyBox, False, False)
        self.window2.add(main_vbox)
        self.window2.show_all()
    
    def insert_signature(self, widget, entry):
        """Validates and inserts signature into the stream at the given location"""
        start_index = int(entry.get_text())
        search_val = self.df[self.df['ID']==self.current_signature]
        search_val.reset_index(drop=True, inplace=True)
        id = self.current_signature
        #sign_val = search_val['Original'][0]
        sign_size = search_val['Size'][0]/8
        end_index = start_index + sign_size - 1
        
        search_val_stream = self.stream_df[self.stream_df['SID']==self.current_stream]
        stream_index = search_val_stream.index[0]
        stream_length = self.stream_df['Size'][stream_index]/8
        error_override=0
        
        if(start_index>=stream_length):
            self.message_display(message_text="Start Index cannot be greater than stream length")
            return
        
        retVal, retMessage = self.validate_signature_pattern_for_stream(id, start_index, end_index, stream_index, stream_length)        
        if(retVal):
            retValueMsg = self.message_display(message_text=retMessage, _type=gtk.MESSAGE_ERROR, buttons=(gtk.BUTTONS_OK_CANCEL))
            #Stop if user presses cancel
            if retValueMsg==-6:
                return 1
            else:
                #Truncate signature if greater than stream length
                if(end_index>=stream_length):
                    end_index = int(stream_length-1)
                    error_override=1
        
        elif(retVal==0 and len(retMessage)>0):
            retValueMsg = self.message_display(message_text=retMessage, _type=gtk.MESSAGE_WARNING, buttons=(gtk.BUTTONS_OK_CANCEL))
            if retValueMsg==-6:
                return 1
            
        #Update records
        #Check if value is -1 for intitial condition
        if(self.history_index[stream_index][0]==[-1, -1, -1, -1]):
            self.history_index[stream_index] = [[id, start_index, end_index, error_override]]
        else:
            self.history_index[stream_index].append([id, start_index, end_index, error_override])        
        
        #Create entry only if signature length is valid
        if(error_override==0):
            #Create an entry in the dictionary for size
            if(self.size_history.has_key(sign_size)):
                self.size_history[sign_size] += 1
            else:
                self.size_history[sign_size] = 1
        
        #Update Stream to new value
        """
        stream_data = stream_data[0:start_index] + sign_val + stream_data[end_index+1:]
        self.stream_df['Original'][stream_index] = stream_data
        self.stream_df['Hex'][stream_index] = stream_data.encode("hex")
        """
        
        hist_linear = self.SgnPosition[stream_index].get_label()
        if error_override==0:
            hist_linear +='('+str(id)+':'+str(start_index)+'-'+str(end_index)+') '
        else:
            hist_linear +='<span color="red">('+str(id)+':'+str(start_index)+'-'+str(end_index)+') </span>'
        hist_newline = self.History.get_label()
        hist_newline +=str(self.current_stream)+': '+str(id)+'-->'+str(start_index)+', '+str(end_index)+'\n'
        self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=None, SgnPosition=hist_linear, History=hist_newline, index=stream_index)
        
    def undo_insert(self, widget):
        """Undo insert of stream in stream map"""
        search_val_stream = self.stream_df[self.stream_df['SID']==self.current_stream]
        stream_index = search_val_stream.index[0]
        
        if(len(self.history_index[stream_index])>0 and self.history_index[stream_index]!=[[-1, -1, -1, -1]]):            
            undo_data = self.history_index[stream_index][-1]
            start_index = undo_data[1]
            end_index = undo_data[2]
            sign_size = end_index - start_index + 1
            
            self.history_index[stream_index] = self.history_index[stream_index][:-1]
            
            #Reset value if no signatures are left
            if len(self.history_index[stream_index])==0:
                self.history_index[stream_index]=[[-1, -1, -1, -1]]
                
            #Update Size dictionary
            #Create an entry in the dictionary for size
            if(self.size_history.has_key(sign_size) and self.size_history[sign_size]>0):
                self.size_history[sign_size] -= 1
            
            
            hist_newline = self.History.get_label()
            hist_newline +='Undo of '+str(self.current_stream)+': '+str(undo_data[0])+'-->'+str(undo_data[1])+', '+str(undo_data[2])+'\n'
            
            hist_linear = ''
            #If not default value
            if(self.history_index[stream_index]!=[[-1, -1, -1, -1]]):
                for i in self.history_index[stream_index]:
                    if(i[3]<1):
                        hist_linear +='('+str(i[0])+':'+str(i[1])+'-'+str(i[2])+') '
                    else:
                        hist_linear +='<span color="red">('+str(i[0])+':'+str(i[1])+'-'+str(i[2])+') </span>'
            
            self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=None, SgnPosition=hist_linear, History=hist_newline, index=stream_index)
                        
        else:
            self.message_display("No more data to perform undo")
    
    def update_index(self, widget):
        """Rolls over cursor from stream selection radio button"""
        try:
            stream_index = self.stream_df[self.stream_df['SID']==self.current_stream].index[0]
            if(stream_index+1<self.current_index):
                self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=True, SgnPosition=None, History=None, index=stream_index+1)
            else:
                self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=True, SgnPosition=None, History=None, index=0)
        except:
            pass
        
    def add_new_stream(self, SID, Stream):
        """Adds new stream based on input parameters"""
        #Add new entry in dataframe
        self.stream_df.loc[self.current_index]=[int(SID), len(Stream)*8, Stream.encode("Hex"), Stream]
        
        #Update GUI with new entry
        self.update_Stream_GUI(SID=SID, Size_Stream=len(Stream), Select_Stream=True, SgnPosition=None, History=None, index=self.current_index)
        
        #Update index
        self.current_index += 1
        
        self.stream_df['SID'] = self.stream_df['SID'].astype(int)
        self.stream_df['Size'] = self.stream_df['Size'].astype(int)
        
        #Make a copy of the stream to have an option to undo later
        self.stream_df_copy = self.stream_df.copy()
        
    def create_stream(self, widget):
        """Pops up a dialog box to take in SID and Stream Length. 
            Generates a random stream and updates the table"""
        dialog = gtk.Dialog(title="Generate Random Text for Stream", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(200,150)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("Stream ID")
        Entry = gtk.Entry()
        Entry.set_width_chars(5)
        Entry.set_text(str(self.current_stream+1))
        HBox.pack_start(Label)
        HBox.pack_start(Entry, expand = False, fill = False, padding=15)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("Stream length(bits)")
        Adj = gtk.Adjustment(value=3*8, lower=3*8, upper=130*8, step_incr=1*8)
        Spin_Btn = gtk.SpinButton(adjustment=Adj, climb_rate=0.0, digits=0)
        HBox.pack_start(Label)
        HBox.pack_start(Spin_Btn)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        dialog.vbox.show_all()
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            SID = Entry.get_text()
            
            #Exit input if invalid byte is entered
            if(Spin_Btn.get_value_as_int()%8!=0):
                self.message_display('Size value not a valid byte! Please try again.')
                dialog.destroy()
                return 1
            Stream_Length = Spin_Btn.get_value_as_int()/8
            dialog.destroy()
            Stream = id_generator(size=Stream_Length)
            self.add_new_stream(SID, Stream)
        else:
            dialog.destroy()
    
    def save_binary_stream_output(self, widget, data):
        """Saves Binary Stream output as a CSV File based on current stream dataframe"""
        stream_df_map = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Pattern'])
        
        for ctr in range(self.current_index):
            SID = self.stream_df['SID'][ctr]
            Size_stream = self.stream_df['Size'][ctr]
            stream_data = self.stream_df['Original'][ctr]
            search_val_stream = self.stream_df[self.stream_df['SID']==SID]
            stream_index = search_val_stream.index[0]
            pattern_data = self.SgnPosition[ctr].get_text()
            if(pattern_data!=''):
                pattern_data = pattern_data.replace('<span color="red">', '')
                #pattern_data = pattern_data.replace('<span color="blue">', '')
                pattern_data = pattern_data.replace('</span>', '')
                pattern_data = pattern_data.split(' ')[:-1]
                count_valid_signatures=0
                pattern_val=''
                #pattern_val = str(len(pattern_data))+','
                for i in pattern_data:
                    #Remove brackets
                    i=i.strip('(')
                    i=i.strip(')')
                    i=i.split(':')
                    ID = i[0]
                    S_Index = int(i[1].split('-')[0])
                    E_Index = int(i[1].split('-')[1])
                    
                    #Check if there are any signature overflow cases 
                    #to avoid writing into the binary file
                    Full_Signature = 1
                    for j in self.history_index[stream_index]:
                        if(int(j[0])==int(ID) and int(j[1])==int(S_Index)):
                            Full_Signature = 0 if int(j[3])==1 else 1
                            break
                        
                    #Insert signature into stream
                    search_val = self.df[self.df['ID']==int(ID)]
                    search_val.reset_index(drop=True, inplace=True)
                    sign_val = search_val['Original'][0]
                    
                    stream_data = stream_data[0:S_Index] + sign_val + stream_data[E_Index+1:]
                    stream_data = stream_data[:int(Size_stream)/8]
                    if(Full_Signature):
                        pattern_val+=str(ID)+','+str(S_Index)+','+str(E_Index)+','
                        count_valid_signatures+=1                            
                        
                
                #Remove trailing ,
                pattern_val = pattern_val[:-1]
                pattern_val=str(count_valid_signatures)+","+pattern_val                    
                    
            else:
                pattern_val = r"0"
            
            Hex = stream_data.encode('hex')
            
            stream_df_map.loc[ctr]=[SID, Size_stream, Hex, str(pattern_val)]
        
        stream_df_map['SID'] = stream_df_map['SID'].astype(int)
        stream_df_map['Size'] = stream_df_map['Size'].astype(int)
        stream_df_map['Pattern'] = stream_df_map['Pattern'].astype(str)
        
        
        size_arr = []
        sorted_size = sorted(self.size_history.items(), key=operator.itemgetter(0), reverse=True)
        for i in sorted_size:
            if i[1]>0:
                #Convert to bits
                size_arr.append(i[0]*8)
        #size_arr = sorted(size_arr, reverse=True)
        if(len(size_arr)==0):
            Load_Line = 'L,0,0,0,0,0'
        elif(len(size_arr)==1):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,0,0'
        elif(len(size_arr)==2):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,0,'+str(size_arr[1])
        elif(len(size_arr)==3):
            Load_Line = 'L,'+str(size_arr[0])+',0,0,'+str(size_arr[1])+','+str(size_arr[2])
        elif(len(size_arr)==4):
            Load_Line = 'L,'+str(size_arr[0])+',0,'+str(size_arr[1])+','+str(size_arr[2])+','+str(size_arr[3])
        else:
            Load_Line = 'L,'+str(size_arr[0])+','+str(size_arr[1])+','+str(size_arr[2])+','+str(size_arr[3])+','+str(size_arr[4])
        
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=stream_df_map, header=True)
        
        for line in fileinput.input(file_location, inplace=True):
            if 'SID' in line:
                print Load_Line
            else:
                line = line.replace('"', '')
                line = line.strip('\n')
                print line
    def save_stats(self, widget, data):
        """Saves Stats file as a CSV File based on a File save GUI"""
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=self.ver_df, header=True)
        if(len(file_location)>0):
            stats_data = ''
            for i in self.ver_stats:
                stats_data=stats_data+str(i[0])+','
            #Remove last comma, replace with \n instead
            stats_data=stats_data[:-1]
            stats_data=stats_data+'\n'
            for i in self.ver_stats:
                stats_data=stats_data+str(i[1])+','
            stats_data=stats_data[:-1]
            stats_data=stats_data+'\n\n'
            
            #Read old file, push verification content a line below, after appending summary
            with open(file_location, 'r+') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(stats_data + content)
                
    def save_stream_map(self, widget, data):
        """Saves Stream map as a CSV File based on a File save GUI"""
        stream_df_map = pd.DataFrame(columns = ['SID', 'Stream_Size', 'ID', 'Start_index', 'End_Index', 'Full_Signature'])
        idx=0
        for ctr in range(self.current_index):
            SID = self.stream_df['SID'][ctr]
            Size_stream = self.stream_df['Size'][ctr]
            pattern_data = self.SgnPosition[ctr].get_text()
            search_val_stream = self.stream_df[self.stream_df['SID']==SID]
            stream_index = search_val_stream.index[0]
            if(pattern_data!=''):
                pattern_data = pattern_data.replace('<span color="red">', '')
                #pattern_data = pattern_data.replace('<span color="blue">', '')
                pattern_data = pattern_data.replace('</span>', '')
                pattern_data = pattern_data.split(' ')[:-1]
                for i in pattern_data:
                    #Remove brackets
                    i=i.strip('(')
                    i=i.strip(')')
                    i=i.split(':')
                    ID = i[0]
                    S_Index = i[1].split('-')[0]
                    E_Index = i[1].split('-')[1]
                    Full_Signature = 1
                    for j in self.history_index[stream_index]:
                        if(int(j[0])==int(ID) and int(j[1])==int(S_Index)):
                            Full_Signature = 0 if int(j[3])==1 else 1
                            break
                    stream_df_map.loc[idx]=[SID, Size_stream, ID, S_Index, E_Index, Full_Signature]
                    idx=idx+1     
            else:
                stream_df_map.loc[idx]=[SID, Size_stream, 0, 0, 0, 0]
                idx=idx+1
                
        stream_df_map['SID'] = stream_df_map['SID'].astype(int)
        stream_df_map['Stream_Size'] = stream_df_map['Stream_Size'].astype(int)
        stream_df_map['ID'] = stream_df_map['ID'].astype(int)
        stream_df_map['Start_index'] = stream_df_map['Start_index'].astype(int)
        stream_df_map['End_Index'] = stream_df_map['End_Index'].astype(int)
        stream_df_map['Full_Signature'] = stream_df_map['Full_Signature'].astype(int)
        
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=stream_df_map, header=False)
            
    def create_insertion_dialog(self, widget, data, undoButton=True):
        """Function to create stream construction dialog box"""
        if(hasattr(self,'current_signature')!=1):
            self.message_display("Please open the Signature window before proceeding further!", _type=gtk.MESSAGE_ERROR)
            return           
        self.insertionDialog = gtk.Dialog(title="Stream Construction", parent=None, 
                                flags=gtk.DIALOG_NO_SEPARATOR, 
                                buttons=None)
        
        self.insertionDialog.set_default_size(400,300)
        VBoxL = gtk.VBox()
        HBoxL = gtk.HBox()
        label = gtk.Label("Current signature: ")
        self.current_signature_label = gtk.Label(self.current_signature)        
        label2 = gtk.Label("Current stream: ")
        self.current_stream_label = gtk.Label(self.current_stream)
        
        HBoxL.pack_start(label)
        HBoxL.pack_start(self.current_signature_label)
        HBoxL.pack_start(label2)
        HBoxL.pack_start(self.current_stream_label)
        VBoxL.pack_start(HBoxL)
        self.insertionDialog.vbox.pack_start(VBoxL)
        
        
        HBoxI = gtk.HBox()
        label = gtk.Label("Signature Start (Byte) index")
        entry = gtk.Entry()
        entry.set_text("0")
        entry.set_alignment(0)
        entry.set_width_chars(3)
        tooltips = gtk.Tooltips()
        tooltips.set_tip(entry, "Enter a valid byte index")
        HBoxI.pack_start(label)
        HBoxI.pack_start(entry, expand = False, fill = False, padding=15)
        self.insertionDialog.vbox.pack_start(HBoxI)
        
        button = gtk.Button("Insert Signature")
        self.insertionDialog.vbox.pack_start(button)
        button.connect("clicked", self.insert_signature, entry)
        
        self.undo_button = gtk.Button("Undo Insert")
        self.insertionDialog.vbox.pack_start(self.undo_button)
        self.undo_button.connect("clicked", self.undo_insert)
        self.undo_button.set_sensitive(undoButton)
        
        button3 = gtk.Button("Done with current stream")
        self.insertionDialog.vbox.pack_start(button3)
        button3.connect("clicked", self.update_index)
        
        button4 = gtk.Button("Add a stream")
        self.insertionDialog.vbox.pack_start(button4)
        button4.connect("clicked", self.create_stream)
        
        button5 = gtk.Button("Save Stream Map")
        self.insertionDialog.vbox.pack_start(button5)
        button5.connect("clicked", self.save_stream_map, "")
        
        button6 = gtk.Button("Create Stream Binary output file for simulation")
        self.insertionDialog.vbox.pack_start(button6)
        button6.connect("clicked", self.save_binary_stream_output, "")
        
        self.insertionDialog.vbox.show_all()
        self.insertionDialog.show()
        #response = dialog.run()
        
        #if response == gtk.RESPONSE_OK:
            #dialog.destroy()
    
    def close_insertion_dialog(self):
        """Closes stream construction dialog"""
        if(hasattr(self,'insertionDialog')):
            self.insertionDialog.destroy()
            
    def change_signature_select_line_state(self, state=True):
        """Changes signature select lines to state"""
        if(hasattr(self,'df')):
            for i in range(0, len(self.df)):
                if(self.button[i]!=None):
                    self.button[i].set_sensitive(state)
    
    def construct_stream(self, widget, data):
        """Callback function to initiate stream construction process"""
        
        #Make signature select line active
        self.change_signature_select_line_state()
        
        #Create a new window to load the streams
        self.create_stream_window()
        
        #Create global variables for tracking history
        self.current_stream = 0
        self.history_index = [[[-1, -1, -1, -1]]] * MAX_COUNT_STREAMS
        self.size_history = {}
        self.current_index = 0
        self.stream_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Original'])
    
    def verify_stream(self, widget, data):
        """Callback function to inititate verification process"""
        dummy_df = pd.DataFrame(columns = ['SID', 'Time', 'Query_Op', 'Start_Index', 'End_Index', 'Verification_Result', 'ID'])
        dummy_df.loc[0]=['', '', '', '', '', '', '']
        dummy_stats = (('Signature Count', ''),\
             ('Full Count', ''),('True Full Count', ''),('False Full Count', ''),\
             ('Prefix Count', ''),('True Prefix Count', ''),('False Prefix Count', ''))
    
        self.create_verification_window(dummy_df, dummy_stats)
    
    def validate_signature_pattern_for_stream(self, id, start_index, end_index, stream_index, stream_size):
        """Validates if signature pattern can be used for the given stream"""
        ErrorMessage = ''
        ErrorFlag = 0
        for i in self.history_index[stream_index]:
            #Check if start index is less than any old end index
            if start_index == i[1]:
                ErrorMessage+="Warning: SID #"+str(id)+" will overlap from starting index of SID #"+str(i[0]) +"\n"
            elif start_index != i[1] and start_index <= i[2]:
                ErrorFlag = 1
                ErrorMessage+="SID #"+str(id)+" will overlap end index of SID #"+str(i[0]) +"\n"
                
        if(end_index>=stream_size):
            ErrorFlag=1
            ErrorMessage+="SID #"+str(id)+" exceeds size of Stream\n"            
        
        return ErrorFlag, ErrorMessage
                
    
    
    def message_display(self, message_text, _type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK):
        """Generates a pop up message based on input parameters"""
        message = gtk.MessageDialog(type=_type, buttons=buttons)
        message.set_markup(message_text)
        message.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        retVal = message.run()
        message.destroy()
        return retVal
    
    def destroy(self, widget, data=None):
        """Destroys the GUI instance"""
        gtk.main_quit()
    
    def get_main_menu(self, window, menu_items):
        """Returns a menu object that can be inserted into a window"""
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
        item_factory.create_items(menu_items)

        # Attach the new accelerator group to the window.
        window.add_accel_group(accel_group)

        # need to keep a reference to item_factory to prevent its destruction
        self.item_factory = item_factory
        # Finally, return the actual menu bar created by the item factory.
        return item_factory.get_widget("<main>")
   
    def create_signature_window(self, widget, df, si, file_location):
        """
            Creates Signature Window based on input df, si and file location
        """            
        #Retrieve Dataframe and Size dictionary
        self.df = df
        self.si = si
        self.file_location = file_location
        
        self.current_signature = df['ID'][0]
        
        #Create new GTK Window instance
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", lambda w: self.window.destroy())
        self.window.connect("delete_event", self.delete_signature_window)
        self.window.set_title(TOOL_NAME+" | File: "+str(self.file_location))
        self.window.set_default_size(640, 480)
        
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        main_vbox.show()
        
        self.menu_items = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Load Hex Signatures with IDs & Size(.csv)",     "<control>O", self.read_from_csv, 0, None ),
            ( "/File/_Load Text Signatures(.txt)",    "<control>T", self.read_from_text, 0, None ),
            ( "/File/_Save As..",    "<control>S", self.save_signature, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_signature_window, 0, None ),
            ( "/_Display",      None,         None, 0, "<Branch>" ),
            ( "/Display/_Display Text View of Signatures",  "<control>D", self.display_original_text, 0, None ),
            ( "/_Generate",         None,         None, 0, "<Branch>" ),
            ( "/Generate/Generate Random Text Signatures",   None, self.generate_pattern, 0, None ),
            ( "/_Construct",         None,         None, 0, "<Branch>" ),
            ("/_Construct/Construct Stream",   None, self.construct_stream, 0, None ),
            #( "/_View",         None,         None, 0, "<Branch>" ),
            #("/_View/Stream View",   None, self.stream_view, 0, None ),
            )
        
        menubar = self.get_main_menu(self.window, self.menu_items)

        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        
        #Create partition for Data display
        dataBox = gtk.VBox(spacing=30)
        frame = gtk.Frame("Pattern Values")
        
        #Create scrollable display.
        #Scrollability policy based on number of elements.
        scrolledWin = gtk.ScrolledWindow()
        if(len(df)<15):
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        else:
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        #Create Table to display values
        table = gtk.Table(rows=len(df)+1, columns=4, homogeneous=False) 
        table.set_col_spacings(10)
        title_print_bar = ['ID', 'Size(bytes)', 'Select', 'Hex']
        title_bar = ['ID', 'Size', 'Select', 'Hex']
        for i in range(4):
            label = gtk.Label(title_print_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 12"))
            label.set_alignment(0, 0)
            table.attach(label, i, i+1, 0, 1, xpadding=5)
        
        #Loop through table to display values
        ctr = 0
        self.button = [None]*len(df)
        for i in range(4):
            ctr = 0
            for j in range(1, len(df)+1):
                if(i!=2):
                    if(i==1):
                        #Convert size back to bytes for display
                        if(str(df[title_bar[i]][j-1])!=''):
                            label = gtk.Label(str(df[title_bar[i]][j-1]/8))
                        else:
                            label = gtk.Label('')
                        label.set_alignment(0.5, 0.5)
                    else:
                        label = gtk.Label(str(df[title_bar[i]][j-1]))
                        label.set_alignment(0, 0)
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_selectable(True)
                    table.attach(label, i, i+1, j, j+1, xpadding=5)
                
                elif(i==2):
                    
                    #Create and associate a button for each ID
                    ID = str(df['ID'][j-1])
                    #Don't Create button in case of dummy entry
                    if(ID==''):
                        continue
                    
                    if(j==1):
                        self.button[ctr] = gtk.RadioButton(None)
                        self.button[ctr].set_active(True)
                    else:
                        self.button[ctr] = gtk.RadioButton(self.button[0])
                    self.button[ctr].connect("clicked", self.active_signature, ID)
                    self.button[ctr].set_sensitive(False)
                    self.button[ctr].set_alignment(0.5, 0.5)
                    table.attach(self.button[ctr], i, i+1, j, j+1, xpadding=5)
                    ctr = ctr + 1
                

        scrolledWin.add_with_viewport(table)
        table.set_col_spacings(15)
        table.show()
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        if(len(df)<15):
            dataBox.pack_start(frame,  expand = False, fill = False, padding = 15)
        else:
            dataBox.pack_start(frame,  expand = True, fill = True, padding = 15)            
        
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
                if(i==0):
                    #Converrt bits to bytes
                    label = gtk.Label(str(sorted_size[j-1][i]/8))
                else:
                    label = gtk.Label(str(sorted_size[j-1][i]))
                table2.attach(label, i, i+1, j, j+1)
        frame.add(table2)            
        
        sizeBox.pack_start(frame,  expand = False, fill = True, padding = 20)
        
        #Arrange all the elements legibly
        self.window.add(main_vbox)
        main_vbox.pack_start(dataBox, True, True)
        main_vbox.pack_start(sizeBox, False, False)
        
        self.window.show_all()
        
        #Enable select line if stream window already present
        if(hasattr(self, 'window2')):
            self.change_signature_select_line_state(True)
        
        #Verification utility
        retVal, textVal = verify_size(self.si)
        if (retVal):
            self.message_display("Signatures have the following error(s):\n"+textVal)
            
    def __init__(self):
        """
            Initializes pyGTK and creates Welcome Screen Window
        """
        self.windowInit = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.windowInit.connect("destroy", lambda w: gtk.main_quit())
        self.windowInit.connect("delete_event", self.delete_load_window)
        self.windowInit.set_title("Signatures/Stream Utility")
        self.windowInit.set_default_size(400, 300)
        
        main_vbox = gtk.VBox(False, 5)        
        
        button = gtk.Button(TOOL_NAME)
        main_vbox.pack_start(button, expand = True, fill = True)
        dummy_df = pd.DataFrame(columns = ['ID', 'Size', 'Hex'])
        dummy_df.loc[0]=['', '', '']
        button.connect("clicked", self.create_signature_window, dummy_df, {}, '')
        
        button2 = gtk.Button("Stream Construction")
        main_vbox.pack_start(button2, expand = True, fill = True)
        button2.connect("clicked", self.construct_stream, "")
        
        button3 = gtk.Button("Stream Verification")
        main_vbox.pack_start(button3, expand = True, fill = True)
        button3.connect("clicked", self.verify_stream, "")
        
        main_vbox.show_all()
        self.windowInit.add(main_vbox)
        self.windowInit.show()


def verify_size(size_index):
    """Verifies if constraints are met for size of signatures.
        Returns True, None if constraints are met
        Returns False, ErrorMessage if contraints aren't met
        Inputs:
        size_index: dictionary of sizes and their counts
    """
    
    sorted_size = sorted(size_index.items(), key=operator.itemgetter(0))
    flag=0;
    ErrorMessage = ""
    
    if(len(sorted_size)>MAX_N_LENGTHS):
        flag=1
        ErrorMessage = "Count of lengths greater than: "+str(MAX_N_LENGTHS)+"\n"
    elif(len(sorted_size)<MIN_N_LENGTHS and len(sorted_size)!=0):
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
        size_arr: Array of sizes to generate
        Optional parameters should be changed preferably via constants
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
def verifyStats(ver_df, stream_bin_file_location):
    """Verifies if signatures are present in the specified stream based on the binary file.
        Generates processed stats dataframe and stats array of tuples.
        Returns dataframe consisting of SID, Query OP, Start/End Index, Result and ID
        Also return array of tuples of verification summary
        Inputs:
        ver_df: Dataframe of Verification data to be correlated with the binary file
        stream_bin_file_location: Location of the file
    """
    ver_df['Verification_Result'] = ''
    ver_df['ID'] = ''
    full_count = 0
    full_correct_count = 0
    prefix_count = 0
    prefix_correct_count = 0
    sign_count = 0
    stream_df_map = pd.read_csv(stream_bin_file_location, skiprows=[0], header=None)
    for i in range(len(ver_df)):
        SID = int(ver_df['SID'][i])
        Query_Op = ver_df['Query_Op'][i]
        Start_Index = int(ver_df['Start_Index'][i])
        End_Index = int(ver_df['End_Index'][i])
        Verification_Result = ''
        Verification_ID = ''
        #Skip for Q_START
        if('START' in Query_Op):
            continue
        elif('FULL' in Query_Op):
            full_count+=1
        elif('PREFIX' in Query_Op):
            prefix_count+=1
        
        #Search for data in streams map based on SID
        search_val = stream_df_map[stream_df_map[0]==SID]
        search_val.reset_index(drop=True, inplace=True)
        if(len(search_val)>0):
            sign_count = search_val[3][0]            
            pattern_val = ''
            for p in range(4, 4+(sign_count*3)):
                pattern_val+=str(search_val[p][0])+","
            pattern_val = pattern_val[:-1]
            pattern_val = pattern_val.split(',')
            ctr=0
            for _ in range(sign_count):
                ID = pattern_val[ctr]
                S_Index = int(pattern_val[ctr+1])
                E_Index = int(pattern_val[ctr+2])
                if(('FULL' in Query_Op) and Start_Index==S_Index and End_Index==E_Index):
                    #Verification_Result = Query_Op[:3]+'_TRUE'
                    Verification_Result = 'True Full'
                    Verification_ID = str(ID)
                    full_correct_count+=1
                    break
                elif(('PREFIX' in Query_Op) and Start_Index==S_Index):
                    #Verification_Result = Query_Op[:3]+'_TRUE'
                    Verification_Result = 'True Prefix'
                    Verification_ID = str(ID)
                    prefix_correct_count+=1
                    break
                ctr = ctr + 3
                
            #None of the entries match
            if(len(Verification_Result)==0):
                if('FULL' in Query_Op):
                    Verification_Result = 'False Full'
                else:
                    Verification_Result = 'False Prefix'
            
            ver_df['Verification_Result'][i] = Verification_Result
            ver_df['ID'][i] = Verification_ID
            
        else:
            #SID not found, can't do anything
            ver_df['Verification_Result'][i] = 'Unknown Stream ID'
    
    stats = (('Signature Count', sign_count),\
             ('Full Count', full_count),('True Full Count', full_correct_count),('False Full Count', full_count - full_correct_count),\
             ('Prefix Count', prefix_count),('True Prefix Count', prefix_correct_count),('False Prefix Count', prefix_count - prefix_correct_count))
    
    return ver_df, stats
            
            
def interpretStats(file_location="stats.csv", processed=0):
    """Reads the Stats file and loads it as 'SID', 'Time', 'Query_Op', 'Start_Index' and 'End_Index'. 
        Returns None, 1 on failure and a dataframe, 0 on success
        Inputs:
        file_location: Location of the file
        processed: Is this a processed file/unprocessed file
    """
    try:
        if not processed:
            csv_data = pd.read_csv(file_location, skiprows=[0, 1], header=None, names=['SID', 'Time', 'Query_Op', 'Start_Index', 'End_Index'])
        else:
            #If processed, skip the summary section
            csv_data = pd.read_csv(file_location, skiprows=[0, 1, 2, 3], header=None, names=['SID', 'Time', 'Query_Op', 'Start_Index', 'End_Index', 'Verification_Result', 'ID'])
            csv_data['ID'].fillna(value=-1, inplace=True)
            csv_data['ID'] = csv_data['ID'].astype('int')
            csv_data['ID'].replace(to_replace=-1, value='', inplace=True)
            csv_data.fillna(value='', inplace=True)
    except Exception,e:
        print "Failed to read file with exception" + str(e)
        return None, 1
    
    return csv_data, 0

def interpretStatsSummary(file_location):
    """Reads the processed Stats file and determines the stats in the form of an array of tuples. 
        Returns None, 1 on failure and a stats_array, 0 on success
        Inputs:
        file_location: Location of the file
    """
    try:
        csv_data = pd.read_csv(file_location, nrows=1)
        column_names = list(csv_data.columns.values)
        column_values = [0] * 7
        for row in csv_data.iterrows():
            index, column_values = row
        column_values=column_values.tolist()
        stats_array=[]
        for i in range(7):
            stats_array.append((column_names[i], column_values[i]))
        
    except Exception,e:
        print "Failed to read file with exception" + str(e)
        return None, 1
    
    return stats_array, 0

def interpretPattern(read_csv=False, file_location="patterns.txt"):
    """Reads the pattern file and generates ID, Hex and Size paramters. 
        Returns None, None on failure and a dataframe, dictionary on success
        Inputs:
        read_csv: Is the file a CSV?
        file_location: Name of the file
    """
    if(read_csv):
        try:
            csv_data = pd.read_csv(file_location, header=None, names=['ID', 'Size', 'Hex'])
        except Exception,e:
            print "Failed to read file with exception" + str(e)
            return None, None, 1
        
    proc_data = pd.DataFrame(-1, index=np.arange(0, 1000), columns = ['ID', 'Size', 'Hex', 'Original'])
    #proc_data['Hex']=''
    #proc_data['Original']=''
    size_index = {}
    if not(read_csv):
        try:
            fo = open(file_location, "r")
            i=0
            for line in fo:
                #Strip the newline character
                line = line.strip('\n')
                #Length into 8 for size in bits
                size_line = len(line)*8
                
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
        for i in range(len(csv_data)):
            proc_data['ID'][i] = csv_data['ID'][i]
            proc_data['Size'][i] = csv_data['Size'][i]
            proc_data['Hex'][i] = csv_data['Hex'][i]
            proc_data['Original'][i] = csv_data['Hex'][i].decode("Hex")
            size_line = csv_data['Size'][i]
            if(size_index.has_key(size_line)):
                    size_index[size_line] += 1
            else:
                size_index[size_line] = 1
    
    proc_data = proc_data[(proc_data.T != -1).any()]
    return proc_data, size_index, 0

if __name__ == "__main__":
    PyApp()
    gtk.main()