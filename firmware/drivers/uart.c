#include "uart.h"

#include <stddef.h>

#define RCC_AHB2ENR (*(volatile uint32_t *)0x4002104CUL)
#define RCC_APB1ENR2 (*(volatile uint32_t *)0x4002105CUL)
#define GPIOA_MODER (*(volatile uint32_t *)0x48000000UL)
#define GPIOA_AFRL (*(volatile uint32_t *)0x48000020UL)
#define LPUART1_BASE 0x40008000UL
#define LPUART1_CR1 (*(volatile uint32_t *)(LPUART1_BASE + 0x00UL))
#define LPUART1_CR2 (*(volatile uint32_t *)(LPUART1_BASE + 0x04UL))
#define LPUART1_CR3 (*(volatile uint32_t *)(LPUART1_BASE + 0x08UL))
#define LPUART1_BRR (*(volatile uint32_t *)(LPUART1_BASE + 0x0CUL))
#define LPUART1_ISR (*(volatile uint32_t *)(LPUART1_BASE + 0x1CUL))
#define LPUART1_TDR (*(volatile uint32_t *)(LPUART1_BASE + 0x28UL))
#define NVIC_ISER2 (*(volatile uint32_t *)0xE000E108UL)

#define SYSTEM_CLOCK_HZ 170000000UL
#define UART_BAUD 115200UL
#define TX_BUFFER_SIZE 256U
#define TX_BUFFER_MASK (TX_BUFFER_SIZE - 1U)
#define LPUART_ISR_TC (1UL << 6)
#define LPUART_ISR_TXE (1UL << 7)
#define LPUART_CR1_UE (1UL << 0)
#define LPUART_CR1_TE (1UL << 3)
#define LPUART_CR1_TXEIE (1UL << 7)
#define LPUART1_IRQ_NUMBER 91U

static char tx_buffer[TX_BUFFER_SIZE];
static volatile uint8_t tx_head;
static volatile uint8_t tx_tail;

static void irq_restore(uint32_t primask)
{
    if ((primask & 1UL) == 0UL) {
        __asm volatile("cpsie i" ::: "memory");
    }
}

void uart_init(void)
{
    RCC_AHB2ENR |= 1UL;
    RCC_APB1ENR2 |= 1UL;
    (void)RCC_APB1ENR2;

    const uint32_t pa2_pa3_mode_mask = (3UL << 4) | (3UL << 6);
    GPIOA_MODER = (GPIOA_MODER & ~pa2_pa3_mode_mask) | (2UL << 4) | (2UL << 6);
    const uint32_t pa2_pa3_af_mask = (0xFUL << 8) | (0xFUL << 12);
    GPIOA_AFRL = (GPIOA_AFRL & ~pa2_pa3_af_mask) | (0xCUL << 8) | (0xCUL << 12);

    LPUART1_CR1 = 0U;
    LPUART1_CR2 = 0U;
    LPUART1_CR3 = 0U;
    LPUART1_BRR = (uint32_t)(((uint64_t)SYSTEM_CLOCK_HZ * 256ULL + UART_BAUD / 2UL) / UART_BAUD);
    tx_head = 0U;
    tx_tail = 0U;

    LPUART1_CR1 = LPUART_CR1_TE | LPUART_CR1_UE;
    NVIC_ISER2 = 1UL << (LPUART1_IRQ_NUMBER - 64U);
}

static void enqueue_byte(char byte)
{
    uint8_t next_head;
    uint32_t primask;

    for (;;) {
        next_head = (uint8_t)((tx_head + 1U) & TX_BUFFER_MASK);
        while (next_head == tx_tail) {
            next_head = (uint8_t)((tx_head + 1U) & TX_BUFFER_MASK);
        }

        __asm volatile("mrs %0, primask\n cpsid i" : "=r"(primask) : : "memory");
        next_head = (uint8_t)((tx_head + 1U) & TX_BUFFER_MASK);
        if (next_head != tx_tail) {
            tx_buffer[tx_head] = byte;
            __asm volatile("" ::: "memory");
            tx_head = next_head;
            LPUART1_CR1 |= LPUART_CR1_TXEIE;
            irq_restore(primask);
            return;
        }
        irq_restore(primask);
    }
}

int _write(int file, char *buffer, int length)
{
    (void)file;
    if (length < 0) {
        return -1;
    }

    for (int index = 0; index < length; ++index) {
        enqueue_byte(buffer[index]);
    }
    return length;
}

void LPUART1_IRQHandler(void)
{
    if (((LPUART1_ISR & LPUART_ISR_TXE) != 0U) && ((LPUART1_CR1 & LPUART_CR1_TXEIE) != 0U)) {
        if (tx_tail != tx_head) {
            LPUART1_TDR = (uint8_t)tx_buffer[tx_tail];
            tx_tail = (uint8_t)((tx_tail + 1U) & TX_BUFFER_MASK);
        } else {
            LPUART1_CR1 &= ~LPUART_CR1_TXEIE;
        }
    }
}

void uart_flush(void)
{
    while (tx_head != tx_tail) {
        __asm volatile("wfi");
    }
    while ((LPUART1_ISR & LPUART_ISR_TC) == 0U) {
    }
}

static void uart_write_polled_byte(char byte)
{
    while ((LPUART1_ISR & LPUART_ISR_TXE) == 0U) {
    }
    LPUART1_TDR = (uint8_t)byte;
}

void uart_fault_write(const char *text)
{
    LPUART1_CR1 &= ~LPUART_CR1_TXEIE;

    while (tx_tail != tx_head) {
        uart_write_polled_byte(tx_buffer[tx_tail]);
        tx_tail = (uint8_t)((tx_tail + 1U) & TX_BUFFER_MASK);
    }
    while ((LPUART1_ISR & LPUART_ISR_TC) == 0U) {
    }

    while (*text != '\0') {
        uart_write_polled_byte(*text++);
    }
    while ((LPUART1_ISR & LPUART_ISR_TC) == 0U) {
    }
}
