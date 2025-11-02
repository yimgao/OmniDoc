"""
Unit Tests: ParallelExecutor
Fast, isolated tests for parallel execution
"""
import pytest
import time
from src.utils.parallel_executor import ParallelExecutor, TaskStatus


@pytest.mark.unit
class TestParallelExecutor:
    """Test ParallelExecutor class"""
    
    def test_add_task(self):
        """Test adding tasks"""
        executor = ParallelExecutor()
        
        def test_func(x):
            return x * 2
        
        executor.add_task("task1", test_func, args=(5,))
        
        assert "task1" in executor.tasks
        assert executor.tasks["task1"].status == TaskStatus.PENDING
    
    def test_simple_execution(self):
        """Test executing a simple task"""
        executor = ParallelExecutor()
        
        def add(x, y):
            return x + y
        
        executor.add_task("add", add, args=(2, 3))
        
        results = executor.execute()
        
        assert results["add"] == 5
        assert executor.tasks["add"].status == TaskStatus.COMPLETE
    
    def test_dependency_ordering(self):
        """Test tasks execute in dependency order"""
        executor = ParallelExecutor()
        execution_order = []
        
        def task1():
            execution_order.append(1)
            return 1
        
        def task2():
            execution_order.append(2)
            return 2
        
        def task3():
            execution_order.append(3)
            return 3
        
        executor.add_task("task1", task1)
        executor.add_task("task2", task2, dependencies=["task1"])
        executor.add_task("task3", task3, dependencies=["task2"])
        
        results = executor.execute()
        
        assert execution_order == [1, 2, 3]
        assert results["task1"] == 1
        assert results["task2"] == 2
        assert results["task3"] == 3
    
    def test_parallel_execution(self):
        """Test independent tasks run in parallel"""
        executor = ParallelExecutor(max_workers=2)
        start_times = {}
        end_times = {}
        
        def slow_task(task_id, duration):
            start_times[task_id] = time.time()
            time.sleep(duration)
            end_times[task_id] = time.time()
            return task_id
        
        executor.add_task("task1", slow_task, args=("task1", 0.2))
        executor.add_task("task2", slow_task, args=("task2", 0.2))
        executor.add_task("task3", slow_task, args=("task3", 0.2))
        
        start = time.time()
        results = executor.execute()
        total_time = time.time() - start
        
        # Should be faster than sequential (0.2 * 3 = 0.6s)
        # But slower than single task (0.2s) due to overhead
        assert total_time < 0.7  # Should run in parallel (allows some overhead)
        assert len(results) == 3
    
    def test_error_handling(self):
        """Test error handling in tasks"""
        executor = ParallelExecutor()
        
        def failing_task():
            raise ValueError("Task failed")
        
        executor.add_task("fail", failing_task)
        
        results = executor.execute()
        
        assert results["fail"] is None
        assert executor.tasks["fail"].status == TaskStatus.FAILED
        assert executor.tasks["fail"].error is not None
    
    def test_dependent_task_fails(self):
        """Test that dependent tasks fail if dependency fails"""
        executor = ParallelExecutor()
        
        def failing_task():
            raise ValueError("Failed")
        
        def dependent_task():
            return "should not run"
        
        executor.add_task("fail", failing_task)
        executor.add_task("dependent", dependent_task, dependencies=["fail"])
        
        results = executor.execute()
        
        assert executor.tasks["dependent"].status == TaskStatus.FAILED
        assert "dependent" not in results or results["dependent"] is None
    
    def test_progress_callback(self):
        """Test progress callback functionality"""
        executor = ParallelExecutor()
        progress_updates = []
        
        def progress_callback(completed, total, task_id):
            progress_updates.append((completed, total, task_id))
        
        def task1():
            return 1
        
        def task2():
            return 2
        
        executor.add_task("task1", task1)
        executor.add_task("task2", task2)
        
        executor.execute(progress_callback=progress_callback)
        
        assert len(progress_updates) == 2
        assert progress_updates[0][0] == 1
        assert progress_updates[1][0] == 2
    
    def test_get_results(self):
        """Test getting results"""
        executor = ParallelExecutor()
        
        executor.add_task("task1", lambda: 1)
        executor.add_task("task2", lambda: 2)
        
        executor.execute()
        
        results = executor.get_results()
        
        assert "task1" in results
        assert "task2" in results
        assert results["task1"] == 1
        assert results["task2"] == 2
    
    def test_get_failed_tasks(self):
        """Test getting failed tasks"""
        executor = ParallelExecutor()
        
        def fail():
            raise ValueError("Error")
        
        executor.add_task("fail", fail)
        
        executor.execute()
        
        failed = executor.get_failed_tasks()
        
        assert len(failed) == 1
        assert failed[0][0] == "fail"
        assert isinstance(failed[0][1], ValueError)

