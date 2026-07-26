# Project Introduction

An I3C protocol decoder based on the DSView platform. Currently, the decoder only supports I3C SDR mode. HDR mode will be added in future updates.

# DSView Platform Version Requirements

This decoder was developed using DSView v1.3.2. Since the decoder relies on some DSView platform APIs, it is recommended to use this version or higher (older versions may lack some required APIs).

# How to Add the Decoder to DSView Platform

After installing DSView, open the installation directory and locate the `decoders` folder. Copy the `i3c_sdr` directory into this folder. You can then search for the I3C decoder in DSView.

![i3c_decoder](./img/i3c_decoder.png)

# Decoder Features Overview

## Dynamic Address Assignment (DAA)

The I3C protocol supports dynamic address assignment by the Master.

![dynamic_address](./img/dynamic_address.png)

CCC commands, IBI, etc., work similarly to dynamic address assignment.

## Private Read Mode

The I3C protocol supports private read mode.

![private_read](./img/private_read.png)

## Private Write Mode

The I3C protocol supports private write mode.

![private_write](./img/private_write.png)

### Broadcast CCC

The I3C protocol supports broadcast CCC mode.

![broadcast_ccc](./img/broadcast_ccc.png)

### Direct CCC

The I3C protocol supports direct CCC mode.

![direct_ccc](./img/direct_ccc.png)
