# 🪪 证件管家 Doc Keeper

一个面向大众的**证件/卡券到期提醒**小工具：把身份证、驾驶证、护照、居住证、社保卡、车辆年检、储值卡/会员卡等"会过期"的东西登记进去，到期前按你设置的档位提前提醒，并给出续办指南（材料 / 地点 / 费用 / 时限 / 官方入口）。

> 定位：不是"管理证件"，而是"**别在办证上吃亏**"——录入够快、提醒够主动、续办够省心。

## 技术栈

```
后端  Python + FastAPI (UVicorn, 端口 8000) + SQLAlchemy + PyMySQL
前端  Vue 3 + Vite (端口 5173)
数据  MySQL 8.x（库 doc_keeper）+ Redis（缓存/去重，可选）
安全  JWT(短时效+刷新+注销黑名单) · Argon2 密码哈希 · AES-256-GCM 敏感字段密文落库
```

## 目录结构

```
project3/
├─ backend/                Python 后端
│  ├─ app/
│  │  ├─ main.py           应用入口 + 定时扫提醒
│  │  ├─ config.py / database.py / models.py / schemas.py
│  │  ├─ security.py       JWT + 密码哈希 + AES 加密
│  │  ├─ deps.py           token 校验 / 注销黑名单
│  │  ├─ routers/          auth/documents/calendar/reminders/guides/family/export/health/regions
│  │  └─ services/         到期计算 / 提醒引擎（幂等） / ... 
│  ├─ requirements.txt
│  ├─ .env.example         （复制为 .env 配置）
│  └─ .venv/               Python 虚拟环境（启动脚本自动创建）
├─ frontend/               Vue 3 前端
│  ├─ src/views/           登录/注册/仪表盘/证件/日历/提醒/指南/家庭/设置/指南维护
│  ├─ src/components/      侧边栏布局等
│  └─ vite.config.js       dev 代理 /api -> 8000
├─ database/sql/           01_schema.sql(建表) + 02_seed.sql(证件类型+续办指南种子)
├─ scripts/                init_db / start / stop / check-env / verify_* / create_admin / migrate_provinces
├─ docs/                   项目介绍 / 代码技术架构 / 部署运行说明 / 产品与体验设计
│  ├─ 启动-证件管家.bat      一键启动（推荐）
│  └─ 停止-证件管家.bat      一键停止
```

## 快速开始（推荐，Windows）

```text
1. 双击「启动-证件管家.bat」
2. 脚本会自动：检测环境 → 建 .venv 装依赖 → 生成/使用 backend\.env
   → 初始化数据库(建库+建表+种子指南) → 启动后端(8000)和前端(5173) → 打开浏览器
3. 首次会要求输入 MySQL 密码（用于生成 .env）
4. 浏览器访问  http://localhost:5173 → 注册一个账号使用
```

若嫌脚本，也可手动：

```bash
# 后端
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # 填 DB_PASSWORD / JWT_SECRET(≥32位) / ENC_KEY(可选)
python ..\scripts\init_db.py
python -m uvicorn app.main:app --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev                 # 打开 http://localhost:5173
```

## 管理员 / 指南维护

普通注册的用户是"普通用户"。需要维护「续办指南」时，把某人提升为管理员：

```bash
.venv\Scripts\python scripts\create_admin.py 用户名 密码
```

登录后左侧会出现「指南维护」，可增删改每类证件的续办指南；
来源与更新日期必填、缺的请标"待核实"，保证内容"敢信"。

## 安全说明

- 密码：Argon2 单程哈希，明文不离库。
- 登录态：短时效 Access Token(默认60分钟) + Refresh Token(7天)，退出即用 Redis/内存黑名单注销；JWT 带签名，篡改即拒。
- 证件号等敏感字段：配置 `ENC_KEY`（Base64 的 32 字节）后以 **AES-256-GCM 密文落库**，界面/导出一律脱敏（`610100********9876`），明文仅本人查看详情时按需解密且不落日志。
- 请不要把 `backend\.env`（含数据库密码、JWT/加密密钥）提交到 Git；仓库已含 `.gitignore` 时注意忽略。

> 续办指南来自网络公开的政务办事指南，仅供参考，以当地窗口实际要求为准。

## 常见问题

- **npm install 报 EPERM / ERR_INVALID_ARG_TYPE**：这是部分 npm 环境下 esbuild 构建脚本导致的偶发问题，先执行 `npm install --ignore-scripts`，再 `npm run dev` 即可（二进制已在包内）。
- **启动后 5173 打不开**：在浏览器手动访问 http://localhost:5173 ；后端就绪可用 http://127.0.0.1:8000/api/health 检查。
- **Redis 未装**：提醒生成退化为依赖数据库唯一索引，仍可用；仅退出注销黑名单回退为进程内记忆（重启后旧 token 仍有效的极短期窗口）。