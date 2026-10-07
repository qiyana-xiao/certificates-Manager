// 省份拼音数据：用于省份选择器里的"拼音/首字母"搜索
// P = 全拼小写，I = 首字母缩写，L = 索引首字母
export const PINYIN_MAP = {
  BJ: { P: 'beijing', I: 'bj', L: 'B' },
  SH: { P: 'shanghai', I: 'sh', L: 'S' },
  GD: { P: 'guangdong', I: 'gd', L: 'G' },
  ZJ: { P: 'zhejiang', I: 'zj', L: 'Z' },
  JS: { P: 'jiangsu', I: 'js', L: 'J' },
  SC: { P: 'sichuan', I: 'sc', L: 'S' },
  CQ: { P: 'chongqing', I: 'cq', L: 'C' },
  SD: { P: 'shandong', I: 'sd', L: 'S' },
  HA: { P: 'henan', I: 'hn', L: 'H' },
  TJ: { P: 'tianjin', I: 'tj', L: 'T' },
  HE: { P: 'hebei', I: 'hb', L: 'H' },
  SX: { P: 'shanxi', I: 'sx', L: 'S' },
  NM: { P: 'neimenggu', I: 'nmg', L: 'N' },
  LN: { P: 'liaoning', I: 'ln', L: 'L' },
  JL: { P: 'jilin', I: 'jl', L: 'J' },
  HL: { P: 'heilongjiang', I: 'hlj', L: 'H' },
  AH: { P: 'anhui', I: 'ah', L: 'A' },
  FJ: { P: 'fujian', I: 'fj', L: 'F' },
  JX: { P: 'jiangxi', I: 'jx', L: 'J' },
  HB: { P: 'hubei', I: 'hb', L: 'H' },
  HN: { P: 'hunan', I: 'hn', L: 'H' },
  GX: { P: 'guangxi', I: 'gx', L: 'G' },
  HI: { P: 'hainan', I: 'hn', L: 'H' },
  GZ: { P: 'guizhou', I: 'gz', L: 'G' },
  YN: { P: 'yunnan', I: 'yn', L: 'Y' },
  XZ: { P: 'xizang', I: 'xz', L: 'X' },
  SN: { P: 'shaanxi', I: 'sx', L: 'S' },
  GS: { P: 'gansu', I: 'gs', L: 'G' },
  QH: { P: 'qinghai', I: 'qh', L: 'Q' },
  NX: { P: 'ningxia', I: 'nx', L: 'N' },
  XJ: { P: 'xinjiang', I: 'xj', L: 'X' },
}

// 是否命中：支持 名称 / 全拼 / 首字母缩写 / 单个首字母
export function matchProvince(prov, query) {
  const q = (query || '').trim().toLowerCase()
  if (!q) return true
  const p = PINYIN_MAP[prov.code]
  const nameHit = prov.name.toLowerCase().includes(q)
  if (p) {
    return nameHit || p.I.includes(q) || p.P.includes(q) || p.L.toLowerCase() === q
  }
  return nameHit
}