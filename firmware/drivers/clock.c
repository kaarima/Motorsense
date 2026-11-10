#include "clock.h"

#define RCC_BASE 0x40021000UL
#define RCC_CR (*(volatile uint32_t *)(RCC_BASE + 0x00UL))
#define RCC_CFGR (*(volatile uint32_t *)(RCC_BASE + 0x08UL))
#define RCC_PLLCFGR (*(volatile uint32_t *)(RCC_BASE + 0x0CUL))
#define RCC_APB1ENR1 (*(volatile uint32_t *)(RCC_BASE + 0x58UL))
#define FLASH_ACR (*(volatile uint32_t *)0x40022000UL)
#define PWR_CR1 (*(volatile uint32_t *)0x40007000UL)
#define PWR_SR2 (*(volatile uint32_t *)0x40007014UL)
#define PWR_CR5 (*(volatile uint32_t *)0x40007080UL)

#define RCC_CR_HSIRDY (1UL << 10)
#define RCC_CR_PLLON (1UL << 24)
#define RCC_CR_PLLRDY (1UL << 25)
#define RCC_CFGR_SW_MASK (3UL << 0)
#define RCC_CFGR_SW_PLL (3UL << 0)
#define RCC_CFGR_SWS_MASK (3UL << 2)
#define RCC_CFGR_SWS_PLL (3UL << 2)
#define RCC_PLLCFGR_PLLSRC_HSI16 (2UL << 0)
#define RCC_PLLCFGR_PLLM_DIV4 (3UL << 4)
#define RCC_PLLCFGR_PLLN_85 (85UL << 8)
#define RCC_PLLCFGR_PLLREN (1UL << 24)
#define PWR_CR1_VOS_MASK (3UL << 8)
#define PWR_CR1_VOS_RANGE1 (1UL << 8)
#define PWR_SR2_VOSF (1UL << 10)
#define PWR_CR5_R1MODE (1UL << 8)
#define FLASH_ACR_LATENCY_MASK 0xFUL
#define FLASH_ACR_LATENCY_4WS 4UL
#define FLASH_ACR_PREFETCH (1UL << 8)
#define FLASH_ACR_ICACHE (1UL << 9)
#define FLASH_ACR_DCACHE (1UL << 10)
#define CLOCK_READY_TIMEOUT 1000000UL

static uint32_t wait_for_set(volatile uint32_t *reg, uint32_t mask)
{
    uint32_t timeout = CLOCK_READY_TIMEOUT;
    while (((*reg & mask) != mask) && timeout > 0U) {
        --timeout;
    }
    return timeout > 0U;
}

static uint32_t wait_for_clear(volatile uint32_t *reg, uint32_t mask)
{
    uint32_t timeout = CLOCK_READY_TIMEOUT;
    while (((*reg & mask) != 0U) && timeout > 0U) {
        --timeout;
    }
    return timeout > 0U;
}

uint32_t clock_init(void)
{
    /* Reset selects and starts HSI16; retain it as the PLL input. */
    if (wait_for_set(&RCC_CR, RCC_CR_HSIRDY) == 0U) {
        return 0U;
    }

    RCC_APB1ENR1 |= 1UL << 28;
    PWR_CR1 = (PWR_CR1 & ~PWR_CR1_VOS_MASK) | PWR_CR1_VOS_RANGE1;
    if (wait_for_clear(&PWR_SR2, PWR_SR2_VOSF) == 0U) {
        return 0U;
    }

    /* Range 1 boost mode is selected by clearing R1MODE. */
    PWR_CR5 &= ~PWR_CR5_R1MODE;

    /* Four wait states cover 170 MHz in Range 1 boost mode. */
    FLASH_ACR = (FLASH_ACR & ~FLASH_ACR_LATENCY_MASK) | FLASH_ACR_LATENCY_4WS | FLASH_ACR_PREFETCH |
                FLASH_ACR_ICACHE | FLASH_ACR_DCACHE;

    /* HSI16 / 4 * 85 / 2 = 170 MHz. PLL is disabled after reset. */
    RCC_PLLCFGR =
        RCC_PLLCFGR_PLLSRC_HSI16 | RCC_PLLCFGR_PLLM_DIV4 | RCC_PLLCFGR_PLLN_85 | RCC_PLLCFGR_PLLREN;
    RCC_CR |= RCC_CR_PLLON;
    if (wait_for_set(&RCC_CR, RCC_CR_PLLRDY) == 0U) {
        return 0U;
    }

    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_SW_MASK) | RCC_CFGR_SW_PLL;
    if (wait_for_set(&RCC_CFGR, RCC_CFGR_SWS_PLL) == 0U) {
        return 0U;
    }

    return 1U;
}
