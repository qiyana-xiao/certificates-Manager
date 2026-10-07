-- 证件管家 种子数据（省份参照 + 证件类型 + 续办指南）
USE `doc_keeper`;

-- ---------------- 省份参照表 ----------------
-- jtw_code（交管12123平台子域名字母码）全部核实自公安部互联网交通安全综合服务管理平台官网导航
-- portal_url 仅收录已逐个核实的省级政务服务网；未核实的留空，前端自动回退到国家政务服务平台
INSERT INTO `provinces` (`code`, `name`, `jtw_code`, `portal_name`, `portal_url`, `region_type`, `sort`) VALUES
('BJ', '北京市',           'bj', '京通 · 北京市政务服务网',   'https://banshi.beijing.gov.cn/', '直辖市', 1),
('SH', '上海市',           'sh', '随申办 · 一网通办',        'https://zwdt.sh.gov.cn/',        '直辖市', 2),
('GD', '广东省',           'gd', '粤省事 · 广东政务服务网',  'https://www.gdzwfw.gov.cn/',     '省', 3),
('ZJ', '浙江省',           'zj', '浙里办 · 浙江政务服务网',  'https://zwfw.zj.gov.cn/',        '省', 4),
('JS', '江苏省',           'js', '苏服办 · 江苏政务服务网',  'https://www.jszwfw.gov.cn/',     '省', 5),
('SC', '四川省',           'sc', '天府通办 · 四川政务服务网','https://www.sczwfw.gov.cn/',     '省', 6),
('CQ', '重庆市',           'cq', '渝快办 · 重庆政务服务网',  'https://zwykb.cq.gov.cn/',       '直辖市', 7),
('SD', '山东省',           'sd', '爱山东 · 山东政务服务网',  'http://zwfw.sd.gov.cn/',         '省', 8),
('HA', '河南省',           'ha', '豫事办 · 河南政务服务网',  'https://www.hnzwfw.gov.cn/',     '省', 9),
('TJ', '天津市',           'tj', '津心办 · 天津政务服务网',  'https://zwfw.tj.gov.cn/',         '直辖市', 10),
('HE', '河北省',           'he', '冀时办 · 河北政务服务网',  'http://zwfw.hebei.gov.cn/',       '省', 11),
('SX', '山西省',           'sx', '山西政务服务网',           'http://www.sxzwfw.gov.cn/',       '省', 12),
('NM', '内蒙古自治区',     'nm', '蒙速办 · 内蒙古政务服务网','https://zwfw.nmg.gov.cn/',        '自治区', 13),
('LN', '辽宁省',           'ln', '辽宁政务服务网',           'https://www.lnzwfw.gov.cn/',      '省', 14),
('JL', '吉林省',           'jl', '吉事办 · 吉林政务服务网',  'https://zwfw.jl.gov.cn/',         '省', 15),
('HL', '黑龙江省',         'hl', '龙易办 · 黑龙江政务服务网','https://www.zwfw.hlj.gov.cn/',    '省', 16),
('AH', '安徽省',           'ah', '皖事通 · 安徽政务服务网',  'https://www.ahzwfw.gov.cn/',      '省', 17),
('FJ', '福建省',           'fj', '闽政通 · 福建政务服务网',  'https://zwfw.fujian.gov.cn/',     '省', 18),
('JX', '江西省',           'jx', '赣服通 · 江西政务服务网',  'https://www.jxzwfww.gov.cn/',     '省', 19),
('HB', '湖北省',           'hb', '鄂汇办 · 湖北政务服务网',  'https://zwfw.hubei.gov.cn/',      '省', 20),
('HN', '湖南省',           'hn', '湘易办 · 湖南政务服务网',  'https://zwfw-new.hunan.gov.cn/',  '省', 21),
('GX', '广西壮族自治区',   'gx', '智桂通 · 广西政务服务网',  'https://zwfw.gxzf.gov.cn/',       '自治区', 22),
('HI', '海南省',           'hi', '海易办 · 海南政务服务网',  'https://wssp.hainan.gov.cn/',     '省', 23),
('GZ', '贵州省',           'gz', '贵州政务服务网',           'https://zwfw.guizhou.gov.cn/',    '省', 24),
('YN', '云南省',           'yn', '云南政务服务网',           'https://zwfw.yn.gov.cn/portal',   '省', 25),
('XZ', '西藏自治区',       'xz', '西藏政务服务网',           'https://www.xzzwfw.gov.cn/',      '自治区', 26),
('SN', '陕西省',           'sn', '秦务员 · 陕西政务服务网',  'https://zwfw.shaanxi.gov.cn/',    '省', 27),
('GS', '甘肃省',           'gs', '甘快办 · 甘肃政务服务网',  'https://zwfw.gansu.gov.cn/',      '省', 28),
('QH', '青海省',           'qh', '青松办 · 青海政务服务网',  'https://www.qhzwfw.gov.cn/',      '省', 29),
('NX', '宁夏回族自治区',   'nx', '我的宁夏 · 宁夏政务服务网','https://zwfw.nx.gov.cn/',         '自治区', 30),
('XJ', '新疆维吾尔自治区', 'xj', '新服办 · 新疆政务服务网',  'https://zwfw.xinjiang.gov.cn/',   '自治区', 31);

-- 注：本表收录 31 个大陆省级行政区（23省+4直辖市+5自治区）；"特别行政区"（港/澳）及台湾省不在此列。

-- ---------------- 常用证件类型 ----------------
INSERT INTO `document_types` (`code`, `name`, `issuer`, `icon`, `default_ahead_days`, `valid_years`, `desc`) VALUES
('resident_id',    '居民身份证',   '公安机关',          '🪪', JSON_ARRAY(90,30,7),  NULL, '16周岁以上有效期5/10/20/长期，16周岁以下5年'),
('driving_license','机动车驾驶证', '公安交管部门',      '🚗', JSON_ARRAY(90,30,7),  NULL, '初次6年、换证可10年或长期，注意体检与视力'),
('passport',       '护照',         '出入境管理',        '🛂', JSON_ARRAY(180,90,30,7), 10, '普通护照有效期10年，16周岁以下5年'),
('hm_pass',        '港澳通行证',   '出入境管理',        '✈️', JSON_ARRAY(90,30,7),  5,   '往来港澳通行证有效期5年，有效期短于签注需先换证'),
('residence_permit','居住证',      '居住地公安派出所',  '🏠', JSON_ARRAY(60,30,7), NULL,'按居住地政策，需定期签注续期'),
('social_insurance_card','社会保障卡','人社部门',      '💳', JSON_ARRAY(90,30,7),  NULL, '社保卡需在有效期内使用，到期前换发'),
('vehicle_inspection','机动车检验', '车管所/检测站',     '🚘', JSON_ARRAY(90,30,7),  1,   '六年免检后需按周期上线检验'),
('stored_value_card','储值卡/会员卡','商家/机构',       '🎫', JSON_ARRAY(30,7,1),   NULL, '健身/培训/储值等，防止余额过期浪费');

-- ---------------- 续办指南 ----------------
-- link_mode 说明：
--   FIXED           所有省份统一打开 official_url（如国家移民管理局平台）
--   PROVINCE_PORTAL 按用户省份打开本省政务服务网（身份证/居住证等属地化业务），未收录时回退 official_url
--   PROVINCE_JTW    按用户省份打开本省交管12123平台（xx.122.gov.cn，字母码全部经官网核实）
-- region_code 为 NULL 表示全国通用；管理员可为个别省份补充"本省版"指南（费用/时限差异较大时）
INSERT INTO `renewal_guides`
(`document_type_id`, `title`, `region_code`, `link_mode`, `materials`, `location`, `fee`, `duration`, `official_url`, `source`, `updated_at`, `disclaimer`) VALUES
(
 (SELECT id FROM document_types WHERE code='resident_id'),
 '居民身份证到期换领',
 NULL, 'PROVINCE_PORTAL',
 JSON_ARRAY('原居民身份证原件（领取新证时须交回）','居民户口簿（核验身份用）','本人近期照片（一般现场采集）'),
 '户籍所在地派出所户籍窗口或政务服务中心公安户政窗口；已开通身份证全国通办，可异地办理',
 '换领 20 元/证；丢失补领、损坏换领 40 元/证',
 '承诺时限各地不同（法定 90 个工作日，多数地区 1-20 个工作日，加急或邮寄可更快）',
 'https://gjzwfw.www.gov.cn/',
 '公安部户政管理规范；材料与费用经贵州、陕西、湖南等省政务门户交叉核实',
 '2026-09-27',
 '以当地窗口实际要求为准；邮寄送达与办理时限请以当地确认为准。'
),
(
 (SELECT id FROM document_types WHERE code='driving_license'),
 '机动车驾驶证期满换证',
 NULL, 'PROVINCE_JTW',
 JSON_ARRAY('本人有效身份证原件','一寸白底免冠照片（线上可复用体检照片）','身体条件证明（有资质医疗机构出具，必须提交）'),
 '线上：「交管12123」App 或本省交通安全综合服务管理平台 → 驾驶证补换领 → 期满换证，支持邮寄或车管所自取；线下：车管所窗口',
 '工本费 10 元/证（各地略有差异，邮寄另计邮费）',
 '到期前 90 日内即可申请；线上办理一般数日内寄达，线下可当场或按辖区时限办结',
 'https://www.122.gov.cn/',
 '公安部交通管理局（公安部令第172号）交管12123官方流程，材料经盐城、北京、天长政务门户交叉核实',
 '2026-09-27',
 '以当地车管所与医疗机构实际要求为准；到期前请尽早办理，避免影响驾驶。'
),
(
 (SELECT id FROM document_types WHERE code='passport'),
 '普通护照到期换发',
 NULL, 'FIXED',
 JSON_ARRAY('本人有效身份证原件','近期免冠照片（出入境大厅现场采集）','旧护照（如有）'),
 '户籍地或居住地公安机关出入境管理机构；可在国家移民管理局政务服务平台或"移民局"App预约办理',
 '护照工本费每本 120 元，加注另计（以最新收费标准为准）',
 '法定 30 日内、一般情况下自受理日起 7-15 个工作日办结，可加急或速递',
 'https://s.nia.gov.cn/',
 '国家移民管理局政务服务平台（支持出入境证件预约申请与换补发网上申请）',
 '2026-09-27',
 '护照有效期不足或需换发时请提前办理；具体费用时限以出入境窗口与最新规定为准。'
),
(
 (SELECT id FROM document_types WHERE code='hm_pass'),
 '往来港澳通行证换发',
 NULL, 'FIXED',
 JSON_ARRAY('本人有效身份证原件','近期免冠照片（出入境大厅现场采集）','旧通行证（如有）'),
 '户籍地或居住地公安机关出入境管理机构；国家移民管理局政务服务平台支持证件换补发网上申请与签注办理',
 '以最新收费标准为准（通行证与签注分开计费）',
 '一般数个工作日办结，可加急或速递（以当地公布时限为准）',
 'https://s.nia.gov.cn/',
 '国家移民管理局政务服务平台（入口已核实；费用与细则请以窗口最新公示为准）',
 '2026-09-27',
 '以当地出入境窗口实际要求为准。'
),
(
 (SELECT id FROM document_types WHERE code='residence_permit'),
 '居住证签注续期',
 NULL, 'PROVINCE_PORTAL',
 JSON_ARRAY('本人身份证原件','居住证原件','居住地址或就业、就读证明材料（以本地要求为准）'),
 '居住地公安派出所或政务服务网上办理；多数城市支持线上签注、邮寄到家',
 '签注一般免费（以居住地政策为准）',
 '多数地区当场或数个工作日办结',
 'https://gjzwfw.www.gov.cn/',
 '来源待核实，请按所在城市居住证签注办事指南确认',
 '2026-09-27',
 '以居住地公安派出所与政务平台实际要求为准。'
),
(
 (SELECT id FROM document_types WHERE code='social_insurance_card'),
 '社会保障卡换发',
 NULL, 'FIXED',
 JSON_ARRAY('本人身份证原件','近期免冠照片（部分城市可复用现有照片）','旧社保卡（如有）'),
 '合作银行网点或当地人社部门经办窗口；国家政务服务平台与"电子社保卡"渠道支持线上办理',
 '首次发卡与到期换发一般免费（以当地人社部门政策为准）',
 '以当地人社部门公布时限为准',
 'https://gjzwfw.www.gov.cn/',
 '来源待核实，请管理员按本地人社政策补充',
 '2026-09-27',
 '以当地人社部门实际要求为准。'
),
(
 (SELECT id FROM document_types WHERE code='vehicle_inspection'),
 '机动车检验（年检）',
 NULL, 'PROVINCE_JTW',
 JSON_ARRAY('行驶证原件','交强险凭证','处理完违章（检验前需先处理）'),
 '「交管12123」App 或本省交通安全综合服务管理平台预约 → 前往检测站上线检验',
 '按检测站公示收费标准（不同车型略有差异）',
 '检验合格后即时发放检验合格标志',
 'https://www.122.gov.cn/',
 '公安部交管12123平台检验预约流程（入口已核实；细则以当地车管所为准）',
 '2026-09-27',
 '以当地车管所/检测站实际要求为准。'
),
(
 (SELECT id FROM document_types WHERE code='stored_value_card'),
 '储值卡余额提醒（通用）',
 NULL, 'FIXED',
 JSON_ARRAY('联系发卡商家/机构确认使用规则与过期政策'),
 '', '', '', '',
 '通用提醒，非政务办理项，请以商家/机构规则为准',
 '2026-09-27',
 '储值卡/会员卡为商家约定，请以发卡机构规则为准'
);
