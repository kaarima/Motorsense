#include "spi.h"

#define RCC_AHB2ENR (*(volatile uint32_t *)0x4002104CUL)
#define RCC_APB1ENR1 (*(volatile uint32_t *)0x40021058UL)
#define GPIOB_MODER (*(volatile uint32_t *)0x48000400UL)
#define GPIOB_AFRH (*(volatile uint32_t *)0x48000424UL)
#define GPIOB_BSRR (*(volatile uint32_t *)0x48000418UL)
#define SPI2_BASE 0x40003800UL
#define SPI2_CR1 (*(volatile uint32_t *)(SPI2_BASE + 0x00UL))
#define SPI2_CFG1 (*(volatile uint32_t *)(SPI2_BASE + 0x08UL))
#define SPI2_CFG2 (*(volatile uint32_t *)(SPI2_BASE + 0x0CUL))
#define SPI2_SR (*(volatile uint32_t *)(SPI2_BASE + 0x14UL))
#define SPI2_TXDR (*(volatile uint32_t *)(SPI2_BASE + 0x20UL))
#define SPI2_RXDR (*(volatile uint32_t *)(SPI2_BASE + 0x30UL))

#define GPIOB_CS_PIN 12U
#define SPI_SR_RXP (1UL << 0)
#define SPI_CFG2_MASTER (1UL << 22)
#define SPI_CFG2_SSM (1UL << 26)
#define SPI_CR1_SPE (1UL << 0)
#define SPI_CR1_CSTART (1UL << 9)
#define SPI_CR1_SSI (1UL << 12)

void spi2_init(void)
{
    RCC_AHB2ENR |= 1UL << 1;
    RCC_APB1ENR1 |= 1UL << 14;
    (void)RCC_APB1ENR1;

    const uint32_t pins_mode = (3UL << 24) | (3UL << 26) | (3UL << 28) | (3UL << 30);
    GPIOB_MODER =
        (GPIOB_MODER & ~pins_mode) | (1UL << 24) | (2UL << 26) | (2UL << 28) | (2UL << 30);
    const uint32_t af_mask = (0xFUL << 20) | (0xFUL << 24) | (0xFUL << 28);
    GPIOB_AFRH = (GPIOB_AFRH & ~af_mask) | (5UL << 20) | (5UL << 24) | (5UL << 28);

    GPIOB_BSRR = 1UL << GPIOB_CS_PIN;
    SPI2_CR1 = 0U;
    SPI2_CFG1 = 7UL | (4UL << 28); /* 8-bit transfer, /32 prescaler */
    SPI2_CFG2 = SPI_CFG2_MASTER | SPI_CFG2_SSM;
    SPI2_CR1 = SPI_CR1_SSI | SPI_CR1_SPE | SPI_CR1_CSTART;
}

void spi2_select(void)
{
    GPIOB_BSRR = 1UL << (GPIOB_CS_PIN + 16U);
}

void spi2_deselect(void)
{
    GPIOB_BSRR = 1UL << GPIOB_CS_PIN;
}

uint8_t spi2_transfer(uint8_t value)
{
    SPI2_TXDR = value;
    while ((SPI2_SR & SPI_SR_RXP) == 0U) {
    }
    return (uint8_t)SPI2_RXDR;
}
