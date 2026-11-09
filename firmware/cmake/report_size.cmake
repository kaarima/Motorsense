execute_process(
    COMMAND "${SIZE}" --format=berkeley "${ELF}"
    RESULT_VARIABLE size_result
    OUTPUT_VARIABLE size_output
    ERROR_VARIABLE size_error
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT size_result EQUAL 0)
    message(FATAL_ERROR "arm-none-eabi-size failed: ${size_error}")
endif()

string(REGEX MATCH "[ \t]*([0-9]+)[ \t]+([0-9]+)[ \t]+([0-9]+)[ \t]+[0-9]+[ \t]+[0-9a-fA-F]+[ \t]+[^ \t\n]+" size_match "${size_output}")
if(NOT size_match)
    message(FATAL_ERROR "Could not parse arm-none-eabi-size output:\n${size_output}")
endif()

set(text_bytes "${CMAKE_MATCH_1}")
set(data_bytes "${CMAKE_MATCH_2}")
set(bss_bytes "${CMAKE_MATCH_3}")
math(EXPR flash_used "${text_bytes} + ${data_bytes}")
math(EXPR ram_used "${data_bytes} + ${bss_bytes}")

message(STATUS "MotorSense size report")
message(STATUS "  Flash: ${flash_used} / 524288 bytes (text ${text_bytes} + data ${data_bytes})")
message(STATUS "  SRAM1+SRAM2: ${ram_used} / 98304 bytes (data ${data_bytes} + bss ${bss_bytes})")
message(STATUS "  CCM SRAM capacity: 32768 bytes")
