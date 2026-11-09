#include <stdint.h>

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
void SysTick_Handler(void);

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
    [3] = {.handler = Default_Handler},
    [4] = {.handler = Default_Handler},
    [5] = {.handler = Default_Handler},
    [6] = {.handler = Default_Handler},
    [11] = {.handler = Default_Handler},
    [12] = {.handler = Default_Handler},
    [14] = {.handler = Default_Handler},
    [15] = {.handler = SysTick_Handler},
    [16 ... VECTOR_COUNT - 1] = {.handler = Default_Handler},
};

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
