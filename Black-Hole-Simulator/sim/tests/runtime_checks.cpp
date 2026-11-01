// Behavioral checks for time stepping, the default 2D view and capture failures.
#include "capture.hpp"
#include "settings.hpp"
#include "star_system.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <unistd.h>

int main() {
    int failures = 0;
    auto check = [&](bool passed, const char* name) {
        std::cout << (passed ? "PASS " : "FAIL ") << name << '\n';
        if (!passed) ++failures;
    };
    check(Settings{}.rayCount > 0, "2D opens with visible rays");

    StarSystem reference;
    reference.disruption = false;
    reference.restart(0.0);
    reference.advance(1.0, 1.0);
    const auto expected = reference.suns(1.0);
    for (int fps : {30, 60, 120}) {
        StarSystem framed;
        framed.disruption = false;
        framed.restart(0.0);
        for (int n = 1; n <= fps; ++n) framed.advance(1.0 / fps, double(n) / fps);
        const auto actual = framed.suns(1.0);
        double error = 0.0;
        for (size_t i = 0; i < std::min(expected.size(), actual.size()); ++i)
            error = std::max(error, double(glm::distance(expected[i].centre, actual[i].centre)));
        std::cout << "  " << fps << " frames: position difference " << error << " r_s\n";
        check(actual.size() == expected.size() && error < 0.005,
              "equal elapsed time gives consistent star positions");
    }

    std::string pattern = (std::filesystem::temp_directory_path() / "black-hole-check-XXXXXX").string();
    char* created = mkdtemp(pattern.data());
    if (!created) return 1;
    const std::filesystem::path dir(created);
    const auto path = dir / "quote ' double \" dollar $(printf altered) `printf altered`.png";
    const std::vector<unsigned char> white(12, 255);
    check(capture::writePng(path.string(), "rgb24", 2, 2, white), "capture accepts literal special characters");
    std::ifstream file(path, std::ios::binary);
    unsigned char header[8]{};
    file.read(reinterpret_cast<char*>(header), 8);
    const unsigned char png[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    check(file.gcount() == 8 && std::equal(header, header + 8, png), "PNG exists at the exact requested filename");

    const char* previous = std::getenv("PATH");
    const bool hadPath = previous != nullptr;
    const std::string savedPath = previous ? previous : "";
    setenv("PATH", "", 1);
    const bool incorrectlySaved = capture::writePng((dir / "missing-encoder.png").string(), "rgb24", 2, 2, white);
    if (hadPath) setenv("PATH", savedPath.c_str(), 1); else unsetenv("PATH");
    check(!incorrectlySaved, "missing encoder reports failure without terminating the viewer");
    std::filesystem::remove_all(dir);
    return failures == 0 ? 0 : 1;
}
