'''
author: jixua.chen
date: 2025-08-15
version: v1.0
TODO: detect reset pattern and hdr exit mode

'''

import sigrokdecode as srd

# CMD: [annotation-type-index, long annotation, short annotation]
ann_table = {
    'START':                    [0, 'Start', 'S'],
    'REPEAT START':             [1, 'Repeated start', 'Sr'],
    'STOP':                     [2, 'Stop', 'P'],
    'ACK WITH HANDOFF':         [3, 'ACK with handoff', 'A+H'],
    'ACK WITHOUT HANDOFF':      [4, 'ACK without handoff', 'A-H'],
    'NACK':                     [5, 'NACK', 'N'],
    'TBIT PARITY':              [6, 'Tbit parity', 'TP'],
    'TBIT END OF DATA':         [7, 'Tbit end of data', 'TE'],
    'BIT':                      [8, 'Bits', 'B'],
    'ADDRESS READ':             [9,'Address read', 'AR'],
    'ADDRESS WRITE':            [10,'Address write', 'AW'],
    'I3C CCC COMMAND':          [11, 'I3C CCC command', 'CCC'],
    'I3C ID':                   [12, 'I3C ID', 'ID'],
    'I3C BCR':                  [13, 'I3C BCR', 'BCR'],
    'I3C DCR':                  [14, 'I3C DCR', 'DCR'],
    'I3C ASSIGN ADDRESS':       [15, 'I3C assign address', 'AA'],
    'I3C RESERVED BYTE':        [16, 'I3C reserved byte', 'RB'],
    'I3C DATA READ':            [17, 'I3C data read', 'DR'],
    'I3C DATA WRITE':           [18, 'I3C data write', 'DW'],
    'WARNINGS':                 [19, 'Warnings', 'Warnings'],
    'I3C PARITY':               [20, 'I3C parity bit', 'PAR'],
}

class Decoder(srd.Decoder):
    # 说明需要安装的python版本
    api_version = 3
    # 协议标识，必须唯一
    id = 'i3c_sdr'
    # 协议名称, 不一定要求跟标识一致
    name = 'I3C SDR'
    # 协议长名称
    longname = 'Improved Inter-Integrated Circuit Single Data Rate'
    # 简介内容
    desc = 'Two-wire, multi-master, multi-slave serial bus.'
    # 开源协议
    license = 'gplv2+'
    # 接收的输入的数据源名，如果是多层协议一起工作，可使用上一个协议的输出名
    inputs = ['logic']
    # 输出的数据源名，多层协议模式下，可作为下层协议的输入数据源名
    outputs = ['i3c_sdr']
    # 适用范围标签
    tags = ['Embedded/industrial']

    # 必须要绑定的通道定义，将在界面上可见
    # id:通道标识, 任意命名
    # type:类型，根据需要设置一个值, -1:COMMON,0:SCLK,1:SDATA,2:ADATA
    # name:标签名
    # desc:该通道的说明
    # 注意元组的最后的逗号不能少
    channels = (
        {'id': 'scl','type': 8 ,'name': 'SCL', 'desc': 'Serial clock line'},
        {'id': 'sda', 'type': 108 ,'name': 'SDA', 'desc': 'Serial data line'},
    )

    # 可选通道，其它跟上面的一样
    options = (
        {'id': 'address_format' , 'desc': 'Displayed slave address format',
         'default': 'unshifted', 'values': ('unshifted', 'shifted')},
    )

    # 解析结果项定义
    # annotations里的每一项可以有2到3个属性，当有３个属性时，第一个表示类型
    # 类型对应0-16个颜色，当类型范围在200-299时，将绘制边沿箭头
    annotations = (
        ('7','start','Start condition'),                            #0
        ('6','repeat_start','Repeated start condition'),            #1
        ('1','stop','Stop condition'),                              #2
        ('4','ack_with_handoff','ACK with handoff'),                #3
        ('5','ack_without_handoff','ACK without handoff'),          #4
        ('0','nack','NACK'),                                        #5
        ('9','t_parity','Tbit parity'),                             #6
        ('11','t_end_of_data','Tbit end of data'),                  #7
        ('208','bit','Data/address bit'),                           #8
        ('112','address_read','Address read'),                      #9
        ('111','address_write','Address write'),                    #10
        ('113','i3c_ccc','I3C CCC command'),                        #11
        ('110','i3c_id','I3C ID'),                                  #12
        ('110','i3c_bcr','I3C BCR'),                                #13
        ('110','i3c_dcr','I3c DCR'),                                #14
        ('113','i3c_assign_address','I3c assign address'),          #15
        ('114','i3c_reserved_byte','I3c reserved byte (0x7E)'),     #16
        ('110','i3c_data_read','I3c data read'),                    #17
        ('110','i3c_data_write','I3c data write'),                  #18
        ('1000','warnings','Human-readable warnings'),              #19
        ('9','i3c_par', 'I3C parity bit'),                          #20
    )

    # 解析结果行定义
    annotation_rows = (
        ('bits', 'Bits', (8,)),
        ('addr-data', 'Address/Data', (0,1,2,3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,20,)),
        ('warnings', 'Warnings', (19,)),
    )


    # 构造函数，自动被调用
    def __init__(self):
         # 这里调用一个类成员函数，完成一些参数的初始化
        self.reset()
    
    # 重置函数，在这里做一些重置和定义类私有变量工作
    def reset(self):
        self.sp = self.ep = self.sp_byte = -1
        self.is_repeat_start = False
        self.data_byte = 0
        self.bit_count = 0
        self.wr = -1
        self.bits = []
        self.bitwidth = 1
    
    # 开始执行解码任务时，由c底层代码自动调用一次
    # 这里，完成一些解码结果项annotation类型的注册
    # 类型有: OUTPUT_ANN，OUTPUT_PYTHON，OUTPUT_BINARY，OUTPUT_META
    # self.register函数是c底层类提供的
    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    # 定义一个输出函数
    # a,b为采样位置的起点和终点
    # ann为annotations定义的项序号
    # data是一个列表，列表里有１到３个字符串，它们将显示到屏幕
    # annotation输出到哪一行由annotation_rows决定
    # self.out_ann就是上面注册的消息类型了
    # self.put是c底层类提供的函数
    def put_ann(self,data):
        self.put(self.sp,self.ep,self.out_ann,data)

    # output python
    def put_python(self, data):
        self.put(self.sp, self.ep, self.out_python, data)
    
    # 计算奇偶校验
    def odd_parity_bit(self, x: int, width: int = None) -> int:
        """
        返回 x 在指定位宽内的奇校验位：
        - 若该位宽内 1 的个数为偶数，返回 1(使总数变奇)
        - 若该位宽内 1 的个数为奇数，返回 0
        兼容性：若不传 width,默认按 8 位计算，保持与旧代码一致。
        """
        if width is None:
            width = 8
        if width <= 0:
            # 0 个 1 视为偶数，需要返回 1 以使总数变奇
            return 1

        mask = (1 << width) - 1
        x &= mask
        try:
            ones = x.bit_count()
        except AttributeError:
            # 兼容老 Python：Kernighan 算法统计 1 的个数
            ones = 0
            y = x
            while y:
                y &= y - 1
                ones += 1
        # 若 1 的个数为偶数，返回 1；否则返回 0
        return (ones ^ 1) & 1

    # 处理开始事件
    def handle_start(self):
        self.sp , self.ep = self.samplenum,self.samplenum
        cmd = 'REPEAT START' if self.is_repeat_start else 'START'
        self.put_ann([ann_table[cmd][0], ann_table[cmd][1:]])
        ret_str = 'repeat_start' if self.is_repeat_start else 'start'
        self.is_repeat_start = True
        return ret_str

    # 处理STOP事件
    def handle_stop(self):
        cmd = 'STOP'
        self.sp , self.ep = self.samplenum, self.samplenum
        self.put_ann([ann_table[cmd][0], ann_table[cmd][1:]])
        self.is_repeat_start = False
        self.wr = -1
        self.bits = []
        return 'stop'
    
    # 处理 ack with handoff事件
    def handle_ack_handoff(self,sda):
        self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
        cmd = 'NACK' if(sda == 1) else 'ACK WITH HANDOFF'
        self.put_ann([ann_table[cmd][0], ann_table[cmd][1:]])
        return 'ack_handoff' if(sda == 0) else 'NACK'
    
    # 处理 ack without handoff事件
    def handle_ack_without_handoff(self,sda):
        self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
        cmd = 'NACK' if(sda == 1) else 'ACK WITHOUT HANDOFF'
        self.put_ann([ann_table[cmd][0], ann_table[cmd][1:]])
        return 'ack_without_handoff' if (sda == 0) else 'NACK'

    # 处理 Tbit
    def handle_Tbit(self,sda,compare_byte,rw):
        self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
        cmd = 'TBIT PARITY' if rw == 1 else 'TBIT END OF DATA'
        self.put_ann([ann_table[cmd][0], ['%s: {$}' % ann_table[cmd][1], '%s: {$}' % ann_table[cmd][2], '{$}', sda]])
        # 判断奇偶校验位是否正确
        if rw == 1:
            # 如果是写操作，检查奇偶校验位
            if sda != self.odd_parity_bit(compare_byte,8):
                # 如果不正确，输出警告
                self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
                self.put_ann([ann_table['WARNINGS'][0], ['Tbit parity error']])
        return 'T_bit'
    
    #处理 PAR
    def handle_PAR(self,sda,compare_data):
        self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
        self.put_ann([ann_table['I3C PARITY'][0], ['%s: {$}' % ann_table['I3C PARITY'][1], '%s: {$}' % ann_table['I3C PARITY'][2], '{$}', sda]])
        if sda != self.odd_parity_bit(compare_data,7):
            # 如果不正确，输出警告
            self.sp, self.ep = self.sp_byte, self.sp_byte + self.bitwidth
            self.put_ann([ann_table['WARNINGS'][0], ['PAR parity error']])
        return 'PAR'

    
    # 处理expect_num个数据
    def deal_num_bit_data(self,bit_count,data_byte,bits,samplenum,expect_bits):
        self.bit_count = bit_count
        self.data_byte = data_byte
        self.bits = bits
        self.sp_byte = samplenum
        while self.bit_count < expect_bits:
            # 等待状态
            (scl,sda) = self.wait([{0: 'r'},{0: 'h',1: 'f'},{0: 'h',1: 'r'}])
            # 判断是否匹配到start或者stop
            if (self.matched & (0b1 << 1)):
                # 如果是开始条件
                return self.handle_start()
            elif (self.matched & (0b1 << 2)):
                # 如果是停止条件
                return self.handle_stop()
            # 逐字节保存数据到data_byte
            self.data_byte <<= 1
            self.data_byte |= sda

            if self.bit_count == 0:
                self.sp_byte = self.samplenum
        
            # 将bit存入bits列表
            self.bits.insert(0,[sda,self.samplenum,self.samplenum])

            if self.bit_count > 0:
                self.bits[1][2] = self.samplenum

            if (self.bit_count == expect_bits - 1) and (self.bit_count > 2):
                self.bitwidth = self.bits[1][2] - self.bits[2][2]
                self.bits[0][2] += self.bitwidth

            self.bit_count += 1
        # 如果selif.bitcount为1, 则重新计算self.bitwidth
        if self.bit_count == 1:
            self.wait([{0: 'f'},{0: 'h',1: 'f'},{0: 'h',1: 'r'}])
            # 判断是否匹配到start或者stop
            if (self.matched & (0b1 << 1)):
                # 如果是开始条件
                return self.handle_start()
            elif (self.matched & (0b1 << 2)):
                # 如果是停止条件
                return self.handle_stop()
            self.bitwidth = self.samplenum - self.sp_byte
        return 'DATA'

    
    # 处理读写数据
    def handle_write_read_data(self,rw_state):
        # 接收一个字节
        ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,8)
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state
        
        #保存接收到的字节
        rev_byte = self.data_byte

        # 输出bit数据到屏幕
        self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
        for bit in self.bits:
            self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
        
        #输出data到屏幕
        cmd = 'I3C DATA WRITE' if rw_state == 1 else 'I3C DATA READ'
        self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
        self.put_ann([ann_table[cmd][0],['%s: {$}' % ann_table[cmd][1], '%s: {$}' % ann_table[cmd][2] , '{$}',self.data_byte] ])

        # 判断Tbit
        ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state
        # 如果是数据返回Tbit
        return self.handle_Tbit(self.data_byte,rev_byte,rw_state)
    
    # 处理I3C留字节(0x7e)和target地址
    def handle_reserved_byte_or_address(self):

        # 读取1个字节
        ret_stat = self.deal_num_bit_data(0,0,[],self.samplenum,8)

        if ret_stat == 'start' or ret_stat == 'repeat_start' or ret_stat == 'stop':
            return ret_stat

        now_byte = self.data_byte
        if self.options['address_format'] == 'shifted':
            # 如果是shifted格式，去掉最低位
            now_byte >>= 1
        
        # wr = 0代表读，wr = 1代表写
        self.wr = 0 if (self.data_byte & 1) else 1

        # 输出数据到屏幕
        self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
        for bit in self.bits:
            self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])

        # 判断当前是否为保留字节
        if (self.data_byte >> 1) == 0x7e:
            cmd = 'I3C RESERVED BYTE'
            ret_stat = 'reserved_byte'
        else:
            # 不是保留字节，应该是目标地址
            if self.wr == 0:
                # 读操作
                cmd = 'ADDRESS READ'
            else:
                # 写操作
                cmd = 'ADDRESS WRITE'
            ret_stat = 'target_address'
        self.sp, self.ep = self.sp_byte, self.samplenum
        self.put_ann([ann_table[cmd][0],['%s: {$}' % ann_table[cmd][1], '%s: {$}' % ann_table[cmd][2] , '{$}', now_byte] ])
        
        # 输出wr到屏幕
        self.sp, self.ep = self.samplenum, self.samplenum + self.bitwidth
        w = [0,['Write','Wr','w']] if self.wr else [1,['Read','Rd','r']]
        self.put_ann(w)

        return  ret_stat

    # 处理私有读写,无reserved byte(0x7e)
    def handle_private_write_read_without_reserved(self):
        # 读取数据
        while True:
            ret_state = self.handle_write_read_data(self.wr)
            if ret_state != 'T_bit':
                return ret_state

    # 处理私有读写,有reserved byte(0x7e)
    def handle_private_write_read_with_reserved(self):
        # 此处应该是目标地址
        ret_state = self.handle_reserved_byte_or_address()
        if ret_state == 'stop' or ret_state == 'start' or ret_state == 'repeat_start':
            return ret_state

        # 如果是保留地址输出警告信息
        if ret_state == 'reserved_byte':
            self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
            self.put_ann([ann_table['WARNINGS'][0], ['reserved byte (0x7E) should not be target address']])
        
        if self.wr == 0:
            func_handle_ack = self.handle_ack_without_handoff
        else:
            func_handle_ack = self.handle_ack_handoff

        # 等待ACK handoff
        ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state
        # 收到ACK handoff
        if func_handle_ack(self.data_byte) == 'NACK':
            # 等待stop
            while True:
                ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
                if ret_state != 'DATA':
                    return ret_state
        # 处理数据
        while True:
            rw_state = self.handle_write_read_data(self.wr)
            if rw_state != 'T_bit':
                return rw_state
    
    # 处理动态地址分配
    def handle_dynamic_address_assignment(self):
        while True:
            # 等待开始条件
            self.wait([{0:'h',1: 'f'},{0:'h',1: 'r'}])
            if self.matched & (0b1 << 0):
                self.handle_start()
            elif self.matched & (0b1 << 1):
                return self.handle_stop()
        
            # 处理reserved byte
            ret_state = self.handle_reserved_byte_or_address()
            if ret_state == 'stop' or ret_state == 'start' or ret_state == 'repeat_start':
                return ret_state

            # 处理ACK without handoff
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            ret_state = self.handle_ack_without_handoff(self.data_byte)
            # 如果是NACK则等待STOP 
            if ret_state == 'NACK':
                # 等待stop
                while True:
                    ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
                    if ret_state != 'DATA':
                        return ret_state
        
            # 处理从机返回的数据-> ID
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,48)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 输出bit数据到屏幕
            self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
            for bit in self.bits:
                self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
            # 输出ID
            self.put_ann([ann_table['I3C ID'][0], ['%s: {$}' % ann_table['I3C ID'][1], '%s: {$}' % ann_table['I3C ID'][2] , '{$}',self.data_byte] ])

            # 处理从机返回的数据-> BCR
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,8)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 输出bit数据到屏幕
            self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
            for bit in self.bits:
                self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
            # 输出BCR
            self.put_ann([ann_table['I3C BCR'][0], ['%s: {$}' % ann_table['I3C BCR'][1], '%s: {$}' % ann_table['I3C BCR'][2] , '{$}',self.data_byte] ])

            # 处理从机返回的数据-> DCR
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,8)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 输出bit数据到屏幕
            self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
            for bit in self.bits:
                self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
            # 输出DCR
            self.put_ann([ann_table['I3C DCR'][0], ['%s: {$}' % ann_table['I3C DCR'][1], '%s: {$}' % ann_table['I3C DCR'][2] , '{$}',self.data_byte] ])

            # 处理从机返回的数据-> 赋值地址
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,7)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 输出bit数据到屏幕
            self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
            for bit in self.bits:
                self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
            # 输出赋值地址
            self.put_ann([ann_table['I3C ASSIGN ADDRESS'][0], ['%s: {$}' % ann_table['I3C ASSIGN ADDRESS'][1], '%s: {$}' % ann_table['I3C ASSIGN ADDRESS'][2] , '{$}',self.data_byte] ])
            rev_dddress = self.data_byte

            # 处理PAR
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 输出PAR
            self.handle_PAR(self.data_byte,rev_dddress)

            # 处理ACK without handoff
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            self.handle_ack_without_handoff(self.data_byte)
        
    # 处理broadcast ccc
    def handle_broadcast_ccc(self):
        while True:
            ret_state = self.handle_write_read_data(1)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state

    # 处理direct ccc
    def handle_direct_ccc(self):
        # 处理defining byte
        while True:
            ret_state = self.handle_write_read_data(1)
            if ret_state == 'start' or ret_state == 'stop':
                return ret_state
            elif ret_state == 'repeat_start':
                break
            else:
                continue
        # 处理后续
        while True:
            # 处理目标地址
            ret_state = self.handle_reserved_byte_or_address()
            if ret_state == 'stop' or ret_state == 'start' or ret_state == 'repeat_start':
                return ret_state
            
            # 如果是reserved应该输出警告信息
            if ret_state == 'reserved_byte':
                # 如果是保留字节，输出警告
                self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
                self.put_ann([ann_table['WARNINGS'][0], ['Reserved byte (0x7E) should not be target address']])

            # 处理ACK
            ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                return ret_state
            # 根据wr选择ack处理函数
            ack_fun = self.handle_ack_without_handoff if self.wr == 0 else self.handle_ack_handoff
            ret_state = ack_fun(self.data_byte)
            if ret_state == 'NACK':
                # 等待stop
                while True:
                    ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
                    if ret_state != 'DATA':
                        return ret_state
            
            # 处理optional write/read data
            while True:
                ret_state = self.handle_write_read_data(self.wr)
                if ret_state != 'T_bit':
                    # 如果不是Tbit则返回
                    return ret_state

    # 处理CCC指令
    def handle_ccc(self,bits,bit_count,data_byte,sp_byte):
        # 接收数据
        ret_state = self.deal_num_bit_data(bit_count,data_byte,bits,sp_byte,8)
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state

        # 保存收到的byte
        rev_byte = self.data_byte

        # 如果 ret_state 是 start 或 stop 则返回
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state

        # 输出bit数据到屏幕
        self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
        for bit in self.bits:
            self.put(bit[1],bit[2],self.out_ann,[ann_table['BIT'][0], ['%d' % bit[0]]])
        
        #输出CCC到屏幕
        cmd = 'I3C CCC COMMAND'
        self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
        self.put_ann([ann_table[cmd][0],['%s: {$}' % ann_table[cmd][1], '%s: {$}' % ann_table[cmd][2] , '{$}',self.data_byte] ])

        # 判断Tbit
        ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
        if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
            return ret_state
        self.handle_Tbit(self.data_byte,rev_byte,1)

        # 如果是ENTDAA, 则进入动态地址分配 
        if rev_byte == 0x07:
            return self.handle_dynamic_address_assignment()
        elif rev_byte <= 0x7F:
            return self.handle_broadcast_ccc()
        else:
            return self.handle_direct_ccc()

    
    # 处理CCC指令或者私有读写
    def handle_ccc_or_private_read_write(self):
        # 读取两个bit数据用于判断是private读写还是ccc
        ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,2)
        if ret_state == 'start' or  ret_state == 'repeat_start':
            # 如果是开始条件
            self.handle_start()
            return self.handle_private_write_read_with_reserved()
        elif ret_state == 'stop':
            # 如果是停止条件
            return self.handle_stop()
        elif ret_state == 'DATA':
           return self.handle_ccc(self.bits,self.bit_count,self.data_byte,self.sp_byte)

    # 解码器
    def decode(self):
        ret_state = 'stop'
        while True:
            # 等待开始条件
            if ret_state != 'start' and ret_state != 'repeat_start':
                ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
                while (ret_state != 'repeat_start') and (ret_state != 'start'):
                    ret_state = self.deal_num_bit_data(0,0,[],self.samplenum,1)
                    continue

            # 处理保留字节或者目标地址
            ret_state = self.handle_reserved_byte_or_address()

            # 如果匹配到start或者stop则重新开始解码
            if ret_state == 'start' or ret_state == 'repeat_start' or ret_state == 'stop':
                continue

            # 如果是reserved且为读,应该输出警告
            if (self.wr == 0) and (ret_state == 'reserved_byte'):
                self.sp, self.ep = self.sp_byte, self.samplenum + self.bitwidth
                self.put_ann([ann_table['WARNINGS'][0], ['Reserved byte (0x7E) should not be read']])

            # 等待ACK handoff
            ret_state_ack = self.deal_num_bit_data(0,0,[],self.samplenum,1)
            if ret_state_ack == 'start' or ret_state_ack == 'repeat_start' or ret_state_ack == 'stop':
                continue
            ack_func = self.handle_ack_without_handoff if self.wr == 0 else self.handle_ack_handoff
            # 收到ACK handoff
            if ack_func(self.data_byte) == 'NACK':
                # 等待stop
                while True:
                    ret_state = self.deal_num_bit_data(0, 0, [], self.samplenum, 1)
                    if ret_state != 'DATA':
                        # 如果不是数据则返回
                        break
                continue

            # 处理ccc或则private write read
            if ret_state == 'target_address': 
                ret_state = self.handle_private_write_read_without_reserved()
            elif ret_state == 'reserved_byte':
                ret_state = self.handle_ccc_or_private_read_write()

    