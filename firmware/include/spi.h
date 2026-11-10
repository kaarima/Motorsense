#ifndef MOTORSENSE_SPI_H
#define MOTORSENSE_SPI_H

#include <stdint.h>

void spi2_init(void);
uint8_t spi2_transfer(uint8_t value);
void spi2_select(void);
void spi2_deselect(void);

#endif
