#!/bin/bash
# Build and open the step-by-step shader lessons (keys 1-6, T compare, R reload).
set -e
here="$(cd -P "$(dirname "$0")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$here/learning"
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
exec ./build/ShaderLessons
