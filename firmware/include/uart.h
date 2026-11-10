#ifndef MOTORSENSE_UART_H
#define MOTORSENSE_UART_H

#include <stdint.h>

void uart_init(void);
void uart_flush(void);
void uart_fault_write(const char *text);
void LPUART1_IRQHandler(void);

#endif
