__author__ = 'Robert Cope'
__version__ = 'v0.2'

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
import ttk

from pygments.formatter import Formatter

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

#From StackOverflow http://stackoverflow.com/questions/16369470/tkinter-adding-line-number-to-text-widget
class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)

#From StackOverflow http://stackoverflow.com/questions/16369470/tkinter-adding-line-number-to-text-widget
class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        self.tk.eval('''
            proc widget_proxy {widget widget_command args} {

                # call the real tk widget command with the real args
                set result [uplevel [linsert $args 0 $widget_command]]

                # generate the event for certain types of commands
                if {([lindex $args 0] in {insert replace delete}) ||
                    ([lrange $args 0 2] == {mark set insert}) ||
                    ([lrange $args 0 1] == {xview moveto}) ||
                    ([lrange $args 0 1] == {xview scroll}) ||
                    ([lrange $args 0 1] == {yview moveto}) ||
                    ([lrange $args 0 1] == {yview scroll})} {

                    event generate  $widget <<Change>> -when tail
                }

                # return the result from the real widget command
                return $result
            }
            ''')
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(self)))

