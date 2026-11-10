#include "clock.h"
#include "uart.h"

#include <stdint.h>
#include <stdio.h>

#include "fw_version.h"

#define RCC_AHB2ENR (*(volatile uint32_t *)0x4002104CUL)
#define GPIOA_MODER (*(volatile uint32_t *)0x48000000UL)
#define GPIOA_BSRR (*(volatile uint32_t *)0x48000018UL)
#define SYST_CSR (*(volatile uint32_t *)0xE000E010UL)
#define SYST_RVR (*(volatile uint32_t *)0xE000E014UL)
#define SYST_CVR (*(volatile uint32_t *)0xE000E018UL)

#define LED_PIN 5U
#define SYSTICK_RELOAD (MOTORSENSE_SYSCLK_HZ / 1000UL - 1UL)

static volatile uint32_t tick_ms;

void SysTick_Handler(void)
{
    ++tick_ms;
}

static void systick_init(void)
{
    SYST_CSR = 0U;
    SYST_RVR = SYSTICK_RELOAD;
    SYST_CVR = 0U;
    SYST_CSR = 0x7U;
}

static void gpio_init(void)
{
    RCC_AHB2ENR |= 1UL;
    (void)RCC_AHB2ENR;
    GPIOA_MODER = (GPIOA_MODER & ~(3UL << (LED_PIN * 2U))) | (1UL << (LED_PIN * 2U));
    GPIOA_BSRR = 1UL << (LED_PIN + 16U);
}

static void delay_ms(uint32_t delay)
{
    const uint32_t start = tick_ms;
    while ((tick_ms - start) < delay) {
        __asm volatile("wfi");
    }
}

int main(void)
{
    if (clock_init() == 0U) {
        for (;;) {
            __asm volatile("wfi");
        }
    }

    systick_init();
    gpio_init();
    uart_init();
    __asm volatile("cpsie i" ::: "memory");

    (void)printf("MotorSense fw %s boot, SYSCLK=%lu\n", MOTORSENSE_FW_VERSION,
                 (unsigned long)MOTORSENSE_SYSCLK_HZ);
    uart_flush();

#if defined(MOTORSENSE_TEST_HARDFAULT)
    __asm volatile("udf #0");
#endif

    uint32_t led_is_on = 0U;
    for (;;) {
        delay_ms(500U);
        led_is_on ^= 1U;
        GPIOA_BSRR = led_is_on != 0U ? (1UL << LED_PIN) : (1UL << (LED_PIN + 16U));
    }
}
