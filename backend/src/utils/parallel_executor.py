"""
Parallel Execution Utility
Manages parallel execution of independent agents with dependency tracking
"""
from typing import List, Dict, Callable, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a task to be executed"""
    task_id: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    dependencies: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.dependencies is None:
            self.dependencies = []


class ParallelExecutor:
    """
    Executes tasks in parallel while respecting dependencies
    
    Features:
    - Dependency tracking
    - Parallel execution of independent tasks
    - Progress tracking
    - Error handling and reporting
    - Thread-safe execution
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel executor
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
    
    def add_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        dependencies: List[str] = None
    ):
        """
        Add a task to be executed
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            dependencies: List of task IDs this task depends on
        """
        if kwargs is None:
            kwargs = {}
        if dependencies is None:
            dependencies = []
        
        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            dependencies=dependencies
        )
        self.tasks[task_id] = task
    
    def _can_run(self, task: Task) -> bool:
        """Check if a task can run (all dependencies are complete)"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETE:
                return False
        return True
    
    def _get_ready_tasks(self) -> List[Task]:
        """Get all tasks that are ready to run (dependencies met)"""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and self._can_run(task):
                ready.append(task)
        return ready
    
    def execute(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute all tasks respecting dependencies
        
        Args:
            progress_callback: Optional callback for progress updates
                Called with (completed_count, total_count, task_id)
        
        Returns:
            Dict mapping task IDs to results
        """
        results = {}
        total_tasks = len(self.tasks)
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            # Continue until all tasks are done
            while completed_count < total_tasks:
                # Get tasks ready to run
                ready_tasks = self._get_ready_tasks()
                
                # Submit ready tasks
                for task in ready_tasks:
                    if task.task_id not in futures:  # Don't resubmit
                        with self.lock:
                            task.status = TaskStatus.RUNNING
                        
                        future = executor.submit(self._execute_task, task)
                        futures[task.task_id] = (future, task)
                
                # Check for completed futures
                for task_id, (future, task) in list(futures.items()):
                    if future.done():
                        try:
                            result = future.result()
                            with self.lock:
                                task.status = TaskStatus.COMPLETE
                                task.result = result
                                results[task_id] = result
                                completed_count += 1
                            
                            if progress_callback:
                                progress_callback(completed_count, total_tasks, task_id)
                        
                        except Exception as e:
                            with self.lock:
                                task.status = TaskStatus.FAILED
                                task.error = e
                                results[task_id] = None
                                completed_count += 1
                            
                            if progress_callback:
                                progress_callback(completed_count, total_tasks, task_id)
                        
                        # Remove completed future
                        del futures[task_id]
                
                # If no tasks are running and none are ready, we're stuck
                if not ready_tasks and not futures:
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
                                with self.lock:
                                    task.status = TaskStatus.FAILED
                                    task.error = Exception(f"Dependencies failed: {failed_deps}")
                                    results[task.task_id] = None
                                    completed_count += 1
                    
                    # If still stuck, break
                    if completed_count < total_tasks and not remaining:
                        break
                
                # Small sleep to avoid busy-waiting
                import time
                time.sleep(0.1)
        
        return results
    
    def _execute_task(self, task: Task) -> Any:
        """Execute a single task"""
        try:
            return task.func(*task.args, **task.kwargs)
        except Exception as e:
            raise e
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    def get_results(self) -> Dict[str, Any]:
        """Get results from all completed tasks"""
        return {
            task_id: task.result
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETE
        }
    
    def get_failed_tasks(self) -> List[Tuple[str, Exception]]:
        """Get list of failed tasks with their errors"""
        return [
            (task_id, task.error)
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.FAILED
        ]

