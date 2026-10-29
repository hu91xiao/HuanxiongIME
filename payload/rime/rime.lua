--- 过滤器：单字在先
function single_char_first_filter(input)
    local l = {}
    for cand in input:iter() do
        if (utf8.len(cand.text) == 1) then
            yield(cand)
        else
            table.insert(l, cand)
        end
    end
    for i, cand in ipairs(l) do
        yield(cand)
    end
end

--- 过滤器：只显示单字
function single_char_only(input)
    for cand in input:iter() do
        if (utf8.len(cand.text) == 1) then
            yield(cand)
        end
    end
end

--- 计算器
--- @KyleBing 2022-01-17
function calculator(input, seg)
    if string.find(input, 'coco') ~= nil then -- 匹配 coco 开头的字符串
        local _, _, a, operation, b = string.find(input, "coco(%d+%.?%d*)([%+%-%*/])(%d+%.?%d*)")
        local result = 0
        if operation == '+' then
            result = a + b
        elseif operation == '-' then
            result = a - b
        elseif operation == '*' then
            result = a * b
        elseif operation == '/' then
            result = a / b
        end
        yield(Candidate("coco", seg.start, seg._end, result, "计算器"))
    end
end


function date_translator(input, seg)

    -- 日期格式说明：

    -- %a	abbreviated weekday name (e.g., Wed)
    -- %A	full weekday name (e.g., Wednesday)
    -- %b	abbreviated month name (e.g., Sep)
    -- %B	full month name (e.g., September)
    -- %c	date and time (e.g., 09/16/98 23:48:10)
    -- %d	day of the month (16) [01-31]
    -- %H	hour, using a 24-hour clock (23) [00-23]
    -- %I	hour, using a 12-hour clock (11) [01-12]
    -- %M	minute (48) [00-59]
    -- %m	month (09) [01-12]
    -- %p	either "am" or "pm" (pm)
    -- %S	second (10) [00-61]
    -- %w	weekday (3) [0-6 = Sunday-Saturday]
    -- %W	week number in year (48) [01-52]
    -- %x	date (e.g., 09/16/98)
    -- %X	time (e.g., 23:48:10)
    -- %Y	full year (1998)
    -- %y	two-digit year (98) [00-99]
    -- %%	the character `%´

    -- 输入完整日期
    if (input == "datetime") then
        yield(Candidate("date", seg.start, seg._end, os.date("%Y-%m-%d %H:%M:%S"), ""))
    end

    -- 输入日期
    if (input == "date") then
        --- Candidate(type, start, end, text, comment)
        yield(Candidate("date", seg.start, seg._end, os.date("%Y-%m-%d"), ""))
        yield(Candidate("date", seg.start, seg._end, os.date("%Y/%m/%d"), ""))
        yield(Candidate("date", seg.start, seg._end, os.date("%Y.%m.%d"), ""))
        yield(Candidate("date", seg.start, seg._end, os.date("%Y年%m月%d日"), ""))
        yield(Candidate("date", seg.start, seg._end, os.date("%m-%d-%Y"), ""))
    end

    -- 输入时间
    if (input == "time") then
        --- Candidate(type, start, end, text, comment)
        yield(Candidate("time", seg.start, seg._end, os.date("%H:%M"), ""))
        yield(Candidate("time", seg.start, seg._end, os.date("%Y%m%d%H%M%S"), ""))
        yield(Candidate("time", seg.start, seg._end, os.date("%H:%M:%S"), ""))
    end

    -- 输入星期
    -- -- @JiandanDream
    -- -- https://github.com/KyleBing/rime-wubi86-jidian/issues/54
    if (input == "week") then
        local weekTab = {'日', '一', '二', '三', '四', '五', '六'}
        yield(Candidate("week", seg.start, seg._end, "周"..weekTab[tonumber(os.date("%w")+1)], ""))
        yield(Candidate("week", seg.start, seg._end, "星期"..weekTab[tonumber(os.date("%w")+1)], ""))
        yield(Candidate("week", seg.start, seg._end, os.date("%A"), ""))
        yield(Candidate("week", seg.start, seg._end, os.date("%a"), "缩写"))
        yield(Candidate("week", seg.start, seg._end, os.date("%W"), "周数"))
    end

    -- 输入月份英文
    if (input == "month") then
        yield(Candidate("month", seg.start, seg._end, os.date("%B"), ""))
        yield(Candidate("month", seg.start, seg._end, os.date("%b"), "缩写"))
    end
end




--- 处理器：回车直接上屏当前输入的编码串（拼音/五笔字母），不选中候选
--- 中文首词改用空格或数字键选择；ascii 模式下不拦截
function commit_raw_on_return(key, env)
    local ctx = env.engine.context
    -- 只处理按下、无修饰键的回车
    if key:release() or key:ctrl() or key:alt() then
        return 2
    end
    if key:repr() ~= "Return" then
        return 2
    end
    if not ctx:has_menu() then
        return 2
    end
    local raw = ctx.input
    if raw == nil or raw == "" then
        return 2
    end
    ctx:clear()
    env.engine:commit_text(raw)
    return 1   -- 1 = 已处理，事件不再往后传
end


------------------------------------------------------------------
-- 中英注释：候选词后面加英文，Ctrl+1~9 直接上屏对应英文
--   空格 / 数字 = 上屏中文，Ctrl+数字 = 上屏英文
--   加词方法：在下面的 zh_en 表里加一行  ["中文"] = "english",
------------------------------------------------------------------
local zh_en = {
  -- 日常
  ["牛奶"] = "milk", ["水"] = "water", ["火"] = "fire", ["山"] = "mountain",
  ["河"] = "river", ["海"] = "sea", ["天"] = "sky", ["地"] = "ground",
  ["太阳"] = "sun", ["月亮"] = "moon", ["星"] = "star", ["云"] = "cloud",
  ["雨"] = "rain", ["雪"] = "snow", ["风"] = "wind", ["树"] = "tree",
  ["花"] = "flower", ["草"] = "grass", ["鸟"] = "bird", ["鱼"] = "fish",
  ["狗"] = "dog", ["猫"] = "cat", ["马"] = "horse", ["牛"] = "cow",
  ["猪"] = "pig", ["鸡"] = "chicken", ["鸭"] = "duck", ["羊"] = "sheep",
  ["老虎"] = "tiger", ["龙"] = "dragon", ["兔子"] = "rabbit", ["熊"] = "bear",
  ["人"] = "person", ["男人"] = "man", ["女人"] = "woman", ["孩子"] = "child",
  ["儿子"] = "son", ["女儿"] = "daughter", ["爸爸"] = "father", ["妈妈"] = "mother",
  ["老师"] = "teacher", ["学生"] = "student", ["医生"] = "doctor", ["朋友"] = "friend",
  ["家"] = "home", ["学校"] = "school", ["公司"] = "company", ["工作"] = "work",
  ["电脑"] = "computer", ["手机"] = "phone", ["书"] = "book", ["名字"] = "name",
  ["时间"] = "time", ["年"] = "year", ["今天"] = "today", ["明天"] = "tomorrow",
  ["昨天"] = "yesterday", ["现在"] = "now", ["早上"] = "morning", ["晚上"] = "evening",
  ["米饭"] = "rice", ["饭"] = "meal", ["菜"] = "dish", ["肉"] = "meat",
  ["茶"] = "tea", ["咖啡"] = "coffee", ["酒"] = "wine", ["面包"] = "bread",
  ["鸡蛋"] = "egg", ["苹果"] = "apple", ["香蕉"] = "banana", ["糖"] = "sugar",
  ["吃"] = "eat", ["喝"] = "drink", ["走"] = "walk", ["跑"] = "run",
  ["跳"] = "jump", ["看"] = "see", ["听"] = "listen", ["说"] = "speak",
  ["写"] = "write", ["读"] = "read", ["买"] = "buy", ["卖"] = "sell",
  ["做"] = "make", ["用"] = "use", ["给"] = "give", ["拿"] = "take",
  ["来"] = "come", ["去"] = "go", ["开"] = "open", ["关"] = "close",
  ["学"] = "learn", ["教"] = "teach", ["想"] = "think", ["知道"] = "know",
  ["喜欢"] = "like", ["爱"] = "love", ["睡"] = "sleep", ["玩"] = "play",
  ["等"] = "wait", ["找"] = "find", ["问"] = "ask", ["回答"] = "answer",
  ["帮助"] = "help", ["需要"] = "need", ["可以"] = "can", ["要"] = "want",
  ["有"] = "have", ["没有"] = "none", ["好"] = "good", ["坏"] = "bad",
  ["大"] = "big", ["小"] = "small", ["多"] = "many", ["少"] = "few",
  ["新"] = "new", ["旧"] = "old", ["快"] = "fast", ["慢"] = "slow",
  ["高"] = "high", ["低"] = "low", ["长"] = "long", ["短"] = "short",
  ["热"] = "hot", ["冷"] = "cold", ["红"] = "red", ["绿"] = "green",
  ["蓝"] = "blue", ["黄"] = "yellow", ["白"] = "white", ["黑"] = "black",
  ["漂亮"] = "beautiful", ["高兴"] = "happy", ["生气"] = "angry", ["累"] = "tired",
  ["忙"] = "busy", ["便宜"] = "cheap", ["贵"] = "expensive", ["钱"] = "money",
  -- 游戏 / 开发
  ["游戏"] = "game", ["玩家"] = "player", ["角色"] = "character", ["敌人"] = "enemy",
  ["武器"] = "weapon", ["剑"] = "sword", ["刀"] = "knife", ["盾"] = "shield",
  ["攻击"] = "attack", ["防御"] = "defense", ["技能"] = "skill", ["生命"] = "health",
  ["血量"] = "health", ["魔法"] = "magic", ["经验"] = "exp", ["等级"] = "level",
  ["任务"] = "quest", ["关卡"] = "stage", ["地图"] = "map", ["场景"] = "scene",
  ["模型"] = "model", ["材质"] = "material", ["贴图"] = "texture", ["网格"] = "mesh",
  ["骨骼"] = "skeleton", ["动画"] = "animation", ["蓝图"] = "blueprint", ["节点"] = "node",
  ["组件"] = "component", ["变量"] = "variable", ["函数"] = "function", ["代码"] = "code",
  ["项目"] = "project", ["文件"] = "file", ["数据"] = "data", ["服务器"] = "server",
  ["客户端"] = "client", ["界面"] = "UI", ["菜单"] = "menu", ["按钮"] = "button",
  ["窗口"] = "window", ["插件"] = "plugin", ["引擎"] = "engine", ["渲染"] = "render",
  ["帧"] = "frame", ["延迟"] = "latency", ["碰撞"] = "collision", ["物理"] = "physics",
  ["特效"] = "effect", ["粒子"] = "particle", ["光照"] = "lighting", ["阴影"] = "shadow",
  ["相机"] = "camera", ["输入"] = "input", ["输出"] = "output", ["错误"] = "error",
  ["崩溃"] = "crash", ["调试"] = "debug", ["测试"] = "test", ["版本"] = "version",
  ["更新"] = "update", ["发布"] = "release", ["下载"] = "download", ["上传"] = "upload",
  ["保存"] = "save", ["删除"] = "delete", ["复制"] = "copy", ["粘贴"] = "paste",
  ["设置"] = "settings", ["配置"] = "config", ["问题"] = "issue", ["修复"] = "fix",
  -- 古风
  ["古风"] = "ancient style", ["汉服"] = "hanfu", ["剑客"] = "swordsman", ["江湖"] = "jianghu",
  ["武功"] = "martial arts", ["门派"] = "sect", ["道士"] = "taoist", ["神仙"] = "immortal",
  ["修炼"] = "cultivate", ["内功"] = "internal energy", ["掌门"] = "sect leader",
  ["弟子"] = "disciple", ["古琴"] = "guqin", ["棋"] = "chess", ["诗"] = "poetry",
  ["寺庙"] = "temple", ["宫殿"] = "palace", ["城墙"] = "city wall", ["灯笼"] = "lantern",
  ["毛笔"] = "brush", ["墨"] = "ink", ["纸"] = "paper", ["衣服"] = "clothes",
  ["裙子"] = "skirt", ["鞋子"] = "shoes", ["帽子"] = "hat", ["头发"] = "hair",
  -- 上面这张表优先级最高，想改哪个词的英文直接在这里覆盖
  ["牛奶"] = "milk", ["牛"] = "cow", ["古风"] = "ancient style", ["剑"] = "sword",
  -- UE5 / 游戏开发术语人工校正（词表自动生成的对这些词不准）
  ["贴图"] = "texture", ["网格"] = "mesh", ["网格体"] = "mesh", ["材质"] = "material",
  ["材质球"] = "material", ["打光"] = "lighting", ["关卡"] = "level", ["存档点"] = "checkpoint",
  ["读条"] = "cast bar", ["掉落物"] = "drop", ["骨骼动画"] = "skeletal animation",
  ["蒙皮"] = "skinning", ["权重"] = "weight", ["关键帧"] = "keyframe", ["时间轴"] = "timeline",
  ["粒子"] = "particle", ["特效"] = "VFX", ["碰撞体"] = "collision body", ["刚体"] = "rigid body",
  ["触发器"] = "trigger", ["动画蓝图"] = "animation blueprint", ["编译"] = "compile",
  ["打包"] = "package", ["关卡设计"] = "level design", ["技能球"] = "skill orb",
  ["蓝图"] = "blueprint", ["编辑器"] = "editor", ["插件"] = "plugin", ["渲染"] = "render",

  -- ========== 程序 / 编程基础 ==========
  ["程序"] = "program", ["模式"] = "mode", ["控制器"] = "controller", ["管理器"] = "manager",
  ["处理器"] = "CPU", ["编译器"] = "compiler", ["解释器"] = "interpreter", ["调度器"] = "scheduler",
  ["迭代器"] = "iterator", ["生成器"] = "generator", ["适配器"] = "adapter", ["构造器"] = "constructor",
  ["析构函数"] = "destructor", ["监听器"] = "listener", ["定时器"] = "timer", ["计数器"] = "counter",
  ["缓冲区"] = "buffer", ["缓存"] = "cache", ["队列"] = "queue", ["栈"] = "stack", ["堆"] = "heap",
  ["数组"] = "array", ["链表"] = "linked list", ["字典"] = "dictionary", ["哈希表"] = "hash table",
  ["集合"] = "set", ["字符串"] = "string", ["整数"] = "integer", ["浮点数"] = "float",
  ["布尔值"] = "boolean", ["常量"] = "constant", ["参数"] = "parameter", ["返回值"] = "return value",
  ["指针"] = "pointer", ["引用"] = "reference", ["对象"] = "object", ["类"] = "class",
  ["结构体"] = "struct", ["接口"] = "interface", ["方法"] = "method", ["枚举"] = "enum",
  ["实例"] = "instance", ["模块"] = "module", ["库"] = "library", ["框架"] = "framework",
  ["线程"] = "thread", ["进程"] = "process", ["协程"] = "coroutine", ["异步"] = "async",
  ["同步"] = "sync", ["并发"] = "concurrency", ["互斥锁"] = "mutex", ["异常"] = "exception",
  ["断言"] = "assert", ["日志"] = "log", ["注释"] = "comment", ["运算符"] = "operator",
  ["表达式"] = "expression", ["语句"] = "statement", ["作用域"] = "scope", ["命名空间"] = "namespace",
  ["全局变量"] = "global variable", ["局部变量"] = "local variable", ["静态"] = "static",
  ["强制转换"] = "cast", ["序列化"] = "serialize", ["反序列化"] = "deserialize",
  ["算法"] = "algorithm", ["数据结构"] = "data structure", ["递归"] = "recursion",
  ["循环"] = "loop", ["遍历"] = "iterate", ["条件"] = "condition", ["赋值"] = "assign",
  ["声明"] = "declare", ["定义"] = "define", ["调用"] = "call", ["回调"] = "callback",
  ["事件"] = "event", ["委托"] = "delegate", ["泛型"] = "generic", ["继承"] = "inherit",
  ["重载"] = "overload", ["重写"] = "override", ["多态"] = "polymorphism", ["封装"] = "encapsulation",
  ["抽象"] = "abstract", ["单例"] = "singleton", ["设计模式"] = "design pattern",
  ["面向对象"] = "OOP", ["内存泄漏"] = "memory leak", ["空指针"] = "null pointer",
  ["死循环"] = "infinite loop", ["递归深度"] = "recursion depth", ["断点"] = "breakpoint",
  ["单步调试"] = "step debugging", ["堆栈"] = "stack trace", ["性能分析"] = "profiling",
  ["优化"] = "optimize", ["重构"] = "refactor", ["性能"] = "performance", ["内存"] = "memory",
  ["显卡"] = "GPU", ["显示器"] = "monitor", ["分辨率"] = "resolution", ["帧率"] = "framerate",
  -- 工程 / 协作
  ["版本控制"] = "version control", ["仓库"] = "repository", ["分支"] = "branch",
  ["提交"] = "commit", ["合并"] = "merge", ["冲突"] = "conflict", ["拉取"] = "pull",
  ["推送"] = "push", ["依赖"] = "dependency", ["环境"] = "environment", ["构建"] = "build",
  ["部署"] = "deploy", ["文档"] = "document", ["需求"] = "requirement", ["方案"] = "solution",
  ["流程"] = "flow", ["逻辑"] = "logic", ["架构"] = "architecture", ["模块化"] = "modularization",
  ["耦合"] = "coupling", ["解耦"] = "decouple", ["兼容"] = "compatible", ["迁移"] = "migrate",
  ["备份"] = "backup", ["恢复"] = "restore", ["权限"] = "permission", ["账号"] = "account",
  ["登录"] = "login", ["注册"] = "register", ["验证"] = "validate", ["加密"] = "encrypt",
  ["解密"] = "decrypt", ["密钥"] = "key", ["令牌"] = "token", ["请求"] = "request",
  ["响应"] = "response", ["连接"] = "connection", ["端口"] = "port", ["协议"] = "protocol",
  ["网络"] = "network", ["数据库"] = "database", ["表"] = "table", ["字段"] = "field",
  ["索引"] = "index", ["查询"] = "query", ["事务"] = "transaction", ["云服务"] = "cloud service",

  -- ========== 游戏系统 ==========
  ["战斗"] = "combat", ["伤害"] = "damage", ["治疗"] = "heal", ["冷却"] = "cooldown",
  ["施法"] = "cast", ["增益"] = "buff", ["减益"] = "debuff", ["状态效果"] = "status effect",
  ["仇恨"] = "aggro", ["掉落"] = "drop", ["掉落率"] = "drop rate", ["拾取"] = "pickup",
  ["背包"] = "inventory", ["道具"] = "item", ["装备"] = "equipment", ["消耗品"] = "consumable",
  ["货币"] = "currency", ["商店"] = "shop", ["交易"] = "trade", ["支线任务"] = "side quest",
  ["主线"] = "main story", ["经验值"] = "experience", ["升级"] = "level up", ["天赋"] = "talent",
  ["属性点"] = "attribute point", ["面板"] = "stats panel", ["词条"] = "affix",
  ["随机"] = "random", ["概率"] = "probability", ["暴击"] = "critical hit", ["闪避"] = "dodge",
  ["格挡"] = "block", ["命中"] = "hit", ["抗性"] = "resistance", ["护甲"] = "armor",
  ["法力"] = "mana", ["体力"] = "stamina", ["耐力"] = "endurance", ["敏捷"] = "agility",
  ["力量"] = "strength", ["智力"] = "intelligence", ["生命值"] = "HP", ["死亡"] = "death",
  ["复活"] = "revive", ["重生"] = "respawn", ["传送"] = "teleport", ["存档"] = "save",
  ["读档"] = "load", ["自动存档"] = "autosave", ["加载"] = "loading", ["加载画面"] = "loading screen",
  ["主菜单"] = "main menu", ["暂停"] = "pause", ["教程"] = "tutorial", ["成就"] = "achievement",
  ["排行榜"] = "leaderboard", ["多人"] = "multiplayer", ["单人"] = "single player",
  ["联机"] = "online", ["局域网"] = "LAN", ["匹配"] = "matchmaking", ["房间"] = "room",
  ["大厅"] = "lobby", ["观战"] = "spectator", ["回放"] = "replay", ["难度"] = "difficulty",
  ["平衡"] = "balance", ["数值"] = "numeric value", ["配表"] = "data table",
  ["战斗系统"] = "combat system", ["技能树"] = "skill tree", ["成长"] = "progression",
  ["局外养成"] = "meta progression", ["肉鸽"] = "roguelike", ["刷宝"] = "loot farming",
  ["角色扮演"] = "RPG", ["开放世界"] = "open world", ["关卡加载"] = "level streaming",
  ["新手引导"] = "onboarding", ["留存"] = "retention", ["手感"] = "game feel",
  ["打击感"] = "hit feedback", ["后摇"] = "recovery frames", ["前摇"] = "startup frames",
  ["硬直"] = "hitstun", ["连招"] = "combo", ["闪避帧"] = "i-frames", ["判定"] = "hitbox check",
  ["攻击判定"] = "hitbox", ["受击判定"] = "hurtbox", ["伤害数字"] = "damage number",

  -- ========== 引擎 / 渲染 / 动画 ==========
  ["预制体"] = "prefab", ["实体"] = "entity", ["状态机"] = "state machine",
  ["行为树"] = "behavior tree", ["寻路"] = "pathfinding", ["导航网格"] = "navmesh",
  ["射线检测"] = "raycast", ["重力"] = "gravity", ["速度"] = "velocity",
  ["加速度"] = "acceleration", ["摩擦"] = "friction", ["阻尼"] = "damping",
  ["插值"] = "interpolation", ["缓动"] = "easing", ["曲线"] = "curve", ["样条"] = "spline",
  ["反向动力学"] = "IK", ["动作捕捉"] = "motion capture", ["混合空间"] = "blend space",
  ["蒙太奇"] = "montage", ["根运动"] = "root motion", ["动画通知"] = "anim notify",
  ["材质实例"] = "material instance", ["着色器"] = "shader", ["顶点"] = "vertex",
  ["三角面"] = "triangle", ["多边形"] = "polygon", ["拓扑"] = "topology", ["法线"] = "normal",
  ["漫反射"] = "diffuse", ["高光"] = "specular", ["粗糙度"] = "roughness",
  ["金属度"] = "metallic", ["自发光"] = "emissive", ["遮罩"] = "mask", ["UV"] = "UV",
  ["视口"] = "viewport", ["视锥"] = "frustum", ["剔除"] = "culling", ["遮挡剔除"] = "occlusion culling",
  ["细节层次"] = "LOD", ["光追"] = "ray tracing", ["全局光照"] = "global illumination",
  ["后处理"] = "post process", ["抗锯齿"] = "antialiasing", ["垂直同步"] = "vSync",
  ["画质"] = "graphics quality", ["渲染管线"] = "render pipeline", ["批次"] = "batch",
  ["绘制调用"] = "draw call", ["显存"] = "VRAM", ["场景加载"] = "scene loading",
  ["世界坐标"] = "world space", ["局部坐标"] = "local space", ["旋转"] = "rotation",
  ["缩放"] = "scale", ["位移"] = "translation", ["变换"] = "transform", ["坐标系"] = "coordinate system",
  ["地形"] = "terrain", ["植被"] = "foliage", ["天空盒"] = "skybox", ["雾效"] = "fog",
  ["后期效果"] = "post effect", ["景深"] = "depth of field", ["泛光"] = "bloom",
  ["色调映射"] = "tonemapping", ["曝光"] = "exposure", ["环境光"] = "ambient light",
  ["点光源"] = "point light", ["聚光灯"] = "spot light", ["平行光"] = "directional light",
  ["反射探针"] = "reflection probe", ["烘焙"] = "bake", ["光照贴图"] = "lightmap",

  -- ========== UI / 交互 ==========
  ["控件"] = "widget", ["布局"] = "layout", ["锚点"] = "anchor", ["对齐"] = "alignment",
  ["透明度"] = "opacity", ["淡入"] = "fade in", ["淡出"] = "fade out", ["过渡"] = "transition",
  ["提示"] = "tooltip", ["弹窗"] = "popup", ["对话框"] = "dialog", ["滚动条"] = "scrollbar",
  ["复选框"] = "checkbox", ["单选框"] = "radio button", ["下拉框"] = "dropdown",
  ["输入框"] = "input field", ["滑块"] = "slider", ["进度条"] = "progress bar",
  ["图标"] = "icon", ["字体"] = "font", ["字号"] = "font size", ["描边"] = "outline",
  ["圆角"] = "rounded corner", ["自适应"] = "responsive", ["交互"] = "interaction",
  ["悬停"] = "hover", ["点击"] = "click", ["拖拽"] = "drag and drop", ["快捷键"] = "shortcut",
  ["手柄"] = "gamepad", ["摇杆"] = "joystick", ["键盘"] = "keyboard", ["鼠标"] = "mouse",
  ["触屏"] = "touchscreen", ["震动"] = "haptic feedback", ["音效"] = "sound effect",
  ["背景音乐"] = "BGM", ["配音"] = "voice over", ["音量"] = "volume", ["字幕"] = "subtitle",

  -- ========== 关卡 / 美术 / 团队 ==========
  ["白模"] = "blockout", ["灰模"] = "graybox", ["关卡策划"] = "level designer",
  ["数值策划"] = "systems designer", ["玩法"] = "gameplay", ["核心玩法"] = "core loop",
  ["引导"] = "tutorial", ["美术"] = "art", ["原画"] = "concept art", ["建模"] = "modeling",
  ["绑定"] = "rigging", ["动作"] = "animation", ["场景美术"] = "environment art",
  ["角色美术"] = "character art", ["纹理"] = "texture", ["配色"] = "color scheme",
  ["风格化"] = "stylized", ["写实"] = "realistic", ["低模"] = "low poly", ["高模"] = "high poly",
  ["法线贴图"] = "normal map", ["光照烘焙"] = "light baking", ["参考图"] = "reference",
  ["素材"] = "asset", ["资源"] = "resource", ["资产"] = "asset", ["资源包"] = "asset pack",
  ["上架"] = "publish", ["审核"] = "review", ["商店页面"] = "store page", ["定价"] = "pricing",
  ["销量"] = "sales", ["收入"] = "revenue", ["评价"] = "review", ["差评"] = "negative review",
  ["愿望单"] = "wishlist", ["折扣"] = "discount", ["内购"] = "in-app purchase",
  ["运营"] = "operations", ["宣传"] = "marketing", ["预告片"] = "trailer", ["演示"] = "demo",
  ["试玩"] = "playtest", ["反馈"] = "feedback", ["问卷"] = "survey", ["社群"] = "community",
  ["漏洞"] = "bug", ["补丁"] = "patch", ["热更新"] = "hotfix", ["外挂"] = "cheat",
  ["封禁"] = "ban", ["反作弊"] = "anti-cheat", ["本地化"] = "localization", ["翻译"] = "translation",
  ["崩溃日志"] = "crash log", ["复现"] = "reproduce", ["排查"] = "troubleshoot", ["定位"] = "locate",
}

-- 取 Rime 用户目录（换电脑、改用户名时也能找到同目录下的词表）
local function rime_user_dir()
  local api = rawget(_G, "rime_api")
  if api and api.get_user_data_dir then
    local ok, d = pcall(api.get_user_data_dir)
    if ok and type(d) == "string" and d ~= "" then
      return d
    end
  end
  return nil
end
local USER_DIR = rime_user_dir() or [[C:\Users\hu\AppData\Roaming\Rime]]

-- 载入同目录下的 lua 词表：先 require，失败再按绝对路径 loadfile 并执行
-- 注意 loadfile 只是把文件编译成函数，必须再 pcall 执行一次才拿到表
local function load_lua_table(name)
  local ok, t = pcall(require, name)
  if ok and type(t) == "table" then
    return t
  end
  local lf = loadfile
  if lf then
    local cok, chunk = pcall(lf, USER_DIR .. "\\" .. name .. ".lua")
    if cok and type(chunk) == "function" then
      local rok, tbl = pcall(chunk)
      if rok and type(tbl) == "table" then
        return tbl
      end
    end
  end
  return nil
end

-- 虚幻 / 游戏开发专用术语（ue_terms.lua）：优先级高于 CC-CEDICT，压掉生硬译法
local ue_terms = load_lua_table("ue_terms")
if ue_terms ~= nil then
  for k, v in pairs(ue_terms) do
    if zh_en[k] == nil then
      zh_en[k] = v
    end
  end
end

-- 载入自动生成的大词表（zh_en_dict.lua，7.3 万条，来源 CC-CEDICT + 青简）
local big_dict = load_lua_table("zh_en_dict")
if big_dict ~= nil then
  for k, v in pairs(big_dict) do
    if zh_en[k] == nil then
      zh_en[k] = v
    end
  end
end

------------------------------------------------------------------
-- 上屏英文的命名风格（只影响 Ctrl+数字 上屏的内容，候选栏注释仍显示原样）
-- 由「小狼毫设置」界面写入下面第一行，四种取值：
--   pascal  program / behavior tree ->  Program / BehaviorTree
--   raw     program / behavior tree ->  program / behavior tree（原样）
--   snake   program / behavior tree ->  program / behavior_tree
--   lower   program / behavior tree ->  program / behaviortree
-- 全大写缩写（HP / GPU / UV / LOD）在 pascal 下保持原样；C++ / C# 任何风格都不动
------------------------------------------------------------------
local EN_COMMIT_STYLE = "pascal"
local PASCAL_IN_COMMENT = false
local KEEP_EXACT = { vSync = true }   -- 需要原样保留的少数写法

-- 把英文释义切成 token（去掉撇号与标点，截掉 ; , ( 之后的内容）
local function en_tokens(s)
  local head = s:match("^([^;,%(]+)") or s
  head = head:gsub("['`]", ""):gsub("%s+$", "")
  local toks = {}
  for tok in head:gmatch("[%w]+") do
    toks[#toks + 1] = tok
  end
  return toks, head
end

local function to_style(s)
  if s == nil or s == "" then
    return s
  end
  if KEEP_EXACT[s] then
    return s
  end
  local toks, head = en_tokens(s)
  if #toks == 0 then
    return s
  end
  if head:find("[+#]") then
    return s                                           -- C++ / C# 这类不动
  end
  if EN_COMMIT_STYLE == "raw" then
    return s
  end
  if EN_COMMIT_STYLE == "snake" or EN_COMMIT_STYLE == "lower" then
    local low = {}
    for i = 1, #toks do
      low[i] = toks[i]:lower()
    end
    if EN_COMMIT_STYLE == "snake" then
      return table.concat(low, "_")
    end
    return table.concat(low)
  end
  -- 默认 pascal：词组去空格首字母大写，全大写缩写原样
  local out = {}
  for i = 1, #toks do
    local tok = toks[i]
    if #tok >= 2 and tok:match("^%u+$") then
      out[i] = tok
    else
      out[i] = tok:sub(1, 1):upper() .. tok:sub(2)
    end
  end
  return table.concat(out)
end

local to_pascal = to_style

-- 当前候选列表里每个位置对应的英文（供 Ctrl+数字 使用）
local en_cache = {}

--- 过滤器：给候选词加英文注释
function en_comment_filter(input, env)
  local idx = 0
  for cand in input:iter() do
    idx = idx + 1
    local en = zh_en[cand.text]
    if en ~= nil then
      local shown = PASCAL_IN_COMMENT and to_style(en) or en
      local old = cand.comment
      if old ~= nil and old ~= "" then
        cand.comment = shown .. "  " .. old
      else
        cand.comment = shown
      end
      en_cache[idx] = en
    else
      en_cache[idx] = nil
    end
    yield(cand)
  end
  for i = idx + 1, 9 do
    en_cache[i] = nil
  end
end

--- 处理器：Ctrl+1~9 直接上屏对应候选的英文
function commit_en_on_ctrl_num(key, env)
  if key:release() or key:alt() or not key:ctrl() then
    return 2
  end
  local n = tonumber(key:repr():match("Control%+(%d)"))
  if n == nil or n < 1 or n > 9 then
    return 2
  end
  local ctx = env.engine.context
  if not ctx:has_menu() or ctx.input == "" then
    return 2
  end
  local en = en_cache[n]
  if en == nil then
    return 2
  end
  ctx:clear()
  env.engine:commit_text(to_style(en))
  return 1
end