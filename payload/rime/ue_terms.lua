-- 虚幻引擎 / 游戏开发专用术语表（中文 -> 英文）
-- 由 rime.lua 的 en_comment_filter 加载：拼音/五笔打出来的候选词后面显示这里的英文，
-- Ctrl+数字 直接上屏英文（风格由 EN_COMMIT_STYLE 决定）。
--
-- 优先级：rime.lua 里的手写 zh_en 表 > 本文件 > zh_en_dict.lua（CC-CEDICT 大词表）
-- 所以这里的译法会盖掉 CC-CEDICT 里那些生硬/错误的对译。
-- 加词：在对应分类里加一行 ["中文"] = "English",
-- 想要「虚幻官方中文界面里那个词」就直接抄官方译名当 key。

return {
  ----------------------------------------------------------------
  -- 编辑器界面 / 操作
  ----------------------------------------------------------------
  ["虚幻引擎"] = "Unreal Engine", ["虚幻"] = "Unreal", ["引擎版本"] = "engine version",
  ["内容浏览器"] = "Content Browser", ["内容抽屉"] = "Content Drawer",
  ["细节面板"] = "Details panel", ["细节"] = "Details", ["世界大纲"] = "World Outliner",
  ["大纲视图"] = "Outliner", ["视口"] = "Viewport", ["关卡编辑器"] = "Level Editor",
  ["蓝图编辑器"] = "Blueprint Editor", ["材质编辑器"] = "Material Editor",
  ["动画编辑器"] = "Animation Editor", ["动画蓝图编辑器"] = "Animation Blueprint Editor",
  ["曲线编辑器"] = "Curve Editor", ["物理资产编辑器"] = "Physics Asset Editor",
  ["序列器"] = "Sequencer", ["关卡序列"] = "Level Sequence",
  ["项目设置"] = "Project Settings", ["编辑器偏好设置"] = "Editor Preferences",
  ["插件浏览器"] = "Plugin Browser", ["输出日志"] = "Output Log", ["消息日志"] = "Message Log",
  ["引用查看器"] = "Reference Viewer", ["类查看器"] = "Class Viewer",
  ["资产注册表"] = "Asset Registry", ["世界设置"] = "World Settings",
  ["工具栏"] = "Toolbar", ["菜单栏"] = "menu bar", ["标签页"] = "tab",
  ["停靠"] = "dock", ["浮动窗口"] = "floating window", ["面板"] = "panel",
  ["编辑器模式"] = "Editor Mode", ["选择模式"] = "Select Mode",
  ["地形模式"] = "Landscape Mode", ["植被模式"] = "Foliage Mode",
  ["建模模式"] = "Modeling Mode", ["网格体绘制"] = "Mesh Paint",
  ["缩略图"] = "thumbnail", ["预览窗口"] = "preview window", ["预览"] = "preview",
  ["选中"] = "selection", ["框选"] = "marquee select", ["吸附"] = "snapping",
  ["网格吸附"] = "grid snapping", ["角度吸附"] = "angle snapping", ["顶点吸附"] = "vertex snapping",
  ["环绕"] = "orbit", ["聚焦"] = "focus", ["书签"] = "bookmark", ["显示标志"] = "show flags",
  ["透视视图"] = "perspective view", ["正交视图"] = "orthographic view",
  ["顶视图"] = "top view", ["前视图"] = "front view", ["侧视图"] = "side view",
  ["撤销"] = "undo", ["重做"] = "redo", ["重命名"] = "rename", ["另存为"] = "Save As",
  ["全部保存"] = "Save All", ["重新导入"] = "reimport", ["导入资产"] = "import asset",
  ["导出资产"] = "export asset", ["吸管"] = "eyedropper", ["实验性功能"] = "experimental",
  ["测试功能"] = "Beta", ["官方文档"] = "official documentation", ["发行说明"] = "release notes",
  ["更新日志"] = "changelog", ["已知问题"] = "known issues", ["迁移指南"] = "migration guide",
  ["示例项目"] = "sample project", ["模板"] = "template", ["快速入门"] = "quick start",

  ----------------------------------------------------------------
  -- 资产类型 / 资源
  ----------------------------------------------------------------
  ["静态网格体"] = "Static Mesh", ["骨骼网格体"] = "Skeletal Mesh", ["几何体"] = "geometry",
  ["简单碰撞"] = "simple collision", ["复杂碰撞"] = "complex collision",
  ["凸包"] = "convex hull", ["球体碰撞"] = "sphere collision", ["盒体碰撞"] = "box collision",
  ["胶囊体碰撞"] = "capsule collision", ["物理资产"] = "Physics Asset",
  ["物理材质"] = "Physical Material", ["布料资产"] = "Cloth Asset",
  ["材质函数"] = "Material Function", ["材质参数集"] = "Material Parameter Collection",
  ["动态材质实例"] = "Dynamic Material Instance", ["纹理采样"] = "texture sampling",
  ["UV 展开"] = "UV unwrap", ["立方体贴图"] = "cube map", ["渲染目标"] = "Render Target",
  ["媒体纹理"] = "Media Texture", ["精灵"] = "sprite", ["贴花"] = "decal",
  ["后期处理材质"] = "post process material", ["数据资产"] = "Data Asset",
  ["数据表"] = "Data Table", ["曲线表"] = "Curve Table", ["结构体"] = "struct",
  ["枚举"] = "enum", ["蓝图类"] = "Blueprint Class", ["蓝图接口"] = "Blueprint Interface",
  ["宏库"] = "Macro Library", ["函数库"] = "Function Library", ["关卡蓝图"] = "Level Blueprint",
  ["输入操作"] = "Input Action", ["输入映射上下文"] = "Input Mapping Context",
  ["增强输入"] = "Enhanced Input", ["按键映射"] = "key mapping", ["修饰键"] = "modifier",
  ["声音提示"] = "Sound Cue", ["声音类"] = "Sound Class", ["声音衰减"] = "Sound Attenuation",
  ["混音"] = "Sound Mix", ["媒体播放器"] = "Media Player", ["控制绑定"] = "Control Rig",
  ["IK 绑定"] = "IK Rig", ["IK 重定向"] = "IK Retargeter", ["元人类"] = "MetaHuman",
  ["毛发"] = "Groom", ["几何体集合"] = "Geometry Collection", ["场景捕获"] = "Scene Capture",
  ["平面反射"] = "Planar Reflection", ["反射捕获"] = "Reflection Capture",
  ["光照贴图"] = "Lightmap", ["光照贴图密度"] = "lightmap density",
  ["光照通道"] = "lighting channel", ["天空光"] = "Sky Light", ["矩形光"] = "Rect Light",
  ["点光源"] = "Point Light", ["聚光灯"] = "Spot Light", ["平行光"] = "Directional Light",
  ["体积云"] = "Volumetric Cloud", ["天空大气"] = "Sky Atmosphere", ["高度雾"] = "Height Fog",
  ["体积雾"] = "Volumetric Fog", ["后期处理体积"] = "Post Process Volume",
  ["地形"] = "Landscape", ["地形层"] = "landscape layer", ["地形材质"] = "landscape material",
  ["植被"] = "Foliage", ["植被类型"] = "Foliage Type", ["样条网格"] = "Spline Mesh",
  ["水体"] = "Water Body", ["资产包"] = "asset pack", ["内容文件夹"] = "Content folder",
  ["插件内容"] = "plugin content", ["引擎内容"] = "engine content",
  ["迁移资产"] = "migrate asset", ["资产引用"] = "asset reference",
  ["资产校验"] = "asset validation", ["重定向器"] = "redirector",
  ["硬引用"] = "hard reference", ["软引用"] = "soft reference", ["异步加载"] = "async load",
  ["流式加载"] = "streaming", ["预加载"] = "preload", ["资源大小"] = "resource size",

  ----------------------------------------------------------------
  -- 蓝图 / 节点 / 编程
  ----------------------------------------------------------------
  ["事件图表"] = "Event Graph", ["构造脚本"] = "Construction Script",
  ["执行引脚"] = "execution pin", ["输入引脚"] = "input pin", ["输出引脚"] = "output pin",
  ["连线"] = "wire", ["节点"] = "node", ["纯函数"] = "pure function",
  ["自定义事件"] = "custom event", ["函数"] = "function", ["宏"] = "macro",
  ["局部变量"] = "local variable", ["成员变量"] = "member variable",
  ["实例可编辑"] = "Instance Editable", ["生成时暴露"] = "Expose on Spawn",
  ["私有"] = "private", ["公开"] = "public", ["重新编译"] = "recompile",
  ["刷新节点"] = "refresh node", ["类型转换"] = "Cast To", ["有效"] = "valid",
  ["无效"] = "invalid", ["空值"] = "null", ["断言"] = "assert",
  ["为每个循环"] = "For Each Loop", ["反向循环"] = "reverse for each loop",
  ["序列节点"] = "Sequence", ["闸门"] = "Gate", ["一次性"] = "Do Once",
  ["触发器节点"] = "Flip Flop", ["延迟"] = "Delay", ["时间轴"] = "Timeline",
  ["计时器"] = "timer", ["设置计时器"] = "Set Timer", ["清除计时器"] = "Clear Timer",
  ["自定义深度"] = "custom depth", ["接口调用"] = "interface call",
  ["父类"] = "parent class", ["子类"] = "child class", ["基类"] = "base class",
  ["超级调用"] = "super call", ["暴露变量"] = "expose variable",
  ["复制通知"] = "RepNotify", ["远程调用"] = "RPC", ["可靠"] = "reliable",
  ["不可靠"] = "unreliable", ["权威"] = "authority", ["仅拥有者"] = "owner only",
  ["模拟代理"] = "simulated proxy", ["自动代理"] = "autonomous proxy",
  ["生成"] = "spawn", ["延迟生成"] = "deferred spawn", ["销毁"] = "destroy",
  ["生命周期"] = "lifecycle", ["数组元素"] = "array element", ["映射"] = "Map",
  ["遍历数组"] = "iterate array", ["去重"] = "deduplicate", ["调试对象"] = "debug object",
  ["观察值"] = "watch value", ["调用栈"] = "call stack", ["性能开销"] = "performance cost",
  ["编译错误"] = "compile error", ["编译警告"] = "compile warning",
  ["折叠节点"] = "collapse node", ["注释框"] = "comment box", ["重路由节点"] = "reroute node",
  ["随机流"] = "random stream", ["种子"] = "seed", ["蓝图导航"] = "blueprint navigation",
  ["蓝图可视化脚本"] = "Blueprint visual scripting", ["主姿势组件"] = "Master Pose Component",
  ["领导者姿势组件"] = "Leader Pose Component", ["网格体插槽"] = "mesh socket",
  ["挂点"] = "socket", ["子组件"] = "child component", ["组件层级"] = "component hierarchy",

  ----------------------------------------------------------------
  -- 框架类 / 世界组织
  ----------------------------------------------------------------
  ["游戏模式"] = "Game Mode", ["游戏状态"] = "Game State", ["玩家状态"] = "Player State",
  ["玩家控制器"] = "Player Controller", ["AI 控制器"] = "AI Controller",
  ["角色类"] = "Character", ["棋子"] = "Pawn", ["游戏实例"] = "Game Instance",
  ["世界子系统"] = "World Subsystem", ["游戏实例子系统"] = "Game Instance Subsystem",
  ["本地玩家"] = "Local Player", ["存档游戏"] = "Save Game", ["出生点"] = "Player Start",
  ["默认棋子类"] = "Default Pawn Class", ["玩家相机管理器"] = "Player Camera Manager",
  ["游戏会话"] = "Game Session", ["在线子系统"] = "Online Subsystem",
  ["网络驱动"] = "Net Driver", ["网络复制"] = "network replication",
  ["属性复制"] = "property replication", ["世界"] = "World", ["子关卡"] = "sublevel",
  ["持久关卡"] = "persistent level", ["世界分区"] = "World Partition",
  ["数据层"] = "Data Layer", ["关卡实例"] = "Level Instance",
  ["打包关卡"] = "Packed Level Actor", ["分层细节层次"] = "HLOD",
  ["关卡流送体积"] = "Level Streaming Volume", ["触发器体积"] = "Trigger Volume",
  ["阻挡体积"] = "Blocking Volume", ["物理体积"] = "Physics Volume",
  ["音频体积"] = "Audio Volume", ["导航网格边界"] = "NavMesh Bounds Volume",
  ["游戏能力系统"] = "Gameplay Ability System", ["游戏能力"] = "Gameplay Ability",
  ["属性集"] = "Attribute Set", ["游戏效果"] = "Gameplay Effect",
  ["游戏提示"] = "Gameplay Cue", ["游戏标签"] = "Gameplay Tag",
  ["能力任务"] = "Ability Task", ["环境查询系统"] = "EQS", ["黑板"] = "Blackboard",
  ["任务节点"] = "task node", ["装饰器"] = "decorator", ["服务节点"] = "service",
  ["AI 感知"] = "AI perception", ["视线检测"] = "line of sight", ["巡逻"] = "patrol",

  ----------------------------------------------------------------
  -- 动画 / 角色管线
  ----------------------------------------------------------------
  ["动画序列"] = "Animation Sequence", ["动画蒙太奇"] = "Animation Montage",
  ["瞄准偏移"] = "Aim Offset", ["姿态资产"] = "Pose Asset", ["骨骼树"] = "Skeleton Tree",
  ["骨骼控制"] = "Skeletal Control", ["重定向"] = "retarget", ["重定向源"] = "retarget source",
  ["根骨骼"] = "root bone", ["附加动画"] = "additive animation",
  ["蒙皮权重"] = "skin weight", ["最大骨骼影响数"] = "max bone influences",
  ["形变目标"] = "Morph Target", ["动画通知"] = "Anim Notify",
  ["通知状态"] = "Anim Notify State", ["同步标记"] = "sync marker",
  ["播放速率"] = "play rate", ["动画层"] = "animation layer",
  ["分层混合"] = "layered blend", ["按骨骼混合"] = "Blend per Bone",
  ["过渡规则"] = "transition rule", ["混入时间"] = "blend time",
  ["动画曲线"] = "animation curve", ["动画压缩"] = "animation compression",
  ["原地动画"] = "in-place animation", ["面部动画"] = "facial animation",
  ["表情"] = "expression", ["口型"] = "lip sync", ["面部绑定"] = "facial rig",
  ["骨骼绑定"] = "skeleton rig", ["权重绘制"] = "weight painting",
  ["绑定姿势"] = "bind pose", ["参考姿势"] = "reference pose", ["静止姿势"] = "rest pose",
  ["骨骼映射"] = "bone mapping", ["布料模拟"] = "cloth simulation",
  ["布料碰撞"] = "cloth collision", ["蒙皮"] = "skinning", ["权重"] = "weight",
  ["关键帧"] = "keyframe", ["时间轴"] = "timeline", ["动作捕捉"] = "motion capture",

  ----------------------------------------------------------------
  -- 渲染 / 性能分析
  ----------------------------------------------------------------
  ["延迟渲染"] = "deferred rendering", ["前向渲染"] = "forward rendering",
  ["基础通道"] = "base pass", ["实例化"] = "instancing",
  ["实例化静态网格"] = "Instanced Static Mesh",
  ["层次实例化静态网格"] = "Hierarchical Instanced Static Mesh",
  ["虚拟阴影贴图"] = "Virtual Shadow Map", ["虚拟几何体"] = "virtualized geometry",
  ["屏幕空间反射"] = "screen space reflection", ["环境光遮蔽"] = "ambient occlusion",
  ["距离场"] = "distance field", ["网格距离场"] = "mesh distance field",
  ["时间超采样"] = "TSR", ["时序抗锯齿"] = "TAA", ["超分辨率"] = "super resolution",
  ["运动模糊"] = "motion blur", ["色差"] = "chromatic aberration", ["暗角"] = "vignette",
  ["胶片颗粒"] = "film grain", ["着色器编译"] = "shader compilation",
  ["着色器缓存"] = "shader cache", ["着色器排列"] = "shader permutation",
  ["材质指令数"] = "material instructions", ["着色复杂度"] = "shader complexity",
  ["纹理流送"] = "texture streaming", ["纹理池"] = "texture pool",
  ["显卡耗时"] = "GPU time", ["CPU 耗时"] = "CPU time", ["帧时间"] = "frame time",
  ["瓶颈"] = "bottleneck", ["开销"] = "overhead", ["内存快照"] = "memory snapshot",
  ["垃圾回收"] = "garbage collection", ["对象计数"] = "object count",
  ["常驻内存"] = "resident memory", ["显存占用"] = "VRAM usage",
  ["资源泄漏"] = "resource leak", ["崩溃转储"] = "crash dump",
  ["渲染线程"] = "render thread", ["游戏线程"] = "game thread",
  ["后台线程"] = "background thread", ["异步计算"] = "async compute",
  ["屏幕百分比"] = "screen percentage", ["可扩展性"] = "scalability",
  ["画质等级"] = "quality level", ["低配"] = "low end", ["高配"] = "high end",
  ["基准测试"] = "benchmark", ["性能预算"] = "performance budget",
  ["绘制调用"] = "draw call", ["批次"] = "batch", ["剔除"] = "culling",

  ----------------------------------------------------------------
  -- 打包 / 工程 / 构建
  ----------------------------------------------------------------
  ["打包项目"] = "package project", ["打包设置"] = "packaging settings",
  ["构建配置"] = "build configuration", ["开发版"] = "Development build",
  ["发布版"] = "Shipping build", ["调试版"] = "Debug build",
  ["编辑器构建"] = "Editor build", ["资源烹饪"] = "asset cooking",
  ["打包输出"] = "packaging output", ["项目启动器"] = "Project Launcher",
  ["生成工程文件"] = "Generate project files", ["实时编码"] = "Live Coding",
  ["热重载"] = "hot reload", ["全量重编译"] = "full rebuild", ["模块"] = "module",
  ["链接错误"] = "linker error", ["未定义符号"] = "undefined symbol",
  ["头文件"] = "header file", ["源文件"] = "source file", ["包含路径"] = "include path",
  ["第三方库"] = "third-party library", ["插件清单"] = "plugin manifest",
  ["项目文件"] = "project file", ["迁移项目"] = "migrate project",
  ["源码构建"] = "source build", ["安装版引擎"] = "installed build",
  ["符号服务器"] = "symbol server", ["崩溃报告"] = "crash report",
  ["引用检查"] = "reference check", ["打包大小"] = "package size",
  ["分块"] = "chunk", ["补丁包"] = "patch package", ["目标平台"] = "target platform",
  ["自动化测试"] = "automation test", ["冒烟测试"] = "smoke test",
  ["回归测试"] = "regression test", ["运行测试"] = "run test",

  ----------------------------------------------------------------
  -- 建模 / 材质 / MetaHuman
  ----------------------------------------------------------------
  ["雕刻"] = "sculpt", ["挤出"] = "extrude", ["倒角"] = "bevel",
  ["循环边"] = "loop cut", ["网格体布尔"] = "mesh boolean",
  ["布尔运算"] = "boolean operation", ["重拓扑"] = "retopology",
  ["自动重拓扑"] = "auto retopo", ["UV 通道"] = "UV channel", ["切线"] = "tangent",
  ["顶点色"] = "vertex color", ["顶点数"] = "vertex count",
  ["三角面数"] = "triangle count", ["面数"] = "poly count",
  ["几何体脚本"] = "geometry script", ["程序化"] = "procedural",
  ["材质槽"] = "material slot", ["材质插槽"] = "material slot",
  ["合并材质"] = "merge materials", ["贴图集"] = "texture atlas",
  ["基础色"] = "base color", ["不透明度"] = "opacity",
  ["次表面散射"] = "subsurface scattering", ["各向异性"] = "anisotropy",
  ["位移"] = "displacement", ["置换贴图"] = "displacement map",
  ["环境贴图"] = "environment map", ["烘焙贴图"] = "baked texture",
  ["平铺"] = "tiling", ["调色"] = "color grading", ["三视图"] = "orthographic views",
  ["网格体 LOD"] = "mesh LOD", ["骨骼缩放"] = "bone scale",

  ----------------------------------------------------------------
  -- 音频
  ----------------------------------------------------------------
  ["衰减"] = "attenuation", ["空间化"] = "spatialization", ["声像"] = "panning",
  ["混响"] = "reverb", ["环境音"] = "ambient sound", ["音源"] = "sound source",
  ["循环音效"] = "looping sound", ["音量衰减"] = "volume attenuation",
  ["音频总线"] = "audio bus", ["子混音"] = "submix",
  ["声音并发"] = "sound concurrency",

  ----------------------------------------------------------------
  -- 玩法 / 数值 / 关卡设计
  ----------------------------------------------------------------
  ["数值公式"] = "formula", ["掉落表"] = "loot table", ["刷新点"] = "spawn point",
  ["刷怪器"] = "spawner", ["波次"] = "wave", ["关卡流程"] = "level flow",
  ["玩家动线"] = "player flow", ["难度曲线"] = "difficulty curve",
  ["数值膨胀"] = "power creep", ["装备词条"] = "item affix", ["奖励"] = "reward",
  ["惩罚"] = "penalty", ["存档点"] = "checkpoint", ["核心循环"] = "core loop",
  ["玩法"] = "gameplay", ["数值"] = "numbers", ["配表"] = "data table",
  ["手感"] = "game feel", ["打击感"] = "hit feedback", ["判定框"] = "hitbox",

  ----------------------------------------------------------------
  -- 发售 / 商店 / 运营（个人开发者常用）
  ----------------------------------------------------------------
  ["虚幻商城"] = "Unreal Marketplace", ["商城资产"] = "marketplace asset",
  ["商品描述"] = "product description", ["许可证"] = "license", ["授权"] = "license",
  ["侵权"] = "infringement", ["退款"] = "refund", ["销售数据"] = "sales data",
  ["转化率"] = "conversion rate", ["曝光量"] = "impressions",
  ["技术审核"] = "technical review", ["上架申请"] = "listing submission",
  ["资产规格"] = "asset specifications", ["定价策略"] = "pricing strategy",
  ["促销"] = "promotion", ["捆绑包"] = "bundle", ["订阅"] = "subscription",
  ["评分"] = "rating", ["付费转化"] = "conversion", ["退款率"] = "refund rate",
}
