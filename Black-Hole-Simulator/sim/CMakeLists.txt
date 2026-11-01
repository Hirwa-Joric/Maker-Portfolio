cmake_minimum_required(VERSION 3.21)
project(BlackHoleSim LANGUAGES CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON) # lets editors find the include paths

find_package(GLEW REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(glm CONFIG REQUIRED)
find_package(OpenGL REQUIRED)

# BlackHole3D: the explorer. BlackHole2D: ray paths in one plane.
add_executable(BlackHole3D app3d.cpp)
add_executable(BlackHole2D paths2d.cpp)
foreach(program IN ITEMS BlackHole3D BlackHole2D)
    target_compile_features(${program} PRIVATE cxx_std_17)
    set_target_properties(${program} PROPERTIES CXX_EXTENSIONS OFF)
    target_link_libraries(${program} PRIVATE glfw GLEW::GLEW glm::glm OpenGL::GL)
    if(APPLE)
        target_compile_definitions(${program} PRIVATE GL_SILENCE_DEPRECATION)
    endif()
endforeach()

# The programs read their GLSL files from build/shaders at run time.
file(GLOB shader_files CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/shaders/*.vert"
    "${CMAKE_CURRENT_SOURCE_DIR}/shaders/*.frag")
set(copied_shaders)
foreach(shader IN LISTS shader_files)
    get_filename_component(name "${shader}" NAME)
    set(copy "${CMAKE_CURRENT_BINARY_DIR}/shaders/${name}")
    add_custom_command(OUTPUT "${copy}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${shader}" "${copy}"
        DEPENDS "${shader}"
        VERBATIM)
    list(APPEND copied_shaders "${copy}")
endforeach()
add_custom_target(shaders ALL DEPENDS ${copied_shaders})
add_dependencies(BlackHole3D shaders)
add_dependencies(BlackHole2D shaders)

include(CTest)
if(BUILD_TESTING)
    add_executable(RuntimeChecks tests/runtime_checks.cpp)
    target_compile_features(RuntimeChecks PRIVATE cxx_std_17)
    target_include_directories(RuntimeChecks PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
    target_link_libraries(RuntimeChecks PRIVATE glfw GLEW::GLEW glm::glm OpenGL::GL)
    if(APPLE)
        target_compile_definitions(RuntimeChecks PRIVATE GL_SILENCE_DEPRECATION)
    endif()
    add_test(NAME runtime_checks COMMAND RuntimeChecks)
endif()
