#ifndef MOTORSENSE_IIS3DWB_H
#define MOTORSENSE_IIS3DWB_H

#include <stdint.h>

#define VIBRATION_WINDOW_SAMPLES 6000U

uint32_t iis3dwb_init(void);
uint32_t iis3dwb_capture_window(float *rms_counts, uint32_t *sample_count,
                                uint32_t *dropped_windows);

#endif
