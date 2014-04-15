#   CodePad
#   Python Tkinter based Code editor
#   Licensed LGPL
#   All Rights Reserved
import traceback

__author__ = 'Robert Cope'
__version__ = 'v0.2.2 (Alpha)'
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
from pygments.lexers import TextLexer, get_all_lexers, guess_lexer_for_filename, ClassNotFound, get_lexer_by_name
import pygments_tk_text.pygtext as pygtext
import pygments_tk_text.tkformatter as pygtkformatter
import sys
from functools import partial
import printer
import platform

SYSTEMTYPE = platform.system()

class CodePadEditor(tk.Frame):
    def __init__(self, root, mainwindow=None, parent=None, lexer=TextLexer(), hashFunction=hash, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.root = root
        self._filename = None
        self._hashFunction = hashFunction
        self._saved = tk.BooleanVar()
        self._saveHash = 0
        self._modified = tk.BooleanVar()
        self._modificationCallbackID = None
        self.editorFormatter = pygtkformatter.TkFormatter()
        self.editorLexer = lexer
        self.mainwindow = mainwindow if mainwindow else root
        self.parent = parent if parent else root
        self.buildTextBox()

    def buildTextBox(self):
        """
            Should be called at initialization, puts the text box and scroll bars in place.
        """
        self.textbox = pygtext.PygmentsText(self, self.editorLexer, self.editorFormatter,
                                            wrap=tk.NONE, autoseparators=False, undo=True)
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
        self.textbox.insertFormatted("end", newContent)
        self.linenumberbox.redraw()

    def setSaved(self, state):
        """
            Set the saved state (should beTrue if the file is now on disk, False othewise)
        """
        self._saved.set(state)
        self.setModifiedFalse()

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
        self.textbox.insertFormatted("end", newtext, True)
        self.linenumberbox.redraw()
        
    def undo(self):
        """
            Undo last operation to the text box.
        """
        try:
            self.textbox.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        """
            Redo last change undone on the text box.
        """
        try:
            self.textbox.edit_redo()
        except tk.TclError:
            pass

    def _on_change(self, event):
        """
            Redraw the line numberbox when we do something new.
        """
        self.linenumberbox.redraw()
        try:
            indx = self.textbox.index(tk.INSERT)
            row, col = indx.split(".", 1)
            self.mainwindow.setRow(row)
            self.mainwindow.setCol(int(col)+1)
            if self._hashFunction(self.getTextContent()) != self._saveHash:
                self._modified.set(True)
            else:
                self._modified.set(False)
        except Exception as e:
            sys.stderr.write("Exception occured: {0}".format(e))


    def getTextContent(self):
        """
            Get the content stored in the textbox
        """
        return self.textbox.get("1.0", tk.END)

    def guessLexer(self):
        """
            Call this to try to use the Pygments lexer guess function on this editor.
            The lexer will be set to whatever the best guess was.
        """
        try:
            newlexer = guess_lexer_for_filename(self.filename, self.getTextContent())
        except ClassNotFound:
            newlexer = TextLexer()
        self.setLexer(newlexer)
        return self.lexer

    def setLexer(self, lexer):
        """
            Set the Lexer to an open lexer instance, and then reformat the code highlighting.
        """
        self.editorLexer = lexer
        self.textbox.setLexer(lexer)
        self.textbox.reformatEverything()

    def setLexerByName(self, lexername):
        """
            Give a valid pygments Lexer name, and if we find it, use it as our new lexer.
            This will reformat the code highlighting.
        """
        try:
            newlexer = get_lexer_by_name(lexername.lower(), stripall=True)
        except ClassNotFound:
            sys.stderr.write("Something went really wrong getting the lexer...\n")
            sys.stderr.write("Lexer name: {0}\n".format(lexername))
            return self.lexer
        self.setLexer(newlexer)
        return self.lexer

    def setModifiedFalse(self):
        """
            Set the modification state to false, and update the save hash (this should be called on save).
        """
        self._saveHash = self._hashFunction(self.getTextContent())
        self._modified.set(False)

    def setModificationCallback(self, callback):
        """
            Allows the parent of the editor to set the callback for the modification variable.
            The callback will get called when the file is modified.
        """
        if self._modificationCallbackID:
            self._modified.trace_vdelete('w', self._modificationCallbackID)
        self._modificationCallbackID = self._modified.trace_variable('w', callback)

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
        return self._saved.get()

    @property
    def modified(self):
        """
            Return if the text in the editor has been modified recently.
        """
        return self._modified.get()

    @property
    def saveHash(self):
        """
            Return the hash that was generated when the file was last saved.
        """
        return self._saveHash

    @property
    def hasContents(self):
        """
            Return if the editor has any contents in it.
        """
        if len(self.getTextContent()) > 1:
            return True
        else:
            return False

    @property
    def lexer(self):
        return self.editorLexer

class CodePadMainWindow(tk.Frame):
    STATUSPADY = 5
    STATUSWIDTH = 10
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.openEditors = []
        self.openFiles = {}
        self.editorNotebook = ttk.Notebook(self)
        self.editorNotebook.enable_traversal()

        self.buildMenubar()
        self.editorNotebook.bind('<<NotebookTabChanged>>', self._onTabChange)

        self.statusBar = self.buildStatusBar(self)
        self.editorNotebook.grid(row=0, column=0, sticky="NSEW")
        self.statusBar.grid(row=1, column=0, sticky="EW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.addNewEditor()

    def buildMenubar(self):
        """
            Construct the Menubar for the application on start up.

            This builds up the menu bar and binds all the hot-keys associated with it.
        """
        self.menubar = tk.Menu(self)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New", command=self.addNewEditor, accelerator="Ctrl+N")
        self.root.bind('<Control-Key-n>', lambda e: self.addNewEditor())
        self.filemenu.add_command(label="Open...", command=self.openFile, accelerator="Ctrl+O")
        self.root.bind('<Control-Key-o>', lambda e: self.openFile())
        self.filemenu.add_command(label="Save", command=self.saveFile, accelerator="Ctrl+S")
        self.root.bind('<Control-Key-s>', lambda e: self.saveFile())
        self.filemenu.add_command(label="Save as...", command=self.saveFileAs, accelerator="Shift+Ctrl+S")
        self.root.bind('<Control-Key-S>', lambda e: self.saveFileAs())
        self.filemenu.add_command(label='Close Tab', command=self.closeCurrentTab, accelerator="Ctrl+W")
        self.root.bind('<Control-Key-w>', lambda e: self.closeCurrentTab())
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Print', command=self.printCurrent, accelerator="Ctrl+P")
        self.root.bind('<Control-Key-p>', lambda e: self.printCurrent())
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.root.destroy, accelerator="Ctrl+Q")
        self.root.bind('<Control-Key-q>', lambda e: self.root.destroy())
        self.menubar.add_cascade(menu=self.filemenu, label='File')

        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Undo", command=self.undoCurrent, accelerator="Ctrl+Z")
        self.root.bind('<Control-Key-z>', lambda e: self.undoCurrent())
        self.editmenu.add_command(label="Redo", command=self.redoCurrent, accelerator="Shift+Ctrl+Z")
        self.root.bind('<Control-Key-Z>', lambda e: self.redoCurrent())
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Cut", command=self.cutCurrent, accelerator="Ctrl+X")
        self.editmenu.add_command(label="Copy", command=self.copyCurrent, accelerator="Ctrl+C")
        self.editmenu.add_command(label="Paste", command=self.pasteCurrent, accelerator="Ctrl+V")
        self.root.bind('<<Paste>>', self.pasteWriteOverOverride)
        self.menubar.add_cascade(menu=self.editmenu, label='Edit')

        self.viewmenu = tk.Menu(self.menubar, tearoff=0)
        self.viewmenu.add_command(label="Find", command=self.findTextCurrent, accelerator="Ctrl+F")
        self.root.bind('<Control-Key-f>', lambda e: self.findTextCurrent())
        self.viewmenu.add_command(label="Replace", accelerator="Ctrl+R")
        self.viewmenu.add_separator()
        self.syntaxmenu = tk.Menu(self.menubar, tearoff=0)
        self.syntaxmenu.add_command(label="Guess Syntax...", command=self.guessLexer)
        self.syntaxmenu.add_separator()
        self.syntaxsubmenus, self.syntaxoptions = self.buildSyntaxSubmenus(self.syntaxmenu)
        self.viewmenu.add_cascade(label="Highlight Syntax...", menu=self.syntaxmenu)
        self.menubar.add_cascade(menu=self.viewmenu, label='View')

        #self.settingsmenu = tk.Menu(self)
        #self.settingsmenu.add_command(label="Plugins...")


        #self.menubar.add_cascade(menu=self.settingsmenu, label='Settings')

        self.projectmenu = tk.Menu(self.menubar)
        self.projectmenu.add_command(label='Run...', command=self.runCurrent, accelerator="Alt+R")
        self.root.bind('<Alt-Key-r>', lambda e: self.runCurrent())
        self.menubar.add_cascade(label='Project', menu=self.projectmenu)

        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Help Contents")
        self.helpmenu.add_command(label="About", command=self.about)

        self.menubar.add_cascade(menu=self.helpmenu, label="Help")



        self.root.config(menu=self.menubar)
        return

    def buildStatusBar(self, parent, *args, **kwargs):
        self.statusBar = tk.Frame(parent, *args, **kwargs)
        self.statusVar = tk.StringVar(self.statusBar)
        self.statusVar.set('Status Bar')
        statusLabel = tk.Label(self.statusBar, textvariable=self.statusVar, relief=tk.SUNKEN)
        statusLabel.grid(row=0, column=0, sticky="EW")


        self.colVar = tk.StringVar(self.statusBar)
        self.colVar.set('Col: 0')
        colLabel = tk.Label(self.statusBar, textvariable=self.colVar, relief=tk.SUNKEN, width=self.STATUSWIDTH)
        colLabel.grid(row=0, column=1)

        self.rowVar = tk.StringVar(self.statusBar)
        self.rowVar.set('Row: 0')
        rowLabel = tk.Label(self.statusBar, textvariable=self.rowVar, relief=tk.SUNKEN, width=self.STATUSWIDTH)
        rowLabel.grid(row=0, column=2)

        self.statusBar.grid_columnconfigure(0, weight=1)
        self.statusBar.grid_rowconfigure(0, pad=self.STATUSPADY)
        return self.statusBar

    def setStatus(self, statusMessage):
        self.statusVar.set(str(statusMessage))

    def setRow(self, row):
        self.rowVar.set('Row: {r}'.format(r=row))

    def setCol(self, col):
        self.colVar.set('Col: {c}'.format(c=col))

    def buildSyntaxSubmenus(self, rootmenu):
        syntaxsubmenus = []
        syntaxoptions = []
        currentmenu = None
        firstLetter, startLetter = None, None
        for i, lexer in enumerate(sorted(get_all_lexers())):
            if not i % 20:
                if currentmenu:

                    rootmenu.add_cascade(label="Submenu {0}-{1}".format(firstLetter, startLetter), menu=currentmenu)
                currentmenu = tk.Menu(rootmenu, tearoff=0)
                firstLetter = lexer[0][0]
                syntaxsubmenus.append(currentmenu)
            startLetter = lexer[0][0]
            newVar = tk.BooleanVar(self)
            callback = partial(self.setLexer, lexer[0])
            syntaxoptions.append((lexer[0], newVar, callback))
            currentmenu.add_checkbutton(label=lexer[0], variable=newVar, command= callback)

        rootmenu.add_cascade(label="Submenu {0}-{1}".format(firstLetter, startLetter), menu=currentmenu)
        return syntaxsubmenus, syntaxoptions


    def addNewEditor(self, filename=None):
        """
            Opens a new editor tab.
            If filename is specified, we will try and open in in ASCII mode and use it to fill the new textbox.
        """
        ed = CodePadEditor(self.root, self, self.editorNotebook)
        self.openEditors.append(ed)
        if not filename:
            ed.setFileName("Untitled")
        else:
            try:
                contents = """"""
                with open(filename, 'rb') as f:
                    contents += f.read()
                try:
                    newcontents = contents.encode('utf-8')
                except UnicodeDecodeError:
                    tkMessageBox.showwarning('Non-UTF-8 Characters', 'Non-UTF-8 characters were detected in this file.\n'
                                                                     'Loading will proceed with these replaced.\n'
                                                                     'Continue at your own risk!', parent=self)
                    try:
                        newcontents = contents.encode('utf-8', 'xmlcharrefreplace')
                    except UnicodeDecodeError:
                        tkMessageBox.showerror('Non-UTF-8 Characters', 'Non-UTF-8 characters were detected in this file.\n'
                                                                     'Loading could not replace characters.\n'
                                                                     'Bad characters will be ignored!\n'
                                                                     'Continue at your own risk!', parent=self)
                        newcontents = contents.encode('utf-8', 'ignore')
                contents = newcontents
            except:
                tkMessageBox.showerror('Could not read file!', 'Failed to read file correctly!\n'
                                                               'You may have selected a non-text file.\n')
                contents = ''
                traceback.print_exc()
            ed.setFileName(filename)
            ed.setSaved(True)
            ed.setTextContent(contents)
            ed.guessLexer()
            ed.setModifiedFalse()
            ed.setModificationCallback(self.currentTabModified)
        self.editorNotebook.add(ed, sticky="NSEW")
        self.setTabTitle(ed, ed.filename)
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
        filename = tkFileDialog.askopenfilename(parent=self,
                                                filetypes=[("All Files", "*"), ("Plaintext File", "*.txt"),
                                                           ("Python Script", "*.py"), ("Ruby Script", "*.rb")])
        if not filename:
            return
        if filename not in self.openFiles:
            self._openFile(filename)
        else:
            self.selectEditor(self.openFiles[filename])

    def loadFiles(self, args):
        """
            This loads a list of files, and should be called at startup.
        """
        for filename in args:
            self._openFile(filename)

    def _openFile(self, filename):
        """
            The private method for loading files into new editors.
        """
        oldeditor = self.getCurrentEditor()
        closeOld = self.isCurrentEmpty
        ed = self.addNewEditor(filename)
        self.openFiles[filename] = ed
        if closeOld:
            self._closeTab(oldeditor)

    def getCurrentEditor(self):
        """
            Grab the current focused editor instance.
        """
        return self.openEditors[self.editorNotebook.index(self.selectEditor())] if self.openEditors else None

    def saveFile(self):
        """
            This is the call back for the regular save in File, (also Ctrl+S). Should spawn a save dialog and
            save the file to disk, if the user doesn't cancel.
        """
        currentEditor = self.getCurrentEditor()
        if not currentEditor.saved:
            return self.saveFileAs()
        else:
            with open(currentEditor.filename, 'w') as f:
                f.write(currentEditor.getTextContent())
            currentEditor.setModifiedFalse()
            return True

    def saveFileAs(self):
        """
            Let the user select to save the file as (then save the file).
        """
        currentEditor = self.getCurrentEditor()
        filename = tkFileDialog.asksaveasfilename()
        if not filename:
            return False
        currentEditor.setFileName(filename)
        currentEditor.setSaved(True)
        self.setTabTitle(currentEditor, filename)
        self.guessLexer()
        with open(currentEditor.filename, 'w') as f:
            f.write(currentEditor.getTextContent())
        currentEditor.setModifiedFalse()
        return True

    def printCurrent(self):
        currentEditor = self.getCurrentEditor()
        if SYSTEMTYPE == 'Linux':
            if not currentEditor.saved or currentEditor.modified:
                if not self.saveFile():
                    tkMessageBox.showwarning('Save File to Print!', 'File must be saved to print!', parent=self)
                    return
            printDialog = printer.PrintDialogLinux(self, currentEditor.filename)
            self.wait_window(printDialog)
        elif SYSTEMTYPE == 'Windows':
            printDialog = printer.PrintDialogLinux(self, currentEditor.getTextContent())
            self.wait_window(printDialog)
        else:
            tkMessageBox.showerror('Printing Not Supported!', 'Printing not supported on this platform!', parent=self)

    def setTabTitle(self, ed, title):
        """
            Set the tab title for the specified editor.
        """
        self.editorNotebook.tab(ed, text=title)

    def currentTabModified(self, *args):
        """
            This is the callback for when the modified variable of the current variable changes.
            This allows us to indicate that the file has changed in the tab title.
        """
        currentEditor = self.getCurrentEditor()
        if currentEditor.modified:
            self.setTabTitle(currentEditor, "*{0}".format(currentEditor.filename))
        else:
            self.setTabTitle(currentEditor, currentEditor.filename)

    def undoCurrent(self):
        """
            Undo last operation on current editor
        """
        currentEditor = self.getCurrentEditor()
        currentEditor.undo()

    def redoCurrent(self):
        currentEditor = self.getCurrentEditor()
        currentEditor.redo()

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

    def cleanUpOnClose(self):
        for editor in self.openEditors:
            if editor.modified:
               self.selectEditor(editor)
               if tkMessageBox.askyesno('Save File Modified File?', 'Save this file before closing?', parent=self):
                   self.saveFile()
            else:
                self._closeTab(editor)

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

    def _onTabChange(self, event):
        currentEditor = self.getCurrentEditor()
        if currentEditor:
            currentLexer = currentEditor.lexer
            self.setLexerSelected(currentLexer)
        else:
            sys.stderr.write('_onTabChange called without an open editor..')
        self.setRootTitleFilename(currentEditor.filename)

    def setRootTitleFilename(self, filename):
        """
            Sets the root window title to have the filename then the editor title string.
        """
        self.root.wm_title('{0} - {1}'.format(filename, self.root.TITLESTRING))

    def setLexer(self, lexername):
        currentEditor = self.getCurrentEditor()
        if currentEditor:
            newLexer = currentEditor.setLexerByName(lexername)
            self.setLexerSelected(newLexer)
        else:
            sys.stderr.write('setLexer called without an open editor..')

    def guessLexer(self):
        currentEditor = self.getCurrentEditor()
        if currentEditor:
            newLexer = currentEditor.guessLexer()
            self.setLexerSelected(newLexer)
        else:
            sys.stderr.write('guessLexer called without an open editor..')

    def setLexerSelected(self, lexer):
        name = lexer.name
        for option in self.syntaxoptions:
            if option[0] == name:
                option[1].set(True)
            else:
                option[1].set(False)

    def runCurrent(self):
        """
            Save the current file, let the user specify the interpreter, and try to run the code in a new window.
        """
        if self.saveFile():
            interpreter = tkSimpleDialog.askstring('Set Interpreter',
                                             'Set the interpreter to run the code',
                                             initialvalue='python', parent=self)
            if interpreter and SYSTEMTYPE == 'Linux':
                subprocess.Popen('xterm -hold -T {title} -e {intrp} {fn}'
                                 ''.format(intrp=interpreter, fn=self.getCurrentEditor().filename,
                                           title="\"CodePad Code Run\""),
                                 shell=True)
            elif interpreter and SYSTEMTYPE == 'Windows':
                subprocess.Popen('cmd.exe /K /u {intrp} {fn}'.format(intrp=interpreter,
                                                                     fn=self.getCurrentEditor().filename), shell=True)
            elif interpreter:
                tkMessageBox.showerror('Run Not Supported!', 'Run not supported on this platform', parent=self)
        else:
            tkMessageBox.showerror('Run Error', 'Must save the file in order to be run!')

    def findTextCurrent(self):
        """
            Open a dialog to find text in the current editor.
        """
        currentEditor = self.getCurrentEditor()
        extrawidgets.textFindWidget(self.root, currentEditor, self)

    def about(self):
        """
            Show the about box.
        """
        aboutMsg = "CodePad Version {version}\nWritten 2014 by Robert Cope".format(version=__version__)
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
    @staticmethod
    def pasteWriteOverOverride(event):
        try:
            event.widget.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass #We didn't have anything selected.





class CodePad(tk.Tk):
    TITLESTRING = 'CodePad {version}'.format(version=__version__)
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title(self.TITLESTRING)
        self.MainWindow = CodePadMainWindow(self)
        self.MainWindow.pack(fill=tk.BOTH, expand=True)

    def cmdLineArgs(self, args):
        self.MainWindow.loadFiles(args)

    def destroy(self):
        self.MainWindow.cleanUpOnClose()
        tk.Tk.destroy(self)


def main(args):
    app = CodePad()
    app.cmdLineArgs(args)
    app.minsize(800, 600)
    app.mainloop()

if __name__ == "__main__":
    main(sys.argv[1:])
