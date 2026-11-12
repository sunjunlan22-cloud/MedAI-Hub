// 免责声明组件（供所有临床计算器共享）
import type { ReactNode } from 'react';

export default function Disclaimer() {
  return (
    <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
      <strong className="block text-amber-900">⚠ 安全声明</strong>
      <p className="mt-1 leading-relaxed">
        本工具完全在您的浏览器本地运行，不收集、不存储、不上传任何患者输入数据，可完全离线使用。
        计算结果仅供专业学术参考，<strong>不能替代临床决策</strong>。
        实际临床应用请结合患者具体情况，必要时参考药品说明书和权威指南，并严格执行 TDM 监测。
      </p>
    </div>
  );
}

// 通用结果卡片
export function ResultCard({ children }: { children: ReactNode }) {
  return (
    <div className="mt-6 rounded-xl border-2 border-blue-500 bg-blue-50 p-5">
      {children}
    </div>
  );
}
