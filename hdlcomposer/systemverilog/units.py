


###############################################################################
# Object-Oriented SystemVerilog Units representation
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
