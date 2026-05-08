# Picture Beauty（picture-beauty）

本地工具：对截图做锐化与适度放大，并可套上类似 [Shots](https://shots.so/) 风格的渐变背景、圆角、投影与边框，方便发到小红书、抖音等平台。

## 效果示例

下面是真实导出示例 **`ShareX_D3NPA1IdN2_enhanced.png`**（ShareX 截了一张深色界面工具截图后，用图形界面默认配置跑出来的成品：**清晰度预设 · 平衡**；**画布 · 16:9 横版 Mockup**；**画框背景 · Shots 对角渐变**）。可作为「清晰化 + 高级感画框」的参照。

![Picture Beauty 导出示例：对角渐变背景、圆角卡片与投影](./ShareX_D3NPA1IdN2_enhanced.png)

若仓库克隆后在 Markdown 预览里看不到图，请确认项目根目录下存在同名 PNG 文件。

## 环境要求

- Windows / macOS / Linux 均可，以下为 Windows 说明。
- 已安装 **Python 3.10+**（安装时勾选 **Add Python to PATH**）。
- 依赖见 `requirements-image.txt`（主要是 Pillow）。

### 安装依赖

在项目目录下执行：

```powershell
cd c:\Users\zhangh\Desktop\shipai
pip install -r requirements-image.txt
```

---

## 方式一：图形界面（推荐）

适合不想记命令行参数时使用。

1. 双击 **`启动图形界面.bat`**（或在终端执行 `python enhance_gui.py`）。
2. **输入**：点 **选文件** 选一张图，或点 **选文件夹** 批量处理该文件夹内所有图片（仅当前文件夹，不含子文件夹；支持 png/jpg/jpeg/webp/bmp/gif）。
3. **输出**：界面内有更细的说明（单张填完整保存路径；批量填统一输出文件夹或留空写回原目录）。详见窗口内灰色提示。
4. 界面默认：**16:9 Mockup + Shots 渐变 + 平衡预设**（与常用 `default_mockup_shots.png` 组合一致），可按需修改。
5. 点击 **开始处理**；批量时可点 **停止**，在当前这张处理完后结束（不会中断 Pillow 正在处理的那一张）。
6. 完成后会弹出提示。

若双击 `.bat` 无反应，请在文件夹空白处 **Shift + 右键 →「在此处打开 PowerShell 窗口」**，执行：

```powershell
python enhance_gui.py
```

根据报错检查 Python 是否已加入 PATH，或是否已执行 `pip install -r requirements-image.txt`。

---

## 打包为 Windows 桌面应用（exe）

无需 `.bat` 也能使用：生成 **`dist\PictureBeauty.exe`**，双击即可打开图形界面（单文件，无黑色控制台窗口）。

1. 在项目目录打开 PowerShell，安装打包依赖并执行打包脚本：

```powershell
cd c:\Users\zhangh\Desktop\shipai
pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\pack_desktop.ps1
```

或直接双击 **`打包桌面应用.bat`**（内部调用上面的 PowerShell 脚本）。

2. 成功后可在 **`dist\PictureBeauty.exe`** 找到可执行文件，可复制到任意路径单独使用。

3. 说明：
   - 首次运行若被 Windows SmartScreen 拦截，可选「仍要运行」或为本机构建的版本添加证书签名。
   - 杀毒软件偶发误报 PyInstaller 打包的 exe，属常见现象；若不放心可自行源码审查后用本地 Python 运行。
   - 修改代码后需重新打包才会体现在 exe 中。

底层命令等价于：`pyinstaller --clean --noconfirm picture-beauty.spec`（配置见 `picture-beauty.spec`）。

---

## 方式二：命令行

### 仅清晰增强（无渐变画框）

默认读取同目录下的 `default.png`，输出 `default_enhanced.png`：

```powershell
python enhance_for_social.py
```

指定输入输出：

```powershell
python enhance_for_social.py -i 截图.png -o 导出.png
```

### 清晰度预设

| 预设 | 说明 |
|------|------|
| `premium` | 默认，平衡 |
| `light` | 较轻 |
| `strong` | 更强锐化与对比 |

```powershell
python enhance_for_social.py --preset strong -i in.png -o out.png
```

### 短边放大像素（默认 1080）

上传平台压图后更清晰可适当调高：

```powershell
python enhance_for_social.py --min-short 1440 -i in.png -o out.png
```

### 画布与 Mockup（三选一）

与 **「画布样式」** 图形界面选项对应：

```powershell
# 16:9 横版：对角渐变 + 圆角 + 投影 + 细边框（接近 Shots）
python enhance_for_social.py -i default.png -o mockup.png --mockup

# 小红书常用 3:4
python enhance_for_social.py -i default.png -o xhs.png --xhs-card

# 抖音竖屏 9:16
python enhance_for_social.py -i default.png -o dy.png --douyin-card
```

### 画框背景风格

```powershell
# 默认：橙红→紫蓝对角渐变（shots 风格）
python enhance_for_social.py --mockup --card-style shots -i in.png -o out.png

# 深色竖渐变（较早版本样式）
python enhance_for_social.py --mockup --card-style minimal -i in.png -o out.png
```

一次只能选一种画布：`--mockup`、`--xhs-card`、`--douyin-card` 不要同时使用。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `enhance_for_social.py` | 主处理脚本（命令行） |
| `enhance_gui.py` | 图形界面入口 |
| `启动图形界面.bat` | Windows 下双击启动 GUI |
| `requirements-image.txt` | 运行脚本所需依赖 |
| `requirements-build.txt` | 含 PyInstaller，用于打包 exe |
| `picture-beauty.spec` | PyInstaller 打包配置 |
| `pack_desktop.ps1` / `打包桌面应用.bat` | 一键打包生成 `dist\PictureBeauty.exe` |
| `ShareX_D3NPA1IdN2_enhanced.png` | 文档用效果示例（默认 Mockup + Shots 导出） |

---

## 常见问题

**双击 bat 闪一下就没了**  
多为未安装 Python 或未装依赖。请用上面的命令在终端运行 `python enhance_gui.py` 查看报错。

**提示找不到 Pillow**  
执行：`pip install -r requirements-image.txt`

**若要自定义渐变颜色**  
可在 `enhance_for_social.py` 中修改函数 `gradient_background_diagonal` 里的 `top_left` / `bottom_right` 两个 RGB 元组。
