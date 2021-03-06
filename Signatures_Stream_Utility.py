"""
    * Usage: python Signatures_Stream_Utility.py            
"""
import gtk, pango
import string, random, operator
import pandas as pd
import numpy as np
import warnings, os, time
import matplotlib.pyplot as plt


pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore",".*GUI is implemented.*")

# Constant to change utility name
TOOL_NAME = "Signatures Dictionary Construction"

# Constants to determine number of elements
MIN_N_LENGTHS = 1
MAX_N_LENGTHS = 5

# Constants to customize allowable signature length
MIN_SIZE_SIGNATURE = 4*8
MAX_SIZE_SIGNATURE = 130*8
DISTANCE_CONSECUTIVE = 2*8

MAX_COUNT_STREAMS = 50
MIN_SIGN_PER_STREAM = 0
MAX_SIGN_PER_STREAM = 10
MIN_PADDING_BYTES = 0
MAX_PADDING_BYTES = 10
MIN_START_OFFSET = 0
MAX_START_OFFSET = 10

ALLOWABLE_CHARS = string.ascii_letters + string.digits + string.punctuation


class PyApp:
    
    def read_from_csv(self, widget, data):
        """
        Function to read file location and open signature dictionary file type. 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening a csv file
            * Update UI with selected dictionary
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Return value
        :rtype: int
        
        """
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
        """
        Function to read file location and open signature dictionary file type. 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening a txt file
            * Update UI with selected dictionary
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Return value
        :rtype: int
        
        """
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
        """
        Function to read csv stats file location and display it on the UI 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening a csv stats file
            * Dialog box to check if STREAMS_IN.csv file from current location should be checked
            * If no, dialog box to specify Stream binary file
            * Update UI with selected statistics
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Return value
        :rtype: int
        
        """
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
        """
        Function to read processed csv stats file location and display it on the UI 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening a csv stats file
            * Update UI with selected statistics
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Return value
        :rtype: int
        
        """
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
        """
        Function to open filter stream output file and display it on the UI 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening filter stream output file
            * Update UI with selected file
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Return value
        :rtype: int
        
        .. note:: Function no longer used. Legacy code.

        """
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
        
    def load_stream_map(self, widget, data, file_location = None):
        """
        Function to open stream map and display it on the UI 
        
        returns return value

        **UI Flow**:
            * Display a dialog for opening stream map
            * Update UI with selected file
            * Open Stream insertion dialog
            
        :param widget: Calling widget
        :param data: Unused
        :param file_location: File location of stream map
        :type widget: gtk.Widget
        :type data: string
        :type file_location: string
        :returns: Return value
        :rtype: int
        
        """
        # Clear old values from GUI
        for i in range(self.current_index):
            self.update_Stream_GUI(SID='', Size_Stream='', Select_Stream=False, SgnPosition='', History='', index=i)
        self.stream_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Original'])
        self.current_index = 0
        self.history_index = [[[-1, -1, -1, -1]]] * MAX_COUNT_STREAMS
        self.size_history = {}
        self.current_index = 0
        self.close_insertion_dialog()
        
        # Allow access to undo button for stream map
        if(hasattr(self,'undo_button')):
            self.undo_button.set_sensitive(True)
        if(file_location==None):
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
                    
                    # Fetch index
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
                            # Add red color for incomplete signatures
                            if Full_Signature:
                                SgnPosition+='('+str(ID)+':'+str(S_Index)+'-'+str(E_Index)+') '
                            else:
                                SgnPosition +='<span color="red">('+str(ID)+':'+str(S_Index)+'-'+str(E_Index)+') </span>'
                            Full_Signature = 0 if Full_Signature==1 else 1
                            if(self.history_index[self.current_index][0]==[-1, -1, -1, -1]):
                                    self.history_index[self.current_index] = [[ID, S_Index, E_Index, Full_Signature]]
                            else:
                                self.history_index[self.current_index].append([ID, S_Index, E_Index, Full_Signature])
                                
                            # Create an entry in the dictionary for size
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
        """
        Function to read file location based with a message and specified file type. 
        
        returns File location

        **UI Flow**:
            * Display a dialog for opening a file
            
        :param widget: Calling widget
        :param data: Unused
        :param message: Title message for opening file
        :param file_type: File type e.g. csv, txt.
        :type widget: gtk.Widget
        :type data: string
        :type message: string
        :type file_type: string
        :returns: File location
        :rtype: string

        """
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
        """
        Function to display original Text Signatures 
        
        returns None

        **UI Flow**:
            * Display a dialog box with hex to string converted signatures
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        """
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
    
    def save_signature(self, widget, data, save_default_df=True, df=None, header=False, dont_save_for_config=False):
        """
        Function to save the dataframe in a location specified by the user 
        Initializes GUI dialog boxes to process inputs.
        
        returns saved_file_location

        **UI Flow**:
            * Pick saved file location
            * Print message with saved file location and success message

        :param save_default_df: Should the default dataframe be saved?            
        :param df: Dataframe to be saved
        :param header: Should header be saved in the file?
        :param dont_save_for_config: Special case for config, where file isn't saved.
        :type save_default_df: Bool
        :type df: pandas.Dataframe
        :type header: Bool
        :type dont_save_for_config: Bool
        :returns: saved_file_location
        :rtype: String

        .. note:: Doesn't store Dataframe index by default

        """
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
            
            #Special case for file config where only file name is needed
            if(dont_save_for_config):
                dialog.destroy()
                open(save_filename, "w+")
                return save_filename
            
            if save_filename.endswith('.csv'):
                try:
                    save_df.to_csv(save_filename, index=False, header=header)
                    self.message_display(message_text="Successfully created "+save_filename, _type=gtk.MESSAGE_INFO)
                    dialog.destroy()
                    if save_default_df:
                        retValue = self.message_display("Would you like to save statistics for the signature(s)?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
                        if retValue==-8:
                            self.save_signature_stats(save_filename)
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
    
    def save_signature_stats(self, file_location):
        """
        Function to save signature stats in a location specified by the user 
        Initializes GUI dialog boxes to process inputs.
        
        returns None

        **UI Flow**:
            * Pick saved file location
            * Print message with saved file location and success message

        :param file_location: Signature save file location
        :type file_location: string
        :returns: None
        :rtype: None

        """
        dialog = gtk.FileChooserDialog("Save File",
                           None,
                           gtk.FILE_CHOOSER_ACTION_SAVE,
                           (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)   
        dialog.set_current_folder(os.getcwd())
        file_location = "".join((file_location.split('.'))[:-1]) + '_stats.csv'
        file_location = file_location.split('\\')[-1]
        dialog.set_current_name(file_location)
        
        #Create a filter to show only csv files
        _filter = gtk.FileFilter()
        _filter.set_name("CSV Only")
        _filter.add_pattern("*.csv")
        dialog.add_filter(_filter)  
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            file_location = dialog.get_filename()
            if file_location.endswith('.csv'):
                try:
                    file_str = 'Size,Count\n'
                    for signature_length, count in self.si.iteritems():
                        file_str+=str(signature_length)+','+str(count)+'\n'
                    with open(file_location, 'wb') as f:
                        f.write(file_str)
                    self.message_display(message_text="Successfully created "+file_location, _type=gtk.MESSAGE_INFO)
                    dialog.destroy()
                #Exception Handling in case file save fails
                except:
                    dialog.destroy()
                    self.message_display(message_text="Failed to create file. Please debug!")
                    
            else:
                self.message_display(message_text="File extension must be '.csv'. Please try again!")
                dialog.destroy()
                self.save_signature_stats(file_location)
        else:
            dialog.destroy()

    def create_random_subset_using_range(self, df, n_signs, rand_seed, min_sign_length, max_sign_length):
        """
        Function to creates a random subset of signatures based on inputs specified through the dialog
        
        returns None
        
        :param df: Dataframe to be saved
        :param n_signs: No. of signatures
        :param rand_seed: Random seed
        :param min_sign_length: Minimum signature length
        :param max_sign_length: Maximum signature length
        :type df: pandas.Dataframe
        :type n_signs: int
        :type rand_seed: int
        :type min_sign_length: int
        :type max_sign_length: int
        
        :returns: None
        :rtype: None

        .. seealso::  generate_random_subset_using_range_dialog
        
        """
        random.seed(rand_seed)
        subset_df = df.loc[df['Size'] >= min_sign_length*8]
        subset_df = subset_df.loc[subset_df['Size'] <= max_sign_length*8]
        subset_df.reset_index(drop=True, inplace=True)
        n_available_signs = len(subset_df)
        
        #Generate a subset from the original dataframe of random values
        if n_signs > n_available_signs:
            retVal = self.message_display('Number of available signatures('+str(n_available_signs)+\
                                          ') is less than desired number of signatures('+str(n_signs)+\
                                          '). All signatures will be selected. Would you like to proceed?\n',\
                                           _type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL)
            if retVal == gtk.RESPONSE_CANCEL:
                return 1
            random_subset = subset_df
        else:
            random_subset = pd.DataFrame(columns = ['ID', 'Size', 'Hex'])
            hist_idx = []
            for i in range(n_signs):
                rand_idx = random.randint(0, n_available_signs-1)
                while(rand_idx in hist_idx):
                    rand_idx = random.randint(0, n_available_signs-1)
                random_subset.loc[i] = [subset_df['ID'][rand_idx], subset_df['Size'][rand_idx], subset_df['Hex'][rand_idx]]
                hist_idx.append(rand_idx)
            random_subset['ID'] = random_subset['ID'].astype(int)
            random_subset['Size'] = random_subset['Size'].astype(int)
        
        widget = None
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=random_subset, header=False)
        if(file_location!=None and len(file_location)>0):
            self.window.destroy()
            df, si, retVal = interpretPattern(read_csv=True, file_location=file_location)
            if(~retVal):
                self.create_signature_window(widget, df, si, file_location)
                retValue = self.message_display("Would you like to save statistics for the signature(s)?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
                if retValue==-8:
                    self.save_signature_stats(file_location)
            else:
                self.message_display("Failed to read file. Please verify the file contents.")

    def generate_random_subset_using_range_dialog(self, widget, data):
        """
        Function to take input for generating a random subset of existing Signatures. 
        Initializes GUI dialog boxes to process inputs.
        
        returns None

        **UI Flow**:
            * Open signatures dictionary file
            * Display dialog to get inputs for random subset creation
            
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. seealso::  create_random_subset_using_range

        """
        file_location = self.read_from_file(widget, data, message="Open Signature CSV", file_type="csv")
        #file_location = 'C:\Users\sanke\workspace\PythonDev\snortDB_50.csv'
        try:
            if(file_location!=None and len(file_location)>0):
                dialog = gtk.Dialog(title="Generate Random subset using Range", parent=None, 
                                        flags=gtk.DIALOG_NO_SEPARATOR,
                                        buttons=("Generate", gtk.RESPONSE_OK))
                dialog.set_default_size(265, 250)
                df, si, retVal = interpretPattern(read_csv=True, file_location=file_location)
                HBoxI = gtk.HBox()
                label = gtk.Label("Number of Signatures:")
                label.set_alignment(0, 0)
                entry1 = gtk.Entry()
                entry1.set_text(str(len(df)))
                entry1.set_alignment(1)
                entry1.set_width_chars(10)
                HBoxI.pack_start(label, padding = 15)
                HBoxI.pack_start(entry1, expand = False, fill = False, padding=15)
                dialog.vbox.pack_start(HBoxI, padding = 10)
                
                HBoxI = gtk.HBox()
                label = gtk.Label("Random Seed:")
                label.set_alignment(0, 0)
                entry2 = gtk.Entry()
                entry2.set_text(str(int(time.time())))
                entry2.set_alignment(1)
                entry2.set_width_chars(10)
                HBoxI.pack_start(label, padding = 15)
                HBoxI.pack_start(entry2, expand = False, fill = False, padding=15)
                dialog.vbox.pack_start(HBoxI, padding = 10)
                
                
                sig_size_frame = self.generate_min_max_frame_for_random_stream_map(frame_name="Allowable values for Signature lengths (bytes)",\
                                                                                    min_val=int(min(df['Size'])/8), \
                                                                                    max_val=int(max(df['Size'])/8))
                dialog.vbox.pack_start(sig_size_frame, padding = 10)
                
                    
                if(hasattr(self,'random_stream_subset_config')==1):
                    entry1.set_text(str(self.random_stream_subset_config[0]))
                    entry2.set_text(str(self.random_stream_subset_config[1]))
                    sig_size_frame.get_children()[0].get_children()[0].get_children()[1].set_value(self.random_stream_subset_config[2])
                    sig_size_frame.get_children()[0].get_children()[1].get_children()[1].set_value(self.random_stream_subset_config[3])
                
                # dialog.set_resizable(False)
                dialog.vbox.show_all()
                dialog.show()
                response = dialog.run()
                
                if response == gtk.RESPONSE_OK:
                    try:
                        n_signs = int(entry1.get_text())
                        rand_seed = int(entry2.get_text())
                        #===============================================================
                        #Frame->VBox->HBox1, HBox2; HBox1->Label, ScaleMin; HBox2->Label, ScaleMax 
                        #===============================================================
                        min_sign_length = int(sig_size_frame.get_children()[0].get_children()[0].get_children()[1].get_value())
                        max_sign_length = int(sig_size_frame.get_children()[0].get_children()[1].get_children()[1].get_value())
                        self.random_stream_subset_config = [n_signs, rand_seed, min_sign_length, max_sign_length]
                        #Verify if number of streams is valid
                        if(n_signs==0 or n_signs>len(df)):
                            self.message_display("Please enter a valid number of signatures!")
                            dialog.destroy()
                            return 1
                        dialog.destroy()
                        self.create_random_subset_using_range(df, n_signs, rand_seed, min_sign_length, max_sign_length)
                        
                    except Exception, e:
                        print e
                        self.message_display("Non-integer value passed as parameter. Please re-check the input")
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1

    def generate(self, widget, Spin_Btn, Btn, Spin_Btn_Count ,entry):
        """
        Function to creates a random set of signatures based on inputs specified through the dialog
        
        returns None
        :param widget: Calling widget
        :param Spin_Btn: Dataframe to be saved
        :param Btn: No. of signatures
        :param Spin_Btn_Count: Random seed
        :param entry: Minimum signature length
        :type widget: pandas.Dataframe
        :type Spin_Btn: gtk.SpinButton
        :type Btn: gtk.Button
        :type Spin_Btn_Count: gtk.SpinButton
        :type entry: gtk.Entry
        
        :returns: None
        :rtype: None

        .. seealso::  generate_pattern
        
        """
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
    
    def create_random_subset(self, widget, dialog, total_signatures, df, si):
        """
        Function to creates a random subset of signatures based on inputs specified through the graph dialog
        
        returns None
        
        :param dialog: Calling dialog
        :param total_signatures: Total no. of signatures
        :param df: Dataframe to be saved
        :param si: Size dictionary
        :type dialog: gtk.Dialog
        :type total_signatures: int
        :type df: pandas.Dataframe
        :type si: dictionary
        
        :returns: None
        :rtype: None

        .. seealso::  generate_random_subset
        
        """
        warning_message = ''
        
        #Generate array for various sizes
        signature_length = []
        
        #Record sizes to perform verification
        size_index = {}
        
        nearest_match_warning_msg = False
        for i in range(5):
            if(self.subset_btn[i]!=None and self.subset_btn[i].state):
                #Append Byte size of Signature length
                try:
                    size_val = int(self.subset_size_entry[i].get_text())
                    nearest_match = min(si, key=lambda x:abs(x-size_val))
                    if(size_val!=nearest_match and nearest_match_warning_msg==False):
                        warning_message+='Exact signature size not found in file. Nearest approximation was taken.\n'
                        warning_message+=str(size_val)+' was replaced with '+str(nearest_match)+'\n'
                        nearest_match_warning_msg = True
                    elif(size_val!=nearest_match and nearest_match_warning_msg==True):
                        warning_message+=str(size_val)+' was replaced with '+str(nearest_match)+'\n'
                        
                    signature_length.append(nearest_match)
                    size_index[nearest_match]=si[nearest_match]
                except:
                    self.message_display("Non-integer value passed as length. Please recheck signature lengths.")
                    return 0
        
        #Verify the sizes entered in the dialog box
        if(len(size_index)>0):
            retVal, textVal = verify_size(size_index)
            if (retVal):
                if not(len(warning_message)):
                    self.message_display("Signatures have the following error(s):\n"+textVal+'\nFile not created. Please try again!')
                    return 0
                else:
                    self.message_display("Signatures have the following error(s):\n"+textVal+'\nError might be generated due to automatic substitution. Please review the substitutions: \n'+warning_message+'\nFile not created. Please try again!')
                    return 0
        else:
            self.message_display("None of the check-boxes were enabled. Please choose at least one signature length.")
            return 0
        if(len([x for x in signature_length if signature_length.count(x) >= 2])>0):
            if not(len(warning_message)):
                self.message_display("Duplicate signature lengths are not allowed. Please choose unique signature lengths.")
                return 0
            else:
                self.message_display("Duplicate signature lengths are not allowed. Error might be generated due to automatic substitution. Please review the substitutions: \n"+warning_message+"\nPlease pick another size for the conflicts!")
                return 0
        try:
            total_sign_count = int(total_signatures.get_text())
        except:
            self.message_display("Non-integer value passed as total number of signatures.")
            return 0
        dialog.destroy()
        actual_sign_count = sum(size_index.values())
        
        #If the actual number of signatures is less than the desired signatures, just take everything
        if(actual_sign_count<total_sign_count):
            warning_message+='Actual number of signatures('+str(actual_sign_count)+') less than desired number of signatures('+str(total_sign_count)+').\n'
            query_str = ''
            for i in signature_length:
                query_str+='Size == ' + str(i) + ' | '
            query_str = query_str[:-3]
            new_df = df.query(query_str)
        #If we have to eliminate some signatures, assign count based 
        #on a round robin fashion to ensure some representation for all signatures
        else:
            actual_size_index = dict.fromkeys(size_index, 0)
            current_idx = 0
            while(total_sign_count>0):
                current_signature = signature_length[current_idx]
                if(size_index[current_signature]>0):
                    actual_size_index[current_signature]+=1
                    size_index[current_signature]-=1
                    total_sign_count -= 1
                current_idx += 1
                if(current_idx==len(size_index)):
                    current_idx = 0
                
            first_time_flag = True
            for signature_length_val, signature_count in actual_size_index.iteritems():
                df_splice = df.loc[df['Size'] == signature_length_val][:signature_count]
                if(first_time_flag):
                    new_df = df_splice
                    first_time_flag = False
                else:
                    new_df = new_df.append(df_splice, ignore_index=True)
        
        new_df.drop('Original', axis=1, inplace=True)
        if(len(warning_message)>0):
            retValueMsg=self.message_display(warning_message, _type=gtk.MESSAGE_WARNING, buttons=(gtk.BUTTONS_OK_CANCEL))
            #Stop if user presses cancel
            if retValueMsg==-6:
                return 1
            
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=new_df, header=False)
        if(file_location!=None and len(file_location)>0):
            self.window.destroy()
            df, si, retVal = interpretPattern(read_csv=True, file_location=file_location)
            if(~retVal):
                self.create_signature_window(widget, df, si, file_location)
                retValue = self.message_display("Would you like to save statistics for the signature(s)?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
                if retValue==-8:
                    self.save_signature_stats(file_location)
            else:
                self.message_display("Failed to read file. Please verify the file contents.")
          
        
    def generate_random_subset(self, widget, data):
        """
        Function to take input for generating a random subset of existing Signatures using a histogram of signature lengths.
        Initializes GUI dialog boxes to process inputs.
        
        returns None

        **UI Flow**:
            * Open signatures dictionary file
            * Display dialog to get inputs for random subset creation
            * Display histogram of signature lengths
            
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. seealso::  create_random_subset

        """
        file_location = self.read_from_file(widget, data, message="Open Signature CSV", file_type="csv")
        #file_location = 'C:\Users\sanke\workspace\PythonDev\snortDB_50.csv'
        try:
            if(file_location!=None and len(file_location)>0):
                dialog = gtk.Dialog(title="Generate a random subset of existing Signatures", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR)
                dialog.set_default_response(gtk.RESPONSE_OK)
                dialog.set_default_size(400,300)
                df, si, retVal = interpretPattern(read_csv=True, file_location=file_location)
                if(retVal):
                    self.message_display("Failed to read file. Please verify the file contents.")
                    return 1
                HBox = [None]*5
                VBox = [None]*5
                Label = [None]*5
                self.subset_size_entry = [None]*5
                self.subset_btn = [None]*5
                tooltips = gtk.Tooltips()
                
                VBoxTotal = gtk.VBox()
                HBoxTotal = gtk.HBox()
                LabelTotal = gtk.Label("Total number of Signatures")
                EntryTotal = gtk.Entry()
                EntryTotal.set_width_chars(4)
                EntryTotal.set_alignment(1)
                EntryTotal.select_region(0,3)
                HBoxTotal.pack_start(LabelTotal, padding=10)
                HBoxTotal.pack_start(EntryTotal, padding=5)
                VBoxTotal.pack_start(HBoxTotal)
                dialog.vbox.pack_start(VBoxTotal)
                
                for i in range(0, 5):
                    HBox[i] = gtk.HBox()
                    VBox[i] = gtk.VBox()
                    Label[i] = gtk.Label(" Bit Size "+str(i+1))                    
                    self.subset_size_entry[i] = gtk.Entry()
                    self.subset_size_entry[i].set_width_chars(4)
                    self.subset_size_entry[i].set_alignment(1)
                    
                    
                    HBox[i].pack_start(Label[i])
                    HBox[i].pack_start(self.subset_size_entry[i])
                    self.subset_btn[i] = gtk.CheckButton()
                    
                    tooltips.set_tip(self.subset_size_entry[i], "Choose the signature size in bits or pick from graph")
                    tooltips.set_tip(self.subset_btn[i], "Check to enable creation")
                    
                    HBox[i].pack_start(self.subset_btn[i], False, False, padding = 5)
                    VBox[i].pack_start(HBox[i])
                    dialog.vbox.pack_start(VBox[i])
                
                VBoxL = gtk.VBox()
                HBoxL = gtk.HBox()
                button = gtk.Button("Pick sizes using Bar graph")
                self.idx_subset = 0
                button.connect("clicked", self.generate_bar_plot_for_subset, si)        
                button2 = gtk.Button("Generate")
                button2.connect("clicked", self.create_random_subset, dialog, EntryTotal, df, si)
                HBoxL.pack_start(button, padding=10)
                HBoxL.pack_start(button2, padding=10)
                VBoxL.pack_start(HBoxL)
                dialog.vbox.pack_start(VBoxL)
                
                dialog.vbox.show_all()
                response = dialog.run()
                
                dialog.destroy()
                
        except:
            self.message_display("Failed to read file. Please check if it matches specifications and try again!")
            return 1
    
    
    def generate_bar_plot_for_subset(self, widget, si):
        """
        Function to create a bar plot of signature dictionary
        
        returns None

        :param widget: Calling widget
        :param si: Sizes of signatures
        :type widget: gtk.Widget
        :type si: dictionary
        :returns: None
        :rtype: None

        .. seealso::  generate_random_subset

        """
        size_arr = si.keys()
        value_arr = si.values()
        plt.title("Size Distribution Graph (Click on a size to select for dialog box)")
        plt.xlabel("Size (in bits)")
        plt.ylabel("Count")
        plt.ion()
        plt.show()
        plt.bar(size_arr, value_arr, width=7, picker=True)
        def select_plot(event):
            plt.pause(0.001)
            x_axis = event.artist._x
            nearest_match = min(si, key=lambda x:abs(x-x_axis))
            self.subset_size_entry[self.idx_subset].set_text(str(nearest_match))
            if(self.subset_btn[self.idx_subset]!=None and self.subset_btn[self.idx_subset].state==False):
                self.subset_btn[self.idx_subset].clicked()
            self.idx_subset+=1
            if(self.idx_subset==5):
                self.idx_subset=0
            self.subset_size_entry[self.idx_subset].select_region(0,4)
            self.subset_size_entry[self.idx_subset].drag_highlight()
            self.subset_btn[self.idx_subset].drag_highlight()
            if(self.idx_subset>0):
                self.subset_size_entry[self.idx_subset-1].drag_unhighlight()
                self.subset_btn[self.idx_subset-1].drag_unhighlight()
            else:
                self.subset_size_entry[4].drag_unhighlight()
                self.subset_btn[4].drag_unhighlight()
            
        plt.connect('pick_event', select_plot)
        

        
    def generate_pattern(self, widget, data):
        """
        Function to take input for generating a random set of Signatures. 
        Initializes GUI dialog boxes to process inputs.
        
        returns None

        **UI Flow**:
            * Display dialog to get inputs for random signature dictionary creation
            
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. seealso::  generate

        """
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
        """
        Function to update active signature from Signature dictionary window
        
        returns None
    
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. seealso::  active_stream

        """
        if widget.get_active():
            if(data!=''):
                self.current_signature = int(data)
            try:
                self.current_signature_label.set_text(data)
            except:
                return
    
    def active_stream(self, widget, data):
        """
        Function to update active stream from Stream map
        
        returns None
    
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. seealso::  active_signature

        """
        if widget.get_active():
            if(data!=''):
                self.current_stream = int(data)
            try:
                self.current_stream_label.set_text(data)
            except:
                return
    
    def active_config_stream(self, widget, data):
        """
        Function to update active config stream
        
        returns None
    
        :param widget: Calling widget
        :param data: Data for widget
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        .. note:: Function no longer used. Legacy code.

        """
        if widget.get_active():
            if(data!=''):
                self.current_config_stream = int(data)
                self.current_config_stream_idx = self.config_df[self.config_df['SID']==self.current_config_stream].index[0]
    
    def update_config_GUI(self, SID=None, L1=None, L2=None, Size=None, Select_Stream=None, Signature=None, SLR=None):
        """
        Function to update config window GUI based on inputs
        
        returns None
    
        :param SID: Stream ID
        :param L1: L1 Hash value
        :param L2: L2 Hash value
        :param Size: Size of stream
        :param Select_Stream: Legacy code. Unused.
        :param Signature: Inserted signatures
        :param SLR: SLR value
        :type SID: int
        :type L1: int
        :type L2: int
        :type Size: int
        :type Select_Stream: bool
        :type Signature: string
        :type SLR: string
        :returns: None
        :rtype: None

        """
        index=self.current_config_stream_idx
        if SID!=None:
            self.Config_SID[index].set_text(str(SID))
        if L1!=None:
            self.Config_L1[index].set_text(str(L1))
        if L2!=None:
            self.Config_L2[index].set_text(str(L2))
        if Size!=None:
            self.Config_Size[index].set_text(str(Size))
        if Signature!=None:
            self.Config_Signature[index].set_text(str(Signature))
        if SLR!=None:
            self.Config_SLR[index].set_text(str(SLR))
    
    def update_Stream_GUI(self, SID, Size_Stream, Select_Stream, SgnPosition, History, index):
        """
        Function to update config window GUI based on inputs
        
        returns None
    
        :param SID: Stream ID
        :param Size_Stream: Size of stream
        :param Select_Stream: Current Stream is active
        :param SgnPosition: Position of inserted signature
        :param History: History for selected stream
        :param index: Index of stream
        :type SID: int
        :type Size_Stream: int
        :type Select_Stream: bool
        :type SgnPosition: string
        :type History: string
        :type index: int
        :returns: None
        :rtype: None

        """
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
        """
        Function to display original Text of current stream 
        
        returns None

        **UI Flow**:
            * Display a dialog box with hex to string converted stream
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None

        """
        try:
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
        except:
            dialog.destroy()
            self.message_display("Please open a stream map before proceeding!")
                
    def create_stream_table(self):
        """
        Function to create a stream table that can be inserted into stream window. Created to separate code flow.
        
        returns None
            
        :returns: None
        :rtype: None

        """
        self.table_stream = gtk.Table(rows=1+MAX_COUNT_STREAMS, columns=4, homogeneous=False) 
        self.table_stream.set_col_spacings(10)
        title_bar = ['Select', 'SID', 'Size(bytes)', 'Signature (ID: Start-End bytes)']
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
                    if(j==1):
                        self.Select_Stream[j-1] = gtk.RadioButton(None)
                        self.Select_Stream[j-1].set_active(True)
                    else:
                        self.Select_Stream[j-1] = gtk.RadioButton(self.Select_Stream[0])
                        self.Select_Stream[j-1].set_alignment(0.5, 0.5)
                    
                    self.Select_Stream[j-1].set_sensitive(False)
                    self.table_stream.attach(self.Select_Stream[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==1):
                    label = gtk.Label("")
                    label.set_alignment(0, 0)
                    self.SID[j-1] = label
                    self.table_stream.attach(self.SID[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==2):
                    label = gtk.Label("")
                    label.set_alignment(0.5, 0.5)
                    self.Size_Stream[j-1] = label
                    self.table_stream.attach(self.Size_Stream[j-1], i, i+1, j, j+1, xpadding=5)
                
                else:
                    label = gtk.Label("")
                    label.set_alignment(0, 0)
                    self.SgnPosition[j-1] = label
                    self.table_stream.attach(self.SgnPosition[j-1], i, i+1, j, j+1, xpadding=5)                        
                                    
        self.table_stream.set_col_spacings(5)
        self.table_stream.show()
    
    def delete_verify_window(self, widget, data=None):
        """
        Function to kill verification window and exit 
        
        returns kill event signal

        **UI Flow**:
            * Display a dialog box confirm if user wants to quit the tool
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Kill event signal for gtk object
        :rtype: bool

        """
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==gtk.RESPONSE_YES:
            self.save_stats(widget, data)
        else:
            self.window3.destroy()
        del self.window3
            
    def delete_stream_window(self, widget, data=None):
        """
        Function to kill stream window and exit 
        
        returns kill event signal

        **UI Flow**:
            * Display a dialog box confirm if user wants to quit the tool
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Kill event signal for gtk object
        :rtype: bool

        """
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==gtk.RESPONSE_YES:
            self.save_stream_map(widget, data)    
        else:
            self.window2.destroy()
        self.change_signature_select_line_state(state=False)
        del self.window2
    
    def delete_configuration_window(self, widget, data=None):
        """
        Function to kill configuration window and exit 
        
        returns kill event signal

        **UI Flow**:
            * Display a dialog box confirm if user wants to quit the tool
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Kill event signal for gtk object
        :rtype: bool

        """
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==gtk.RESPONSE_YES:
            self.save_binary_after_config(widget, data)    
        else:
            self.window4.destroy()
        del self.window4
        
    def delete_signature_window(self, widget, data=None):
        """
        Function to kill signature window and exit 
        
        returns kill event signal

        **UI Flow**:
            * Display a dialog box confirm if user wants to quit the tool
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Kill event signal for gtk object
        :rtype: bool

        """
        retValue = self.message_display("Would you like to save your progress before quitting?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue==gtk.RESPONSE_YES:
            self.save_signature(widget, data)
        else:
            self.window.destroy()
            if(hasattr(self,'current_signature')):
                del self.current_signature
        del self.window
    
    def delete_load_window(self, widget, data=None):
        """
        Function to kill main window and exit 
        
        returns kill event signal

        **UI Flow**:
            * Display a dialog box confirm if user wants to quit the tool
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: Kill event signal for gtk object
        :rtype: bool

        """
        retValue = self.message_display("Are you sure you want to quit?", _type=gtk.MESSAGE_QUESTION, buttons=(gtk.BUTTONS_YES_NO))
        if retValue!=gtk.RESPONSE_YES:
            return True
        return False
    
    def clone_configuration(self, widget):
        """Function no longer used. Legacy code."""
        SID = self.config_df['SID'][len(self.config_df)-1]+1
        self.config_df = self.config_df.append(self.config_df.loc[self.current_config_stream_idx], ignore_index=True)
        self.config_df['SID'][len(self.config_df)-1]=SID
        self.window4.destroy()
        self.create_configuration_window(widget, '', self.config_df)
    
    def load_binary_after_config(self, widget, data):
        """
        Function to load filter after config and display it on the UI 
        
        returns None

        **UI Flow**:
            * Display a dialog for opening Stream Filter file
            * Update UI with selected file
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
        if(hasattr(self,'window4')):
            self.window4.destroy()
        config_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Pattern', 'SLR', 'L1', 'L2'])
        file_location = self.read_from_file(widget, data, message="Open Binary Stream output File", file_type="csv")
        self.window4.set_title("Filter Configuration | "+str(file_location))
        idx=-1
        with open(file_location, 'r+') as f:
            for line in f:
                line = line.strip('\n')
                line_arr = line.split(',')
                if(line_arr[0]=='LC' or line_arr[0]=='PC'):
                    update_now=False
                    idx+=1
                else:
                    update_now=True
                if not(update_now):
                    SLR_val = ','.join(line_arr[1:6])
                    L1_val = line_arr[6]
                    L2_val = line_arr[7]
                else:
                    SID_val = line_arr[0]
                    Size_val = line_arr[1]
                    Hex_val = line_arr[2]
                    Pattern_val = ','.join(line_arr[3:])
                    config_df.loc[idx]=[SID_val, Size_val, Hex_val, Pattern_val, SLR_val, L1_val, L2_val]
        config_df['SID'] = config_df['SID'].astype(int)
        config_df['Size'] = config_df['Size'].astype(int)
        config_df['Pattern'] = config_df['Pattern'].astype(str)
        config_df['SLR'] = config_df['SLR'].astype(str)
        config_df['L1'] = config_df['L1'].astype(int)
        config_df['L2'] = config_df['L2'].astype(int)
        self.create_configuration_window(widget, data, config_df)
        
    def save_binary_after_config(self, widget, data):
        """
        Function to save filter after config
        
        returns None

        **UI Flow**:
            * Display a dialog for saving Stream Filter file
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
        if((self.config_df['L1'] == 0).any()):
            self.message_display("Some configuration fields are missing. Please recheck and try again!")
            return
        file_location = self.save_signature(widget, data=None, save_default_df=False, df=self.config_df, header=True, dont_save_for_config=True)
        if(len(file_location)>0):
            prev_config_data = ''
            file_data = ''
            for _, i in self.config_df.iterrows():
                config_data = str(i['SLR'])+','+str(i['L1'])+','+str(i['L2'])+'\n'
                binary_data = str(i['SID'])+','+str(i['Size'])+','+str(i['Hex'])+','+str(i['Pattern'])+'\n'
                if config_data.strip('\n') == prev_config_data.strip('\n'):
                    config_data = 'PC,' + config_data
                else:
                    config_data = 'LC,' + config_data
                prev_config_data = config_data[3:]
                file_data += config_data + binary_data
            
            with open(file_location, 'w') as f:
                f.seek(0, 0)
                f.write(file_data)
            self.message_display(message_text="Successfully created "+file_location, _type=gtk.MESSAGE_INFO)
                
    def update_configuration(self, widget):
        """
        Function to update config for streams
        
        returns None

        **UI Flow**:
            * Display a dialog for taking in L1, L2 hashes
            
        :param widget: Calling widget
        :type widget: gtk.Widget
        :returns: None
        :rtype: None
        
        """
        dialog = gtk.Dialog(title="Specify L1 and L2 Hashes", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(200,150)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("L1")
        Adj1 = gtk.Adjustment(value=3, lower=3, upper=6, step_incr=3)
        Spin_Btn1 = gtk.SpinButton(adjustment=Adj1, climb_rate=0.0, digits=0)
        HBox.pack_start(Label)
        HBox.pack_start(Spin_Btn1)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("L2")
        Adj2 = gtk.Adjustment(value=6, lower=6, upper=12, step_incr=3)
        Spin_Btn2 = gtk.SpinButton(adjustment=Adj2, climb_rate=0.0, digits=0)
        HBox.pack_start(Label)
        HBox.pack_start(Spin_Btn2)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        dialog.vbox.show_all()
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            #Exit input if invalid byte is entered
            L1_val = Spin_Btn1.get_value_as_int()
            L2_val = Spin_Btn2.get_value_as_int()
            if((L1_val!=3 and L1_val!=6) or (L2_val!=6 and L2_val!=9 and L2_val!=12)):
                self.message_display('Invalid configuration. Please try again!')
                dialog.destroy()
                return 1
            dialog.destroy()
            self.update_config_GUI(L1=L1_val, L2=L2_val)
            self.config_df['L1'][self.current_config_stream_idx] = L1_val
            self.config_df['L2'][self.current_config_stream_idx] = L2_val
        else:
            dialog.destroy()
    
    
    def get_L1_L2(self, widget):
        """
        Function to get config (L1 and L2 hash values) for streams
        
        returns None

        **UI Flow**:
            * Display a dialog for taking in L1, L2 hashes
            
        :param widget: Calling widget
        :type widget: gtk.Widget
        :returns: None
        :rtype: None
        
        """
        dialog = gtk.Dialog(title="Specify L1 and L2 Hashes", parent=None, 
                                flags=gtk.DIALOG_MODAL|gtk.DIALOG_NO_SEPARATOR, 
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(200,150)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("L1")
        Adj1 = gtk.Adjustment(value=3, lower=3, upper=6, step_incr=3)
        Spin_Btn1 = gtk.SpinButton(adjustment=Adj1, climb_rate=0.0, digits=0)
        HBox.pack_start(Label)
        HBox.pack_start(Spin_Btn1)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        HBox = gtk.HBox()
        VBox = gtk.VBox()
        Label = gtk.Label("L2")
        Adj2 = gtk.Adjustment(value=6, lower=6, upper=12, step_incr=3)
        Spin_Btn2 = gtk.SpinButton(adjustment=Adj2, climb_rate=0.0, digits=0)
        HBox.pack_start(Label)
        HBox.pack_start(Spin_Btn2)
        VBox.pack_start(HBox)
        dialog.vbox.pack_start(VBox)
        
        dialog.vbox.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
            try:
                #Exit input if invalid byte is entered
                L1_val = Spin_Btn1.get_value_as_int()
                L2_val = Spin_Btn2.get_value_as_int()
                if((L1_val!=3 and L1_val!=6) or (L2_val!=6 and L2_val!=9 and L2_val!=12)):
                    self.message_display('Invalid configuration. Please try again!')
                    self.get_L1_L2(widget)
                return L1_val, L2_val
            except:
                self.message_display('Invalid configuration. Please try again!')
                self.get_L1_L2(widget)
        
        else:
            dialog.destroy()
            return None, None
    
    def create_configuration_table(self):
        """
        Function to create a config table that can be inserted into config window. Created to separate code flow.
        
        returns None
            
        :returns: None
        :rtype: None

        """
        df=self.config_df
        self.table_configuration = gtk.Table(rows=len(df)+1, columns=5, homogeneous=False) 
        self.table_configuration.set_col_spacings(10)
        title_bar = ['SID', 'L1 Hashes', 'L2 Hashes', 'Size (bytes)', 'Signature (Count, ID, Start, End ...)', 'SLR bits (0,1,2,3,4)']
        for i in range(6):
            label = gtk.Label(title_bar[i])
            label.modify_font(pango.FontDescription("Sans bold 10"))
            label.set_alignment(0, 0)
            self.table_configuration.attach(label, i, i+1, 0, 1, xpadding=5)
        
        stream_count = len(df)
        self.Config_SID = [None] * stream_count
        self.Config_L1 = [None] * stream_count
        self.Config_L2 = [None] * stream_count
#         self.Config_Select = [None] * stream_count
        self.Config_Size = [None] * stream_count
        self.Config_Signature = [None] * stream_count
        self.Config_SLR = [None] * stream_count
        
        #Loop through table to display values
        title_bar = ['SID', 'L1', 'L2', 'Size', 'Pattern', 'SLR']
        for i in range(6):
            for j in range(1, len(df)+1):   
                if(i==0):
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.set_alignment(0, 0)
                    self.Config_SID[j-1] = label
                    self.table_configuration.attach(self.Config_SID[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==1):
                    L1_val = df[title_bar[i]][j-1]
                    if(L1_val==0):
                        label = gtk.Label("")
                    else:
                        label = gtk.Label(str(L1_val))
                        self.dummy_configuration_window = False
                    label.set_alignment(0, 0)
                    self.Config_L1[j-1] = label
                    self.table_configuration.attach(self.Config_L1[j-1], i, i+1, j, j+1, xpadding=5)
                elif(i==2):
                    L2_val = df[title_bar[i]][j-1]
                    if(L2_val==0):
                        label = gtk.Label("")
                    else:
                        label = gtk.Label(str(L2_val))
                    label.set_alignment(0, 0)
                    self.Config_L2[j-1] = label
                    self.table_configuration.attach(self.Config_L2[j-1], i, i+1, j, j+1, xpadding=5)        
#                 elif(i==3):                    
#                     if(j==1):
#                         self.Config_Select[j-1] = gtk.RadioButton(None)
#                         self.Config_Select[j-1].set_active(True)
#                     else:
#                         self.Config_Select[j-1] = gtk.RadioButton(self.Config_Select[0])
#                         self.Config_Select[j-1].set_alignment(0.5, 0.5)
#                     
#                     self.Config_Select[j-1].connect("clicked", self.active_config_stream, self.Config_SID[j-1].get_label())
#                     self.Config_Select[j-1].set_active(True)
#                     self.table_configuration.attach(self.Config_Select[j-1], i, i+1, j, j+1, xpadding=5)
                
                elif(i==3):
                    if(str(df[title_bar[i]][j-1])!=''):
                        label = gtk.Label(str(df[title_bar[i]][j-1]/8))
                    else:
                        label = gtk.Label("")
                        self.Config_Select[0].set_sensitive(False)
                    label.set_alignment(0.5, 0.5)
                    self.Config_Size[j-1] = label
                    self.table_configuration.attach(self.Config_Size[j-1], i, i+1, j, j+1, xpadding=5)
                    
                elif(i==4):
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.set_alignment(0, 0)
                    self.Config_Signature[j-1] = label
                    self.table_configuration.attach(self.Config_Signature[j-1], i, i+1, j, j+1, xpadding=5)
                    
                elif(i==5):
                    label = gtk.Label(str(df[title_bar[i]][j-1]))
                    label.set_alignment(0, 0)
                    self.Config_SLR[j-1] = label
                    self.table_configuration.attach(self.Config_SLR[j-1], i, i+1, j, j+1, xpadding=5)
                    
        self.table_configuration.show()
        
    def create_configuration_window(self, widget, data, streams_df):
        """
        Function to create config window before generating binary 
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :param streams_df: Streams dataframe
        :type widget: gtk.Widget
        :type data: string
        :type streams_df: pandas.Dataframe
        :returns: None
        :rtype: None

        """
        if(hasattr(self,'window4')==1 and self.dummy_configuration_window == False):
            self.message_display("Another window is active. Please close that window before proceeding.", _type=gtk.MESSAGE_WARNING)
            self.delete_configuration_window(widget=None, data=None)
        self.window4 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window4.connect("destroy", lambda w: self.window4.destroy())
        self.window4.connect("delete_event", self.delete_configuration_window)
        self.window4.set_title("Filter Configuration Window")
        self.window4.set_default_size(640, 480)
        
        self.config_df = streams_df
        
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        main_vbox.show()
        menu_items4 = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_Load Stream Filter file",     "<control>O", self.load_binary_after_config, 0, None ),
            ( "/File/_Save Stream Filter file",     "<control>S", self.save_binary_after_config, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_configuration_window, 0, None ),
            )
        
        menubar = self.get_main_menu(self.window4, menu_items4)

        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        
        dataBox = gtk.VBox(spacing=30)
        frame = gtk.Frame("Filter Configuration")
        
        #Create scrollable display
        scrolledWin = gtk.ScrolledWindow()
        if(len(streams_df)<15):
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        else:
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            
        self.create_configuration_table()        
        scrolledWin.add_with_viewport(self.table_configuration)      
        
        frame.add(scrolledWin)
        scrolledWin.show()
        
        if(len(streams_df)<15):
            dataBox.pack_start(frame,  expand = False, fill = False, padding = 15)
        else:
            dataBox.pack_start(frame,  expand = True, fill = True, padding = 15)
        
#         #Create Partition for adding clone/update buttons
#         buttonBox = gtk.VBox()
#         HBoxL = gtk.HBox()
#         button1 = gtk.Button("Clone configuration")
#         button1.connect("clicked", self.clone_configuration)
#         button2 = gtk.Button("Update configuration")
#         button2.connect("clicked", self.update_configuration)
#         HBoxL.pack_start(button1, padding = 10)
#         HBoxL.pack_start(button2, padding = 10)
#         buttonBox.pack_start(HBoxL)
        
        main_vbox.pack_start(dataBox, True, True)
#         main_vbox.pack_start(buttonBox, False, False, padding = 15)
        
        self.window4.add(main_vbox)
        self.window4.show_all() 
        
    def create_verification_table(self):
        """
        Function to create a verification table that can be inserted into verification window. Created to separate code flow.
        
        returns None
            
        :returns: None
        :rtype: None

        """
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
        if df.loc[0][0]!='':
            self.dummy_verification_window = False
        self.table_verification.show()
    
    def create_stats_table(self):
        """
        Function to create a stats table that can be inserted into stats window. Created to separate code flow.
        
        returns None
            
        :returns: None
        :rtype: None

        """
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
        """
        Function to create verification window for viewing stats 
        
        returns None
    
        :param ver_df: Verification dataframe
        :param stats: Stats dictionary
        :type ver_df: pandas.Dataframe
        :type stats: dictionary
        :returns: None
        :rtype: None

        """
        if(hasattr(self,'window3')==1 and self.dummy_verification_window == False):
            self.message_display("Another window is active. Please close that window before proceeding.", _type=gtk.MESSAGE_WARNING)
            self.delete_verify_window(widget=None, data=None)
        self.window3 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window3.connect("destroy", lambda w: self.window3.destroy())
        self.window3.connect("delete_event", self.delete_verify_window)
        self.window3.set_title("Stream Simulation Analysis")
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
        """
        Function to create stream window for viewing and editing streams 
        
        returns None
    
        :returns: None
        :rtype: None

        """
        #Destroy old dialog before allowing a new one
        if(hasattr(self,'window2')==1):
            self.message_display("Another window is active. Please close that window before proceeding.", _type=gtk.MESSAGE_WARNING)
            self.delete_stream_window(widget=None, data=None)
            
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
            #( "/File/_Load Stream Binary file",     "<control>O", self.load_stream_binary_file, 0, None ),
            ( "/File/_Load Stream Map",    "<control>T", self.load_stream_map, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_stream_window, 0, None ),
            ( "/_Display",         None,         None, 0, "<Branch>" ),
            ( "/_Display/_Display Text view of Current Stream (without signatures)",    "<control>D", self.display_text_view, 0, None ),
            ( "/_Create",         None,         None, 0, "<Branch>" ),
            ( "/_Create/_Open Stream Construction Dialog",    "<control>N", self.create_insertion_dialog, 0, None ),
            ( "/_Create/_Generate random Stream Map",    "<control>N", self.generate_random_stream_map_dialog, 0, None ),
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
        """
        Function to insert signature at a specified loation of a stream 
        
        returns None
    
        :param widget: Calling widget
        :param entry: Signature index
        :type widget: gtk.Widget
        :type entry: gtk.Entry
        :returns: None
        :rtype: None

        """
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
        """
        Function to undo insert of last inserted signature in a stream 
        
        returns None
    
        :param widget: Calling widget
        :type widget: gtk.Widget
        :returns: None
        :rtype: None

        """
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
        """
        Function to roll over cursor stream selection window 
        
        returns None
    
        :param widget: Calling widget
        :type widget: gtk.Widget
        :returns: None
        :rtype: None

        """
        try:
            stream_index = self.stream_df[self.stream_df['SID']==self.current_stream].index[0]
            if(stream_index+1<self.current_index):
                self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=True, SgnPosition=None, History=None, index=stream_index+1)
            else:
                self.update_Stream_GUI(SID=None, Size_Stream=None, Select_Stream=True, SgnPosition=None, History=None, index=0)
        except:
            pass
        
    def add_new_stream(self, SID, Stream):
        """
        Function to add a new stream 
        
        returns None
    
        :param SID: Stream ID
        :param Stream: Stream Size
        :type SID: int
        :type Stream: int
        :returns: None
        :rtype: None

        """
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
        """
        Function to get ID and Size for a stream 
        
        returns None
    
        :param widget: Calling widget
        :type widget: gtk.Widget
        :returns: None
        :rtype: None

        """
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
        """
        Function to save filter stream for config
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
        stream_df_map = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Pattern', 'SLR', 'L1', 'L2'])
        L1 = None
        L2 = None
        L1, L2 = self.get_L1_L2(widget)
        if(L1==None or L2==None):
            return
            
        for ctr in range(self.current_index):
            SID = self.stream_df['SID'][ctr]
            Size_stream = self.stream_df['Size'][ctr]
            stream_data = self.stream_df['Original'][ctr]
            search_val_stream = self.stream_df[self.stream_df['SID']==SID]
            size_dict_for_bin = {}
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
                    
                    #Create a record of signatures for individual streams
#                     size_arr_for_bin.append((E_Index-S_Index+1)*8)
#                     size_dict_for_bin[(E_Index-S_Index+1)*8]=1
                    
                    stream_data = stream_data[0:S_Index] + sign_val + stream_data[E_Index+1:]
                    stream_data = stream_data[:int(Size_stream)/8]
                    if(Full_Signature):
                        pattern_val+=str(ID)+','+str(S_Index)+','+str(E_Index)+','
                        size_dict_for_bin[(E_Index-S_Index+1)*8]=1
                        count_valid_signatures+=1                            
                        
                
                #Remove trailing ,
                pattern_val = pattern_val[:-1]
                pattern_val=str(count_valid_signatures)+","+pattern_val
                
                #Generate SLR data for stream   
                SLR_val = self.generate_load_line(sorted(size_dict_for_bin.keys(), reverse = True))[2:]              
                    
            else:
                pattern_val = r"0"
                SLR_val = ""
            
            Hex = stream_data.encode('hex')
            
            stream_df_map.loc[ctr]=[SID, Size_stream, Hex, str(pattern_val), SLR_val, L1, L2]
        
        stream_df_map['SID'] = stream_df_map['SID'].astype(int)
        stream_df_map['Size'] = stream_df_map['Size'].astype(int)
        stream_df_map['Pattern'] = stream_df_map['Pattern'].astype(str)
        stream_df_map['SLR'] = stream_df_map['SLR'].astype(str)
        stream_df_map['L1'] = stream_df_map['L1'].astype(int)
        stream_df_map['L2'] = stream_df_map['L2'].astype(int)
        self.create_configuration_window(widget, data, stream_df_map)
        
        """
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
        """
    
    def generate_load_line(self, size_arr):
        """
        Function to generate SLR line based on size list
        
        returns Load Line

            
        :param size_arr: Size list
        :type size_arr: list
        :returns: Load line
        :rtype: string
        
        """
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
        return Load_Line
    
    def save_stats(self, widget, data):
        """
        Function to save Stats file as a CSV File
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
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
    
    def save_signature_filter(self, widget, data):
        """
        Function to save signature filter data, L1, L2 values along with signature data
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
        L1 = None
        L2 = None
        L1, L2 = self.get_L1_L2(widget)
        if(L1==None or L2==None):
            return
            
        file_location = self.save_signature(widget, data)
        filter_data = 'LC,0,0,0,0,0,'+str(L1)+','+str(L2) +'\n'
        with open(file_location, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(filter_data + content)
        
    def save_stream_map(self, widget, data):
        """
        Function to save Stream map as a CSV File
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
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
    
    def generate_random_stream_map(self, widget, n_streams, rand_seed, min_n_sign_length, max_n_sign_length, \
                 min_sign_per_stream, max_sign_per_stream, min_padding_bytes,\
                 max_padding_bytes, min_start_offset, max_start_offset):
        try:
            set_random_seed(rand_seed)
            file_data = ''
            stream_size = 0
            stream_id = 0
            sign_dict = {}
            size_arr_master = []
            size_arr_invalid = self.si.keys()
            size_arr = [x for x in size_arr_invalid if x>=MIN_SIZE_SIGNATURE and x<=MAX_SIZE_SIGNATURE]
            while(n_streams>0):
                n_sign_length = random_int(min_n_sign_length, max_n_sign_length)
            
                #Pick a few random sizes from the signature dictionary
                size_arr_new = []
                size_dict = {}
                while(n_sign_length>0):
                    rand_val = random.choice(size_arr)
                    if not rand_val in size_arr_new:
                        size_dict[rand_val]=1
                        retVal, _ = verify_size(size_dict)
                        if retVal:
                            del size_dict[rand_val]
                            continue
                        size_arr_new.append(rand_val)
                        n_sign_length-=1
                
                #Make note of all sizes in the master list
                for i in size_arr_new:
                    if i not in size_arr_master:
                        size_arr_master.append(i)
                        
                #Create a subset of the signature dataframe
                query_str = ''
                for i in size_arr_new:
                    query_str+='Size == ' + str(i) + ' | '
                query_str = query_str[:-3]
                df = self.df.query(query_str)
                df.reset_index(drop=True, inplace=True)
                len_df = len(df)
                stream_w_sign = []
                n_sign = random_int(min_sign_per_stream, max_sign_per_stream)
                for i in range(n_sign):
                    rand_idx = random_int(0, len_df-1)
                    sign_id = df['ID'][rand_idx]
                    sign_size = df['Size'][rand_idx]
                    sign_size /= 8 #Convert back to bytes
                    
                    if i==0:
                        start_offset = random_int(min_start_offset, max_start_offset)
                    else:
                        padding_bytes = random_int(min_padding_bytes, max_padding_bytes)
                        start_offset = stream_size + padding_bytes - 1
                    
                    #Signature can't be fit if size is greater
                    if start_offset + sign_size>=130:
                        continue
                    stream_size = start_offset + sign_size
                    stream_w_sign.append([sign_id, start_offset, start_offset+sign_size-1])
                    
                    #Make a record for stats
                    if sign_id in sign_dict.keys():
                        sign_dict[sign_id]+=1
                    else:
                        sign_dict[sign_id]=1
                
                end_padding = random_int(min_padding_bytes, max_padding_bytes)
                stream_size += end_padding
                
                if stream_size>=130:
                    stream_size=130
                    
                for sign_data in stream_w_sign:
                    pos_data = ','.join(str(e) for e in sign_data)
                    #Adding a 1 at the end, since all combinations will be valid
                    file_data += str(stream_id) + ',' + str(stream_size*8) + ',' + str(pos_data) + ',1\n'
                stream_id+=1
                n_streams-=1
            
            file_location = self.save_signature(widget, data=None, save_default_df=False, df=df, header=True, dont_save_for_config=True)
#             file_location = 'test.csv'
            with open(file_location, 'w') as f:
                f.seek(0, 0)
                f.write(file_data)
            message_text = "Successfully created "+file_location+"\n"
            message_text+= "The following signature lengths (bytes) were chosen at random:\n"+(', '.join(str(e/8) for e in sorted(size_arr_master)))+'\n'
            message_text+="Repetition frequency of Signature IDs (ID, Count):\n"
            sorted_size = sorted(sign_dict.items(), key=operator.itemgetter(1))
            for i in sorted_size:
                message_text+="{0:8}\t{1}\n".format(str(i[0]),str(i[1]))
            self.message_display(message_text, _type=gtk.MESSAGE_INFO)
            self.load_stream_map(widget, data=None, file_location = file_location)
        except Exception,e:
            print e
            self.message_display("Failed to process inputs")
        
    def generate_random_stream_map_dialog(self, widget, data):
        """
        Function to take input for generating a Random Stream Map
        
        returns None
    
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        :returns: None
        :rtype: None
        
        """
        if(hasattr(self,'current_signature')!=1):
            self.message_display("Please open the Signature window before proceeding further!", _type=gtk.MESSAGE_ERROR)
            return
        
        dialog = gtk.Dialog(title="Generate random Stream Map", parent=None, 
                                flags=gtk.DIALOG_NO_SEPARATOR, 
                                buttons=("Generate", gtk.RESPONSE_OK))
        dialog.set_default_size(250, 300)
        
        HBoxI = gtk.HBox()
        label = gtk.Label("Number of Streams:")
        label.set_alignment(0, 0)
        entry1 = gtk.Entry()
        entry1.set_text("0")
        entry1.set_alignment(1)
        entry1.set_width_chars(10)
        HBoxI.pack_start(label, padding = 15)
        HBoxI.pack_start(entry1, expand = False, fill = False, padding=15)
        dialog.vbox.pack_start(HBoxI, padding = 10)
        
        HBoxI = gtk.HBox()
        label = gtk.Label("Random Seed:")
        label.set_alignment(0, 0)
        entry2 = gtk.Entry()
        entry2.set_text(str(int(time.time())))
        entry2.set_alignment(1)
        entry2.set_width_chars(10)
        HBoxI.pack_start(label, padding = 15)
        HBoxI.pack_start(entry2, expand = False, fill = False, padding=15)
        dialog.vbox.pack_start(HBoxI, padding = 10)
        
        sig_size_frame = self.generate_min_max_frame_for_random_stream_map(frame_name="Number of different Signature lengths per stream",\
                                                                            min_val=MIN_N_LENGTHS, max_val=MAX_N_LENGTHS)
        dialog.vbox.pack_start(sig_size_frame, padding = 10)
        
        sig_per_stream_frame = self.generate_min_max_frame_for_random_stream_map(frame_name="Number of Signatures per stream",\
                                                                            min_val=MIN_SIGN_PER_STREAM, max_val=MAX_SIGN_PER_STREAM)
        dialog.vbox.pack_start(sig_per_stream_frame, padding = 10)
        
        padding_bytes_frame = self.generate_min_max_frame_for_random_stream_map(frame_name="Number of padding bytes between Signatures",\
                                                                            min_val=MIN_PADDING_BYTES, max_val=MAX_PADDING_BYTES)
        dialog.vbox.pack_start(padding_bytes_frame, padding = 10)
        
        start_offset_frame = self.generate_min_max_frame_for_random_stream_map(frame_name="Number of start offset bytes",\
                                                                            min_val=MIN_START_OFFSET, max_val=MAX_START_OFFSET)
        #=======================================================================
        # Block to restore previous configuration
        #=======================================================================
        if(hasattr(self,'random_stream_map_config')==1):
            entry1.set_text(str(self.random_stream_map_config[0]))
            entry2.set_text(str(self.random_stream_map_config[1]))
            sig_size_frame.get_children()[0].get_children()[0].get_children()[1].set_value(self.random_stream_map_config[2])
            sig_size_frame.get_children()[0].get_children()[1].get_children()[1].set_value(self.random_stream_map_config[3])
            sig_per_stream_frame.get_children()[0].get_children()[0].get_children()[1].set_value(self.random_stream_map_config[4])
            sig_per_stream_frame.get_children()[0].get_children()[1].get_children()[1].set_value(self.random_stream_map_config[5])
            padding_bytes_frame.get_children()[0].get_children()[0].get_children()[1].set_value(self.random_stream_map_config[6])
            padding_bytes_frame.get_children()[0].get_children()[1].get_children()[1].set_value(self.random_stream_map_config[7])
            start_offset_frame.get_children()[0].get_children()[0].get_children()[1].set_value(self.random_stream_map_config[8])
            start_offset_frame.get_children()[0].get_children()[1].get_children()[1].set_value(self.random_stream_map_config[9])
        
        dialog.vbox.pack_start(start_offset_frame, padding = 10)
        dialog.vbox.show_all()
        dialog.show()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            try:
                n_streams = int(entry1.get_text())
                rand_seed = int(entry2.get_text())
                #===============================================================
                #Frame->VBox->HBox1, HBox2; HBox1->Label, ScaleMin; HBox2->Label, ScaleMax 
                #===============================================================
                min_n_sign_length = int(sig_size_frame.get_children()[0].get_children()[0].get_children()[1].get_value())
                max_n_sign_length = int(sig_size_frame.get_children()[0].get_children()[1].get_children()[1].get_value())
                min_sign_per_stream = int(sig_per_stream_frame.get_children()[0].get_children()[0].get_children()[1].get_value())
                max_sign_per_stream = int(sig_per_stream_frame.get_children()[0].get_children()[1].get_children()[1].get_value())
                min_padding_bytes = int(padding_bytes_frame.get_children()[0].get_children()[0].get_children()[1].get_value())
                max_padding_bytes = int(padding_bytes_frame.get_children()[0].get_children()[1].get_children()[1].get_value())
                min_start_offset = int(start_offset_frame.get_children()[0].get_children()[0].get_children()[1].get_value())
                max_start_offset = int(start_offset_frame.get_children()[0].get_children()[1].get_children()[1].get_value())
                self.random_stream_map_config = [n_streams, rand_seed, min_n_sign_length, max_n_sign_length,\
                                                 min_sign_per_stream, max_sign_per_stream, min_padding_bytes,\
                                                 max_padding_bytes, min_start_offset, max_start_offset]
                #Verify if number of streams is valid
                if(n_streams==0 or n_streams>MAX_COUNT_STREAMS):
                    self.message_display("Please enter a valid number of streams!")
                    dialog.destroy()
                    self.generate_random_stream_map_dialog(widget, data=None)
                
                dialog.destroy()
                self.generate_random_stream_map(widget, n_streams, rand_seed, min_n_sign_length, max_n_sign_length, \
                 min_sign_per_stream, max_sign_per_stream, min_padding_bytes,\
                 max_padding_bytes, min_start_offset, max_start_offset)
            except:
                self.message_display("Non-integer value passed as parameter. Please re-check the input")
        else:
            dialog.destroy()
        
    def update_min_max_val_for_random_stream_map(self, widget, scaleMin, scaleMax, minFlag):
        """
        Function to ensure Min/Max value are always separated in generate_random_subset_dialog
        
        returns None
            
        :param widget: Calling widget
        :param scaleMin: Minimum value slider
        :param scaleMax: Maximum value slider
        :param minFlag: To reuse the function for both min/max
        :type widget: gtk.Widget
        :type scaleMin: int
        :type scaleMax: int
        :type minFlag: int
        
        :returns: None
        :rtype: None

        .. seealso::  generate_random_stream_map_dialog
        
        """
        if scaleMin.get_value()>scaleMax.get_value() and minFlag==True:
            scaleMax.set_value(scaleMin.get_value()+1)
        
        if scaleMax.get_value()<scaleMin.get_value() and minFlag==False:
            scaleMin.set_value(scaleMax.get_value()-1)
        
    def generate_min_max_frame_for_random_stream_map(self, frame_name, min_val, max_val):
        """
        Function to generate a frame to simplify UI creation code for generate_random_stream_map_dialog
        
        returns Frame
            
        :param frame_name: Title for the frame
        :param min_val: Minimum value for the slider
        :param max_val: Maximum value for the slider
        :type frame_name: string
        :type min_val: int
        :type max_val: int
        
        :returns: Frame
        :rtype: gtk.Frame

        .. seealso::  generate_random_stream_map_dialog
        
        """
        frame = gtk.Frame(frame_name)
        HBox1 = gtk.HBox()
        label = gtk.Label("Min:")
        label.set_alignment(0, 0)
        lengthAdjMin = gtk.Adjustment(value=min_val, lower=min_val, upper=max_val, step_incr=1)
        scaleMin = gtk.HScale(lengthAdjMin)
        scaleMin.set_digits(0)
        scaleMin.set_value_pos(gtk.POS_RIGHT)
        HBox1.pack_start(label, expand = False, fill = False, padding = 15)
        HBox1.pack_start(scaleMin, expand = True, fill = True, padding = 5)
        HBox2 = gtk.HBox()
        label = gtk.Label("Max:")
        label.set_alignment(0, 0)
        lengthAdjMax = gtk.Adjustment(value=max_val, lower=min_val, upper=max_val, step_incr=1)
        scaleMax = gtk.HScale(lengthAdjMax)
        scaleMax.set_digits(0)
        scaleMax.set_value_pos(gtk.POS_RIGHT)
        HBox2.pack_start(label, expand = False, fill = False, padding = 15)
        HBox2.pack_start(scaleMax, expand = True, fill = True, padding = 5)
        VBox = gtk.VBox()
        VBox.pack_start(HBox1, padding=5)
        VBox.pack_start(HBox2, padding=5)
        lengthAdjMin.connect("value_changed", self.update_min_max_val_for_random_stream_map, scaleMin, scaleMax, True)
        lengthAdjMax.connect("value_changed", self.update_min_max_val_for_random_stream_map, scaleMin, scaleMax, False)
        frame.add(VBox)
        return frame
        
    def create_insertion_dialog(self, widget, data, undoButton=True):
        """
        Function to create stream construction dialog box
        
        returns None
            
        :param widget: Calling widget
        :param data: Unused
        :param undoButton: Show undo button?
        :type widget: gtk.Widget
        :type data: string
        :type undoButton: bool
        
        :returns: None
        :rtype: None

        """
        if(hasattr(self,'current_signature')!=1):
            self.message_display("Please open the Signature window before proceeding further!", _type=gtk.MESSAGE_ERROR)
            return
        #Destroy old dialog before allowing a new one
        if(hasattr(self,'insertionDialog')==1):
            self.insertionDialog.destroy()
                
        self.insertionDialog = gtk.Dialog(title="Stream Construction", parent=None, 
                                flags=gtk.DIALOG_NO_SEPARATOR, 
                                buttons=None)
        
        self.insertionDialog.set_default_size(250,300)
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
        
        """
        button7 = gtk.Button("Open Signatures Dictionary")
        dummy_df = pd.DataFrame(columns = ['ID', 'Size', 'Hex'])
        dummy_df.loc[0]=['', '', '']
        self.insertionDialog.vbox.pack_start(button7)
        button7.connect("clicked", self.create_signature_window, dummy_df, {}, '')
        """

        button4 = gtk.Button("Add a stream")
        self.insertionDialog.vbox.pack_start(button4)
        button4.connect("clicked", self.create_stream)
        
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
        
        button5 = gtk.Button("Save Stream Map")
        self.insertionDialog.vbox.pack_start(button5)
        button5.connect("clicked", self.save_stream_map, "")
        
        button6 = gtk.Button("Create Stream Filter output file for simulation")
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
        """
        Function to initiate stream construction window generation process
        
        returns None
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        
        :returns: None
        :rtype: None

        """
        
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
        """
        Function to initiate verification window generation process
        
        returns None
            
        :param widget: Calling widget
        :param data: Unused
        :type widget: gtk.Widget
        :type data: string
        
        :returns: None
        :rtype: None

        """
        dummy_df = pd.DataFrame(columns = ['SID', 'Time', 'Query_Op', 'Start_Index', 'End_Index', 'Verification_Result', 'ID'])
        dummy_df.loc[0]=['', '', '', '', '', '', '']
        dummy_stats = (('Signature Count', ''),\
             ('Full Count', ''),('True Full Count', ''),('False Full Count', ''),\
             ('Prefix Count', ''),('True Prefix Count', ''),('False Prefix Count', ''))
        self.dummy_verification_window = True
        self.create_verification_window(dummy_df, dummy_stats)
    
    def validate_signature_pattern_for_stream(self, id, start_index, end_index, stream_index, stream_size):
        """Validates if signature pattern can be used for the given stream"""
        ErrorMessage = ''
        ErrorFlag = 0
        for i in self.history_index[stream_index]:
            #Check if start index is less than any old end index
            if start_index == i[1]:
                ErrorMessage+="Warning: signature ID #"+str(id)+" will overlap from starting index of signature ID #"+str(i[0]) +"\n"
            elif start_index != i[1] and start_index <= i[2]:
                ErrorFlag = 1
                ErrorMessage+="Signature ID #"+str(id)+" will overlap end index of signature ID #"+str(i[0]) +"\n"
                
        if(end_index>=stream_size):
            ErrorFlag=1
            ErrorMessage+="Signature ID #"+str(id)+" exceeds size of Stream\n"            
        
        return ErrorFlag, ErrorMessage
                
    
    
    def message_display(self, message_text, _type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK):
        """
        Function to generate a pop up message based on input parameters. 
        
        returns Response

        **UI Flow**:
            * Display Message box with specified text and buttons
            
        :param message_text: Message text to be printed
        :param _type: Is it an Error/Info/Question message box?
        :param buttons: gtk.Buttons
        :type message_text: string
        :type _type: gtk.MessageType
        :type buttons: gtk.Button
        :returns: Response
        :rtype: gtk.Response

        """
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
        """
        Function to create a menu object that can be inserted into a window 
        
        returns menu object
            
        :param window: Calling window
        :param menu_items: Menu Items to be included
        :type widget: gtk.Window
        :type menu_items: tuple
        :returns: Menu objecct
        :rtype: gtk.MenuBar

        """
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
        Function to create signature window 
        
        returns None

        :param widget: Calling widget
        :param df: Signature dataframe
        :param si: Size dictionary
        :param file_location: File location
        :type widget: gtk.Widget
        :type ver_df: pandas.Dataframe
        :type stats: dictionary
        :type file_location: string
        :returns: None
        :rtype: None

        """
        if(hasattr(self,'window')==1 and self.dummy_signature_window == False):
            self.message_display("Another window is active. Please close that window before proceeding.", _type=gtk.MESSAGE_WARNING)
            self.delete_signature_window(widget=None, data=None)
            
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
            ( "/File/_Open Hex Signatures with IDs & Size(.csv)",     "<control>O", self.read_from_csv, 0, None ),
            ( "/File/_Open Text Signatures(.txt)",    "<control>T", self.read_from_text, 0, None ),
            ( "/File/_Save Signature dictionary",    "<control>S", self.save_signature, 0, None ),
            ( "/File/_Save Filter Signature dictionary",    "<control>D", self.save_signature_filter, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Exit",     "<control>Q", self.delete_signature_window, 0, None ),
            ( "/_Display",      None,         None, 0, "<Branch>" ),
            ( "/Display/_Display Text View of Signatures",  "<control>D", self.display_original_text, 0, None ),
            ( "/_Generate",         None,         None, 0, "<Branch>" ),
            ( "/Generate/Generate random Text Signatures",   None, self.generate_pattern, 0, None ),
            ( "/Generate/Generate a random subset of Signatures using a graph",   None, self.generate_random_subset, 0, None ),
            ( "/Generate/Generate a random subset of Signatures using a range",   None, self.generate_random_subset_using_range_dialog, 0, None ),
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
        title_print_bar = ['Select', 'ID', 'Size(bytes)', 'Hex']
        title_bar = ['Select', 'ID', 'Size', 'Hex']
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
                if(i!=0):
                    if(i==2):
                        #Convert size back to bytes for display
                        if(str(df[title_bar[i]][j-1])!=''):
                            label = gtk.Label(str(df[title_bar[i]][j-1]/8))
                            self.dummy_signature_window = False
                        else:
                            label = gtk.Label('')
#                             self.dummy_signature_window = False
                        label.set_alignment(0.5, 0.5)
                    else:
                        label = gtk.Label(str(df[title_bar[i]][j-1]))
                        label.set_alignment(0, 0)
                    label.modify_font(pango.FontDescription("Sans 10"))
                    label.set_selectable(True)
                    table.attach(label, i, i+1, j, j+1, xpadding=5)
                
                elif(i==0):
                    
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
        table2.attach(gtk.Label("Size (bytes)"), 0, 1, 0, 1)
        table2.attach(gtk.Label("Count"), 1, 2, 0, 1)
        
        for i in range(2):
            for j in range(1, len(sorted_size)+1):
                if(i==0):
                    #Converrt bits to bytes
                    label = gtk.Label(str(sorted_size[j-1][i]/8))
                else:
                    label = gtk.Label(str(sorted_size[j-1][i]))
                table2.attach(label, i, i+1, j, j+1)
        if(len(si)<6):
            frame.add(table2)            
            sizeBox.pack_start(frame,  expand = False, fill = True, padding = 20)
        else:
            scrolledWin = gtk.ScrolledWindow()
            scrolledWin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scrolledWin.add_with_viewport(table2)
            frame.add(scrolledWin)
            scrolledWin.show()
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
            if(textVal.count("\n")<21):
                self.message_display("Signatures have the following error(s):\n"+textVal)
            else:
                with open('error.log', 'wb') as f:
                    f.write(textVal)
                self.message_display("More than 20 errors detected. Please check "+os.getcwd()+"\\error.log for the full list")
            
    def __init__(self):
        """
            
            Initializes pyGTK and creates Welcome Screen Window

        """
        self.windowInit = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.windowInit.connect("destroy", lambda w: gtk.main_quit())
        self.windowInit.connect("delete_event", self.delete_load_window)
        self.windowInit.set_title("Filter Control Panel")
        self.windowInit.set_default_size(200, 250)
        
        main_vbox = gtk.VBox(False, 5)        
        
        button = gtk.Button(TOOL_NAME)
        main_vbox.pack_start(button, expand = True, fill = True)
        dummy_df = pd.DataFrame(columns = ['ID', 'Size', 'Hex', 'Original'])
        dummy_df.loc[0]=['', '', '', '']
        
        self.dummy_signature_window = True
        button.connect("clicked", self.create_signature_window, dummy_df, {}, '')
        
        button2 = gtk.Button("Stream Construction")
        main_vbox.pack_start(button2, expand = True, fill = True)
        button2.connect("clicked", self.construct_stream, "")
        
        button21 = gtk.Button("Filter Configuration")
        main_vbox.pack_start(button21, expand = True, fill = True)
        dummy_df = pd.DataFrame(columns = ['SID', 'Size', 'Hex', 'Pattern', 'SLR', 'L1', 'L2'])
        dummy_df.loc[0]=['', '', '', '', '', 0, 0]
        self.dummy_configuration_window = True
        button21.connect("clicked", self.create_configuration_window, dummy_df, '') 
        
        button3 = gtk.Button("Stream Simulation Analysis")
        main_vbox.pack_start(button3, expand = True, fill = True)
        button3.connect("clicked", self.verify_stream, "")
        
        main_vbox.show_all()
        self.windowInit.add(main_vbox)
        self.windowInit.show()


def verify_size(size_index):
    """
        Verifies if constraints are met for size of signatures.
        
        Returns 0, None if constraints are met
        
        Returns 1, ErrorMessage if contraints aren't met
        
        Inputs:
        
        size_index: dictionary of sizes and their counts
    
    """
    
    sorted_size = sorted(size_index.items(), key=operator.itemgetter(0))
    flag=0;
    ErrorMessage = ""
    ErrorHeader = ""
    n_sigs_high_count = 0
    n_sigs_low_count = 0
    n_sigs_max = 0
    n_sigs_min = 0
    n_sigs_distance = 0
    
    if(len(sorted_size)>MAX_N_LENGTHS):
        flag=1
        #ErrorMessage = "Count of lengths greater than: "+str(MAX_N_LENGTHS)+"\n"
        n_sigs_high_count = len(sorted_size)
    elif(len(sorted_size)<MIN_N_LENGTHS and len(sorted_size)!=0):
        flag=1
        #ErrorMessage += "Count of lengths less than: "+str(MIN_N_LENGTHS)+"\n"
        n_sigs_low_count = len(sorted_size)
        
    for i in range(len(sorted_size)):
        if len(sorted_size)==1:
            min_check = MIN_SIZE_SIGNATURE - 8
        else:
            min_check = MIN_SIZE_SIGNATURE
        
        if sorted_size[i][0]%8!=0:
            flag=1
            ErrorMessage+= "Signature is not a multiple of 8. It's not a valid byte.\n"
        
        if sorted_size[i][0]>MAX_SIZE_SIGNATURE:
            flag=1
            #ErrorMessage+= 'Signature length ('+str(sorted_size[i][0])+') greater than: '+str(MAX_SIZE_SIGNATURE)+'\n'
            n_sigs_max += 1
        elif sorted_size[i][0]<min_check:
            flag=1
            #ErrorMessage+= "Signature length ("+str(sorted_size[i][0])+") less than: "+str(MIN_SIZE_SIGNATURE)+"\n"
            n_sigs_min += 1
        if(i==0):
            previous_val=sorted_size[0][0]
            continue
        
        if(sorted_size[i][0]-previous_val<DISTANCE_CONSECUTIVE):
            flag=1
            #ErrorMessage+= "Distance between consecutive signatures ("+str(sorted_size[i][0]-previous_val)+") less than: "+str(DISTANCE_CONSECUTIVE)+"\n"
            n_sigs_distance += 1
        previous_val=sorted_size[i][0]
    
    if(flag):
        if(n_sigs_high_count>0):
            ErrorHeader += "Rule #1: Maximum of "+str(MAX_N_LENGTHS)+" different signature lengths are allowed.\n"
            ErrorMessage += "#1: Only "+str(MAX_N_LENGTHS)+" different signature lengths are allowed, but "+str(n_sigs_high_count)+" lengths are present in the dictionary.\n"
        if(n_sigs_low_count>0):
            ErrorHeader += "Rule #2: Minimum of "+str(MIN_N_LENGTHS)+" different signature lengths are needed.\n"
            ErrorMessage += "#2: At least "+str(MIN_N_LENGTHS)+" different signature lengths are needed, but "+str(n_sigs_high_count)+" lengths are present in the dictionary.\n"
        if(n_sigs_max>0):
            ErrorHeader += "Rule #3: Signature length must be less than "+str(MAX_SIZE_SIGNATURE)+" bits.\n"
            ErrorMessage += "#3: "+str(n_sigs_max)+" signatures have a length greater than "+str(MAX_SIZE_SIGNATURE)+" bits.\n"
        if(n_sigs_min>0):
            ErrorHeader += "Rule #4: Signature length must be greater than "+str(MIN_SIZE_SIGNATURE)+" bits.\n"
            ErrorMessage += "#4: "+str(n_sigs_min)+" signatures have a length less than "+str(MIN_SIZE_SIGNATURE)+" bits.\n"
        if(n_sigs_distance>0):
            ErrorHeader += "Rule #5: Signature lengths should be separated by "+str(DISTANCE_CONSECUTIVE)+" bits.\n"
            ErrorMessage += "#5: "+str(n_sigs_distance)+" signatures have a separation of less than "+str(DISTANCE_CONSECUTIVE)+" bits between them.\n"
        
        return 1, ErrorHeader+'\n'+ErrorMessage
    else:
        return 0, None

def random_int(range_low, range_high):
    return random.randint(range_low, range_high)

def set_random_seed(seed):
    random.seed(seed)
    
def id_generator(size=MIN_SIZE_SIGNATURE, chars=ALLOWABLE_CHARS):
    """
        Generates a random signature of specified size and characters
        
        returns random signature

        :param size: Size of signature
        :param chars: Allowable characters for signature creation
        :type size: int
        :type chars: string.Type
        
        :returns: Random signature
        :rtype: string

    """
    return ''.join(random.choice(chars) for _ in range(size))

def patternGenerator(file_name="patterns.txt", size_arr = [], min_n_lengths=MIN_N_LENGTHS, 
                     max_n_lengths=MAX_N_LENGTHS, min_size_signature=MIN_SIZE_SIGNATURE,
                     max_size_signature=MAX_SIZE_SIGNATURE, distance_consecutive=DISTANCE_CONSECUTIVE):
    """
        Generates a file in the local directory with a set of random patterns.
        
        Constraints:
        
        Length is between MIN_SIZE_SIGNATURE, MAX_SIZE_SIGNATURE
        
        Count is between MIN_N_LENGTHS, MAX_N_LENGTHS
        
        Distance between lengths is greater than or equal to DISTANCE_CONSECUTIVE
        
        returns return value
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
    """
        Verifies if signatures are present in the specified stream based on the binary file.
        
        Generates processed stats dataframe and stats array of tuples.
        
        Returns dataframe consisting of SID, Query OP, Start/End Index, Result and ID
        
        Also return array of tuples of verification summary
        
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
    """
        Reads the Stats file and loads it as 'SID', 'Time', 'Query_Op', 'Start_Index' and 'End_Index'. 
        
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
    """
        Reads the processed Stats file and determines the stats in the form of an array of tuples. 
        
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
    """
        Reads the pattern file and generates ID, Hex and Size paramters. 
        
        Returns None, None on failure and a dataframe, dictionary on success
        
        Inputs:
        
        read_csv: Is the file a CSV?
        
        file_location: Name of the file

    """
    if(read_csv):
        try:
            csv_data = pd.read_csv(file_location, header=None, names=['ID', 'Size', 'Hex'])
            csv_data['Original'] = csv_data.apply(lambda row: row.Hex.decode("Hex"), axis=1)
        except Exception,e:
            print "Failed to read file with exception" + str(e)
            return None, None, 1
        
    proc_data = pd.DataFrame(columns = ['ID', 'Size', 'Hex', 'Original'])
    
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
                
                
                # proc_data['ID'][i] = i
                # proc_data['Hex'][i] = line.encode("Hex")
                # proc_data['Original'][i] = line
                # proc_data['Size'][i] = size_line
                proc_data.loc[i] = [i, size_line, line.encode("Hex"), line] 
                #Generate bitstream
                #stream_data = ''.join('{0:04b}'.format(int(c, 16)) for c in proc_data['Hex'][i])
                
                i=i+1
        except Exception,e:
            print "Failed to open file with exception" + str(e)
            return None, None, 1
    
    else:
        proc_data = csv_data
        for i in range(len(csv_data)):
            # proc_data['ID'][i] = csv_data['ID'][i]
            # proc_data['Size'][i] = csv_data['Size'][i]
            # proc_data['Hex'][i] = csv_data['Hex'][i]
            # proc_data['Original'][i] = csv_data['Hex'][i].decode("Hex")

            # proc_data.loc[i] = [csv_data['ID'][i], csv_data['Size'][i], csv_data['Hex'][i], csv_data['Hex'][i].decode("Hex")]
            size_line = csv_data['Size'][i]
            if(size_index.has_key(size_line)):
                    size_index[size_line] += 1
            else:
                size_index[size_line] = 1
    proc_data['ID'] = proc_data['ID'].astype(int)
    proc_data['Size'] = proc_data['Size'].astype(int)
    proc_data['Hex'] = proc_data['Hex'].astype(str)
    proc_data['Original'] = proc_data['Original'].astype(str)
    # proc_data = proc_data[(proc_data.T != -1).any()]
    return proc_data, size_index, 0

if __name__ == "__main__":
    PyApp()
    gtk.main()
