#   CodePad
#   Python Tkinter based Code editor
#   Licensed LGPL
#   All Rights Reserved

__author__ = 'Robert Cope'
__version__ = 'v0.1 (Alpha)'
__license__ = 'LGPL'

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import ttk
import subprocess
import tkSimpleDialog
import tkMessageBox
import tkFileDialog
import extrawidgets



class CodePadEditor(tk.Frame):
    def __init__(self, root, parent=None, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.root = root
        self._filename = None
        self._saved = False
        self.parent = parent if parent else root
        self.buildTextBox()

    def buildTextBox(self):
        """
            Should be called at initialization, puts the text box and scroll bars in place.
        """
        self.textbox = extrawidgets.CustomText(self, wrap=tk.NONE)
        self.textbox.grid(row=0, column=1, sticky="NSEW")
        self.textbox.tag_configure("search", background="green")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.linenumberbox = extrawidgets.TextLineNumbers(self, width=40)
        self.linenumberbox.attach(self.textbox)
        self.linenumberbox.grid(row=0, column=0, sticky="NS")

        self.vscroll = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.vscroll.grid(row=0, column=2, sticky="NS")

        self.hscroll = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.hscroll.grid(row=1, column=1, sticky="EW")

        self.textbox.config(yscrollcommand=self.vscroll.set, xscrollcommand=self.hscroll.set)
        self.vscroll.config(command=self.textbox.yview)
        self.hscroll.config(command=self.textbox.xview)

        self.textbox.bind("<<Change>>", self._on_change)
        self.textbox.bind("<<Configure>>", self._on_change)


    def setTextContent(self, newContent):
        """
            Clear the text box and fill it's contents.
        """
        self.textbox.delete("1.0", tk.END)
        self.textbox.insert("1.0", newContent)

    def setSaved(self, state):
        """
            Set the saved state (should beTrue if the file is now on disk, False othewise)
        """
        self._saved = state

    def setFileName(self, name):
        """
            Set the filename the file should be saved to the disk as.
        """
        self._filename = name

    def copySelectedText(self):
        """
            Grab the selected text in the textbox.
        """
        return self.textbox.selection_get()

    def cutSelectedText(self):
        """
            Grab and delete the selected text in the textbox.
        """
        text = self.textbox.get("sel.first", "sel.last")
        self.textbox.delete("sel.first", "sel.last")
        return text

    def insertText(self, newtext):
        """
            Delete selected and insert next text in its place.
        """
        try:
            self.textbox.delete("sel.first", "sel.last")
        except tk.TclError, e:
            pass
        self.textbox.insert("insert", newtext)

    def _on_change(self, event):
        """
            Redraw the line numberbox when we do something new.
        """
        self.linenumberbox.redraw()

    def getTextContent(self):
        """
            Get the content stored in the textbox
        """
        return self.textbox.get("1.0", tk.END)

    @property
    def filename(self):
        """
            Get the associated filename for this editor
        """
        return self._filename

    @property
    def saved(self):
        """
            Return if the editor has been saved at any point or not.
        """
        return self._saved

    @property
    def hasContents(self):
        """
            Return if the editor has any contents in it.
        """
        if len(self.getTextContent()) > 1:
            return True
        else:
            return False



class textFindWidget(tk.Toplevel):
    BUTTONWIDTH = 15
    def __init__(self, root, editor, parent=None, *args, **kwargs):
        tk.Toplevel.__init__(self, root, *args, **kwargs)
        self.root = root
        self.editor = editor
        self.parent = parent if parent else root
        self.searchTextVar = tk.StringVar(self)

        self.lframe = ttk.Labelframe(self, text='Find')
        self.rowOne = tk.Frame(self.lframe)
        tk.Label(self.rowOne, text="Search Text:").grid(row=0, column=0)

        self.searchEntry = tk.Entry(self.rowOne, textvariable=self.searchTextVar, width=40)
        self.searchEntry.grid(row=0, column=1, sticky="NSEW")
        self.rowOne.grid(row=0, column=0, sticky="NSEW")
        self.rowOne.grid_rowconfigure(0, weight=1)
        self.rowOne.grid_columnconfigure(1, weight=1)

        self.rowTwo = tk.Frame(self.lframe)
        self.findButton = tk.Button(self.rowTwo, text="Find", width=self.BUTTONWIDTH, command=self.findText)
        self.findButton.grid(row=0, column=0, sticky="NSEW")

        self.closeButton = tk.Button(self.rowTwo, text="Close", command=self.destroy, width=self.BUTTONWIDTH)
        self.closeButton.grid(row=0, column=1, sticky="NSEW")
        self.rowTwo.grid(row=1, column=0, sticky="NSEW")
        self.rowTwo.grid_rowconfigure(0, weight=1)
        self.rowTwo.grid_rowconfigure(1, weight=1)
        self.rowTwo.grid_columnconfigure(0, weight=1)
        self.rowTwo.grid_columnconfigure(1, weight=1)

        self.clearButton = tk.Button(self.rowTwo, text="Clear Highlight", width=self.BUTTONWIDTH,
                                     command=self.clearHighlight)
        self.clearButton.grid(row=1, column=0, sticky="NSEW")
        self.lframe.grid(row=0, column=0, sticky="NSEW")


    def findText(self):
        """
            Find and highlight all of the text that matches what we are looking for in the current editor.
        """
        offSetVar = tk.StringVar(self)
        offSetVar.set("0")
        currentpos = "0.0"
        while currentpos:
            startPos = "{position} + {offset}c".format(position=currentpos, offset=offSetVar.get())
            currentpos = self.editor.textbox.search(self.searchTextVar.get(), startPos, stopindex="end",
                                                     count=offSetVar)
            if currentpos:
                self.editor.textbox.tag_add("search", currentpos,
                                    "{position} + {offset}c".format(position=currentpos, offset=offSetVar.get()))
        return

    def clearHighlight(self):
        """
            Clear all of the highlights form the current editor.
        """
        self.editor.textbox.tag_remove("search", "1.0", tk.END)


class CodePadMainWindow(tk.Frame):
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.openEditors = []
        self.openFiles = {}
        self.buildMenubar()

        self.editorNotebook = ttk.Notebook(self)
        self.editorNotebook.enable_traversal()


        self.editorNotebook.grid(row=0, column=0, sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.addNewEditor()

    def buildMenubar(self):
        """
            Construct the Menubar for the application on start up.

            This builds up the menu bar and binds all the hot-keys associated with it.
        """
        self.menubar = tk.Menu(self)

        self.filemenu = tk.Menu(self)
        self.filemenu.add_command(label="New", command=self.addNewEditor, accelerator="Ctrl+N")
        self.root.bind('<Control-Key-n>', lambda e: self.addNewEditor())
        self.filemenu.add_command(label="Open...", command=self.openFile, accelerator="Ctrl+O")
        self.root.bind('<Control-Key-o>', lambda e: self.openFile())
        self.filemenu.add_command(label="Save", command=self.saveFile, accelerator="Ctrl+S")
        self.root.bind('<Control-Key-s>', lambda e :self.saveFile())
        self.filemenu.add_command(label="Save as...")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.destroy, accelerator="Ctrl+Q")
        self.root.bind('<Control-Key-q>', lambda e: self.root.destroy())
        self.menubar.add_cascade(menu=self.filemenu, label='File')

        self.editmenu = tk.Menu(self)
        self.editmenu.add_command(label="Cut", command=self.cutCurrent, accelerator="Ctrl+X")
        self.root.bind('<Control-Key-x>', lambda e: self.cutCurrent())
        self.editmenu.add_command(label="Copy", command=self.copyCurrent, accelerator="Ctrl+C")
        self.root.bind('<Control-Key-c>', lambda e: self.copyCurrent())
        self.editmenu.add_command(label="Paste", command=self.pasteCurrent, accelerator="Ctrl+V")
        self.root.bind('<Control-Key-v>', lambda e: self.pasteCurrent())
        self.menubar.add_cascade(menu=self.editmenu, label='Edit')

        self.viewmenu = tk.Menu(self)
        self.viewmenu.add_command(label="Find", command=self.findTextCurrent, accelerator="Ctrl+F")
        self.root.bind('<Control-Key-f>', lambda e: self.findTextCurrent())
        self.viewmenu.add_command(label="Replace")
        self.menubar.add_cascade(menu=self.viewmenu, label='View')

        self.settingsmenu = tk.Menu(self)
        self.settingsmenu.add_command(label="Plugins...")


        self.menubar.add_cascade(menu=self.settingsmenu, label='Settings')

        self.menubar.add_command(label='Run...', command=self.runCurrent, accelerator="Alt+R")
        self.root.bind('<Alt-Key-r>', lambda e: self.runCurrent())
        self.menubar.add_command(label='Close Tab', command=self.closeCurrentTab)

        self.helpmenu = tk.Menu(self)
        self.helpmenu.add_command(label="Help Contents")
        self.helpmenu.add_command(label="About", command=self.about)

        self.menubar.add_cascade(menu=self.helpmenu, label="Help")



        self.root.config(menu=self.menubar)
        return

    def addNewEditor(self, filename=None):
        """
            Opens a new editor tab.
            If filename is specified, we will try and open in in ASCII mode and use it to fill the new textbox.
        """
        ed = CodePadEditor(self.root, self.editorNotebook)
        self.openEditors.append(ed)
        if not filename:
            ed.setFileName("Untitled")
        else:
            try:
                contents = ''
                with open(filename, 'r') as f:
                    contents = f.read()
            except:
                tkMessageBox.showerror('Could not read file!', 'Failed to read file correctly!')
                contents = ''
            ed.setFileName(filename)
            ed.setSaved(True)
            ed.setTextContent(contents)
        self.editorNotebook.add(ed, text=ed.filename, sticky="NSEW")
        self.selectEditor(ed)
        return ed

    def selectEditor(self, ed=None):
        """
            Bring the given editor to focus.
            If no editor is specified, we will return the ID of the currently focused editor.
        """
        return self.editorNotebook.select(ed)

    def openFile(self):
        """
            The open file callback in the file menu (also mapped to Ctrl+0). Spawns a dialog and opens a new editor if
            a file was specified. If we canceled, it does nothing.
        """
        filename = tkFileDialog.askopenfilename(parent=self, defaultextension=".txt",
                                                filetypes=[("Plaintext File", "*.txt"), ("Python Script", "*.py"),
                                                           ("All Files", "*")])
        if filename not in self.openFiles:
            oldeditor = self.getCurrentEditor()
            closeOld = self.isCurrentEmpty
            ed = self.addNewEditor(filename)
            self.openFiles[filename] = ed
            if closeOld:
                self._closeTab(oldeditor)
        else:
            self.selectEditor(self.openFiles[filename])

    def getCurrentEditor(self):
        """
            Grab the current focused editor instance.
        """
        return self.openEditors[self.editorNotebook.index(self.selectEditor())]

    def saveFile(self):
        """
            This is the call back for the regular save in File, (also Ctrl+S). Should spawn a save dialog and
            save the file to disk, if the user doesn't cancel.
        """
        currentEditor = self.getCurrentEditor()
        if not currentEditor.saved:
            filename = tkFileDialog.asksaveasfilename()
            if not filename:
                return False
            currentEditor.setFileName(filename)
            currentEditor.setSaved(True)
            self.setTitle(currentEditor, filename)
        with open(currentEditor.filename, 'w') as f:
            f.write(currentEditor.getTextContent())
        return True

    def setTitle(self, ed, title):
        """
            Set the tab title for the specified editor.
        """
        self.editorNotebook.tab(ed, text=title)

    def cutCurrent(self):
        """
            Cut the current selection in the editor, and load it into the clipboard.
        """
        currentEditor = self.getCurrentEditor()
        self.root.clipboard_clear()
        self.root.clipboard_append(currentEditor.cutSelectedText())

    def copyCurrent(self):
        """
            Copy the current selection to the clipboard.
        """
        currentEditor = self.getCurrentEditor()
        self.root.clipboard_clear()
        self.root.clipboard_append(currentEditor.copySelectedText())

    def pasteCurrent(self):
        """
            Paste over the current selection with whatever was on the clipboard.
        """
        currentEditor = self.getCurrentEditor()
        currentEditor.insertText(self.root.clipboard_get())

    def closeCurrentTab(self):
        """
            Close whatever tab is currently focused.
        """
        currentEditor = self.getCurrentEditor()
        return self._closeTab(currentEditor)

    def _closeTab(self, editor):
        """
            The private method for closing any editor.
        """
        if len(self.openEditors) == 1:
            self.addNewEditor()
        self.editorNotebook.forget(editor)
        self.openEditors.remove(editor)
        if editor.filename in self.openFiles:
            self.openFiles.pop(editor.filename)
        del editor

    def runCurrent(self):
        """
            Save the current file, let the user specify the interpreter, and try to run the code in a new window.
        """
        if self.saveFile():
            interpreter = tkSimpleDialog.askstring('Set Interpreter',
                                             'Set the interpreter to run the code',
                                             initialvalue='python', parent=self)
            subprocess.Popen('xterm -hold -T {2} -e {0} {1}'.format(interpreter, self.getCurrentEditor().filename, "\"CodePad Code Run\""), shell=True)
        else:
            tkMessageBox.showerror('Run Error', 'Must save the file in order to be run!')

    def findTextCurrent(self):
        """
            Open a dialog to find text in the current editor.
        """
        currentEditor = self.getCurrentEditor()
        textFindWidget(self.root, currentEditor, self)

    def about(self):
        """
            Show the about box.
        """
        aboutMsg = 'CodePad Version {version}\nWritten 2014 by Robert Cope'.format(version=__version__)
        tkMessageBox.showinfo('About', aboutMsg, parent=self)

    @property
    def isCurrentEmpty(self):
        """
            isCurrentEmpty will return True if the current editor has not been saved and has no contents.
            Otherwise, it will return False.
        """
        currentEditor = self.getCurrentEditor()
        if not currentEditor.saved and not currentEditor.hasContents:
            return True
        else:
            return False


class CodePad(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title('CodePad {version}'.format(version=__version__))
        self.MainWindow = CodePadMainWindow(self)
        self.MainWindow.pack(fill=tk.BOTH, expand=True)




def main():
    app = CodePad()
    app.mainloop()

if __name__ == "__main__":
    main()