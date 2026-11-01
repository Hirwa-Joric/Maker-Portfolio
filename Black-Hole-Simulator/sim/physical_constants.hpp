#pragma once
#include <cmath>
#include <cstdio>
#include <string>

namespace physical {
// SI units. Adopt the rounded GRAVITY estimate for Sagittarius A*:
// https://www.eso.org/public/news/eso2119/
inline constexpr double c = 299792458.0;
inline constexpr double G = 6.67430e-11;
inline constexpr double solarMassKg = 1.98847e30;
inline constexpr double solarRadiusM = 6.957e8;
inline constexpr double sagittariusMassSolar = 4.30e6;
inline constexpr double sagittariusMassKg = sagittariusMassSolar * solarMassKg;
inline constexpr double schwarzschildRadiusM = 2.0 * G * sagittariusMassKg / (c * c);
inline constexpr double lightCrossingTimeS = schwarzschildRadiusM / c;
inline constexpr double ghostOffsetRs = 1e-6;

// Solar-star disruption scale; illustrative particles have exaggerated masses/radii.
inline double solarTidalRadiusRs() {
    return solarRadiusM * std::cbrt(sagittariusMassSolar) / schwarzschildRadiusM;
}

inline std::string windowTitle(const char* view) {
    char text[160];
    std::snprintf(text, sizeof(text), "Sagittarius A* — geodesic renderer | %.2f million solar masses | %s",
                  sagittariusMassSolar / 1e6, view);
    return text;
}

inline void printScales() {
    std::printf("Sagittarius A* (Schwarzschild model)\n"
                "Mass: %.8g solar masses (%.8g kg)\n"
                "Schwarzschild radius: %.8g m\n"
                "Light-crossing time r_s/c: %.8g s\n"
                "Ghost offset: %.8g r_s (%.8g km)\n"
                "Solar-star tidal radius: %.8g r_s\n",
                sagittariusMassSolar, sagittariusMassKg, schwarzschildRadiusM,
                lightCrossingTimeS, ghostOffsetRs,
                ghostOffsetRs * schwarzschildRadiusM / 1000.0, solarTidalRadiusRs());
}
} // namespace physical
