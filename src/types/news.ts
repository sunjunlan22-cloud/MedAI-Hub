// 资讯共享类型定义
// 严格对齐 PRD 第 3.3、4.3、5.2 节【确定】字段

// 事实类型：明确区分事实 / 分析 / 预测（PRD 3.3）
export type FactType = 'fact' | 'analysis' | 'forecast';

// ===== 行业资讯 =====

// 行业资讯五轴评分（PRD 5.2）
export interface IndustryScores {
  policyImpact: number;          // 政策/医保影响度 (1-10)
  marketImpact: number;          // 市场/销售额波及面 (1-10)
  breakthrough: number;          // 产品/管线突破性 (1-10)
  competitiveImpact: number;     // 企业/竞争格局影响 (1-10)
  timelinessAuthority: number;   // 时效性与权威可信度 (1-10)
}

export interface IndustryNews {
  id: string;
  title: string;                          // 标题
  eventTime: string;                      // 事件发生时间 (ISO)
  publishTime: string;                    // 发布时间 (ISO)
  sourceName: string;                     // 来源名称
  sourceUrl: string;                      // 原始链接
  category: string;                       // 事件分类（集采/医保/BD/获批/财报/政策/反腐）
  tags: string[];                         // 标签
  summary: string;                        // AI 摘要
  impact: string;                         // 行业影响评估
  scores: IndustryScores;                 // 五轴评分
  totalScore: number;                     // 总分（满分 50，准入线 35）
  isCluster: boolean;                     // 多来源/聚类标记
  factType: FactType;                     // 事实/分析/预测
  // —— 以下为 B4/B5 阶段新增字段（可选，兼容旧数据）——
  contentType?: string;                   // 内容类型：policy/approval/surveillance/news/resource 等
  approvalStatus?: string;                // 审批状态（filed/underReview/approved/rejected/withdrawn）
  policyStatus?: string;                  // 政策状态（draft/published/effective/revised/expired）
  marketAccessType?: string;              // 市场准入类型（nmpa/fda/ema/pmda/insurance/hospital）
  externalId?: string;                    // 外部系统 ID（NMPA 文号 / 报告编号）
  sourceType?: string;                    // 来源类型（regulatory/society/enterprise/journal/database/media/other）
  pathogens?: string[];                   // 病原体（GLASS 监测/审批）
  drugs?: string[];                       // 药物（GLASS 监测/审批）
  abstract?: string;                      // 原文摘要 / 结构化监测数据（含 PDF 链接）
}

// ===== 科研资讯 =====

// 科研资讯五轴评分（PRD 5.2）
export interface ResearchScores {
  topicInspiration: number;       // 课题启发性 (1-10)
  clinicalApplicability: number;  // 临床可落地性 (1-10)
  evidenceLevel: number;          // 证据等级 (1-10)
  specialtyUniversality: number;  // 专科普适性 (1-10)
  researchValue: number;          // 科研增益价值 (1-10)
}

export type StudyType = 'RCT' | 'cohort' | 'real-world' | 'meta-analysis' | 'review' | 'preprint' | 'other';
export type PublishStatus = 'published' | 'preprint' | 'in-review';

export interface ResearchNews {
  id: string;
  title: string;                          // 研究标题
  sourceName: string;                     // 原始来源（期刊/平台）
  sourceUrl: string;                      // 原始链接
  studyType: StudyType;                   // 研究类型
  publishStatus: PublishStatus;           // 发表状态
  sampleSize?: string | null;              // 样本量（若原文提供）
  publishTime: string;                    // 发布时间 (ISO)
  coreFindings: string;                   // 核心发现
  limitations: string;                    // 研究局限
  inspiration: string;                    // 临床/科研启发
  evidenceLevel: string;                  // 证据等级提示
  scores: ResearchScores;                 // 五轴评分
  totalScore: number;                     // 总分（满分 50，准入线 35）
  isPreprint: boolean;                    // 是否预印本（强制标注"未同行评议"）
  tags: string[];                         // 标签
  // —— 以下为新增字段（可选，兼容旧数据）——
  contentType?: string;                   // 内容类型（默认 research）
  studyDesign?: string;                   // 研究设计（rct/cohort/caseControl/metaAnalysis/systematicReview/realWorld/preprint/other）
  trialId?: string;                       // 临床试验注册号（如 NCT 号）
  trialStatus?: string;                   // 临床试验状态（registered/recruiting/completed/terminated/unknown）
  publicationStatus?: string;             // 发表状态（registered/resultsPosted/published/preprint/inReview）
  pmid?: string;                          // PubMed PMID
  evidenceQuality?: string;               // 证据质量（原文分级或「原文未评估」）
  abstract?: string;                      // 原文摘要
  diseases?: string[];                    // 疾病
  drugs?: string[];                       // 药物
  relatedRecords?: string[];              // 关联记录 ID
}
