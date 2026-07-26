# I3C SDR Decoder

An I3C SDR (Single Data Rate) protocol decoder based on the [DSView](https://github.com/DreamSourceLab/DSView) platform.

> Currently only supports I3C SDR mode. HDR mode will be added in a future release.

## Features

| Feature | Description |
|---------|-------------|
| Dynamic Address Assignment (DAA) | Master dynamically assigns slave addresses |
| Private Read | Private read transfer |
| Private Write | Private write transfer |
| Broadcast CCC | Broadcast common command |
| Direct CCC | Direct common command |
| IBI (In-Band Interrupt) | In-band interrupt |
| Parity Check | Automatic Tbit / PAR parity error detection with warnings |
| Address Format Toggle | Supports shifted / unshifted address display formats |

## Requirements

- **DSView** >= v1.3.2 (the decoder relies on certain APIs; older versions may not be compatible)
- Signal channels: `SCL` (clock), `SDA` (data)

## Installation

1. Install DSView
2. Open the DSView installation directory and locate the `decoders` folder
3. Copy the `i3c_sdr` directory into `decoders`
4. Restart DSView and search for **I3C SDR** in the protocol decoder list

![i3c_decoder](./img/i3c_decoder.png)

## Decode Examples

### Dynamic Address Assignment (DAA)

Master sends the reserved byte `0x7E`, the slave returns a 48-bit ID, BCR, and DCR, then the Master assigns a 7-bit dynamic address.

![dynamic_address](./img/dynamic_address.png)

### Private Read

![private_read](./img/private_read.png)

### Private Write

![private_write](./img/private_write.png)

### Broadcast CCC

![broadcast_ccc](./img/broadcast_ccc.png)

### Direct CCC

![direct_ccc](./img/direct_ccc.png)

## Project Structure

```
i3c_sdr_decoder/
├── i3c_sdr/                    # Decoder source
│   ├── __init__.py
│   └── pd.py                   # Main decoding logic
├── test/                       # Test data (DSView .dsl files)
│   ├── dynamic_address.dsl
│   ├── private_read.dsl
│   ├── private_write.dsl
│   ├── broadcast_ccc.dsl
│   └── direct_ccc.dsl
├── i3c_basic_specification/    # I3C Basic specification documents
├── img/                        # Screenshots
├── README.MD                   # Chinese documentation
└── README_EN.md                # English documentation
```

## References

- [MIPI I3C Basic Specification v1.1.1](./i3c_basic_specification/mipi_I3C-Basic_specification_v1-1-1.pdf)