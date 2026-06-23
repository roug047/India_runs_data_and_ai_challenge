# does the ranking chain actually import scipy/sklearn anywhere?
import ast, os
def deep_imports(path, seen=None):
    if seen is None: seen=set()
    if path in seen or not os.path.exists(path): return set()
    seen.add(path)
    t = ast.parse(open(path,encoding="utf-8").read())
    out=set()
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names: out.add(a.name.split(".")[0])
        elif isinstance(n,ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
    return out
chain=["rank.py","stage7/scoring.py","stage7/reasoning.py","stage5/composite.py","common/io.py","common/config.py"]
allimp=set()
for f in chain: allimp|=deep_imports(f)
print("scipy needed:", "scipy" in allimp)
print("sklearn needed:", "sklearn" in allimp)
print("full set:", sorted(allimp))