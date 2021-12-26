
from networkml import config

config.set_log_config("log4p.conf")


from networkml.network import NetworkClass, ExtensibleWrappedAccessor, NetworkClassInstance, NetworkInstance
from networkml.network import NetworkMethod, NetworkCallable
from networkml.lexer import NetworkParser, NetworkParserError
from networkml.specnetwork import SpecValidator
import traceback

script = """
function fibo(i) {
  //print("i=", i);
  if (i==1) {
    return 1;
  } elif (i==0) {
    print("return 0");
    return 0;
  } else {
    b = i - 1;
    x = fibo(b);
    a = i - 2;
    y = fibo(a);
    r = x + y;
    return r;
  }
}
//print("fibo[0]=", fibo(0));
//print("fibo[1]=", fibo(1));
print("-------------------");
print("fibo[2]=", fibo(2));
print("-------------------");

//print("hello");
"""
try:
    from networkml.network import ExtensibleWrappedAccessor

    meta = NetworkClass(None, "GCScriptClass")
    clazz_sig = "{}[{}]".format("NetworkML", 1)
    embedded = ()
    args = ()
    clazz = meta(meta, (clazz_sig, embedded, args))
    sig = "{}.{}".format(clazz.signature, clazz.next_instance_id)
    initializer_args = ()
    toplevel: NetworkInstance = clazz(clazz, (sig, (), initializer_args))
    toplevel.set_stack_enable(True)
    # validator/evaluator
    validator = SpecValidator(owner=toplevel)
    toplevel.set_validator(validator)
    # methods
    printer = ExtensibleWrappedAccessor(toplevel, "print", None,
                                        lambda ao, c, eo, ca, ea: print(" ".join([str(_) for _ in ca])),
                                        globally=True)
    toplevel.declare_method(printer, globally=True)
    append = ExtensibleWrappedAccessor(toplevel, "append", None,
                                       lambda ao, c, eo, ca, ea: ca[0].append(ca[1]),
                                       globally=True)
    toplevel.declare_method(append, globally=True)
    length = ExtensibleWrappedAccessor(toplevel, "len", None,
                                       lambda ao, c, eo, ca, ea: len(ca[0]),
                                       globally=True)
    toplevel.declare_method(length, globally=True)
    keys = ExtensibleWrappedAccessor(toplevel, "keys", None,
                                     lambda ao, c, eo, ca, ea: ca[0].keys())
    toplevel.declare_method(keys, globally=True)
    # parse
    parser = NetworkParser(toplevel)
    ret = parser.parse_script(script)
    for r in ret:
        if isinstance(r, NetworkClassInstance):
            toplevel.declare_class(r, globally=True)
            print('class {} declared.'.format(r))
        elif isinstance(r, NetworkMethod):
            toplevel.declare_method(r, globally=True)
            print('method {} declared.'.format(r.signature))
        elif isinstance(r, NetworkCallable):
            # rtn = r(toplevel)
            # self.reporter.report(str(rtn))
            r(toplevel)
        else:
            pass
except Exception as ex:
    print(traceback.format_exc())
