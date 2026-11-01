// Screenshots and video through ffmpeg. Frames are read from the back buffer,
// bottom row first; ffmpeg flips them upright. Encoder failures remain visible.
#pragma once
#include <GL/glew.h>
#include <csignal>
#include <cstdio>
#include <ctime>
#include <filesystem>
#include <string>
#include <vector>

namespace capture {

inline std::vector<unsigned char> readBackBuffer(int w, int h) {
    std::vector<unsigned char> rgb(size_t(w) * size_t(h) * 3);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, rgb.data());
    return rgb;
}

// Treat the entire path as one literal shell argument, including quotes and $().
inline std::string shellArgument(const std::string& value) {
    std::string out = "'";
    for (char c : value) out += c == '\'' ? "'\\''" : std::string(1, c);
    return out + "'";
}

inline FILE* encoder(const std::string& command) {
    // A failed encoder closes its pipe. Report the failed write instead of killing the viewer.
    std::signal(SIGPIPE, SIG_IGN);
    FILE* pipe = popen(command.c_str(), "w");
    if (!pipe) std::fprintf(stderr, "[capture] could not start ffmpeg\n");
    return pipe;
}

inline std::string ffmpegInput(const char* pixelFormat, int w, int h) {
    return "ffmpeg -y -loglevel error -f rawvideo -pix_fmt " + shellArgument(pixelFormat) +
           " -s " + std::to_string(w) + "x" + std::to_string(h);
}

// "<dir>/live-20261029-153000<ext>", creating the folder if needed.
inline std::string timestampedPath(const std::string& dir, const char* ext) {
    std::filesystem::create_directories(dir);
    char stamp[32];
    const std::time_t now = std::time(nullptr);
    std::strftime(stamp, sizeof(stamp), "%Y%m%d-%H%M%S", std::localtime(&now));
    return dir + "/live-" + stamp + ext;
}

inline bool writePng(const std::string& path, const char* pixelFormat, int w, int h,
                     const std::vector<unsigned char>& pixels) {
    FILE* pipe = encoder(ffmpegInput(pixelFormat, w, h) +
                        " -i - -vf vflip -frames:v 1 " + shellArgument(path));
    if (!pipe) return false;
    const bool written = std::fwrite(pixels.data(), 1, pixels.size(), pipe) == pixels.size();
    const bool flushed = std::fflush(pipe) == 0;
    const bool exited = pclose(pipe) == 0;
    if (!(written && flushed && exited)) {
        std::fprintf(stderr, "[capture] could not save %s\n", path.c_str());
        return false;
    }
    return true;
}

inline void saveStill(int w, int h, const std::string& dir) {
    const std::string path = timestampedPath(dir, ".png");
    if (writePng(path, "rgb24", w, h, readBackBuffer(w, h)))
        std::printf("[capture] saved %s\n", path.c_str());
}

// H.264 at 30 frames a second; one add() per shown frame.
class Video {
public:
    bool start(const std::string& path, int w, int h) {
        stop();
        width = w; height = h; frames = 0; failed = false;
        pipe = encoder(ffmpegInput("rgb24", w, h) +
            " -r 30 -i - -vf vflip -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p " + shellArgument(path));
        failed = pipe == nullptr;
        if (pipe) std::printf("[capture] recording %dx%d to %s\n", w, h, path.c_str());
        return !failed;
    }
    void add() {
        if (!pipe) return;
        const auto rgb = readBackBuffer(width, height);
        const bool written = std::fwrite(rgb.data(), 1, rgb.size(), pipe) == rgb.size();
        if (!written || std::fflush(pipe) != 0) {
            failed = true;
            stop();
            return;
        }
        ++frames;
    }
    void stop() {
        if (!pipe) return;
        const int status = pclose(pipe);
        pipe = nullptr;
        failed = failed || status != 0;
        if (failed) std::fprintf(stderr, "[capture] encoder failed; video may be incomplete\n");
        else std::printf("[capture] saved %d frames\n", frames);
    }
    bool active() const { return pipe != nullptr; }
    bool ok() const { return !failed; }
    ~Video() { stop(); }

private:
    FILE* pipe = nullptr;
    int width = 0, height = 0, frames = 0;
    bool failed = false;
};

} // namespace capture
