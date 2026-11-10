set(FIRMWARE_SOURCES
    app/main.c
    drivers/clock.c
    drivers/uart.c
    startup/startup.c
)

set(VERSION_HEADER "${CMAKE_CURRENT_BINARY_DIR}/generated/fw_version.h")
add_custom_target(firmware-version
    COMMAND ${CMAKE_COMMAND}
        -DREPOSITORY=${CMAKE_SOURCE_DIR}
        -DOUTPUT=${VERSION_HEADER}
        -P ${CMAKE_SOURCE_DIR}/firmware/cmake/write_version.cmake
    BYPRODUCTS "${VERSION_HEADER}"
    VERBATIM
)

function(add_firmware_image target_name output_name)
    add_executable(${target_name} ${FIRMWARE_SOURCES})
    add_dependencies(${target_name} firmware-version)
    target_include_directories(${target_name} PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CMAKE_CURRENT_BINARY_DIR}/generated"
    )

    target_compile_options(${target_name} PRIVATE
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

    target_link_options(${target_name} PRIVATE
        -mcpu=cortex-m4
        -mthumb
        -mfpu=fpv4-sp-d16
        -mfloat-abi=hard
        -nostartfiles
        --specs=nano.specs
        --specs=nosys.specs
        -Wl,--gc-sections
        -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/${output_name}.map
        -T${CMAKE_CURRENT_SOURCE_DIR}/linker/stm32g474.ld
    )

    set_target_properties(${target_name} PROPERTIES
        OUTPUT_NAME ${output_name}
        SUFFIX .elf
    )
endfunction()

add_firmware_image(motorsense motorsense)
add_firmware_image(motorsense_fault_test motorsense_fault_test)
target_compile_definitions(motorsense_fault_test PRIVATE MOTORSENSE_TEST_HARDFAULT=1)

add_custom_target(size-report ALL
    COMMAND ${CMAKE_COMMAND}
        -DELF=$<TARGET_FILE:motorsense>
        -DSIZE=${CMAKE_SIZE}
        -P ${CMAKE_SOURCE_DIR}/firmware/cmake/report_size.cmake
    COMMAND ${CMAKE_COMMAND}
        -DELF=$<TARGET_FILE:motorsense_fault_test>
        -DSIZE=${CMAKE_SIZE}
        -P ${CMAKE_SOURCE_DIR}/firmware/cmake/report_size.cmake
    DEPENDS motorsense motorsense_fault_test
    VERBATIM
)
