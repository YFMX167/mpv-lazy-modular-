# 本地验证记录

测试日期：2026-10-18（Asia/Shanghai）。这是一台实际 Fedora 桌面上的短时合成素材验证，不是所有媒体格式的兼容性认证。

## 环境

- Fedora 44 KDE，Wayland；AMD Radeon RX 9070 XT（RADV GFX1201）。
- Mesa 26.2.4；当前显示模式 3840×2160@120Hz；KDE HDR/WCG 开启。
- mpv RPM：`mpv-0.41.0-5.fc44.x86_64`。
- libplacebo RPM：`libplacebo-7.360.1-3.fc44.x86_64`。
- Mesa Vulkan RPM：`mesa-vulkan-drivers-26.2.4-1.fc44.x86_64`。
- FFmpeg RPM：`ffmpeg-8.1.3-1.fc44.x86_64`。mpv 显示 FFmpeg 编译时 8.0.1、运行时 8.1.3。
- 驱动输出 `radv is not a conformant Vulkan implementation, testing use only` 警告；渲染仍成功，保留此限制，不隐藏警告。

## 已执行

| 检查 | 实际结果 |
|---|---|
| 固定依赖安装 | 10 个资源经 SHA-256 校验，release 成功激活 |
| 幂等安装 | 再次执行提示 Already installed，没有重复 release |
| 备份 | 本机生成归档；不包含媒体文件 |
| 安装管理测试 | 4 个测试通过：越界拒绝、校验失败、更新失败保留当前版本、安装/更新/备份/回滚/篡改检测 |
| film | 合成 720p24 FFV1，gpu-next + Vulkan 播放 3 秒，退出码 0 |
| anime | 同素材加载五个不同的固定 Anime4K shader 文件（一个重复 upscale pass），编译成功，退出码 0 |
| 4K 全屏动漫 | 日志确认渲染窗口 3840×2160；首次约 3 秒测试出现 3 次丢帧；缓存后 4 秒复测状态显示 dropped=0 |
| uosc/缩略图 | Lua 正常加载；日志确认 uosc 向 thumbfast 请求缩略图，并通过 overlay-add 显示 BGRA 缩略图 |
| HDR | 合成 1080p24、10-bit、BT.2020/PQ 标记 FFV1；选中 `A2B10G10R10_UNORM_PACK32 + HDR10_ST2084` surface，退出码 0 |
| HDR 转 SDR | 同素材选中 `SRGB_NONLINEAR` surface，退出码 0 |
| 播放后完整性 | doctor 返回 integrity=OK |
| RIFE 适配器 | 命令行帮助/语法检查通过；未构建二进制、未推理 |

首轮全屏丢帧与初次 shader 编译时间相伴；缓存后结果改善，但短时测试不足以证明原因唯一或长期零丢帧。
启动/退出缩略图子进程时可出现 `Subprocess failed: killed`，在本次日志中发生于播放器正常退出阶段。
未将原始日志提交到仓库，避免暴露路径、设备标识或媒体信息。

## 尚未验收

- 真正 HDR 影片、HDR10 元数据、电视峰值亮度/色准、HDMI 位深与色度抽样的外部测量。
- HEVC/AV1/H.264 硬解、Dolby Vision、音频直通、字幕字体覆盖及长时间音画同步。
- 真实 4K 高码率内容的长时丢帧、显存和功耗；合成 FFV1 测试未证明硬件解码。
- RIFE Vulkan 的 Fedora 44 编译、模型许可逐项审阅、推理与吞吐；没有实时补帧结论。
- uosc 可选在线字幕下载辅助程序未安装。

原有 `~/.config/mpv` 未导入、未覆盖。所有测试使用项目专属 config-dir，未修改系统显示参数或默认应用关联。
