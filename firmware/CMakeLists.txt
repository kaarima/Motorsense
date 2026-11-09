add_executable(motorsense
    startup/startup.c
    app/main.c
)

target_compile_options(motorsense PRIVATE
    -mcpu=cortex-m4
    -mthumb
    -mfpu=fpv4-sp-d16
    -mfloat-abi=hard
    -ffreestanding
    -fdata-sections
    -ffunction-sections
    -fno-common
    -Wall
    -Wextra
    -Werror
)

target_link_options(motorsense PRIVATE
    -mcpu=cortex-m4
    -mthumb
    -mfpu=fpv4-sp-d16
    -mfloat-abi=hard
    -nostartfiles
    --specs=nano.specs
    --specs=nosys.specs
    -Wl,--gc-sections
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/motorsense.map
    -T${CMAKE_CURRENT_SOURCE_DIR}/linker/stm32g474.ld
)

set_target_properties(motorsense PROPERTIES
    OUTPUT_NAME motorsense
    SUFFIX .elf
)

add_custom_target(size-report ALL
    COMMAND ${CMAKE_COMMAND}
        -DELF=$<TARGET_FILE:motorsense>
        -DSIZE=${CMAKE_SIZE}
        -P ${CMAKE_SOURCE_DIR}/firmware/cmake/report_size.cmake
    DEPENDS motorsense
    VERBATIM
)
