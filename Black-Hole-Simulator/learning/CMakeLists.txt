cmake_minimum_required(VERSION 3.21)
project(ShaderLessons LANGUAGES CXX)

find_package(GLEW REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(glm CONFIG REQUIRED)
find_package(OpenGL REQUIRED)

add_executable(ShaderLessons lessons.cpp)
target_compile_features(ShaderLessons PRIVATE cxx_std_17)
# The lessons are read straight from this folder, so an edited shader reloads with R.
target_compile_definitions(ShaderLessons PRIVATE LESSON_DIR="${CMAKE_CURRENT_SOURCE_DIR}/lessons" GL_SILENCE_DEPRECATION)
target_link_libraries(ShaderLessons PRIVATE glfw GLEW::GLEW glm::glm OpenGL::GL)
