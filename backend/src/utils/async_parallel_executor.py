"""
Async Parallel Executor
Executes async tasks in parallel while respecting dependencies using asyncio
"""
import asyncio
from typing import Dict, List, Optional, Callable, Any, Coroutine
from enum import Enum
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class AsyncTask:
    """Represents an async task to be executed"""
    task_id: str
    coro: Coroutine  # Async function/coroutine
    dependencies: List[str]  # List of task IDs this task depends on
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None


class AsyncParallelExecutor:
    """
    Executes async tasks in parallel while respecting dependencies
    
    Features:
    - Dependency tracking
    - Parallel execution of independent tasks using asyncio.gather
    - Progress tracking
    - Error handling and reporting
    - Async-safe execution
    """
    
    def __init__(self, max_workers: int = 8):
        """
        Initialize async parallel executor
        
        Args:
            max_workers: Maximum number of concurrent tasks (for semaphore control)
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, AsyncTask] = {}
        self.semaphore = asyncio.Semaphore(max_workers)
    
    def add_task(
        self,
        task_id: str,
        coro: Coroutine,
        dependencies: List[str] = None
    ):
        """
        Add an async task to be executed
        
        Args:
            task_id: Unique identifier for the task
            coro: Coroutine to execute
            dependencies: List of task IDs this task depends on
        """
        if dependencies is None:
            dependencies = []
        
        task = AsyncTask(
            task_id=task_id,
            coro=coro,
            dependencies=dependencies
        )
        self.tasks[task_id] = task
    
    def _can_run(self, task: AsyncTask) -> bool:
        """Check if a task can run (all dependencies are complete)"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETE:
                return False
        return True
    
    def _get_ready_tasks(self) -> List[AsyncTask]:
        """Get all tasks that are ready to run (dependencies met)"""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and self._can_run(task):
                ready.append(task)
        return ready
    
    async def _execute_task(self, task: AsyncTask) -> Any:
        """Execute a single async task with semaphore control"""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            try:
                result = await task.coro
                task.status = TaskStatus.COMPLETE
                task.result = result
                return result
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = e
                logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
                raise
    
    async def execute(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute all tasks respecting dependencies (async)
        
        Args:
            progress_callback: Optional async callback for progress updates
                Called with (completed_count, total_count, task_id)
        
        Returns:
            Dict mapping task IDs to results
        """
        results = {}
        total_tasks = len(self.tasks)
        completed_count = 0
        
        # Continue until all tasks are done
        while completed_count < total_tasks:
            # Get tasks ready to run
            ready_tasks = self._get_ready_tasks()
            
            if not ready_tasks:
                # Check for remaining tasks
                remaining = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
                if remaining:
                    # Some tasks might be blocked by failed dependencies
                    for task in remaining:
                        failed_deps = [
                            dep_id for dep_id in task.dependencies
                            if self.tasks[dep_id].status == TaskStatus.FAILED
                        ]
                        if failed_deps:
                            task.status = TaskStatus.FAILED
                            task.error = Exception(f"Dependencies failed: {failed_deps}")
                            results[task.task_id] = None
                            completed_count += 1
                            
                            if progress_callback:
                                await progress_callback(completed_count, total_tasks, task.task_id)
                    
                    # If still stuck, break
                    if completed_count < total_tasks and not remaining:
                        break
                else:
                    break
            
            # Execute ready tasks in parallel
            if ready_tasks:
                task_coros = [self._execute_task(task) for task in ready_tasks]
                
                # Use asyncio.gather to run tasks in parallel
                # Return exceptions instead of raising them
                task_results = await asyncio.gather(*task_coros, return_exceptions=True)
                
                # Process results
                for task, result in zip(ready_tasks, task_results):
                    if isinstance(result, Exception):
                        # Task failed
                        task.status = TaskStatus.FAILED
                        task.error = result
                        results[task.task_id] = None
                    else:
                        # Task succeeded
                        results[task.task_id] = result
                    
                    completed_count += 1
                    
                    if progress_callback:
                        await progress_callback(completed_count, total_tasks, task.task_id)
        
        return results

