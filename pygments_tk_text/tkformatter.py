from pygments.formatter import Formatter
import string

class TkFormatter(Formatter):
    
    """A Pygments formatter that creates tags suitable for use in Tkinter.Text objects.
    
    A naive implemenation that attempts to handle neither string encodings
    (unicode/bytes/UTF-8 etc) nor Python 3 vs Python 2 issues. Tested only on
    Python 2.7 and Mac OS X. No unit tests. Works, but at the proof-of-concept
    rather than polished-product level."""


    def __init__(self, **options):
        Formatter.__init__(self, **options)

        # create a dict of tagName: [(attname, attval), .. } values for use in later formatting
        # method later
        self.styles = {}
        self.tktags = {} # parallel to self.styles, but with tagNames
        
        # Prepare a token & tagName -> style mapping
        for token, style in self.style:
            tagName = self.tokenToTagName(token)
            tkStyle = self.pygmentsStyleToTkStyle(style)
            self.styles[token]   = True     # self.format() doesn't need a token ->
                                            # rendered style mapping, just to know
                                            # whether one exists
            self.tktags[tagName] = tkStyle  # But the calling Tk Text object will need
                                            # the style details


    def pygmentsStyleToTkStyle(self, style):
        """Given a pygments style definition, return a list of tuples suitable
        for setting the attributes of an equivalent / very similar Tk Text tag (ie, a Tk style)."""
        
        tkatts = []
        if style['underline']: tkatts.append( ( 'underline', True ) )
        if style['color']:     tkatts.append( ( 'foreground', "#%s" % style['color'] ) )
        if style['bgcolor']:   tkatts.append( ( 'background', "#%s" % style['bgcolor'] ) )
        if style['border']:    pass # TBD
        
        fontspec = []
        if style['bold']:   fontspec.append('bold')
        if style['italic']: fontspec.append('italic')
        if style['mono']:   pass # TBD
        if style['sans']:   pass # TBD
        if style['roman']:  pass # TBD
        
        tkatts.append( ( 'font', ' '.join(fontspec) ) )
        
        # NB unlike the other attributes, font specs aren't the full
        # specification, because we don't know what the Tk Text base font is.
        # These attributes will need to be combined with, rather than overwrite,
        # Tk's existing font spec
        
        return tkatts
    

    def get_style_defs(self, arg=""):
        """Called by the client (a Tk Text object) to learn what styles to use."""
        return self.tktags
    
    
    def tokenToTagName(self, token):
        """Tokens are pygments 'style names' or 'style classes'. Here we
        translate between pygments tokens and Tk's Text equivalent 'tag' names."""
        
        if token is None:
            return "None"
        tagName = string.replace(str(token), ".", "") 
        tagName = string.replace(tagName, "Token", "pygments.", 1)  
        return tagName

        
    def tkTaggedStr(self, s, token):
        """Return a tag:quoted-string\n string that a Tk Text element can easily
        use. Note that s may come in as unicode string, so down-code back to str
        (at least for Python 2.7)"""
        
        tagName = self.tokenToTagName(token) or ""
        s = string.replace(s, "\n", "\\n")
        taggedStr = tagName + ':' + s + "\n"
        return str(taggedStr)
        

    def format(self, tokensource, outfile):
        # lastval is a string we use for caching
        # because it's possible that an lexer yields a number
        # of consecutive tokens with the same token type.
        # to minimize the size of the generated markup we
        # try to join the values of same-type tokens here
        
        lastval = ''
        lasttype = None
        
        for ttype, value in tokensource:
            # if the token type doesn't exist in the stylemap
            # we try it with the parent of the token type
            # eg: parent of Token.Literal.String.Double is
            # Token.Literal.String
            while ttype not in self.styles:
                ttype = ttype.parent
            if ttype == lasttype:
                # the current token type is the same of the last
                # iteration. cache it
                lastval += value
            else:
                # not the same token as last iteration, but we
                # have some data in the buffer. wrap it with the
                # defined style and write it to the output file
                if lastval:
                    tkstr = self.tkTaggedStr(lastval, lasttype)
                    outfile.write(tkstr)
                # set lastval/lasttype to current values
                lastval = value
                lasttype = ttype

        # we're done; if something's left in the buffer, write it now
        if lastval:
            tkstr = self.tkTaggedStr(lastval, ttype)
            outfile.write(tkstr)

