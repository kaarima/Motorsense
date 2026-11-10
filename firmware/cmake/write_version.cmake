execute_process(
    COMMAND git -c "safe.directory=${REPOSITORY}" describe --always --dirty --tags
    WORKING_DIRECTORY "${REPOSITORY}"
    RESULT_VARIABLE git_result
    OUTPUT_VARIABLE firmware_version
    ERROR_QUIET
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT git_result EQUAL 0 OR firmware_version STREQUAL "")
    set(firmware_version "unknown")
endif()

get_filename_component(generated_dir "${OUTPUT}" DIRECTORY)
file(MAKE_DIRECTORY "${generated_dir}")
set(version_header "#ifndef MOTORSENSE_FW_VERSION_H\n#define MOTORSENSE_FW_VERSION_H\n#define MOTORSENSE_FW_VERSION \"${firmware_version}\"\n#endif\n")

if(EXISTS "${OUTPUT}")
    file(READ "${OUTPUT}" existing_header)
else()
    set(existing_header "")
endif()

if(NOT existing_header STREQUAL version_header)
    file(WRITE "${OUTPUT}" "${version_header}")
endif()
