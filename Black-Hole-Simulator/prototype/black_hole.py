"""A still image of a black hole, ray-marched in Python with NumPy.

A CPU teaching companion to the interactive renderer, prepared alongside the
current program rather than retained as an early source file. It shows a flat
disk of one colour family, no Doppler shift, no tone mapping, and one still frame
written as a PNG. The interactive GPU tracer is in ../sim/shaders/trace.frag.

Each pixel's ray stays in one plane through the hole. In that plane the path
obeys the photon orbit equation of Schwarzschild spacetime,

    d^2u/dphi^2 + u = (3/2) u^2,     u = r_s / r,

which is integrated with fourth-order Runge-Kutta steps in the angle phi.
For simplicity the camera's viewing direction is used directly as a
coordinate direction (the C++ version corrects for the camera's position).

Usage:  python3 black_hole.py [WIDTH HEIGHT]     writes black_hole.png
"""
import struct
import sys
import time
import zlib

import numpy as np

CAMERA_DISTANCE = 20.0          # Schwarzschild radii
CAMERA_POLAR_DEG = 80.0         # 90 would be exactly in the disk plane
FIELD_OF_VIEW_DEG = 60.0
DISK_INNER, DISK_OUTER = 3.0, 10.0
EXIT_RADIUS = 60.0
MAX_STEPS = 4000


def camera_rays(width, height):
    polar = np.radians(CAMERA_POLAR_DEG)
    eye = CAMERA_DISTANCE * np.array([np.sin(polar), np.cos(polar), 0.0])
    ahead = -eye / np.linalg.norm(eye)
    right = np.cross(ahead, [0.0, 1.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, ahead)
    t = np.tan(np.radians(FIELD_OF_VIEW_DEG) / 2)
    xs = (2 * (np.arange(width) + 0.5) / width - 1) * t * width / height
    ys = (1 - 2 * (np.arange(height) + 0.5) / height) * t
    sx, sy = np.meshgrid(xs, ys)
    d = ahead + sx[..., None] * right + sy[..., None] * up
    return eye, (d / np.linalg.norm(d, axis=-1, keepdims=True)).reshape(-1, 3)


def orbit_slope(u, w):
    """(du/dphi, dw/dphi) for the photon orbit equation, with w = du/dphi."""
    return w, 1.5 * u * u - u


def trace(eye, directions):
    n = len(directions)
    r0 = np.linalg.norm(eye)
    e1 = np.broadcast_to(eye / r0, (n, 3))
    # the ray's plane: e1 points from the hole to the camera, e2 along the ray's sideways motion
    radial = directions @ (eye / r0)
    sideways = directions - radial[:, None] * e1
    b = np.linalg.norm(sideways, axis=1)
    straight = b < 1e-9
    e2 = sideways / np.where(straight, 1.0, b)[:, None]

    u = np.full(n, 1.0 / r0)
    w = -u * radial / np.where(straight, 1.0, b)    # du/dphi from the starting direction
    phi = np.zeros(n)
    position = np.broadcast_to(eye, (n, 3)).copy()

    colour = np.zeros((n, 3))
    active = ~straight      # a ray aimed exactly at the hole falls straight in and stays black

    for _ in range(MAX_STEPS):
        idx = np.nonzero(active)[0]
        if idx.size == 0:
            break
        ui, wi = u[idx], w[idx]
        h = 0.02 / (1.0 + np.abs(wi) / ui)          # smaller angle steps when r changes quickly
        k1u, k1w = orbit_slope(ui, wi)
        k2u, k2w = orbit_slope(ui + 0.5 * h * k1u, wi + 0.5 * h * k1w)
        k3u, k3w = orbit_slope(ui + 0.5 * h * k2u, wi + 0.5 * h * k2w)
        k4u, k4w = orbit_slope(ui + h * k3u, wi + h * k3w)
        u[idx] = ui + h / 6 * (k1u + 2 * k2u + 2 * k3u + k4u)
        w[idx] = wi + h / 6 * (k1w + 2 * k2w + 2 * k3w + k4w)
        phi[idx] += h

        before = position[idx]
        safe_u = np.maximum(u[idx], 1e-6)
        after = (np.cos(phi[idx])[:, None] * e1[idx] + np.sin(phi[idx])[:, None] * e2[idx]) / safe_u[:, None]
        position[idx] = after

        # crossing the disk plane (y = 0) between 3 and 10 r_s: a flat, opaque disk
        crossed = before[:, 1] * after[:, 1] < 0
        t = before[:, 1] / np.where(crossed, before[:, 1] - after[:, 1], 1.0)
        hit = before + t[:, None] * (after - before)
        rho = np.hypot(hit[:, 0], hit[:, 2])
        on_disk = crossed & (rho >= DISK_INNER) & (rho <= DISK_OUTER)
        glow = (DISK_INNER / rho[on_disk]) ** 2
        colour[idx[on_disk]] = glow[:, None] * np.array([1.0, 0.62, 0.28])

        fell = (u[idx] >= 1.0) | ((u[idx] > 2 / 3) & (w[idx] > 0))   # inside 1.5 r_s heading in
        escaped = (u[idx] < 1.0 / EXIT_RADIUS) & (w[idx] < 0)
        if escaped.any():
            out = after[escaped] - before[escaped]
            colour[idx[escaped]] = stars(out / np.linalg.norm(out, axis=1, keepdims=True))
        active[idx[on_disk | fell | escaped]] = False
    return colour


def stars(directions):
    """A sparse field of white stars, fixed to directions in the sky."""
    cells = np.floor(directions * 160).astype(np.int64)
    key = (cells[:, 0] * 73856093) ^ (cells[:, 1] * 19349663) ^ (cells[:, 2] * 83492791)
    bright = (key % 997) < 4
    return bright[:, None] * np.array([0.9, 0.9, 1.0])


def write_png(path, rgb):
    height, width, _ = rgb.shape
    rows = b"".join(b"\x00" + rgb[y].tobytes() for y in range(height))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(rows, 9)))
        f.write(chunk(b"IEND", b""))


def main():
    width, height = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (320, 180)
    start = time.time()
    eye, directions = camera_rays(width, height)
    colour = trace(eye, directions).reshape(height, width, 3)
    image = (np.clip(colour, 0.0, 1.0) * 255).astype(np.uint8)  # no tone mapping: bright gas just clips
    write_png("black_hole.png", image)
    print(f"wrote black_hole.png ({width}x{height}) in {time.time() - start:.1f} s")


if __name__ == "__main__":
    main()
