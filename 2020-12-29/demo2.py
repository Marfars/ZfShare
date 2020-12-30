# coding=utf-8
from unicorn import *
from unicorn.arm_const import *
import binascii


def writ_to_file(content):
    fp = open("./test.txt", "a", encoding="utf-8")
    fp.write(content + "\n")
    fp.close()


# 目标代码执行一次，他就执行一次
def hook_code(uc, address, size, userdata):
    writ_to_file(">>> Tracing instruction at 0x%x, instruction size = 0x%x" % (address, size))


# 所有未映射内存访问的事件发生一次，就执行一次
def hook_memory(uc, access, address, size, value, userdata):
    pc = uc.reg_read(UC_ARM_REG_PC)
    writ_to_file("memory error: pc:%x address:%x size:%x" % (pc, address, size))


a1 = b'123'
mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)

# 映射内存
image_base = 0x0
image_size = 0x10000 * 8
mu.mem_map(image_base, image_size)

# 加载so库
binary = open('libnative-lib.so', 'rb').read()
mu.mem_write(image_base, binary)

# 映射栈
stack_base = 0xa0000
stack_size = 0x10000 * 3
stack_top = stack_base + stack_size - 0x4
mu.mem_map(stack_base, stack_size)
mu.reg_write(UC_ARM_REG_SP, stack_top)

# 写入数据段
data_base = 0xf0000
data_size = 0x10000 * 3
mu.mem_map(data_base, data_size)
mu.mem_write(data_base, a1)
mu.reg_write(UC_ARM_REG_R0, data_base)

# 目前不需要关注这个，这个是模拟IDA对汇编代码进行了一个重定位
mu.mem_write(0x1EDB0, b'\xD9\x98\x00\x00')

# 设置hook函数
mu.hook_add(UC_HOOK_CODE, hook_code, 0)
mu.hook_add(UC_HOOK_MEM_UNMAPPED, hook_memory, 0)

# 设置虚拟器执行的起始和终止内存地址
target = image_base + 0x9B68
target_end = image_base + 0x9C2C

# start
try:
    mu.emu_start(target + 1, target_end)
    r2 = mu.reg_read(UC_ARM_REG_R2)
    result = mu.mem_read(r2, 16)

    print(binascii.b2a_hex(result))

except UcError as e:
    print(e)
