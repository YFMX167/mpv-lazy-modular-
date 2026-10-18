# RIFE Vulkan：可选离线实验模块

默认不下载、不编译、不加载到 mpv。主播放器不依赖此模块。
固定官方 `20221029` 版本，对应提交见 `source.lock.json`；这不是声称最新或最佳模型。
本项目仅提供 SDR PNG 帧目录适配器。**未验证 Fedora 44 上的 RIFE 编译、推理性能或画质；不承诺 4K/120fps 实时补帧。**

## 单独构建（用户明确选择后）

需要 `git cmake gcc-c++ vulkan-headers vulkan-loader-devel`，可通过 Fedora 包管理器安装。
在独立工作目录执行：

```bash
git clone --no-checkout https://github.com/nihui/rife-ncnn-vulkan.git rife-src
git -C rife-src checkout --detach a7532fc3f9f8f008cd6eecd6f2ffe2a9698e0cf7
git -C rife-src submodule update --init --recursive
cmake -S rife-src/src -B rife-src/build -DCMAKE_BUILD_TYPE=Release
cmake --build rife-src/build -j 4
sha256sum rife-src/build/rife-ncnn-vulkan
```

子模块由固定父提交锁定；不执行 `git submodule update --remote`。本机构建的二进制校验值用于防止后续误替换，并不构成第三方来源认证。模型从同一固定源码目录选取，检查该模型许可，不混用来历不明的模型。

## 运行与基准

先只测试 2–5 秒、低分辨率 SDR 片段。PNG 会占用大量磁盘空间。视频提取、音频、变帧率、字幕、时长与最终封装需要另外处理；脚本不猜测帧率，也不转换 HDR。

```bash
python3 modules/rife/interpolate.py \
  --binary /absolute/rife-src/build/rife-ncnn-vulkan \
  --sha256 YOUR_VERIFIED_SHA256 \
  --model /absolute/rife-src/models/rife-v4.6 \
  --input /absolute/sdr-png-frames \
  --output /absolute/new-output-frames \
  --frames 96 --gpu 0
```

输出目录必须不存在；失败保留中间结果方便诊断。`--frames` 是目标帧数，不是帧率。可变时间步需要支持的模型（如 v4），以固定上游文档为准。
脚本打印实际离线吞吐量；包含 PNG I/O，不能外推为 mpv 实时表现。检查切镜、遮挡、字幕、运动边缘的伪影。胶片电影默认保留原帧率。
HDR/PQ/HLG/Dolby Vision 不进入此 8-bit PNG 工作流；它不保留 HDR 元数据和完整色彩链路。
停用方式是停止调用此目录的脚本；不影响 MPV-LAZY。

上游用法与许可证：[rife-ncnn-vulkan 固定源码](https://github.com/nihui/rife-ncnn-vulkan/tree/a7532fc3f9f8f008cd6eecd6f2ffe2a9698e0cf7)。
