
###############################################################################
# Object-Oriented VHDL Units representation
###############################################################################

TAB = 2

GENERATE_STATEMENTS = ['if-generate', 'for-generate']


def print_children(element):
    print(' ' * element.indentation + str(element))
    if element.children:
        for child in element.children:
            print_children(child)




class Unit:
    def __init__(self, name, parent, indentation):
        self.name = name
        self.parent = parent
        self.indentation = indentation

    def print_children(self):
        print_children(self)



class Generate(Unit):

    def __init__(self, name, parent, indentation, value, generates=None, instances=None):
        super().__init__(name, parent, indentation)
        self.value = value
        self.generates = generates or []
        self.instances = instances or []
        setattr(parent, name, self)
        parent.generates.append(self)


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return self.generates + self.instances




class Entity(Unit):

    def __init__(self, name, parent, indentation, arch='', generates=None, instances=None,
                 ports=None, signals=None, processes=None):
        super().__init__(name, parent, indentation)
        self.arch = arch
        self.generates = generates or []
        self.instances = instances or []
        self.ports = ports or []
        self.signals = signals or []
        self.processes = processes or []
        setattr(parent, name, self)
        parent.entity = self


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return self.generates + self.instances




class Instance(Unit):

    def __init__(self, name, indentation, parent=None, entity=None):
        super().__init__(name, parent, indentation)
        self.entity = entity or {}
        if parent:
            setattr(parent, name, self)
            parent.instances.append(self)


    def __repr__(self):
        return self.type + ' ' + self.name

    def __str__(self):
        return self.name


    @property
    def type(self):
        return self.__class__.__name__


    @property
    def children(self):
        return [self.entity]




class Top(Instance):
      def __init__(self, name, packages=None):
        super().__init__(name, parent=None, indentation=-TAB)
        self.packages = packages or []
