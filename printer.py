#   CodePad Printer
#   Python Tkinter based Code editor
#   Licensed LGPL
#   All Rights Reserved

__author__ = 'Robert Cope'
__version__ = 'v0.1'
__license__ = 'LGPL'

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import extrawidgets
import ttk
import tkMessageBox

try:
    import cups
    CUPSAVAILABLE = True
except ImportError:
    CUPSAVAILABLE = False

try:
    import win32print
    WIN32PRINT = True
except ImportError:
    WIN32PRINT = False



class PrintDialogLinux(tk.Toplevel):
    """
        A dialog for handling printing.
    """
    BUTTONWIDTH = 20
    def __init__(self, parent, filename, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        if not CUPSAVAILABLE:
            tkMessageBox.showerror('CUPS Not Available!', 'CUPS is necessary to print. Please install!',
                                   parent=self)
            self.destroy()
            return
        self.parent = parent
        self.filename = filename
        self.grab_set()
        self.wm_title("Print Code...")


        self.conn = cups.Connection()
        printerDictRef = self.conn.getPrinters()

        self.printerListFrame = ttk.Labelframe(self, text="Printers")
        self.printerList = extrawidgets.ScrollListbox(self.printerListFrame)
        for key in printerDictRef.keys():
            self.printerList.Listbox.insert(tk.END, key)
        self.printerList.pack(expand=1, fill=tk.BOTH)
        self.printerListFrame.grid(row=0, column=0, columnspan=2, sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.printButton = tk.Button(self, text="Print", command=self.sendToPrinter,
                                     width=self.BUTTONWIDTH)
        self.printButton.grid(row=1, column=0)

        self.cancelButton = tk.Button(self, text="Cancel", command=self.destroy,
                                      width=self.BUTTONWIDTH)
        self.cancelButton.grid(row=1, column=1)

        self.getPrinterSelected()

    def __del__(self):
        """
            Make sure when this gets recycled that we've released the grab.
        """
        self.grab_release()

    def destroy(self):
        """
            Release the grab, and destroy the dialog.
        """
        self.grab_release()
        tk.Toplevel.destroy(self)

    def getPrinterSelected(self):
        return self.printerList.Listbox.get(tk.ACTIVE)

    def sendToPrinter(self):
        try:
            self.conn.printFile(self.getPrinterSelected(), self.filename, "{0} - CodePad".format(self.filename), {})
        except cups.IPPError:
            tkMessageBox.showerror('Failed to Print!', 'Failed to Print! Check printer!', parent=self)


class PrintDialogWindows(tk.Toplevel):
    """
        A dialog for handling printing.
    """
    def __init__(self, parent, printData, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        if not CUPSAVAILABLE:
            tkMessageBox.showerror('Win32Print Not Available!', 'Win32Print is necessary to print. Please install!',
                                   parent=self)
            self.destroy()
            return
        self.parent = parent
        self.printData = printData
        self.grab_set()
        self.wm_title("Print Code...")


    def __del__(self):
        """
            Make sure when this gets recycled that we've released the grab.
        """
        self.grab_release()

    def destroy(self):
        """
            Release the grab, and destroy the dialog.
        """
        self.grab_release()
        tk.Toplevel.destroy(self)