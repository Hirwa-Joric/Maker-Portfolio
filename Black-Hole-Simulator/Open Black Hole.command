#!/bin/bash
# Build and launch the interactive simulator. Additional CLI options are forwarded.
set -e
launcher="$0"
while [ -L "$launcher" ]; do
    launcher_dir="$(cd -P "$(dirname "$launcher")" && pwd)"
    launcher="$(readlink "$launcher")"
    [[ "$launcher" = /* ]] || launcher="$launcher_dir/$launcher"
done
project_dir="$(cd -P "$(dirname "$launcher")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$project_dir/sim"
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
cd build
exec ./BlackHole3D --fps --out "$project_dir/sim/build/captures" "$@"
