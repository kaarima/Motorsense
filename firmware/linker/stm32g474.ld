ENTRY(Reset_Handler)

_Min_Heap_Size = 0x400;
_Min_Stack_Size = 0x800;

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 96K
    CCMRAM (xrw): ORIGIN = 0x10000000, LENGTH = 32K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(512);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } > FLASH

    .text :
    {
        . = ALIGN(4);
        *(.text.Reset_Handler)
        *(.text*)
        *(.rodata*)
        *(.glue_7)
        *(.glue_7t)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        _etext = .;
    } > FLASH

    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } > FLASH

    .ARM.exidx :
    {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } > FLASH

    .preinit_array :
    {
        PROVIDE_HIDDEN(__preinit_array_start = .);
        KEEP(*(.preinit_array*))
        PROVIDE_HIDDEN(__preinit_array_end = .);
    } > FLASH

    .init_array :
    {
        PROVIDE_HIDDEN(__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array*))
        PROVIDE_HIDDEN(__init_array_end = .);
    } > FLASH

    .fini_array :
    {
        PROVIDE_HIDDEN(__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array*))
        PROVIDE_HIDDEN(__fini_array_end = .);
    } > FLASH

    _sidata = LOADADDR(.data);
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT > FLASH

    _siccmram = LOADADDR(.ccmram);
    .ccmram :
    {
        . = ALIGN(4);
        _sccmram = .;
        *(.ccmram*)
        . = ALIGN(4);
        _eccmram = .;
    } > CCMRAM AT > FLASH

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    .ccm_bss (NOLOAD) :
    {
        . = ALIGN(4);
        _sccm_bss = .;
        *(.ccm_bss*)
        . = ALIGN(4);
        _eccm_bss = .;
    } > CCMRAM

    .heap (NOLOAD) :
    {
        . = ALIGN(8);
        _heap_start = .;
        end = _heap_start;
        _end = _heap_start;
        . += _Min_Heap_Size;
        _heap_end = .;
    } > RAM

    .stack ORIGIN(RAM) + LENGTH(RAM) - _Min_Stack_Size (NOLOAD) :
    {
        . = ALIGN(8);
        _stack_limit = .;
        . += _Min_Stack_Size;
        _stack_top = .;
    } > RAM

    /DISCARD/ :
    {
        *(.note*)
        *(.comment*)
    }
}

ASSERT(_heap_end <= _stack_limit, "SRAM1+SRAM2 overflow: heap and stack overlap")
ASSERT(_eccmram <= ORIGIN(CCMRAM) + LENGTH(CCMRAM), "CCM SRAM overflow")
