# Python prototype

[black_hole.py](black_hole.py) is a small CPU teaching companion to the interactive simulator. Each pixel's ray is followed with the photon orbit equation u″ + u = 3/2 u² and fourth-order Runge–Kutta steps. The disk is flat and opaque, there is no Doppler shift or tone mapping, and the result is one PNG. This example was prepared alongside the current program to explain the basic approach; it is not an archived early source file.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python black_hole.py          # writes black_hole.png (320 x 180)
.venv/bin/python black_hole.py 640 360  # larger
```

The C++ program in [../sim/](../sim/) provides the interactive GPU renderer.
