// ============ 新标准内容模型（camelCase 驼峰命名）============
// A2 阶段新增：定义统一 Schema 继承模型与内存层 Normalize 契约。
// 与 news.ts（旧类型/兼容层）并存，绝不删除旧字段。
// 本文件仅做类型定义与内存映射，不写任何 JSON / Markdown 文件。

import type {
  FactType,
  IndustryNews,
  IndustryScores,
  PublishStatus,
  ResearchNews,
  ResearchScores,
  StudyType,
} from './news';

// ============ 通用枚举 ============
export type SourceType = 'regulatory' | 'society' | 'enterprise' | 'journal' | 'database' | 'media' | 'other';
export type GeographicScope = 'global' | 'china' | 'us' | 'eu' | 'japan' | 'other';
export type Language = 'zh' | 'en' | 'other';
export type ContentType =
  | 'policy'
  | 'approval'
  | 'safety'
  | 'research'
  | 'guideline'
  | 'consensus'
  | 'surveillance'
  | 'news'
  | 'resource'
  | 'other';

// 状态机三字段（独立语义，互不替代）
export type RecordStatus = 'active' | 'duplicate' | 'archived' | 'withdrawn';
export type VerificationStatus = 'pending' | 'verified' | 'rejected';
export type ReviewStatus = 'autoProcessed' | 'manualReview' | 'approved';

// 版权许可（两字段分离，不可相互推导）
export type LicenseStatus = 'unknown' | 'verified' | 'permissionRequired' | 'restricted';
export type LicensePermission = 'metadata' | 'abstract' | 'fullTextStorage' | 'publicDisplay';

// ============ 通用基础模型 ============
export interface BaseContent {
  id: string; // 站内统一记录 ID
  externalId?: string; // 外部系统 ID（NMPA 文号 / NCT / PMID）
  title: string;
  sourceName: string;
  sourceType?: SourceType; // 来源类型（与可信度解耦）
  geographicScope?: GeographicScope;
  sourceUrl: string;
  language?: Language;
  abstract?: string; // 原文摘要（严格对齐原文）
  authors?: string[];
  doi?: string;
  licenseUrl?: string;
  licenseStatus?: LicenseStatus;
  licensePermissions?: LicensePermission[];
  sourceUpdatedAt?: string;
  ingestedAt?: string;
  lastCheckedAt?: string;
  contentType?: ContentType;
  summaryZh?: string; // AI 生成中文摘要（需绑定 verificationStatus）
  departments?: string[];
  diseases?: string[];
  drugs?: string[];
  pathogens?: string[];
  tags?: string[];
  recordStatus?: RecordStatus;
  verificationStatus?: VerificationStatus;
  reviewStatus?: ReviewStatus;
  supersedesId?: string;
  relatedRecords?: string[];
}

// ============ 行业资讯 ============
export type PolicyStatus = 'draft' | 'published' | 'effective' | 'revised' | 'expired';
export type ApprovalStatus = 'filed' | 'underReview' | 'approved' | 'rejected' | 'withdrawn';
export type MarketAccessType = 'nmpa' | 'fda' | 'ema' | 'pmda' | 'insurance' | 'hospital';

export interface IndustryContent extends BaseContent {
  policyStatus?: PolicyStatus;
  approvalStatus?: ApprovalStatus;
  marketAccessType?: MarketAccessType;
  factType?: FactType; // 事实/分析/预测（与 sourceType 分离）
  // —— 兼容旧字段（回归测试前保留，A2.1 暂不迁移评分）——
  publishTime?: string;
  eventTime?: string;
  summary?: string;
  impact?: string;
  category?: string;
  scores?: IndustryScores; // 旧五轴评分（内部算法评分，不能替代证据质量）
  totalScore?: number;     // 旧总分（准入线 35）
  isCluster?: boolean;     // 多来源/聚类标记
}

// ============ 科研前沿 ============
export type StudyDesign =
  | 'rct'
  | 'cohort'
  | 'caseControl'
  | 'metaAnalysis'
  | 'systematicReview'
  | 'realWorld'
  | 'preprint'
  | 'other';
export type TrialStatus = 'registered' | 'recruiting' | 'completed' | 'terminated' | 'unknown';
export type PublicationStatus = 'registered' | 'resultsPosted' | 'published' | 'preprint' | 'inReview';

export interface ResearchContent extends BaseContent {
  studyDesign?: StudyDesign; // 研究设计类型（与 evidenceQuality 正交）
  evidenceQuality?: string; // 证据质量：原文分级 + 体系名，或「原文未评估」
  trialId?: string;
  trialStatus?: TrialStatus;
  publicationStatus?: PublicationStatus;
  pmid?: string;
  // —— 兼容旧字段（回归测试前保留）——
  publishTime?: string;
  publishStatus?: PublishStatus; // 旧字段，保留（in-review 等原始状态不丢失）
  studyType?: string; // 旧字段，保留
  evidenceLevel?: string; // 旧字段，保留
  coreFindings?: string;
  limitations?: string;
  inspiration?: string;
  sampleSize?: string | null;
  isPreprint?: boolean;
  scores?: ResearchScores; // 旧五轴评分（内部算法评分，不能替代证据质量）
  totalScore?: number;     // 旧总分（准入线 35）
}

// ============ 抗感染指南 ============
export interface GuidelineContent extends BaseContent {
  slug: string; // 指南详情页路由标识（不可因统一模型改变）
  guidelineVersion?: string; // 新规范版本
  version?: string; // 旧字段，暂保留
  organization?: string;
  year?: number;
  reviewDate?: string;
  docType?: string[];
  infectionSyndromes?: string[]; // 感染综合征（含 ARDS）
  specialPopulations?: string[]; // 特殊人群（粒缺/移植/儿童/妊娠）
  clinicalScenarios?: string[]; // 临床场景（含 CRRT/ECMO）
  preventionManagement?: string[]; // 感染预防与管理
  susceptibilityStandards?: string[]; // 药敏标准/耐药监测
  imagingDiagnosis?: string[];
  comparisons?: string[];
  evidenceQuality?: string;
  recommendationGrade?: string;
  description?: string;
}

// ============ 内存层 Normalize 契约 ============
// 将可选状态字段在「回填默认值后」变为必填的标准化契约。
type Normalize<T> = Omit<
  T,
  'recordStatus' | 'verificationStatus' | 'reviewStatus' | 'licenseStatus' | 'licensePermissions'
> & {
  recordStatus: RecordStatus;
  verificationStatus: VerificationStatus;
  reviewStatus: ReviewStatus;
  licenseStatus: LicenseStatus;
  licensePermissions: LicensePermission[];
};

export type NormalizedIndustryContent = Normalize<IndustryContent>;
export type NormalizedResearchContent = Normalize<ResearchContent>;
export type NormalizedGuidelineContent = Normalize<GuidelineContent>;

// 证据质量/推荐等级：仅原文明确提供或经规范评价时才填写；否则一律「原文未评估」
export const UNASSESSED = '原文未评估';

// 旧 → 新字段映射常量（保守原则）
const STUDY_DESIGN_MAP: Record<StudyType, StudyDesign> = {
  'RCT': 'rct',
  'cohort': 'cohort',
  'real-world': 'realWorld',
  'meta-analysis': 'metaAnalysis',
  'review': 'other', // 普通综述不自动升级为系统综述；无法区分时保守归为 other
  'preprint': 'preprint',
  'other': 'other',
};

const PUBLICATION_STATUS_MAP: Partial<Record<PublishStatus, PublicationStatus>> = {
  published: 'published',
  preprint: 'preprint',
  'in-review': 'inReview', // 投稿后同行评审中，不静默丢失
};

// Normalize 输入：旧字段（news.ts）+ 可能已存在的新字段（content.ts，均可选）。
// 用于兼容「仅旧字段的历史数据」与「已含部分新字段/已人工核验的数据」。
export type IndustryInput = IndustryNews & Partial<IndustryContent>;
export type ResearchInput = ResearchNews & Partial<ResearchContent>;

/**
 * 行业资讯标准化（内存层，不写文件）。
 * 原则：新字段已有合法值 → 优先保留；缺失/为空 → 才回填保守默认。
 * 状态机绝不自动置 verified；版权绝不自动置 verified/permissionRequired。
 * contentType 不因数据模型类型而强制 news：缺失保持 undefined（待分类）。
 */
export function normalizeIndustry(raw: IndustryInput): NormalizedIndustryContent {
  return {
    // 标识与来源
    id: raw.id,
    externalId: raw.externalId,
    title: raw.title,
    sourceName: raw.sourceName,
    sourceType: raw.sourceType,
    geographicScope: raw.geographicScope,
    sourceUrl: raw.sourceUrl,
    language: raw.language,
    abstract: raw.abstract,
    authors: raw.authors,
    doi: raw.doi,
    licenseUrl: raw.licenseUrl,
    // 版权：优先保留已有值，缺失才回填 unknown / []
    licenseStatus: raw.licenseStatus || 'unknown',
    licensePermissions: raw.licensePermissions ?? [],
    sourceUpdatedAt: raw.sourceUpdatedAt,
    ingestedAt: raw.ingestedAt,
    lastCheckedAt: raw.lastCheckedAt,
    // 业务内容类型：不强制 news，缺失/为空保持 undefined（待分类）
    contentType: raw.contentType || undefined,
    summaryZh: raw.summaryZh,
    departments: raw.departments,
    diseases: raw.diseases,
    drugs: raw.drugs,
    pathogens: raw.pathogens,
    tags: raw.tags ?? [],
    // 状态机：优先保留已有值（含人工核验），缺失才回填保守默认
    recordStatus: raw.recordStatus || 'active',
    verificationStatus: raw.verificationStatus || 'pending',
    reviewStatus: raw.reviewStatus || 'autoProcessed',
    supersedesId: raw.supersedesId,
    relatedRecords: raw.relatedRecords,
    // 行业专属
    policyStatus: raw.policyStatus,
    approvalStatus: raw.approvalStatus,
    marketAccessType: raw.marketAccessType,
    factType: raw.factType,
    // 兼容旧字段（保留，不删除）
    publishTime: raw.publishTime,
    eventTime: raw.eventTime,
    summary: raw.summary,
    impact: raw.impact,
    category: raw.category,
    scores: raw.scores,
    totalScore: raw.totalScore,
    isCluster: raw.isCluster,
  };
}

/**
 * 科研前沿标准化（内存层，不写文件）。
 * studyType → studyDesign 映射；evidenceQuality 保守填「原文未评估」，
 * 不自动推断证据/推荐等级；已有 evidenceQuality/studyDesign/publicationStatus 优先保留。
 */
export function normalizeResearch(raw: ResearchInput): NormalizedResearchContent {
  return {
    // 标识与来源
    id: raw.id,
    externalId: raw.externalId,
    title: raw.title,
    sourceName: raw.sourceName,
    sourceType: raw.sourceType,
    geographicScope: raw.geographicScope,
    sourceUrl: raw.sourceUrl,
    language: raw.language,
    abstract: raw.abstract,
    authors: raw.authors,
    doi: raw.doi,
    licenseUrl: raw.licenseUrl,
    licenseStatus: raw.licenseStatus || 'unknown',
    licensePermissions: raw.licensePermissions ?? [],
    sourceUpdatedAt: raw.sourceUpdatedAt,
    ingestedAt: raw.ingestedAt,
    lastCheckedAt: raw.lastCheckedAt,
    // 科研内容的天然业务类型为 research，允许显式覆盖为 consensus/guideline 等
    contentType: raw.contentType || 'research',
    summaryZh: raw.summaryZh,
    departments: raw.departments,
    diseases: raw.diseases,
    drugs: raw.drugs,
    pathogens: raw.pathogens,
    tags: raw.tags ?? [],
    recordStatus: raw.recordStatus || 'active',
    verificationStatus: raw.verificationStatus || 'pending',
    reviewStatus: raw.reviewStatus || 'autoProcessed',
    supersedesId: raw.supersedesId,
    relatedRecords: raw.relatedRecords,
    // 研究设计：优先保留已有值，缺失才从 studyType 映射
    studyDesign: raw.studyDesign || STUDY_DESIGN_MAP[raw.studyType] || 'other',
    // 证据质量：优先保留已有值，缺失/为空才填「原文未评估」
    evidenceQuality: raw.evidenceQuality || UNASSESSED,
    trialId: raw.trialId,
    trialStatus: raw.trialStatus,
    // 发表状态：优先保留已有值，缺失才从 publishStatus 映射
    publicationStatus: raw.publicationStatus || PUBLICATION_STATUS_MAP[raw.publishStatus],
    pmid: raw.pmid,
    // 兼容旧字段（保留，不删除）
    publishTime: raw.publishTime,
    publishStatus: raw.publishStatus,
    studyType: raw.studyType,
    evidenceLevel: raw.evidenceLevel,
    coreFindings: raw.coreFindings,
    limitations: raw.limitations,
    inspiration: raw.inspiration,
    sampleSize: raw.sampleSize,
    isPreprint: raw.isPreprint,
    scores: raw.scores,
    totalScore: raw.totalScore,
  };
}
