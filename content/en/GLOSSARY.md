# 英文版译名与体例（GLOSSARY）

中文是源文本，英文按同一套键写在本目录的 `*.json` 里（结构见 `src/i18n.py` 开头）。本文件记录译名体例，新增或修改英文时照此执行；同一个名称在全图各处必须写法一致（地图注记、悬停说明、索引、对照表、年表、节点说明）。体例与《宋辽夏金元形势图》相同，两图共有的名称（宋、辽、吴越、高丽、大理、甘州回鹘、各州府等）写法一致；下面第三节是本图特有的约定（藩镇、带“军”的藩镇名在本图另有写法，见第三节）。

## 一、总原则

1. **说真话**：英文只翻译中文已有的内容，不增不减；中文本身有误时先改中文，再改英文（并运行 `python tools/i18n.py lock`）。
2. **通俗写法，全图统一**：采用英文读者最常见的写法（An Lushan Rebellion、Khitan、Uyghurs、Kucha、Khotan），不用学术转写。
3. **地名用当时当地的名称**：中国及汉字文化圈的地名用汉语拼音转写中文古名；汉字圈以外的地名用当地当时名称的通行英文写法，而不是把中文译音再转回拼音（八剌沙衮 → Balasagun，斡耳朵八里 → Ordu-Baliq，娑陵水 → Selenge River，臧河 → Tsangpo）。中文自起的名称照拼音（葱岭河 Congling River、蒲昌海 Puchang Lake）。
4. **今地/今名**用今天的通行英文名和行政区（Kaifeng, Henan；Tokmok, Kyrgyzstan）。行政区划变了中英文一起改（越南 2025 年 7 月并省：广南并入岘港、永福并入富寿）。
5. **地图注记不加中文里没有的消歧义**：同音的不同地名（易水、伊水都作 Yi River）照写，靠位置和悬停里的汉字区分；中文自带的区别字样照译（洛水（北）→ Northern Luo River）。“今地 / 今名”一栏是给英文读者定位用的，英文同名时可括注地区（Min River (Sichuan)），英文读者更熟悉另一通行名时可括注（Nu River (Salween)）。
6. **政权全称可括注别称**（Huanwang (Champa)、Wendan (Land Chenla)），地图短名不括注。
7. 英文界面里，地图注记只显示英文；悬停说明、索引、对照表、年表在英文名后附注汉字原名。

## 二、拼音与通名

| 类别 | 写法 | 例 |
|---|---|---|
| 拼音 | 不标声调；音节界限有歧义时加撇号；ü 保留 | Chang'an、Huai'an、Yelü、Lüliang |
| 州（单音节专名） | 连写 | 汴州 Bianzhou、泷州 Shuangzhou、蔚州 Yuzhou |
| 州（多音节专名） | 分写 Zhou | 安乐州 Anle Zhou、万安州 Wan'an Zhou |
| 府 / 军 | 分写，不意译 | 京兆府 Jingzhao Fu、兴王府 Xingwang Fu、天雄军 Tianxiong Jun |
| 县 / 郡 | County / Commandery | 马邑县 Mayi County、东平郡 Dongping Commandery |
| 城 | City；英文已有定名的从定名 | 太和城 Taihe City、中受降城 Central Shouxiang City、石堡城 Shibao Fortress |
| 镇（军镇）/ 守捉 | Garrison | 播仙镇 Boxian Garrison、葱岭守捉 Congling Garrison、清海镇 Cheonghae Garrison |
| 都护府 | Protectorate | 单于都护府 Chanyu Protectorate、安东都护府 Andong Protectorate |
| 京（陪都） | 府名在前，京名意译加括注 | 上京龙泉府 Longquan Fu (Supreme Capital)、中京显德府 Xiande Fu (Central Capital) |
| 都城的括注 | 意译 | 洛阳（东都）Luoyang (Eastern Capital)、杭州（西府）Hangzhou (Western Seat)、太原（晋王府）Taiyuan (seat of the Prince of Jin) |
| 牙帐 | camp | 回鹘牙帐 Uyghur khagan's camp、奚王牙帐 Xi king's camp |
| 关 / 口 | Pass；已成专名者照拼 | 潼关 Tong Pass、飞狐口 Feihu Pass、古北口 Gubeikou |
| 水 / 河 / 江 | X River；与他河撞名或英文惯用 -shui 的连写 | 汾水 Fen River、湟水 Huangshui、弱水 Ruoshui |
| 湖 / 海 / 泽 / 泊 | Lake X 或 X Lake，从英文习惯；泽 Marsh | 太湖 Lake Tai、蒲昌海 Puchang Lake、大野泽 Daye Marsh |
| 山 | 山脉 X Mountains；单峰 Mount X | 太行山 Taihang Mountains、泰山 Mount Tai、邙山 Mount Mang、紫金山 Mount Zijin |
| 蛮 | tribes（不用 barbarian） | 牂牁蛮 Zangke tribes、黄洞蛮 Huangdong tribes |

## 三、本图特有的约定

| 中文 | 英文 | 说明 |
|---|---|---|
| 藩镇（类别） | fanzhen（复数同形） | 着色按钮 Fanzhen，悬停标签 Fanzhen，索引组头 Fanzhen (military circuits)，计数 46 fanzhen；藩镇名本身不加通名：魏博 Weibo、成德 Chengde、昭义 Zhaoyi。不单用 circuit：circuit 是“道”的对译，指唐前期的监察区，不等于节度使掌兵、财、民政的藩镇 |
| 名称里带“道”的 | X Circuit | 道才作 circuit：关内道 Guannei Circuit、山南东道 Shannan East Circuit、江南西道 Jiangnan West Circuit |
| 名称里带“军”的 | X Jun | 照“军”分写的通例：定难军 Dingnan Jun、归义军 Guiyi Jun、天雄军 Tianxiong Jun |
| 管（岭南五管） | Command | 桂管 Gui Command、邕管 Yong Command、岭南（广管）Lingnan (Guang Command) |
| 京畿 / 都畿、东都畿 | Capital District / Eastern Capital District | 同宋元“府界 Capital District” |
| 割据（斜线） | autonomous | 图例“割据藩镇”作 Autonomous fanzhen，悬停标签作 Autonomous |
| 节度使 | military governor | 九节度使 nine military governors |
| 回纥 / 回鹘 | Uyghurs | 两种汉字写法英文不分；汗国全称 Uyghur Khaganate |
| 吐蕃 | Tibetan Empire（短名 Tibet） | 842 年后的吐蕃诸部作 Tibetan tribes |
| 契丹 | Khitan | 作政权名用于胜负、标题（Khitan defeated Balhae）；947 年后的当年别名作 Liao |
| 渤海 | Balhae | 渤海的府州用拼音（同宋元）；渤海人名用新罗马字（大諲譔 Dae Inseon） |
| 新罗、后百济、泰封 | Silla、Later Baekje、Taebong | 新罗州名用新罗马字（汉州 Hanju、武珍州 Mujinju），不套用同名的中国州名拼音 |
| 越南 | 越南读音，保留声调符号 | 州名同宋元（交州 Giao Châu、爱州 Ái Châu）；人名 Ngô Quyền、Khúc Hạo；唐的建置名用拼音（安南 Annan、静海 Jinghai）；今地里有英文通行名的大城市不加声调（Hanoi、Haiphong、Da Nang），其余保留（Ninh Bình、Quảng Nam） |
| 环王、文单 | Huanwang (Champa)、Wendan (Land Chenla) | 唐人自起的国名照拼音，括注通行名 |
| 安史之乱 | An Lushan Rebellion | 通行写法；燕（安史）作 Yan (An Lushan and Shi Siming) |

## 四、人名、政权、王朝

- 汉人名：姓在前、拼音（Guo Ziyi、Li Keyong）；复姓连写（Geshu Han、Pugu Huai'en、Zhuye Chixin、Yelü Abaoji）；帝王用“Emperor + 庙号 + of + 朝”（Emperor Taizong of Song）。
- 姓氏读音：查 Zha（查文徽）、单 Shan、尉迟 Yuchi。
- 吐蕃、回鹘人名按汉文史籍拼音（Shang Jiezan、Lun Mangre、Jiegan Jiasi）；可汗作 Khagan（Wujie Khagan），叶护作 yabghu。
- 朝鲜用新罗马字（Gung Ye、Gyeon Hwon、Wang Geon）；日本用平文式（Heian-kyō、Ennin）；越南保留声调符号（Ngô Quyền、Đinh Bộ Lĩnh）。
- 五代十国：后梁 Later Liang、后唐 Later Tang、后晋 Later Jin、后汉 Later Han、后周 Later Zhou；前蜀 Former Shu、后蜀 Later Shu、南唐 Southern Tang、南汉 Southern Han、北汉 Northern Han、荆南（南平）Jingnan (Nanping)。
- 和议、盟约一律作 Treaty of X（Treaty of Jingyang、Treaty of Diancang）。
- 政权名见 `units.json`：地图上用短名（s），说明里用全称（n）。

## 五、年代

- 中文写农历月份，英文照写农历月序，不换算公历：
  - 755 年十一月 → 11th month, 755；闰十一月 → intercalary 11th month；正月 → 1st month
  - 春、夏、秋、冬 → spring / summer / autumn / winter 938
  - 跨月、跨年：757 年正—二月 → 1st–2nd month, 757；925 年十二月—926 年正月 → 12th month, 925 – 1st month, 926
  - 年份是该农历年大部分所在的公历年，所以十二月可能已在次年 1 月。
- 年号：Tianbao 14、Taiping Xingguo 4（年号拼音 + 序数；“载”“年”不分）。
- 约 → c.；年份区间用 en dash：868–869；世纪 9th century。

## 六、战役

- 名称：Battle of X / Siege of X，英文已有通行名称的用通行名称（Battle of Bạch Đằng）；中文不是“X之战”的照意译（吐蕃陷长安 Tibetan capture of Chang'an、收复三关 Recovery of the Three Passes）。
- 同地多次战役，英文以年份括注区别：Battle of Taiyuan (757) / (979)。
- 交战结果：“A defeated B”，城破加注 “(city fell)”；守城作 “A held the city”，攻陷作 “A took the city”，惨胜作 “won a costly victory over”。
- 主将：“A and B vs. C”；三人以上 “A, B and C”。

## 七、维护

- `python tools/i18n.py status`：缺译、过期、未登记指纹的条数。
- `python tools/i18n.py todo [文件]`：逐条列出缺译与过期的中文。
- 改完英文：`python tools/i18n.py lock` 记下中文指纹；以后中文一改，对应英文就会报“过期”。
- `python run.py --html` 默认严格：有缺译或过期就停下；`--draft` 允许先出草稿（缺译处显示中文）。
- `python tools/i18n.py table` 导出中英对照表 `build/i18n-review.tsv` 供审校。
