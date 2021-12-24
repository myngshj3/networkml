
import inspect
import networkml.genericutils as GU


class Hello:
    def __init__(self):
        self.vars = {}
        pass

    def get_var(self, name: str, value: int, what: float):
        if name in self.vars.keys():
            return self.vars[name]
        return None

    def analyze_self(self):
        I = inspect.getmembers(self, inspect.ismethod)
        for n, m in I:
            sig = inspect.signature(m)
            print(n, sig.return_annotation, sig.parameters, self.__class__)


# H = Hello()
# H.analyze_self()

tree = GU.read_xml("app/SpecificationGraph.desc.xml")
root = tree.getroot()
for m in root:
    print(m)
#    print(m)
