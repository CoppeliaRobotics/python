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
find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_custom_command(
    OUTPUT
        ${CMAKE_CURRENT_BINARY_DIR}/generated/sim/enums.py
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_BINARY_DIR}/generated/sim
    COMMAND ${CMAKE_COMMAND} -E env _GENERATING_ENUMS_PY=1
        ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/pycpp.py
        --input-file ${CMAKE_CURRENT_SOURCE_DIR}/templates/sim/enums.py.in
        --output-file ${CMAKE_CURRENT_BINARY_DIR}/generated/sim/enums.py
        --python-path ${CMAKE_CURRENT_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    DEPENDS
        ${COPPELIASIM_INCLUDE_DIR}/sim/objects.xml
        ${CMAKE_CURRENT_SOURCE_DIR}/templates/sim/enums.py.in
        ${CMAKE_CURRENT_SOURCE_DIR}/sim/apidoc.py
        ${CMAKE_CURRENT_SOURCE_DIR}/pycpp.py
)
add_custom_target(
    generate_sim_const_py ALL
    DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/generated/sim/enums.py
)
coppeliasim_add_python(${CMAKE_CURRENT_BINARY_DIR}/generated/sim/enums.py SUBDIR sim)

file(GLOB PYTHON_FILES CONFIGURE_DEPENDS *.py)
foreach(PYTHON_FILE IN LISTS PYTHON_FILES)
    coppeliasim_add_python(${PYTHON_FILE})
endforeach()
coppeliasim_add_python_directory(sim)
