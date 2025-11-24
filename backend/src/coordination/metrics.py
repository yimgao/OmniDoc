"""
Metrics and observability for parallel document generation.

Tracks execution times, parallelization efficiency, and dependency graphs.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime

from src.utils.logger import get_logger
from src.web.monitoring import increment_counter, record_timing

logger = get_logger(__name__)


class ParallelExecutionMetrics:
    """Tracks metrics for parallel document generation"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.start_time = time.time()
        self.document_times: Dict[str, Dict[str, float]] = {}
        self.wave_executions: List[Dict[str, Any]] = []
        self.total_documents = 0
        self.completed_documents = 0
        self.failed_documents = 0
        
    def record_document_start(self, document_id: str) -> None:
        """Record when a document starts generation"""
        self.document_times[document_id] = {
            "start": time.time(),
            "end": None,
            "duration": None
        }
    
    def record_document_complete(self, document_id: str, success: bool = True) -> None:
        """Record when a document completes generation"""
        if document_id in self.document_times:
            end_time = time.time()
            self.document_times[document_id]["end"] = end_time
            duration = end_time - self.document_times[document_id]["start"]
            self.document_times[document_id]["duration"] = duration
            
            if success:
                self.completed_documents += 1
                record_timing("coordination.document.generation_time", duration)
                increment_counter(f"coordination.document.completed.{document_id}")
            else:
                self.failed_documents += 1
                increment_counter(f"coordination.document.failed.{document_id}")
        else:
            logger.warning(f"Document {document_id} completed but never started (metrics)")
    
    def record_wave_execution(
        self,
        wave_number: int,
        documents: List[str],
        execution_time: float,
        parallel_efficiency: float
    ) -> None:
        """Record a wave of parallel execution"""
        self.wave_executions.append({
            "wave_number": wave_number,
            "documents": documents,
            "execution_time": execution_time,
            "parallel_efficiency": parallel_efficiency,
            "timestamp": datetime.now().isoformat()
        })
        
        record_timing("coordination.wave.execution_time", execution_time)
        increment_counter(f"coordination.wave.size.{len(documents)}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary metrics"""
        total_time = time.time() - self.start_time
        
        # Calculate parallelization efficiency
        # If all docs ran sequentially, what would the time be?
        sequential_time = sum(
            doc.get("duration", 0) for doc in self.document_times.values()
            if doc.get("duration") is not None
        )
        
        parallel_efficiency = (
            (sequential_time / total_time) * 100 if total_time > 0 else 0
        )
        
        # Calculate average wave size (number of documents per wave)
        avg_wave_size = (
            sum(len(w["documents"]) for w in self.wave_executions) / len(self.wave_executions)
            if self.wave_executions else 0
        )
        
        return {
            "project_id": self.project_id,
            "total_time": total_time,
            "sequential_time_estimate": sequential_time,
            "speedup": sequential_time / total_time if total_time > 0 else 1.0,
            "parallel_efficiency_percent": parallel_efficiency,
            "total_documents": self.total_documents,
            "completed_documents": self.completed_documents,
            "failed_documents": self.failed_documents,
            "waves_executed": len(self.wave_executions),
            "average_wave_size": avg_wave_size,
            "document_times": {
                doc_id: {
                    "duration": data.get("duration"),
                    "start_offset": data.get("start", 0) - self.start_time
                }
                for doc_id, data in self.document_times.items()
            }
        }
    
    def log_summary(self) -> None:
        """Log execution summary"""
        summary = self.get_summary()
        
        logger.info(
            f"📊 Parallel Execution Metrics [Project: {self.project_id}]:\n"
            f"  Total time: {summary['total_time']:.2f}s\n"
            f"  Sequential estimate: {summary['sequential_time_estimate']:.2f}s\n"
            f"  Speedup: {summary['speedup']:.2f}x\n"
            f"  Parallel efficiency: {summary['parallel_efficiency_percent']:.1f}%\n"
            f"  Completed: {summary['completed_documents']}/{summary['total_documents']}\n"
            f"  Waves executed: {summary['waves_executed']}"
        )
        
        # Log to monitoring system
        record_timing("coordination.workflow.total_time", summary["total_time"])
        increment_counter(f"coordination.workflow.completed.{self.project_id}")


# Global metrics storage (project_id -> metrics)
_metrics_store: Dict[str, ParallelExecutionMetrics] = {}


def get_metrics(project_id: str) -> ParallelExecutionMetrics:
    """Get or create metrics for a project"""
    if project_id not in _metrics_store:
        _metrics_store[project_id] = ParallelExecutionMetrics(project_id)
    return _metrics_store[project_id]


def clear_metrics(project_id: str) -> None:
    """Clear metrics for a project (after completion)"""
    if project_id in _metrics_store:
        del _metrics_store[project_id]

