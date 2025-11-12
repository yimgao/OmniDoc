#!/usr/bin/env python3
"""
快速测试 Phase 1
"""
import asyncio
from src.coordination.coordinator import WorkflowCoordinator

async def main():
    print("🚀 开始测试 Phase 1...")
    print()
    
    coordinator = WorkflowCoordinator()
    
    results = await coordinator.async_generate_all_docs(
        user_idea="创建一个任务管理应用",
        project_id="test_phase1_only",
        profile="team",
        phase1_only=True  # 只运行 Phase 1
    )
    
    print()
    print("=" * 80)
    print("✅ Phase 1 完成！")
    print("=" * 80)
    print()
    print("📄 生成的文档:")
    for doc_type, file_path in results.get('files', {}).items():
        status = results.get('status', {}).get(doc_type, 'unknown')
        print(f"  ✅ {doc_type}: {status}")

if __name__ == "__main__":
    asyncio.run(main())
