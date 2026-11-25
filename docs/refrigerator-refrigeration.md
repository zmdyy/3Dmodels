# 冰箱把热送到哪里？

[打开课件](../models/refrigerator-refrigeration.html)

面向八年级物态变化教学。学生沿着同一段制冷剂观察汽化、压缩、液化和节流，判断热量流向，并在「水与霜」里辨认凝固、凝华与熔化。

| 项目 | 实现 |
|---|---|
| 引擎与坐标 | 单实例 Three.js r160，内嵌 RoundedBoxGeometry。冰箱底座为场景基准。位置用近似米制坐标，时间用秒，镜头角度用弧度。 |
| 复用资源 | `camera-navigation@1.0.0`，依次加载 Three.js、圆角几何、`shared/lab-kit/navigation.js`、场景脚本。页面内嵌资源，可离线打开。 |
| 回路连接 | 毛细管出口 → 箱内蒸发器 → 回气管 → 压缩机 → 排气管 → 背部冷凝器 → 过滤干燥器 → 毛细管入口。 |
| 物理状态 | 三维管内示踪、阀片与右侧状态共用动画进度。制冷剂物性弹窗使用绝对压强和对应的饱和温度，压强单位为 kPa，温度单位为 °C。工况示例采用 R600a。 |
| 镜头与时间 | 以 72 秒的动画跟踪一圈，在蒸发器、压缩机、冷凝器各停 8 秒供阅读。可保持暂停或继续。手动接管镜头后可点「恢复跟随」。 |
| 局部观察 | 原位拉近压缩机缸体和簧片，其余部件可在同一个三维画面中选择「部件详解」。手机竖屏时讲解区排在模型下方。 |
| 材质与文字 | 金属、铜管、塑料与玻璃搁板使用受光三维材质。图解使用 SVG，文字使用系统中文字体。 |
| 简化 | 使用上置冷冻室、背部自然散热的直冷冰箱代表构型。局部流道、管径、阀片行程与压强条为教学示意。 |
| 验收材料 | 首页封面来自课件实际 WebGL 剖视场景。点击模型说明可查看结构出处和模拟范围。 |

`assets/covers/refrigerator-refrigeration-scene.jpg` 为实际三维画面截图。

## 课堂观察

1. 在蒸发器阶段观察箱内空气怎样经铝板和管壁把热传给低温制冷剂，以及液体怎样沿途汽化。
2. 在压缩机阶段点选「吸气」「压缩」「排气」，观察簧片开合、缸内容积与压强。蒸发器一侧靠压缩机抽走蒸气、毛细管限制补入维持低压。
3. 在冷凝器阶段点击管内物态图，选择 R600a 和 600 kPa。该绝对压强对应约 44.7 °C 的沸点。蒸气降到这个温度时，仍能向更凉的室内空气放热并逐渐液化。

资料见 [ASHRAE 家用制冷](https://handbook.ashrae.org/handbooks/R26/SI/r26_ch17/r26_ch17_si.aspx)、[Secop KLF 压缩机爆炸图](https://www.secop.com/fileadmin/user_upload/products/compressor-basics/secop-compressor-klf-exploded.pdf)、[CoolProp 纯工质物性](https://coolprop.org/fluid_properties/PurePseudoPure.html)。
