"""Binary/ASCII STL loader + watertightness checks (edge-manifold, orientation, components, genus, volume)."""
import numpy as np, struct, sys

def load(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[80:84])[0] if len(b) >= 84 else 0
    if len(b) == 84 + n * 50:
        a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
        return a['v'].reshape(-1, 3, 3).astype(float), 'binary'
    V = []
    for line in b.decode(errors='ignore').splitlines():
        t = line.split()
        if t and t[0] == 'vertex':
            V.append([float(t[1]), float(t[2]), float(t[3])])
    return np.array(V).reshape(-1, 3, 3), 'ascii'

def index(T, tol=1e-5):
    P = T.reshape(-1, 3)
    key = np.round(P / tol).astype(np.int64)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    V = np.zeros((len(uniq), 3))
    np.add.at(V, inv, P)
    cnt = np.bincount(inv)
    V /= cnt[:, None]
    F = inv.reshape(-1, 3)
    return V, F

def check(path, verbose=True):
    T, fmt = load(path)
    V, F = index(T)
    deg = (F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])
    Fd = F[~deg]
    E = np.vstack([Fd[:, [0, 1]], Fd[:, [1, 2]], Fd[:, [2, 0]]])
    und = np.sort(E, axis=1)
    _, ucnt = np.unique(und, axis=0, return_counts=True)
    _, dcnt = np.unique(E, axis=0, return_counts=True)
    nonman = int(np.sum(ucnt != 2))
    dupdir = int(np.sum(dcnt > 1))
    # components (union-find on faces via vertices)
    parent = np.arange(len(V))
    def find(x):
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r
    for a, b_, c in Fd:
        ra, rb, rc = find(a), find(b_), find(c)
        parent[rb] = ra; parent[find(rc)] = ra
    roots = np.array([find(v) for v in range(len(V))])
    used = np.unique(Fd)
    comps = np.unique(roots[used])
    # signed volume
    a, b_, c = V[Fd[:, 0]], V[Fd[:, 1]], V[Fd[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b_, c)).sum() / 6
    nE = len(np.unique(und, axis=0)); nV = len(used); nF = len(Fd)
    chi = nV - nE + nF
    genus = (2 * len(comps) - chi) / 2
    lo, hi = V[used].min(0), V[used].max(0)
    res = dict(file=path.split('/')[-1], fmt=fmt, tris=len(F), degenerate=int(deg.sum()), nonmanifold_edges=nonman,
               dup_directed_edges=dupdir, components=len(comps), genus=genus, volume_cm3=vol / 1000,
               bbox_min=np.round(lo, 2).tolist(), bbox_max=np.round(hi, 2).tolist())
    res['watertight'] = (nonman == 0 and dupdir == 0 and vol > 0)
    if verbose:
        print(res)
    return res

if __name__ == '__main__':
    for p in sys.argv[1:]:
        check(p)
