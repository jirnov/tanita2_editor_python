try:
    import Tanita2
    from Tanita2 import *
except: pass

class Fonts(Tanita2.GameObject):
    '''
    Fonts collection
    '''
    class DummySequence:
        def play(self):
            pass
        def render(self):
            pass
    
    def __init__(self):
        Tanita2.GameObject.__init__(self)
        self.states = {}
        self.sequences = {}
        self.state = '__empty__'
        from Overrides import Smeshfont
        self.metrics = (Smeshfont.LettersHeight, Smeshfont.LettersWidth)
        self.lines = []
        self.renderers = []
        import Core
        self.fonts = {}
        self.loadFonts()


    def loadFonts(self):
        import Core, Tanita2
        origResourceId = Tanita2.ResourceId
        class changedResourceId(origResourceId):
            def __init__(self, name, id):
                self.data = (name, id)
                origResourceId.__init__(self, name, id)
        Core.ResourceId = changedResourceId
        Tanita2.ResourceId = changedResourceId
        from World.Common.FontsLayer.FontsPackage import Fonts as FontPackage
        class FontsCollection(FontPackage):
            def add_sequence(this, name, resourceId, frames, flag):
                self.fonts[name] = origResourceId(*resourceId.data)
                FontPackage.add_sequence(this, name, resourceId, frames, flag)
        FontsCollection().construct()
        Core.ResourceId = origResourceId
        Tanita2.ResourceId = origResourceId
    

    def add_sequence(self, name, path, frames, flag):
        self.sequences[name] = self.DummySequence()


    def get_text_width(self, text):
        width = 0
        for c in text:
            width += self.metrics[1][ord(c)]
        return width


    def get_text_height(self, text):
        return len(text.split("\n")) * self.metrics[0]
    

    def get_width(self, name):
        return self.metrics[name][1]


    def get_height(self):
        return self.metrics[0]


    def get_path(self, name):
        return self.fonts[name]
        

    def setText(self, text, color='White'):
        assert color in ('Green', 'White', 'Blue'), "Color must be 'Green', 'White' or 'Blue'"
        fontName = color
        self.lines = text.split('\n')
        if len(self.lines) > len(self.renderers):
            for i in xrange(len(self.renderers), len(self.lines)):
                fontRender = self.objects['font%d' % i] = Tanita2.TextRenderObject()
                fontRender.loadFont(self.get_path(fontName), self.metrics[1])
                self.renderers.append(fontRender)
                fontRender.position = vec2(0, i * self.metrics[0])
        for i in xrange(len(self.renderers)):
            if i >= len(self.lines):
                self.renderers[i].setText("")
            else:
                self.renderers[i].setText(self.lines[i])
