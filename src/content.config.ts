import { defineCollection, z } from 'astro:content';

// 抗感染指南与临床证据：Markdown 知识库（人工维护，受保护）
// 多维分类架构对齐 Evidence Navigator 体系（PRD 7.1 / 7.2）
const guides = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      title: z.string(),                          // 指南/证据名称
      organization: z.string(),                   // 发布组织（如 IDSA/ATS/中华医学会）
      year: z.number(),                           // 发布年份
      version: z.string(),                        // 版本号
      sourceUrl: z.string().url().optional(),      // 原文链接（raw_materials 本地解析可缺省）
      reviewDate: z.string(),                     // 整理审核日期（ISO，如 2026-11-01）

      // —— 多维分类（均为多选标签）——

      // 1) 指南共识（Type）：指南 / 专家共识 / 推荐依据
      docType: z.array(z.string()).default([]),
      // 2) 致病菌与耐药菌（Pathogen / Resistance）
      //    真菌类 + 耐药菌类 + 混合感染
      pathogens: z.array(z.string()).default([]),
      // 3) 感染部位与临床场景（Infection Site / Scene）
      infectionSites: z.array(z.string()).default([]),
      // 4) 特殊人群与器官支持（Special Population）：CRRT / ECMO / ARDS
      specialPopulations: z.array(z.string()).default([]),
      // 5) 医学影像与诊断（Imaging & Diagnosis）：肺部 CT / 影像鉴别 / TDM
      imagingDiagnosis: z.array(z.string()).default([]),
      // 6) 疗效与安全性比较（Comparison Dimensions）
      comparisons: z.array(z.string()).default([]),

      // —— A2 新增字段（全部 optional / 带默认值，向后兼容）——
      guidelineVersion: z.string().optional(),            // 新规范版本（旧 version 保留）
      infectionSyndromes: z.array(z.string()).default([]), // 感染综合征（含 ARDS）
      clinicalScenarios: z.array(z.string()).default([]),  // 临床场景（含 CRRT/ECMO）
      preventionManagement: z.array(z.string()).default([]), // 感染预防与管理
      susceptibilityStandards: z.array(z.string()).default([]), // 药敏标准/耐药监测
      evidenceQuality: z.string().optional(),             // 证据质量（原文分级或「原文未评估」）
      recommendationGrade: z.string().optional(),         // 推荐等级（原文分级）

      // —— 兼容旧字段 ——
      syndromes: z.array(z.string()).default([]), // 适用综合征/临床问题
      antibioticClasses: z.array(z.string()).default([]), // 抗菌药物分类
      tags: z.array(z.string()).default([]),      // 标签
      description: z.string().default(''),        // 摘要
      cover: image().optional(),                  // 封面图（可选）
      draft: z.boolean().default(false),          // 草稿标记
    }),
});

// 药品说明书：Markdown 知识库（人工维护，受保护）
// 字段严格对齐 PRD 第 8.1 节【确定】要求
const drugLabels = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      drugName: z.string(),                        // 通用名
      brandNames: z.array(z.string()).default([]), // 商品名（可选多个）
      manufacturer: z.string(),                    // 生产企业
      dosageForm: z.string(),                      // 剂型（如：注射剂、片剂）
      strengths: z.array(z.string()).nonempty(),   // 规格（如：["500mg/支", "1g/支"]）
      atcCode: z.string().default(''),             // ATC 分类代码
      antibioticClass: z.string().default(''),     // 抗菌药物分类
      indications: z.array(z.string()).nonempty(), // 适应证
      contraindications: z.array(z.string()).default([]), // 禁忌
      specialPopulations: z.array(z.string()).default([]), // 特殊人群（妊娠/哺乳/儿童/老年）
      renalAdjustment: z.boolean().default(false), // 是否需肾功能调整
      hepaticAdjustment: z.boolean().default(false), // 是否需肝功能调整
      drugInteractions: z.array(z.string()).default([]), // 药物相互作用
      preparation: z.string().default(''),         // 给药配置说明（如溶媒、浓度、滴速）
      sourceUrl: z.string().url().optional(),      // 原文链接（NMPA 或制药商公开）
      reviewDate: z.string(),                      // 整理审核日期
      tags: z.array(z.string()).default([]),
      description: z.string().default(''),
      cover: image().optional(),
      draft: z.boolean().default(false),
    }),
});

export const collections = {
  guides,
  'drug-labels': drugLabels,
};
