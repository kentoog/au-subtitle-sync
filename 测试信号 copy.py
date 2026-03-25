import mido
import time

# 1. 自动搜索匹配的端口名
def find_port():
    input_names = mido.get_input_names()
    print(f"当前系统可用端口: {input_names}")
    for name in input_names:
        if 'AU_MTC' in name: # 只要包含这个关键词就行
            return name
    return None

target_port = find_port()

if not target_port:
    print("❌ 错误：未找到包含 'AU_MTC' 的 loopMIDI 端口，请检查 loopMIDI 是否运行。")
else:
    print(f"✅ 已找到端口: {target_port}")
    # 模拟一个 12 位的 Mackie 时间显示器
    # 索引 0-11 分别对应 Mackie 的 12 个显示位置
    time_display = [" "] * 12

    try:
        with mido.open_input(target_port) as inport:
            print("⏳ 正在监听 Audition 信号，请在 AU 中点击播放...")
            for msg in inport:
                # 过滤 Mackie 控制台的时间 CC 信号 (64-75)
                if msg.type == 'control_change' and 64 <= msg.control <= 75:
                    # 映射：CC 75 是左边第一位，CC 64 是右边最后一位
                    index = 75 - msg.control 
                    if 0 <= index < 12:
                        # 转换十六进制值为字符
                        time_display[index] = chr(msg.value)
                        
                        # 拼接字符串并实时刷新显示
                        current_time_raw = "".join(time_display)
                        # 清理掉多余空格，格式化输出
                        print(f"\r播放头位置: {current_time_raw}", end="", flush=True)

    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"\n发生错误: {e}")