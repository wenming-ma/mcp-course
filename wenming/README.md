# KiCad MCP Servers

This directory contains two different approaches to KiCad manipulation via MCP:

## 1. kicad-agent-server (预定义工具)

**File**: `kicad_agent_server01.py`
**Command**: `kicad-agent-server`

### 特点
- 预定义了4个具体的工具
- 每个工具执行一个特定的KiCad操作
- 适合常见、标准化的操作

### 可用工具
1. `get_board_info()` - 获取板子基本信息
2. `create_via_grid()` - 创建过孔网格
3. `organize_footprints_in_grid()` - 按网格排列封装
4. `adjust_pad_clearance()` - 调整pad间隙（支持模糊匹配和相对调整）

### 使用场景
适合需要频繁执行固定操作的场景。

---

## 2. kicad-code-executor (动态代码执行)

**File**: `kicad_code_executor.py`
**Command**: `kicad-code-executor`

### 特点
- 提供KiCad Python API的完整文档作为Resources
- 只有一个通用的执行工具
- LLM可以根据API文档动态生成代码
- 更加灵活，可以执行任意KiCad操作

### 架构

```
┌─────────────────────────────────────────────┐
│  LLM (Claude)                               │
│                                             │
│  1. 读取 Resources 了解 API                 │
│  2. 生成符合需求的 Python 代码              │
│  3. 调用 execute_kicad_code 工具执行        │
│  4. 获取执行结果                            │
└─────────────────────────────────────────────┘
```

### 可用 Resources

| URI | 说明 |
|-----|------|
| `kicad-api://overview` | API快速参考 |
| `kicad-api://board.py` | Board类完整源码 |
| `kicad-api://board_types.py` | 所有PCB元素类型定义 |
| `kicad-api://geometry.py` | 几何图形API |
| `kicad-api://examples/list` | 列出所有示例 |
| `kicad-api://examples/{name}` | 获取特定示例代码 |

### 可用 Tool

**`execute_kicad_code(code: str, description: str = None)`**

执行Python代码，自动注入常用导入：
- `KiCad`, `Board`, `Net`, `Pad`, `Via`, etc.
- `Vector2`, `Angle`, `from_mm()`, `to_mm()`

### 使用示例

#### 在Cursor/Claude Desktop中使用

1. **配置MCP服务器**（在Claude Desktop的配置文件中）：
```json
{
  "mcpServers": {
    "kicad-code-executor": {
      "command": "kicad-code-executor"
    }
  }
}
```

2. **与Claude对话**：
```
用户: 帮我把所有以"GND"开头的网络的pad间隙调整为0.5mm

Claude会:
1. 读取 kicad-api://overview 了解API
2. 读取 kicad-api://board_types.py 查看Pad的API
3. 生成代码:
   ```python
   kicad = KiCad()
   board = kicad.get_board()

   # 获取所有GND开头的网络
   all_nets = board.get_nets()
   gnd_nets = [net for net in all_nets if net.name.startswith("GND")]

   # 修改所有相关pad的间隙
   all_footprints = board.get_footprints()
   commit = board.begin_commit()

   modified_count = 0
   for footprint in all_footprints:
       for pad in footprint.definition.pads:
           if pad.net and any(pad.net.name == net.name for net in gnd_nets):
               pad._proto.copper_clearance_override.value_nm = from_mm(0.5)
               modified_count += 1

   board.update_items(all_footprints)
   board.push_commit(commit, "Adjust GND pad clearance to 0.5mm")

   print(f"Modified {modified_count} pads")
   ```

4. 调用 execute_kicad_code 执行代码
5. 返回执行结果
```

### 优势对比

| 特性 | kicad-agent-server | kicad-code-executor |
|------|-------------------|---------------------|
| 灵活性 | ⭐⭐ 固定功能 | ⭐⭐⭐⭐⭐ 任意操作 |
| 可维护性 | ⭐⭐⭐ 需要添加新工具 | ⭐⭐⭐⭐⭐ 只需更新API文档 |
| 执行速度 | ⭐⭐⭐⭐⭐ 直接调用 | ⭐⭐⭐⭐ 需要生成代码 |
| 安全性 | ⭐⭐⭐⭐⭐ 预定义操作 | ⭐⭐⭐ 执行任意代码 |
| 适用场景 | 常见固定操作 | 复杂自定义需求 |

---

## 安装和使用

### 1. 安装
```bash
# 可编辑模式安装（推荐开发时使用）
uv pip install -e .

# 修改Python代码后无需重新安装，直接生效
# 只有修改 pyproject.toml 时才需要重新安装
```

### 2. 运行

```bash
# 预定义工具服务器
kicad-agent-server

# 代码执行服务器
kicad-code-executor
```

### 3. 在Cursor中配置

编辑Cursor的MCP配置文件，添加：

```json
{
  "mcpServers": {
    "kicad-tools": {
      "command": "kicad-agent-server",
      "description": "预定义的KiCad操作工具"
    },
    "kicad-executor": {
      "command": "kicad-code-executor",
      "description": "动态KiCad代码执行器"
    }
  }
}
```

### 4. 注意事项

⚠️ **运行前确保**:
1. KiCad 9.0+ 已启动
2. KiCad API服务器已启用（Preferences > Plugins）
3. 有一个PCB文件已打开

---

## 开发建议

### 何时使用 kicad-agent-server
- 需要快速执行标准操作
- 操作需要高度可靠和安全
- 团队成员不熟悉KiCad API

### 何时使用 kicad-code-executor
- 需要执行复杂的自定义操作
- 需求频繁变化
- 想要探索KiCad API的可能性
- 需要组合多个操作形成工作流

### 混合使用
可以同时配置两个服务器，根据任务选择合适的工具：
- 简单操作 → 使用预定义工具
- 复杂操作 → 使用代码执行器

---

## 示例场景

### 场景1: 创建过孔网格（简单操作）
**使用**: kicad-agent-server
**工具**: `create_via_grid(50, 50, 5, 5, 2.54, 0.8, 0.4, "GND")`

### 场景2: 复杂布局优化（复杂操作）
**使用**: kicad-code-executor
**描述**: "将所有电阻按阻值分组，每组内按网格排列，不同组之间留10mm间距"
**实现**: LLM自动生成约50行代码完成

---

## 许可证

MIT License
