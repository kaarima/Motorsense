#include <stdint.h>

#include "uart.h"

extern uint32_t _estack;
extern uint32_t _sidata;
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sbss;
extern uint32_t _ebss;
extern uint32_t _siccmram;
extern uint32_t _sccmram;
extern uint32_t _eccmram;
extern uint32_t _sccm_bss;
extern uint32_t _eccm_bss;

int main(void);

void Reset_Handler(void);
void Default_Handler(void);
void HardFault_Handler(void);
void SysTick_Handler(void);
void LPUART1_IRQHandler(void);

typedef union {
    uintptr_t initial_stack_pointer;
    void (*handler)(void);
} vector_entry_t;

enum { VECTOR_COUNT = 16 + 128 };

__attribute__((used, section(".isr_vector"), aligned(512)))
const vector_entry_t vector_table[VECTOR_COUNT] = {
    [0] = {.initial_stack_pointer = (uintptr_t)&_estack},
    [1] = {.handler = Reset_Handler},
    [2] = {.handler = Default_Handler},
    [3] = {.handler = HardFault_Handler},
    [4] = {.handler = Default_Handler},
    [5] = {.handler = Default_Handler},
    /* A disabled UsageFault escalates to HardFault on silicon. Renode 1.15.3
     * vectors UDF directly through this slot, so share the diagnostic handler. */
    [6] = {.handler = HardFault_Handler},
    [11] = {.handler = Default_Handler},
    [12] = {.handler = Default_Handler},
    [14] = {.handler = Default_Handler},
    [15] = {.handler = SysTick_Handler},
    [16 ... 106] = {.handler = Default_Handler},
    [107] = {.handler = LPUART1_IRQHandler},
    [108 ... VECTOR_COUNT - 1] = {.handler = Default_Handler},
};

static void emit_hex32(uint32_t value)
{
    static const char digits[] = "0123456789ABCDEF";
    char text[11] = "0x00000000";
    for (uint32_t index = 0U; index < 8U; ++index) {
        const uint32_t shift = (7U - index) * 4U;
        text[index + 2U] = digits[(value >> shift) & 0xFUL];
    }
    uart_fault_write(text);
}

static void emit_register(const char *name, uint32_t value, const char *suffix)
{
    uart_fault_write(name);
    emit_hex32(value);
    uart_fault_write(suffix);
}

void hardfault_c(uint32_t *stacked, uint32_t exc_return)
{
    if ((exc_return & (1UL << 4)) == 0U) {
        stacked += 18;
    }

    uart_fault_write("\r\nFault register dump\r\n");
    emit_register("R0=", stacked[0], " ");
    emit_register("R1=", stacked[1], " ");
    emit_register("R2=", stacked[2], " ");
    emit_register("R3=", stacked[3], "\r\n");
    emit_register("R12=", stacked[4], " ");
    emit_register("LR=", stacked[5], " ");
    emit_register("PC=", stacked[6], " ");
    emit_register("xPSR=", stacked[7], "\r\n");
    emit_register("CFSR=", *(volatile uint32_t *)0xE000ED28UL, " ");
    emit_register("HFSR=", *(volatile uint32_t *)0xE000ED2CUL, "\r\n");
    emit_register("MMFAR=", *(volatile uint32_t *)0xE000ED34UL, " ");
    emit_register("BFAR=", *(volatile uint32_t *)0xE000ED38UL, "\r\n");

    for (;;) {
        __asm volatile("wfi");
    }
}

__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile("tst lr, #4\n"
                   "ite eq\n"
                   "mrseq r0, msp\n"
                   "mrsne r0, psp\n"
                   "mov r1, lr\n"
                   "b hardfault_c\n");
}

static void enable_fpu(void)
{
    volatile uint32_t *const cpacr = (volatile uint32_t *)0xE000ED88UL;
    *cpacr |= (0xFUL << 20);
    __asm volatile("dsb" ::: "memory");
    __asm volatile("isb" ::: "memory");
}

void Reset_Handler(void)
{
    enable_fpu();

    uint32_t *source = &_sidata;
    for (uint32_t *destination = &_sdata; destination < &_edata; ++destination) {
        *destination = *source++;
    }

    source = &_siccmram;
    for (uint32_t *destination = &_sccmram; destination < &_eccmram; ++destination) {
        *destination = *source++;
    }

    for (uint32_t *destination = &_sbss; destination < &_ebss; ++destination) {
        *destination = 0U;
    }

    for (uint32_t *destination = &_sccm_bss; destination < &_eccm_bss; ++destination) {
        *destination = 0U;
    }

    (void)main();
    for (;;) {
        __asm volatile("wfi");
    }
}

void Default_Handler(void)
{
    for (;;) {
        __asm volatile("wfi");
    }
}
