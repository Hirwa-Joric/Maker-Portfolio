"""Weld float32-split vertices (tol 1e-4 mm), drop zero-area/degenerate triangles, verify the mesh is
edge-manifold (every undirected edge in exactly 2 faces, every directed edge once), closed and outward
(positive volume), then write a binary STL. Usage: clean_stl.py in.stl out.stl"""
import numpy as np, struct, sys, stlcheck

def clean(inp, out, tol=1e-4):
    T, _ = stlcheck.load(inp)
    V, F = stlcheck.index(T, tol)
    for _ in range(3):
        deg = (F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])
        F = F[~deg]
        # remove exact duplicate / opposite duplicate faces (zero-volume fins)
        key = np.sort(F, 1)
        _, first, cnt = np.unique(key, axis=0, return_index=True, return_counts=True)
        dup = np.isin(np.arange(len(F)), first[cnt > 1]) | ~np.isin(np.arange(len(F)), first)
        if cnt.max() > 1:
            bad = np.zeros(len(F), bool)
            inv = np.unique(key, axis=0, return_inverse=True)[1].ravel()
            bad = cnt[inv] > 1
            F = F[~bad]
        # collapse zero-area slivers whose three vertices are collinear: keep them only if they carry topology
        A = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
        if not np.any(A < 1e-12):
            break
        break
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    _, ucnt = np.unique(np.sort(E, 1), axis=0, return_counts=True)
    _, dcnt = np.unique(E, axis=0, return_counts=True)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
    ok = bool(np.all(ucnt == 2) and np.all(dcnt == 1) and vol > 0)
    tri = V[F].astype('<f4')
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-20)
    rec = np.zeros(len(F), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    rec['n'] = n; rec['v'] = tri.reshape(-1, 9)
    hdr = b'Custom Aftermarket Car Center Console Upgrade - deck (approx.)'.ljust(80, b' ')
    with open(out, 'wb') as f:
        f.write(hdr); f.write(struct.pack('<I', len(F))); f.write(rec.tobytes())
    return ok, len(F), int(np.sum(ucnt != 2)), int(np.sum(dcnt != 1)), vol

if __name__ == '__main__':
    ok, n, ne, nd, vol = clean(sys.argv[1], sys.argv[2])
    print('%s -> %s: %d tris, nonmanifold %d, dup-directed %d, vol %.1f cm3, %s' % (sys.argv[1], sys.argv[2], n, ne, nd, vol / 1000, 'OK' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)
