#include "iis3dwb.h"

#include "spi.h"

#include <stddef.h>

#define IIS3DWB_WHO_AM_I 0x0FU
#define IIS3DWB_CTRL1_XL 0x10U
#define IIS3DWB_CTRL3_C 0x12U
#define IIS3DWB_FIFO_CTRL1 0x07U
#define IIS3DWB_FIFO_CTRL3 0x09U
#define IIS3DWB_FIFO_CTRL4 0x0AU
#define IIS3DWB_INT2_CTRL 0x0EU
#define IIS3DWB_FIFO_STATUS1 0x3AU
#define IIS3DWB_FIFO_STATUS2 0x3BU
#define IIS3DWB_FIFO_DATA_OUT_TAG 0x78U
#define IIS3DWB_FIFO_TAG_ACCEL 0x02U
#define IIS3DWB_FIFO_OVERRUN_MASK 0x50U
#define IIS3DWB_ODR_RATIO_UP 9U
#define IIS3DWB_ODR_RATIO_DOWN 20U
#define SAMPLE_BLOCK_SAMPLES 128U

static const float resample_fir[9] = {
    -0.0017117425F, -0.0217269554F, 0.0271047786F,  0.2720401644F,  0.4485875100F,
    0.2720401644F,  0.0271047786F,  -0.0217269554F, -0.0017117425F,
};

/* Temporary CPU-filled ping-pong blocks; DMA wiring is a follow-up. */
static int16_t sample_blocks[2][SAMPLE_BLOCK_SAMPLES];

static uint8_t read_register(uint8_t address)
{
    spi2_select();
    (void)spi2_transfer((uint8_t)(address | 0x80U));
    const uint8_t value = spi2_transfer(0xFFU);
    spi2_deselect();
    return value;
}

static void write_register(uint8_t address, uint8_t value)
{
    spi2_select();
    (void)spi2_transfer(address);
    (void)spi2_transfer(value);
    spi2_deselect();
}

static uint16_t fifo_count(void)
{
    const uint16_t low = read_register(IIS3DWB_FIFO_STATUS1);
    const uint16_t high = read_register(IIS3DWB_FIFO_STATUS2) & 0x03U;
    return (uint16_t)(low | (high << 8));
}

static uint32_t fifo_read_sample(int16_t *x, int16_t *y, int16_t *z)
{
    uint8_t frame[7];
    spi2_select();
    (void)spi2_transfer((uint8_t)(IIS3DWB_FIFO_DATA_OUT_TAG | 0x80U));
    for (uint32_t index = 0U; index < 7U; ++index) {
        frame[index] = spi2_transfer(0xFFU);
    }
    spi2_deselect();

    if (((frame[0] >> 3) & 0x1FU) != IIS3DWB_FIFO_TAG_ACCEL) {
        return 0U;
    }

    *x = (int16_t)((uint16_t)frame[1] | ((uint16_t)frame[2] << 8));
    *y = (int16_t)((uint16_t)frame[3] | ((uint16_t)frame[4] << 8));
    *z = (int16_t)((uint16_t)frame[5] | ((uint16_t)frame[6] << 8));
    return 1U;
}

uint32_t iis3dwb_init(void)
{
    spi2_init();
    if (read_register(IIS3DWB_WHO_AM_I) != 0x7BU) {
        return 0U;
    }

    write_register(IIS3DWB_CTRL3_C, 0x44U);  /* BDU + register auto-increment */
    write_register(IIS3DWB_CTRL1_XL, 0xA4U); /* three axes, ±16 g */
    write_register(IIS3DWB_FIFO_CTRL1, 64U);
    write_register(IIS3DWB_FIFO_CTRL3, 0x0AU); /* batch accelerometer at 26,667 Hz */
    write_register(IIS3DWB_INT2_CTRL, 0x08U);  /* FIFO watermark */
    write_register(IIS3DWB_FIFO_CTRL4, 0x06U); /* continuous mode */
    return 1U;
}

uint32_t iis3dwb_capture_window(float *rms_counts, uint32_t *sample_count,
                                uint32_t *dropped_windows)
{
    float history[9] = {0.0F};
    float square_sum = 0.0F;
    uint32_t phase = 0U;
    uint32_t outputs = 0U;
    uint32_t raw_count = 0U;
    uint32_t block_index = 0U;
    uint32_t block_fill = 0U;
    uint32_t windows_dropped = 0U;

    while (outputs < VIBRATION_WINDOW_SAMPLES) {
        if (fifo_count() == 0U) {
            continue;
        }

        const uint8_t fifo_status = read_register(IIS3DWB_FIFO_STATUS2);
        if ((fifo_status & IIS3DWB_FIFO_OVERRUN_MASK) != 0U) {
            ++windows_dropped;
        }

        int16_t x;
        int16_t y;
        int16_t z;
        if (fifo_read_sample(&x, &y, &z) == 0U) {
            ++windows_dropped;
            continue;
        }
        (void)y;
        (void)z;

        sample_blocks[block_index][block_fill++] = x;
        if (block_fill == SAMPLE_BLOCK_SAMPLES) {
            block_index ^= 1U;
            block_fill = 0U;
        }

        for (uint32_t tap = 8U; tap > 0U; --tap) {
            history[tap] = history[tap - 1U];
        }
        history[0] = (float)x;
        float filtered = 0.0F;
        for (uint32_t tap = 0U; tap < 9U; ++tap) {
            filtered += history[tap] * resample_fir[tap];
        }

        phase += IIS3DWB_ODR_RATIO_UP;
        if (phase >= IIS3DWB_ODR_RATIO_DOWN) {
            phase -= IIS3DWB_ODR_RATIO_DOWN;
            square_sum += filtered * filtered;
            ++outputs;
        }
        ++raw_count;
    }

    *rms_counts = __builtin_sqrtf(square_sum / (float)outputs);
    *sample_count = outputs;
    *dropped_windows = windows_dropped;
    (void)raw_count;
    return 1U;
}
