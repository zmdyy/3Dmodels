# 浮沉子 · 定量探究实验

- 首页入口：`models/cartesian-diver.html`（V9 独立离线版，WebGL2 / Canvas 三维网格兼容渲染）；`models/cartesian-diver-three-r160.html` 为仓库 Three.js r160 原生适配备选。两版使用同一套物理状态和触控修正。
- 教学目标：比较浮力、重力与实际排水体积；观察底部开口的水流、被困空气压缩及浮沉现象。研究对象不含自由进出小瓶的水。
- 单位：m、N、s；压强 kPa，体积 mL。几何排水体积与静水压强积分分别计算，重力由材料质量计算。气体近似等温，形变和流向示踪为教学示意，非实测数据。
- 复用：LabKit camera-navigation 的手动接管机制，透明器材外观参考 glass-beaker；水流橙色箭头参考 automatic-plant-watering。新增 touchstart/touchmove/touchend 同步处理触点，避免缩放下限处平移误缩放。
- 验收：2026-11-25 Chromium 兼容渲染运行，无页面脚本错误；CDP 双指张开相机距离 0.132→0.090 m，两指平移时距离保持 0.090 m，目标 x/y 均变化，松手不回弹。封面为同一案例实际运行截图。当前环境 WebGL2 不可用，Three.js 原生渲染及实体触屏设备未验收；完整仓库脚本未运行。
