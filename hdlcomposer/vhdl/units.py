TAB = 2
GENERATE_STATEMENTS = ['if-generate', 'for-generate']



###############################################################################
# Object-Oriented VHDL Units representation
###############################################################################

class Unit():
    """ Base unit with common properties
    """

    def __init__(self, name, parent, indentation):
        self.name = name
        self.parent = parent
        self.indentation = indentation



    @property
    def type(self):
        return self.__class__.__name__



    def __repr__(self):
        return self.type + ' ' + self.name



    def __str__(self):
        return self.name



    @property
    def children(self):
        return []



    def print_children(self):
        self.print_hierarchy(self)



    @staticmethod
    def print_hierarchy(element):
        print(' ' * element.indentation + str(element))
        if element.children:
            for child in element.children:
                element.print_hierarchy(child)



class Generate(Unit):
    """ if-generate or for-generate statements
    """

    def __init__(self, name, parent, indentation, value, generates=None,
                 instances=None, processes=None):
        super().__init__(name, parent, indentation)
        self.value = value
        self.generates = generates or []
        self.instances = instances or []
        self.processes = processes or []
        setattr(parent, name, self)
        parent.generates.append(self)



    @property
    def children(self):
        return self.generates + self.instances



class Entity(Unit):
    """ VHDL entity
    """

    def __init__(self, name, parent, indentation, arch='', generates=None,
                 instances=None, ports=None, signals=None, processes=None):
        super().__init__(name, parent, indentation)
        self.arch = arch
        self.generates = generates or []
        self.instances = instances or []
        self.ports = ports or []
        self.signals = signals or []
        self.processes = processes or []
        setattr(parent, name, self)
        parent.entity = self



    @property
    def children(self):
        return self.generates + self.instances



class Instance(Unit):
    """ Instance of a VHDL entity
    """

    def __init__(self, name, indentation, parent=None, entity=None, ports=None):
        super().__init__(name, parent, indentation)
        self.entity = entity or {}
        self.ports = ports or []
        if parent:
            setattr(parent, name, self)
            parent.instances.append(self)



    @property
    def children(self):
        return [self.entity]



class Process(Unit):
    """ VHDL process
    """

    def __init__(self, name, indentation, parent=None):
        super().__init__(name, parent, indentation)
        if parent:
            setattr(parent, name, self)
            parent.processes.append(self)



class Port(Unit):
    """ VHDL port
    """

    def __init__(self, name, indentation, direction, parent=None):
        self.direction = direction
        super().__init__(name, parent, indentation)
        if parent:
            setattr(parent, name, self)
            parent.ports.append(self)



class Signal(Unit):
    """ VHDL signal
    """

    def __init__(self, name, indentation, parent=None):
        super().__init__(name, parent, indentation)
        if parent:
            setattr(parent, name, self)
            parent.signals.append(self)



class Top(Instance):
    """ Top entity
    """

    def __init__(self, name, packages=None):
        super().__init__(name, parent=None, indentation=-TAB)
        self.packages = packages or []
