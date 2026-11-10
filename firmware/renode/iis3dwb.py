"""Renode SPI2/IIS3DWB register shim with an interleaved CWRU FIFO source."""

# Renode injects `request` and keeps script globals alive between accesses.
# ruff: noqa: F821
if "spi_registers" not in globals():
    spi_registers = {}
    spi_rx_byte = 0
    spi_command = None
    spi_phase = 0
    fifo_byte = 0
    fifo_sample = 0
    fifo_overruns = 0
    sensor_registers = {0x0F: 0x7B}
    try:
        with open("/workspace/build/cwru_iis3dwb.bin", "rb") as playback_file:
            playback_bytes = playback_file.read()
    except OSError:
        playback_bytes = b""
    playback_sample_count = len(playback_bytes) // 6
if request.isRead:
    if request.offset == 0x14:  # SPI_SR: TXP and RXP are immediately ready.
        request.value = 0x3
    elif request.offset == 0x30:  # SPI_RXDR
        request.value = spi_rx_byte
        spi_rx_byte = 0
    else:
        request.value = spi_registers.get(request.offset, 0)
elif request.isWrite:
    if request.offset == 0x20:  # SPI_TXDR, one 8-bit transfer.
        tx_byte = request.value & 0xFF
        if spi_phase == 0:
            spi_command = tx_byte
            spi_phase = 1
            fifo_byte = 0
            spi_rx_byte = 0
        elif spi_command & 0x80:
            sensor_address = spi_command & 0x7F
            if sensor_address == 0x78:
                sample_offset = fifo_sample * 6
                if fifo_sample >= playback_sample_count:
                    spi_rx_byte = 0
                elif fifo_byte == 0:
                    spi_rx_byte = 0x10  # accelerometer FIFO tag
                else:
                    spi_rx_byte = ord(playback_bytes[sample_offset + fifo_byte - 1])
                fifo_byte += 1
                if fifo_byte == 7:
                    fifo_sample += 1
                    spi_phase = 0
            else:
                remaining = max(0, playback_sample_count - fifo_sample)
                if sensor_address == 0x3A:
                    spi_rx_byte = min(remaining, 0xFF)
                elif sensor_address == 0x3B:
                    spi_rx_byte = (remaining >> 8) & 0x03
                else:
                    spi_rx_byte = sensor_registers.get(sensor_address, 0)
                spi_phase = 0
        else:
            sensor_registers[spi_command & 0x7F] = tx_byte
            spi_rx_byte = 0
            spi_phase = 0
    else:
        spi_registers[request.offset] = request.value

    if request.offset == 0x14:
        spi_registers[0x14] = 0x3
