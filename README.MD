# 项目介绍

一个基于 DSView 平台的 I3C 协议解码器。当前解码器只支持 I3C SDR 模式。后续迭代更新 HDR 模式。

# DSView 平台版本需求

开发该解码器时使用的是 DSView v1.3.2 版本，由于解码器中依赖一些 DSView 平台的 API，最好使用该版本或更高版本（低版本有些 API 可能没有）。

# 如何添加解码器到 DSView 平台

安装 DSView 平台后，打开安装目录，找到 `decoders` 目录，将 `i3c_sdr` 目录复制到该目录下。然后就可以在 DSView 中搜索到 I3C 解码器。

![i3c_decoder](./img/i3c_decoder.png)


# 解码器功能一览

## 动态地址分配

I3C 协议支持 Master 动态地址分配。
    
![dynamic_address](./img/dynamic_address.png)

ccc指令 ibi 等与 dynamic address 类似。

## private read 模式

I3C 协议支持 private read 模式。

![private_read](./img/private_read.png)

## private write 模式

I3C 协议支持 private write 模式。

![private_write](./img/private_write.png)

### broadcast ccc

I3C 协议支持 broadcast ccc 模式。

![broadcast_ccc](./img/broadcast_ccc.png)

### direct ccc

I3C 协议支持 direct ccc 模式。

![direct_ccc](./img/direct_ccc.png)
