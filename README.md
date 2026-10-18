# MPV-LAZY Modular

适用于 **Fedora 44 / KDE Wayland / AMD RX 9070 XT / LG C4 42 英寸 OLED** 的独立 mpv 配置项目。
默认电影原画模式，提供 uosc、thumbfast、Anime4K 动漫增强、HDR 输出及 HDR 转 SDR profiles。
项目代码采用 MIT；当前仓库为私人仓库，尚未向公众公开。

## 快速开始

需要 Python ≥ 3.12、mpv ≥ 0.41、Mesa Vulkan 驱动。诊断额外使用 vulkan-tools、kscreen-doctor；FFmpeg 用于生成测试素材和可选离线处理。

```bash
sudo dnf install mpv python3 mesa-vulkan-drivers vulkan-tools
# 进入本项目目录
python3 lazy.py doctor
python3 lazy.py install
./mpv-lazy /path/to/video.mkv
python3 lazy.py play -- --profile=anime /path/to/anime.mkv
python3 lazy.py play -- --profile=hdr /path/to/hdr.mkv
```

安装器不调用 sudo、不改变软件源、不改显示器设置、不覆盖 `~/.config/mpv`，也不修改默认文件关联。
所有播放器配置位于项目 `runtime/releases/`，`runtime/current` 指向启用版本。依赖缓存位于 `.cache/`。
安装后移动整个项目目录仍可通过 `python3 lazy.py` 启动。
普通 `mpv` 命令仍使用原来的配置；本项目必须通过 `lazy.py play` 启动。

| 快捷键 | profile | 行为 |
|---|---|---|
| Ctrl+0 | film | 原帧率、清除着色器、SDR 输出；默认模式 |
| Ctrl+1 | anime | SDR Anime4K Mode A Medium；手动启用 |
| Ctrl+2 | hdr | 关闭 Anime4K，向 Wayland/Vulkan 请求 HDR 色彩空间 |
| Ctrl+3 | hdr-sdr | HDR 到 BT.709 SDR 的 BT.2390 色调映射 |
| 右键 | uosc 菜单 | 轨道、字幕等本地播放控制 |

控制栏、进度条、音量与标题栏在窗口和全屏模式下常驻。右键或点击左下角菜单，前四项可直接切换电影原画、动漫增强、HDR 输出和 HDR 转 SDR；切换后显示中文提示。已有窗口需要关闭后重新打开才能加载新界面。

uosc 时间轴联动 thumbfast。网络缩略图默认关闭。未安装 uosc 的 ziggy 辅助可执行文件，因此依赖该工具的在线字幕下载等功能不在支持范围；本地菜单和缩略图不受影响。
Anime4K 会改变画面，不用于真人电影或默认 HDR；Medium 是保守起点，不是针对全部动漫的最佳画质保证。

## 版本固定与供应链

`dependencies.lock.json` 固定 uosc 5.13.0、thumbfast 提交、Anime4K 提交及每个下载文件的 SHA-256。
安装前先验证下载内容；不运行 curl 管道安装脚本。ZIP 拒绝越界路径、符号链接与过大展开，且排除附带的跨平台可执行文件。
首次校验值来自官方 HTTPS 下载，不等同于上游独立签名认证。
运行目录具有逐文件清单，启动和回滚检查完整性。项目源文件本身应通过可信 Git 提交取得。

系统 mpv/Mesa/FFmpeg 由 Fedora 管理，**不冻结系统安全更新**。实测 RPM 版本见 `docs/VALIDATION.md`，配置要求 mpv ≥ 0.41。
这保证脚本和着色器的版本可重装，不能保证不同系统驱动或编译器产生相同渲染结果。

## 更新、备份与回滚

```bash
python3 lazy.py backup
# 获取并审阅可信的新项目版本或修改 config/ 后：
python3 lazy.py update
python3 lazy.py doctor
python3 lazy.py rollback
```

`update` 仅安装当前源码与 lock 所描述的版本，不自动追踪 upstream HEAD。
每个新版本先在临时目录构建，校验完成才原子切换 `current`；旧版本保留，自动归档到 `runtime/backups/` 并记录 `previous`。
重复安装相同版本不重复生成 release。下载失败保留旧活动版本。安装与切换用文件锁互斥。
`rollback` 切回上一版本，再次执行可切回；首次安装没有 previous，明确报错。
备份包含生成的配置与依赖，不包含用户影片。自行加入配置的敏感信息也可能进入备份，应自行保管。
不自动导入原 mpv 配置；若需要迁移，先自行备份并逐项编辑项目 `config/`，不要直接编辑受校验保护的 release 目录。
备份恢复：在新的空目录解包归档，核对 `manifest.json` 后再人工选择恢复；不自动覆盖现有运行目录。
卸载只需停止播放器并移走本项目目录（先保留所需备份）；系统 mpv 与旧配置保持原状。

## HDR 与 4K120Hz

本机已观察到 3840×2160@120Hz、KDE HDR/WCG 开启。mpv HDR 合成测试选中了 10-bit PQ HDR10 Vulkan surface。
这些证据不等于电视面板校准或真实 HDR 影片验收。LG C4 峰值亮度依窗口面积、电视模式和系统设置变化，不写死虚构峰值。
显示器 120Hz 也不意味着视频有 120 个不同帧；24fps 电影保留原帧率，是否均匀呈现仍由合成器与显示链路决定。
若偏灰/过亮，先核对 KDE HDR、电视输入模式及视频元数据；用 `hdr-sdr` 对照。不要同时叠加不同播放器的色调映射建议。
硬解设为 `auto-safe`，允许回退；编解码器支持取决于本机包、驱动及素材，没有宣称所有片源均硬解。

## 可选 RIFE

[独立 RIFE 离线模块](modules/rife/README.md) 固定官方源码版本，支持经过校验的外部二进制处理 SDR PNG 帧目录。
不自动安装、不嵌入 mpv、不提供未经测试的实时补帧承诺。尚未实测该模块推理性能。默认电影播放不补帧。

## 诊断与测试

```bash
python3 lazy.py doctor
python3 -m unittest discover -s tests -v
# 以下命令只用于你自己的本地排查：
kscreen-doctor -o
vulkaninfo --summary
python3 lazy.py play -- --log-file=/tmp/mpv-lazy-private.log /path/to/test.mkv
```

诊断命令只报告少量工具状态、版本和完整性，不自动上传日志。完整 mpv 日志、kscreen 输出可能包含本地路径、片名、输出设备标识，公开前需人工脱敏。
合成播放验证与限制见 [验证记录](docs/VALIDATION.md)。单元测试覆盖路径越界、下载校验失败、幂等安装、更新备份、回滚和篡改检测。
遇到 Wayland 无法连接，请在桌面会话中运行，不从无图形会话或受限容器推断显卡故障。

## 许可证与上游

本仓库原创管理脚本/配置：MIT，见 `LICENSE`。第三方依赖安装时获取，各自许可不被本项目 MIT 替代：

- [mpv](https://mpv.io/manual/stable/)：系统包，许可依构建，通常 GPL；本仓库不分发。
- [uosc 5.13.0](https://github.com/tomasklaen/uosc/tree/5.13.0)：LGPL-3.0，安装时保留许可证；字体等资产遵循上游各自声明。
- [thumbfast](https://github.com/po5/thumbfast)：MPL-2.0，安装时保留许可证。
- [Anime4K](https://github.com/bloc97/Anime4K)：MIT，安装时保留许可证。
- [RIFE ncnn Vulkan](https://github.com/nihui/rife-ncnn-vulkan)：可选外部组件；源码及模型遵循上游各自许可证。

不提交运行依赖、媒体、日志、缓存、账号凭据或原有个人配置。发布为公开仓库须由仓库所有者另行决定。
