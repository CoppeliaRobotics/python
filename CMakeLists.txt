cmake_minimum_required(VERSION 3.12)
project(pythonFiles)

if(NOT COPPELIASIM_INCLUDE_DIR)
    if(DEFINED ENV{COPPELIASIM_ROOT_DIR})
        set(COPPELIASIM_INCLUDE_DIR $ENV{COPPELIASIM_ROOT_DIR}/programming/include)
    else()
        set(COPPELIASIM_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../include)
    endif()
endif()
list(APPEND CMAKE_MODULE_PATH ${COPPELIASIM_INCLUDE_DIR}/cmake)
find_package(CoppeliaSim 4.5.0.7 REQUIRED)

file(GLOB PYTHON_FILES CONFIGURE_DEPENDS *.py)
foreach(PYTHON_FILE IN LISTS PYTHON_FILES)
    coppeliasim_add_resource(${PYTHON_FILE} SUBDIR python)
endforeach()
