# 视觉矩阵 (Visual Matrix) v8.0

一个为全球电商生态提供以用户产品图为输入的高度稳定、富有创意且具备商业扩展性的AI视觉内容自动化生产平台。

## 项目特性

- 🎨 AI智能图片分析与生成
- 🖼️ 多风格模板支持
- ✏️ 在线图片编辑器
- 💰 灵活的积分与会员体系
- 📁 项目文件管理
- 🔄 实时任务状态更新

## 技术栈

### 后端
- Python 3.10+
- Flask
- SQLAlchemy
- Celery
- Redis
- Pillow

### 前端
- Vue.js 3
- Vite
- Element Plus
- Fabric.js

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- Redis

### 后端设置

1. 创建虚拟环境
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

2.安装依赖
pip install -r requirements.txt

3.配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际配置

4.初始化数据库
python app.py

前端设置
1.安装依赖
cd frontend
npm install

2.启动开发服务器
npm run dev

访问应用
前端：http://localhost:3000
后端API：http://localhost:5000

部署
详细部署说明请参考 docs/deployment.md

许可证
MIT License
### 5.3 Git初始化和GitHub上传指令

**在Visual_Matrix根目录执行以下命令：**

```bash
# 1. 初始化Git仓库
git init

# 2. 添加所有文件到暂存区
git add .

# 3. 进行首次提交
git commit -m "Initial commit: Visual Matrix v8.0 项目初始化

- 完成后端Flask框架搭建
- 完成前端Vue.js项目初始化
- 实现用户认证系统
- 实现基础数据库模型
- 完成核心页面组件开发
- 配置开发环境和构建工具"

# 4. 在GitHub创建仓库后，关联远程仓库（替换为你的实际仓库地址）
git remote add origin https://github.com/yourusername/visual-matrix.git

# 5. 推送到GitHub
git branch -M main
git push -u origin main