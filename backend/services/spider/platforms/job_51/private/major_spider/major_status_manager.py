from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from backend.services.spider.platforms.job_51.public.base_json_store import BaseJsonStore


class MajorStatusManager(BaseJsonStore):
    """
    管理层级化爬虫状态 (学科 -> 二级学科 -> 专业 -> [岗位列表])。

    【重要使用规范】
    1. 本类设计为“短生命周期”对象。
    2. 建议在外部配合锁使用 (见 open_spider_state_store 上下文管理器)。
    3. 每次实例化都会重新加载磁盘数据，确保数据新鲜。
    """

    def __init__(self, file_path: Path, subject: str, secondary_subject: str, major: str):
        super().__init__(file_path)

        self.subject = subject
        self.secondary_subject = secondary_subject
        self.major = major

        # 【关键修复】确保路径存在，如果不存在则自动创建并挂载到 self.data
        self._current_major_data = self._ensure_node_exists(subject, secondary_subject, major)

    def _ensure_node_exists(self, s1: str, s2: str, s3: str) -> Dict[str, Any]:
        """
        确保三级路径存在。如果不存在，自动创建空结构并挂载。
        返回最终节点的引用 (直接指向 self.data 内部)。
        """
        # 1. 确保第一层
        if s1 not in self.data:
            self.data[s1] = {}

        # 2. 确保第二层
        if s2 not in self.data[s1]:
            self.data[s1][s2] = {}

        # 3. 确保第三层
        if s3 not in self.data[s1][s2]:
            self.data[s1][s2][s3] = {}

        node = self.data[s1][s2][s3]

        # 确保节点是字典 (防止被意外写成其他类型)
        if not isinstance(node, dict):
            raise TypeError(f"节点 {s1}/{s2}/{s3} 存在但不是字典类型")

        return node

    def _get_job_node(self, job_name: str, create_if_missing: bool = False) -> Optional[Dict[str, Any]]:
        """获取特定岗位的节点"""
        # if job_name not in self._current_major_data:
        #     if create_if_missing:
        #         self._current_major_data[job_name] = {
        #             "target_count": 0,
        #             "current_count": 0,
        #             "status": "pending"
        #         }
        #     else:
        #         return None
        return self._current_major_data[job_name]

    # --- 业务逻辑 ---

    def update_target_counts(self, updates: List[Tuple[str, int]]) -> int:
        """批量更新岗位的目标数量"""
        updated_count = 0
        for job_name, new_count in updates:
            job_info = self._get_job_node(job_name, create_if_missing=True)
            if job_info:
                job_info['target_count'] = new_count
                # 如果是新创建的，确保 status 和 current_count 初始化
                if 'status' not in job_info:
                    job_info['status'] = 'pending'
                if 'current_count' not in job_info:
                    job_info['current_count'] = 0
                updated_count += 1

        if updated_count > 0:
            self.save()
        return updated_count

    def get_next_pending_job(self) -> Optional[Tuple[str, int, int]]:
        """
        获取下一个待处理的岗位。
        返回: (job_name, target_count, current_count) 或 None
        """
        for job_name, job_info in self._current_major_data.items():
            if not isinstance(job_info, dict):
                continue

            # 跳过已完成的
            if job_info.get('status') == 'completed':
                continue

            target = job_info.get('target_count', 0)
            current = job_info.get('current_count', 0)

            # 只有目标大于0 且 当前未完成 才算 pending
            if target > 0 and current < target:
                return job_name, target, current

        return None

    def mark_job_as_completed(self, job_name: str) -> bool:
        job_info = self._get_job_node(job_name)
        if not job_info:
            return False

        job_info['status'] = 'completed'
        # 确保 current_count 至少等于 target_count (防御性)
        if job_info.get('current_count', 0) < job_info.get('target_count', 0):
            job_info['current_count'] = job_info.get('target_count', 0)

        self.save()
        return True

    def update_fetched_count(self, job_name: str, increment: int = 1) -> bool:
        """增加已抓取数量并立即保存"""
        try:
            job_info = self._get_job_node(job_name, create_if_missing=True)
            if not job_info:
                return False

            job_info['current_count'] = job_info.get('current_count', 0) + increment

            self.save()
            return True
        except Exception as e:
            print(f"❌ 更新计数失败 [{job_name}]: {e}")
            return False

    def get_all_job_names(self) -> List[str]:
        return list(self._current_major_data.keys())

    def are_all_jobs_completed(self) -> bool:
        """
        判断是否所有任务都已完成。
        逻辑：只要存在任何一个 status != 'completed' 的岗位，就返回 False。
        (不再特殊处理 target_count=0 的情况，0 目标的任务也必须显式标记为 completed 才算完成)
        """
        if not self._current_major_data:
            return True  # 【建议修改】空列表通常视为“没有任务需要完成”，即已完成。
            # 如果你希望空列表视为异常/未完成，可改回 False。

        for job_info in self._current_major_data.values():
            if not isinstance(job_info, dict):
                continue

            # 【核心修改】直接检查状态
            if job_info.get('status') != 'completed':
                return False

        return True

    def get_progress_summary(self) -> Dict[str, int]:
        """获取当前专业的进度摘要"""
        total_target = 0
        total_current = 0
        completed_count = 0

        for job_info in self._current_major_data.values():
            if not isinstance(job_info, dict):
                continue
            t = job_info.get('target_count', 0)
            c = job_info.get('current_count', 0)
            total_target += t
            total_current += c
            if job_info.get('status') == 'completed' or (t > 0 and c >= t):
                completed_count += 1

        return {
            "total_target": total_target,
            "total_current": total_current,
            "completed_jobs": completed_count,
            "total_jobs": len(self._current_major_data)
        }


import json
import os
import tempfile
from pathlib import Path
import sys

# 确保项目根目录在路径中，以便导入 backend 模块
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_FILE_PATH = _PROJECT_ROOT / 'data' / 'json' / '51job_major_data.json'

def test_with_sample_data():
    print("🚀 开始测试 MajorStatusManager (基于提供的经济统计学数据)...\n")

    test = MajorStatusManager(_FILE_PATH, "经济学", "经济学类", "经济统计学")

    print(test.get_all_job_names())
    print(test.are_all_jobs_completed())
    print(test.get_progress_summary())



if __name__ == "__main__":
    test_with_sample_data()