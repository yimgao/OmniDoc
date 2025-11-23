"""
Context Manager
Manages shared context database for agent collaboration
"""
import os
import json
import threading
# Path removed - content is stored in database, not files
from typing import Optional, Dict, List
from datetime import datetime
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from src.context.shared_context import (
    SharedContext,
    RequirementsDocument,
    AgentOutput,
    CrossReference,
    AgentType,
    DocumentStatus
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContextManager:
    """Manages shared context in PostgreSQL database"""
    
    def __init__(self, db_url: Optional[str] = None, min_conn: int = 1, max_conn: int = 10):
        """
        Initialize context manager with connection pooling
        
        Args:
            db_url: PostgreSQL connection URL (e.g., postgresql://user:password@localhost/dbname)
                   If None, reads from DATABASE_URL environment variable
            min_conn: Minimum number of connections in pool
            max_conn: Maximum number of connections in pool
        """
        if db_url is None:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError(
                    "DATABASE_URL environment variable is not set. "
                    "Please set it in Railway Variables or your .env file."
                )
        
        self.db_url = db_url
        self._lock = threading.Lock()
        self._min_conn = min_conn
        self._max_conn = max_conn
        
        # Connection statistics for monitoring
        self._connection_stats = {
            "total_created": 0,
            "total_closed": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "pool_gets": 0,
            "pool_puts": 0,
            "last_warning_time": None,
        }
        
        # Parse connection URL for pool
        try:
            # Create connection pool
            self._connection_pool: Optional[pool.ThreadedConnectionPool] = pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                db_url
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create connection pool: {e}")
            # Fallback to single connection
            self._connection_pool = None
        
        self._initialize_database()
    
    def _get_connection(self):
        """Get a database connection from pool with health check and monitoring"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self._connection_pool is None:
                    # Fallback to direct connection if pool failed
                    conn = psycopg2.connect(self.db_url)
                    self._connection_stats["total_created"] += 1
                    self._connection_stats["active_connections"] += 1
                else:
                    conn = self._connection_pool.getconn()
                    self._connection_stats["pool_gets"] += 1
                    self._connection_stats["active_connections"] += 1
                
                # Health check: verify connection is still alive
                if conn.closed:
                    logger.warning(f"Connection from pool is closed, getting new connection (attempt {attempt + 1}/{max_retries})")
                    # Decrement counter for the bad connection we already counted
                    # (we incremented it when we first got it above)
                    self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
                    
                    if self._connection_pool is not None:
                        try:
                            self._connection_pool.putconn(conn, close=True)
                        except Exception:
                            pass
                        # Get replacement connection from pool
                        conn = self._connection_pool.getconn()
                        # Increment statistics for the new connection from pool
                        self._connection_stats["pool_gets"] += 1
                        self._connection_stats["active_connections"] += 1
                    else:
                        # Direct connection mode
                        conn = psycopg2.connect(self.db_url)
                        self._connection_stats["total_created"] += 1
                        self._connection_stats["active_connections"] += 1
                
                # Test connection with a simple query
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                
                # Check for connection pool capacity warnings
                self._check_connection_pool_health()
                
                return conn
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                self._connection_stats["failed_connections"] += 1
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying..."
                    )
                    import time
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Failed to get database connection after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                self._connection_stats["failed_connections"] += 1
                logger.error(f"Unexpected error getting database connection: {e}")
                raise
    
    def _check_connection_pool_health(self):
        """Check connection pool health and log warnings if needed"""
        import time
        current_time = time.time()
        
        # Only warn once per minute to avoid log spam
        last_warning = self._connection_stats.get("last_warning_time")
        if last_warning and (current_time - last_warning) < 60:
            return
        
        active = self._connection_stats["active_connections"]
        capacity_threshold = self._max_conn * 0.9  # 90% of max capacity
        
        if active >= capacity_threshold:
            logger.warning(
                "⚠️ Connection pool near capacity: %d/%d active connections (%.1f%%)",
                active,
                self._max_conn,
                (active / self._max_conn) * 100
            )
            self._connection_stats["last_warning_time"] = current_time
            
            # Check for potential connection leaks
            if active >= self._max_conn:
                logger.error(
                    "❌ Connection pool at maximum capacity! Possible connection leak detected. "
                    "Stats: created=%d, closed=%d, active=%d, failed=%d",
                    self._connection_stats["total_created"],
                    self._connection_stats["total_closed"],
                    active,
                    self._connection_stats["failed_connections"]
                )
    
    def _put_connection(self, conn):
        """Return a connection to the pool with health check and monitoring"""
        if conn is None:
            return
        
        # Check if connection is still valid before returning to pool
        if conn.closed:
            logger.debug("Connection is closed, not returning to pool")
            self._connection_stats["total_closed"] += 1
            self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
            return
        
        if self._connection_pool is not None:
            try:
                # Test connection before returning to pool
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self._connection_pool.putconn(conn)
                self._connection_stats["pool_puts"] += 1
                self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                # Connection is bad, close it instead of returning to pool
                logger.warning(f"Connection is invalid, closing instead of returning to pool: {e}")
                try:
                    conn.close()
                    self._connection_stats["total_closed"] += 1
                    self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
                except Exception:
                    pass
            except Exception as e:
                # Other errors - try to return to pool, but close if that fails
                try:
                    self._connection_pool.putconn(conn)
                    self._connection_stats["pool_puts"] += 1
                    self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
                except Exception:
                    try:
                        conn.close()
                        self._connection_stats["total_closed"] += 1
                        self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
                    except Exception:
                        pass
        else:
            # Direct connection mode - just close it
            try:
                conn.close()
                self._connection_stats["total_closed"] += 1
                self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)
            except Exception:
                pass
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics for monitoring.
        
        Returns:
            Dictionary with connection statistics including health status
        """
        stats = {
            **self._connection_stats,
            "max_connections": self._max_conn,
            "min_connections": self._min_conn,
            "pool_utilization_percent": (
                (self._connection_stats["active_connections"] / self._max_conn) * 100
                if self._max_conn > 0 else 0
            ),
        }
        
        # Add health status
        utilization = stats["pool_utilization_percent"]
        if utilization < 70:
            stats["health_status"] = "healthy"
        elif utilization < 90:
            stats["health_status"] = "warning"
        else:
            stats["health_status"] = "critical"
        
        # Add pool status
        stats["pool_initialized"] = self._connection_pool is not None
        stats["failed_rate"] = (
            (stats["failed_connections"] / max(stats["total_created"], 1)) * 100
        ) if stats["total_created"] > 0 else 0
        
        return stats
    
    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor with connection retry"""
        conn = None
        cursor = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                yield cursor
                conn.commit()
                break  # Success, exit retry loop
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                error_str = str(e).lower()
                is_connection_error = any(keyword in error_str for keyword in [
                    "connection", "closed", "ssl", "network", "timeout", "broken"
                ])
                
                if conn:
                    try:
                        if not conn.closed:
                            conn.rollback()
                    except Exception:
                        pass
                    try:
                        # Close bad connection
                        if not conn.closed:
                            conn.close()
                    except Exception:
                        pass
                
                if is_connection_error and attempt < max_retries - 1:
                    logger.warning(
                        f"Database connection error (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying with new connection..."
                    )
                    import time
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    conn = None
                    cursor = None
                    continue
                else:
                    logger.error(f"Database error after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                if conn:
                    try:
                        if not conn.closed:
                            conn.rollback()
                    except Exception:
                        pass
                logger.error(f"Unexpected error in database operation: {e}")
                raise
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                if conn:
                    try:
                        # Only return to pool if connection is still valid
                        if not conn.closed:
                            self._put_connection(conn)
                        else:
                            # Connection is closed, don't return to pool
                            logger.debug("Connection was closed, not returning to pool")
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
                        try:
                            conn.close()
                        except Exception:
                            pass
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id VARCHAR(255) PRIMARY KEY,
                    user_idea TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # Requirements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    project_id VARCHAR(255) PRIMARY KEY,
                    user_idea TEXT NOT NULL,
                    project_overview TEXT,
                    core_features TEXT,  -- JSON array
                    technical_requirements TEXT,  -- JSON object
                    user_personas TEXT,  -- JSON array
                    business_objectives TEXT,  -- JSON array
                    constraints TEXT,  -- JSON array
                    assumptions TEXT,  -- JSON array
                    generated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                )
            """)
            
            # Agent outputs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_outputs (
                    output_id VARCHAR(255) PRIMARY KEY,
                    project_id VARCHAR(255) NOT NULL,
                    agent_type VARCHAR(100) NOT NULL,
                    document_type VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,  -- Optional virtual path (for reference only, not used for file storage)
                    quality_score REAL,
                    status VARCHAR(50) NOT NULL,
                    dependencies TEXT,  -- JSON array
                    generated_at TIMESTAMP,
                    version INTEGER DEFAULT 1,  -- Document version (1, 2, 3, etc.)
                    approved INTEGER DEFAULT 0,  -- 0 = pending, 1 = approved, 2 = rejected
                    approved_at TIMESTAMP,  -- Timestamp when approved
                    approval_notes TEXT,  -- User notes during approval
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                )
            """)
            
            # Migrate existing table: make file_path nullable if it's not already
            try:
                cursor.execute("""
                    ALTER TABLE agent_outputs 
                    ALTER COLUMN file_path DROP NOT NULL
                """)
            except Exception:
                # Column might already be nullable or migration not needed
                pass
            
            # Cross-references table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_references (
                    ref_id VARCHAR(255) PRIMARY KEY,
                    project_id VARCHAR(255) NOT NULL,
                    from_document VARCHAR(255) NOT NULL,
                    to_document VARCHAR(255) NOT NULL,
                    reference_type VARCHAR(100) NOT NULL,
                    description TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                )
            """)
            
            # Project status table for workflow state management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_status (
                    project_id VARCHAR(255) PRIMARY KEY,
                    status VARCHAR(50) NOT NULL,
                    user_idea TEXT NOT NULL,
                    profile VARCHAR(50),
                    provider_name VARCHAR(100),
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    failed_at TIMESTAMP,
                    error TEXT,
                    completed_agents TEXT,  -- JSON array
                    results TEXT,  -- JSON object (serialized results)
                    phase1_approved INTEGER DEFAULT 0,  -- 0 = pending, 1 = approved, 2 = rejected
                    phase1_approved_at TIMESTAMP,  -- Timestamp when Phase 1 was approved
                    phase1_approval_notes TEXT,  -- User notes/comments during approval
                    selected_documents TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                )
            """)
            
            # Check if selected_documents column exists (PostgreSQL way)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='project_status' AND column_name='selected_documents'
            """)
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE project_status ADD COLUMN selected_documents TEXT")
            
            conn.commit()
            cursor.close()
        finally:
            self._put_connection(conn)
    
    def create_project(self, project_id: str, user_idea: str) -> str:
        """
        Create a new project context
        
        Args:
            project_id: Unique project identifier
            user_idea: Original user idea
            
        Returns:
            project_id
        """
        now = datetime.now()
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO projects (project_id, user_idea, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (project_id) DO UPDATE SET
                    user_idea = EXCLUDED.user_idea,
                    updated_at = EXCLUDED.updated_at
            """, (project_id, user_idea, now, now))
        return project_id
    
    def save_requirements(self, project_id: str, requirements: RequirementsDocument):
        """Save requirements document (thread-safe)"""
        with self._lock:
            try:
                with self._get_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO requirements (
                            project_id, user_idea, project_overview, core_features,
                            technical_requirements, user_personas, business_objectives,
                            constraints, assumptions, generated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project_id) DO UPDATE SET
                            user_idea = EXCLUDED.user_idea,
                            project_overview = EXCLUDED.project_overview,
                            core_features = EXCLUDED.core_features,
                            technical_requirements = EXCLUDED.technical_requirements,
                            user_personas = EXCLUDED.user_personas,
                            business_objectives = EXCLUDED.business_objectives,
                            constraints = EXCLUDED.constraints,
                            assumptions = EXCLUDED.assumptions,
                            generated_at = EXCLUDED.generated_at
                    """, (
                        project_id,
                        requirements.user_idea,
                        requirements.project_overview,
                        json.dumps(requirements.core_features),
                        json.dumps(requirements.technical_requirements),
                        json.dumps(requirements.user_personas),
                        json.dumps(requirements.business_objectives),
                        json.dumps(requirements.constraints),
                        json.dumps(requirements.assumptions),
                        requirements.generated_at
                    ))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving requirements for {project_id}: {e}", exc_info=True)
                raise
    
    def get_requirements(self, project_id: str) -> Optional[RequirementsDocument]:
        """Get requirements for a project"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM requirements WHERE project_id = %s", (project_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                return None
            
            generated_at = row["generated_at"]
            if isinstance(generated_at, str):
                generated_at = datetime.fromisoformat(generated_at)
            
            return RequirementsDocument(
                user_idea=row["user_idea"],
                project_overview=row["project_overview"] or "",
                core_features=json.loads(row["core_features"] or "[]"),
                technical_requirements=json.loads(row["technical_requirements"] or "{}"),
                user_personas=json.loads(row["user_personas"] or "[]"),
                business_objectives=json.loads(row["business_objectives"] or "[]"),
                constraints=json.loads(row["constraints"] or "[]"),
                assumptions=json.loads(row["assumptions"] or "[]"),
                generated_at=generated_at
            )
        finally:
            self._put_connection(conn)
    
    def save_agent_output(self, project_id: str, output: AgentOutput, version: Optional[int] = None):
        """
        Save agent output (thread-safe)
        
        Args:
            project_id: Project identifier
            output: AgentOutput to save
            version: Optional version number (auto-incremented if None)
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get next version number if not provided
                # Use document_type to get version (more reliable for custom document types)
                if version is None:
                    # Try to get version by document_type first (more specific)
                    try:
                        cursor.execute("""
                            SELECT MAX(version) FROM agent_outputs 
                            WHERE project_id = %s AND document_type = %s
                        """, (project_id, output.document_type))
                        result = cursor.fetchone()
                        current_version = result[0] if result[0] is not None else 0
                        version = current_version + 1
                    except Exception as e:
                        # Fallback to agent_type if document_type query fails
                        try:
                            current_version = self.get_document_version(project_id, output.agent_type)
                            version = current_version + 1
                        except:
                            version = 1  # Start with version 1 if all else fails
                
                # Use document_type as part of output_id to ensure uniqueness for custom document types
                # This allows documents not in AgentType enum to be saved correctly
                output_id = f"{project_id}_{output.document_type}_v{version}"  # Use document_type for uniqueness
                
                # Ensure dependencies is a list (handle None or other types)
                dependencies = output.dependencies
                if dependencies is None:
                    dependencies = []
                elif not isinstance(dependencies, list):
                    # Try to convert to list if possible
                    dependencies = list(dependencies) if hasattr(dependencies, '__iter__') else []
                
                # Ensure all values are properly formatted
                generated_at = output.generated_at
                if generated_at and isinstance(generated_at, str):
                    generated_at = datetime.fromisoformat(generated_at)
                
                # Use INSERT ... ON CONFLICT for upsert
                # file_path is optional - can be None if storing only in database
                file_path = output.file_path if output.file_path else None
                cursor.execute("""
                    INSERT INTO agent_outputs (
                        output_id, project_id, agent_type, document_type,
                        content, file_path, quality_score, status,
                        dependencies, generated_at, version, approved
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (output_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        file_path = EXCLUDED.file_path,
                        quality_score = EXCLUDED.quality_score,
                        status = EXCLUDED.status,
                        dependencies = EXCLUDED.dependencies,
                        generated_at = EXCLUDED.generated_at,
                        approved = EXCLUDED.approved
                """, (
                    output_id,
                    project_id,
                    output.agent_type.value,
                    output.document_type,
                    output.content,
                    file_path,
                    output.quality_score,
                    output.status.value,
                    json.dumps(dependencies),
                    generated_at,
                    version,
                    0  # Default: pending approval
                ))
                
                conn.commit()
                cursor.close()
            except Exception as e:
                # Log error and re-raise
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving agent output for {project_id}/{output.document_type}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def get_agent_output(self, project_id: str, agent_type: AgentType) -> Optional[AgentOutput]:
        """Get agent output for a project (latest version)"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get the latest version of the document
                cursor.execute("""
                    SELECT * FROM agent_outputs 
                    WHERE project_id = %s AND agent_type = %s
                    ORDER BY version DESC LIMIT 1
                """, (project_id, agent_type.value))
                row = cursor.fetchone()
                cursor.close()
                
                if not row:
                    return None
                
                generated_at = row["generated_at"]
                if generated_at and isinstance(generated_at, str):
                    generated_at = datetime.fromisoformat(generated_at)
                
                return AgentOutput(
                    agent_type=AgentType(row["agent_type"]),
                    document_type=row["document_type"],
                    content=row["content"],
                    file_path=row["file_path"],
                    quality_score=row["quality_score"],
                    status=DocumentStatus(row["status"]),
                    generated_at=generated_at,
                    dependencies=json.loads(row["dependencies"] or "[]")
                )
            finally:
                self._put_connection(conn)
    
    def get_document_content_by_type(self, project_id: str, document_type: str) -> Optional[str]:
        """Get document content by raw document type string (latest version)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT content FROM agent_outputs 
                WHERE project_id = %s AND document_type = %s
                ORDER BY version DESC LIMIT 1
            """, (project_id, document_type))
            row = cursor.fetchone()
            cursor.close()
            if row:
                return row["content"]
            return None
        finally:
            self._put_connection(conn)

    def get_all_agent_outputs(self, project_id: str) -> Dict[AgentType, AgentOutput]:
        """Get all agent outputs for a project"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM agent_outputs 
                WHERE project_id = %s AND status = %s
            """, (project_id, DocumentStatus.COMPLETE.value))
            
            outputs = {}
            for row in cursor.fetchall():
                agent_type = AgentType(row["agent_type"])
                generated_at = row["generated_at"]
                if generated_at and isinstance(generated_at, str):
                    generated_at = datetime.fromisoformat(generated_at)
                
                outputs[agent_type] = AgentOutput(
                    agent_type=agent_type,
                    document_type=row["document_type"],
                    content=row["content"],
                    file_path=row["file_path"],
                    quality_score=row["quality_score"],
                    status=DocumentStatus(row["status"]),
                    generated_at=generated_at,
                    dependencies=json.loads(row["dependencies"] or "[]")
                )
            
            cursor.close()
            return outputs
        finally:
            self._put_connection(conn)
    
    def save_cross_reference(self, project_id: str, ref: CrossReference):
        """Save cross-reference (thread-safe)"""
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                ref_id = f"{project_id}_{ref.from_document}_{ref.to_document}"
                
                cursor.execute("""
                    INSERT INTO cross_references (
                        ref_id, project_id, from_document, to_document,
                        reference_type, description
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ref_id) DO UPDATE SET
                        project_id = EXCLUDED.project_id,
                        from_document = EXCLUDED.from_document,
                        to_document = EXCLUDED.to_document,
                        reference_type = EXCLUDED.reference_type,
                        description = EXCLUDED.description
                """, (
                    ref_id,
                    project_id,
                    ref.from_document,
                    ref.to_document,
                    ref.reference_type,
                    ref.description
                ))
                
                conn.commit()
                cursor.close()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving cross-reference for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def get_shared_context(self, project_id: str) -> SharedContext:
        """Get complete shared context for a project"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get project
            cursor.execute("SELECT * FROM projects WHERE project_id = %s", (project_id,))
            project_row = cursor.fetchone()
            
            if not project_row:
                cursor.close()
                raise ValueError(f"Project {project_id} not found")
            
            # Get requirements
            requirements = self.get_requirements(project_id)
            
            # Get all agent outputs
            agent_outputs = self.get_all_agent_outputs(project_id)
            
            # Get workflow status
            cursor.execute("""
                SELECT agent_type, status FROM agent_outputs WHERE project_id = %s
            """, (project_id,))
            
            workflow_status = {
                AgentType(row["agent_type"]): DocumentStatus(row["status"])
                for row in cursor.fetchall()
            }
            
            # Get cross-references
            cursor.execute("SELECT * FROM cross_references WHERE project_id = %s", (project_id,))
            cross_references = [
                CrossReference(
                    from_document=row["from_document"],
                    to_document=row["to_document"],
                    reference_type=row["reference_type"],
                    description=row["description"]
                )
                for row in cursor.fetchall()
            ]
            
            created_at = project_row["created_at"]
            updated_at = project_row["updated_at"]
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            
            cursor.close()
            return SharedContext(
                project_id=project_id,
                user_idea=project_row["user_idea"],
                requirements=requirements,
                agent_outputs=agent_outputs,
                cross_references=cross_references,
                workflow_status=workflow_status,
                created_at=created_at,
                updated_at=updated_at
            )
        finally:
            self._put_connection(conn)
    
    def update_project_status(
        self,
        project_id: str,
        status: str,
        user_idea: Optional[str] = None,
        profile: Optional[str] = None,
        provider_name: Optional[str] = None,
        completed_agents: Optional[List[str]] = None,
        results: Optional[Dict] = None,
        error: Optional[str] = None,
        selected_documents: Optional[List[str]] = None,
    ):
        """
        Update project workflow status in database (thread-safe)
        
        Args:
            project_id: Project identifier
            status: Workflow status ("in_progress", "complete", "failed")
            user_idea: User idea (required for initial status creation)
            profile: Project profile ("team" or "individual")
            provider_name: LLM provider name
            completed_agents: List of completed agent names
            results: Generation results dictionary
            error: Error message (if status is "failed")
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now()
                
                # Check if status record exists and get existing values to preserve
                cursor.execute("""
                    SELECT status, started_at, profile, provider_name 
                    FROM project_status 
                    WHERE project_id = %s
                """, (project_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Preserve existing profile and provider_name if not explicitly provided
                    existing_profile = existing[2] if len(existing) > 2 else None
                    existing_provider_name = existing[3] if len(existing) > 3 else None
                    
                    # Use existing values if new values are not explicitly provided (None means preserve)
                    # Store the original values to check if they were passed
                    profile_provided = profile is not None
                    provider_name_provided = provider_name is not None
                    
                    # If not provided, use existing values (even if None)
                    if not profile_provided:
                        profile = existing_profile
                    if not provider_name_provided:
                        provider_name = existing_provider_name
                    # Update existing status
                    update_fields = ["status = %s"]
                    update_values = [status]
                    
                    # Always preserve profile and provider_name if they were set
                    # Only update if explicitly provided, otherwise preserve existing values
                    if profile is not None:
                        update_fields.append("profile = %s")
                        update_values.append(profile)
                    
                    if provider_name is not None:
                        update_fields.append("provider_name = %s")
                        update_values.append(provider_name)
                    
                    if user_idea is not None:
                        update_fields.append("user_idea = %s")
                        update_values.append(user_idea)
                    
                    if completed_agents is not None:
                        update_fields.append("completed_agents = %s")
                        update_values.append(json.dumps(completed_agents) if completed_agents else "[]")
                    
                    if results is not None:
                        update_fields.append("results = %s")
                        update_values.append(json.dumps(results) if results else "{}")
                    
                    if error is not None:
                        update_fields.append("error = %s")
                        update_fields.append("failed_at = %s")
                        update_values.append(error)
                        update_values.append(now)
                    elif status == "complete":
                        update_fields.append("completed_at = %s")
                        update_values.append(now)
                    
                    if selected_documents is not None:
                        update_fields.append("selected_documents = %s")
                        update_values.append(json.dumps(selected_documents))

                    update_values.append(project_id)
                    cursor.execute(f"""
                        UPDATE project_status 
                        SET {', '.join(update_fields)}
                        WHERE project_id = %s
                    """, update_values)
                    
                    # Also update projects table updated_at
                    cursor.execute("""
                        UPDATE projects 
                        SET updated_at = %s
                        WHERE project_id = %s
                    """, (now, project_id))
                else:
                    # Create new status record
                    if not user_idea:
                        raise ValueError("user_idea is required when creating new project status")
                    
                    cursor.execute("""
                        INSERT INTO project_status (
                            project_id, status, user_idea, profile, provider_name,
                            started_at, completed_agents, results, error, phase1_approved, selected_documents
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        project_id,
                        status,
                        user_idea,
                        profile,
                        provider_name or "default",
                        now,
                        json.dumps(completed_agents or []),
                        json.dumps(results or {}),
                        error,
                        0,  # Default: pending approval
                        json.dumps(selected_documents or []),
                    ))
                
                conn.commit()
                cursor.close()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating project status for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def _safe_get_row_value(self, row, key: str, default):
        """Safely get a value from dict-like row, returning default if key doesn't exist"""
        try:
            return row[key]
        except (KeyError, IndexError):
            return default
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """
        Get project workflow status from database
        
        Args:
            project_id: Project identifier
            
        Returns:
            Status dictionary or None if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM project_status WHERE project_id = %s", (project_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                return None
            
            return {
                "project_id": row["project_id"],
                "status": row["status"],
                "user_idea": row["user_idea"],
                "profile": row["profile"],
                "provider_name": row["provider_name"],
                "started_at": row["started_at"].isoformat() if isinstance(row["started_at"], datetime) else row["started_at"],
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] and isinstance(row["completed_at"], datetime) else row["completed_at"],
                "failed_at": row["failed_at"].isoformat() if row["failed_at"] and isinstance(row["failed_at"], datetime) else row["failed_at"],
                "error": row["error"],
                "completed_agents": json.loads(row["completed_agents"] or "[]"),
                "results": json.loads(row["results"] or "{}") if row["results"] else {},
                "selected_documents": json.loads(row["selected_documents"] or "[]")
                if "selected_documents" in row.keys()
                else [],
                # Handle optional columns that may not exist in older database schemas
                "phase1_approved": self._safe_get_row_value(row, "phase1_approved", 0),  # 0 = pending, 1 = approved, 2 = rejected
                "phase1_approved_at": self._safe_get_row_value(row, "phase1_approved_at", None),
                "phase1_approval_notes": self._safe_get_row_value(row, "phase1_approval_notes", None)
            }
        finally:
            self._put_connection(conn)
    
    def approve_phase1(self, project_id: str, notes: Optional[str] = None) -> bool:
        """
        Approve Phase 1 documents to proceed to Phase 2+
        
        Args:
            project_id: Project identifier
            notes: Optional approval notes/comments
            
        Returns:
            True if approval was successful
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now()
                
                cursor.execute("""
                    UPDATE project_status 
                    SET phase1_approved = %s, phase1_approved_at = %s, phase1_approval_notes = %s
                    WHERE project_id = %s
                """, (1, now, notes, project_id))
                
                conn.commit()
                cursor.close()
                return True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error approving Phase 1 for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def reject_phase1(self, project_id: str, notes: Optional[str] = None) -> bool:
        """
        Reject Phase 1 documents (workflow stops)
        
        Args:
            project_id: Project identifier
            notes: Optional rejection notes/comments
            
        Returns:
            True if rejection was successful
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now()
                
                cursor.execute("""
                    UPDATE project_status 
                    SET phase1_approved = %s, phase1_approved_at = %s, phase1_approval_notes = %s, status = %s
                    WHERE project_id = %s
                """, (2, now, notes, "phase1_rejected", project_id))
                
                conn.commit()
                cursor.close()
                return True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error rejecting Phase 1 for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def is_phase1_approved(self, project_id: str) -> Optional[bool]:
        """
        Check if Phase 1 is approved
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if approved, False if rejected, None if pending
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT phase1_approved FROM project_status WHERE project_id = %s", (project_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                return None
            
            approved = row["phase1_approved"]
            if approved == 1:
                return True
            elif approved == 2:
                return False
            else:
                return None  # Pending
        finally:
            self._put_connection(conn)
    
    def approve_document(self, project_id: str, agent_type: AgentType, notes: Optional[str] = None) -> bool:
        """
        Approve a specific document to proceed
        
        Args:
            project_id: Project identifier
            agent_type: AgentType of the document to approve
            notes: Optional approval notes/comments
            
        Returns:
            True if approval was successful
        """
        with self._lock:
            conn = None
            try:
                import logging
                logger = logging.getLogger(__name__)
                conn = self._get_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                now = datetime.now()
                
                # First, check if document exists
                cursor.execute("""
                    SELECT version, approved FROM agent_outputs 
                    WHERE project_id = %s AND agent_type = %s
                    ORDER BY version DESC LIMIT 1
                """, (project_id, agent_type.value))
                existing = cursor.fetchone()
                
                if not existing:
                    cursor.close()
                    logger.warning(f"No document found to approve: project_id={project_id}, agent_type={agent_type.value}")
                    return False
                
                max_version = existing['version']
                logger.info(f"Approving document: project_id={project_id}, agent_type={agent_type.value}, version={max_version}")
                
                # Update the latest version of the document (use explicit version number to avoid subquery issues)
                cursor.execute("""
                    UPDATE agent_outputs 
                    SET approved = %s, approved_at = %s, approval_notes = %s
                    WHERE project_id = %s AND agent_type = %s AND version = %s
                """, (1, now, notes, project_id, agent_type.value, max_version))
                
                rows_affected = cursor.rowcount
                conn.commit()
                cursor.close()
                
                if rows_affected == 0:
                    logger.warning(f"No rows updated when approving document: project_id={project_id}, agent_type={agent_type.value}")
                    return False
                
                logger.info(f"✅ Document approved: {agent_type.value} (version {max_version})")
                return True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error approving document {agent_type.value} for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def reject_document(self, project_id: str, agent_type: AgentType, notes: Optional[str] = None) -> bool:
        """
        Reject a specific document (workflow stops)
        
        Args:
            project_id: Project identifier
            agent_type: AgentType of the document to reject
            notes: Optional rejection notes/comments
            
        Returns:
            True if rejection was successful
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now()
                
                # Update the latest version of the document
                cursor.execute("""
                    UPDATE agent_outputs 
                    SET approved = %s, approved_at = %s, approval_notes = %s
                    WHERE project_id = %s AND agent_type = %s AND version = (
                        SELECT MAX(version) FROM agent_outputs 
                        WHERE project_id = %s AND agent_type = %s
                    )
                """, (2, now, notes, project_id, agent_type.value, project_id, agent_type.value))
                
                conn.commit()
                cursor.close()
                return True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error rejecting document {agent_type.value} for {project_id}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def is_document_approved(self, project_id: str, agent_type: AgentType) -> Optional[bool]:
        """
        Check if a specific document is approved (checks latest version only)
        
        Args:
            project_id: Project identifier
            agent_type: AgentType of the document to check
            
        Returns:
            True if approved, False if rejected, None if pending
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                # Get the latest version of the document (regardless of approval status)
                # This ensures we check the most recent version, not an old rejected version
                cursor.execute("""
                    SELECT version, approved FROM agent_outputs 
                    WHERE project_id = %s AND agent_type = %s
                    ORDER BY version DESC LIMIT 1
                """, (project_id, agent_type.value))
                row = cursor.fetchone()
                cursor.close()
                
                if not row:
                    return None  # Document not generated yet
                
                # Check the approval status of the latest version
                approved = row["approved"]
                
                if approved == 1:
                    return True  # Approved
                elif approved == 2:
                    return False  # Rejected
                else:
                    return None  # Pending (approved=0 or NULL)
            finally:
                self._put_connection(conn)
    
    def get_document_version(self, project_id: str, agent_type: AgentType) -> int:
        """
        Get the current version number of a document
        
        Args:
            project_id: Project identifier
            agent_type: AgentType of the document
            
        Returns:
            Version number (default: 1)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT version FROM agent_outputs 
                WHERE project_id = %s AND agent_type = %s
                ORDER BY version DESC LIMIT 1
            """, (project_id, agent_type.value))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                return 1
            
            return row["version"] or 1
        finally:
            self._put_connection(conn)
    
    def save_document_version(
        self,
        project_id: str,
        agent_type: AgentType,
        content: str,
        file_path: str,
        quality_score: Optional[float] = None,
        version: Optional[int] = None
    ) -> int:
        """
        Save a new version of a document
        
        Args:
            project_id: Project identifier
            agent_type: AgentType of the document
            content: Document content
            file_path: File path
            quality_score: Quality score
            version: Version number (auto-incremented if None)
            
        Returns:
            Version number that was saved
        """
        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Get next version number
                if version is None:
                    current_version = self.get_document_version(project_id, agent_type)
                    version = current_version + 1
                output_id = f"{project_id}_{agent_type.value}_v{version}"
                now = datetime.now()
                
                # Get document type from agent type
                document_type = agent_type.value.replace("_", " ").title()
                
                # Use INSERT ... ON CONFLICT for upsert
                cursor.execute("""
                    INSERT INTO agent_outputs (
                        output_id, project_id, agent_type, document_type,
                        content, file_path, quality_score, status,
                        dependencies, generated_at, version, approved
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (output_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        file_path = EXCLUDED.file_path,
                        quality_score = EXCLUDED.quality_score,
                        status = EXCLUDED.status,
                        generated_at = EXCLUDED.generated_at,
                        approved = EXCLUDED.approved
                """, (
                    output_id,
                    project_id,
                    agent_type.value,
                    document_type,
                    content,
                    file_path,
                    quality_score,
                    DocumentStatus.COMPLETE.value,
                    json.dumps([]),
                    now,
                    version,
                    0  # Pending approval
                ))
                
                conn.commit()
                cursor.close()
                return version
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving document version for {project_id}/{agent_type.value}: {e}", exc_info=True)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                if conn:
                    try:
                        self._put_connection(conn)
                    except Exception as e:
                        logger.warning(f"Error returning connection to pool: {e}")
    
    def get_documents_for_project(
        self,
        project_id: str,
        document_ids: Optional[List[str]] = None,
        include_content: bool = False,
    ) -> Dict[str, Dict[str, str]]:
        """
        Retrieve generated documents for a project.

        Args:
            project_id: Target project identifier.
            document_ids: Optional subset of document IDs.
            include_content: When True, include document content by reading from disk.

        Returns:
            Mapping of document_id -> metadata dictionary.
        """
        status = self.get_project_status(project_id)
        if not status:
            return {}

        results = status.get("results") or {}
        documents = results.get("documents") or []
        wanted = set(document_ids) if document_ids else None
        documents_map: Dict[str, Dict[str, str]] = {}

        for entry in documents:
            doc_id = entry.get("id")
            if not doc_id:
                continue
            if wanted and doc_id not in wanted:
                continue

            item = dict(entry)
            # Content is stored in database, not in files
            # If content is not in the entry, try to get it from agent_outputs table
            if include_content and not item.get("content"):
                item["content"] = self.get_document_content_by_type(project_id, doc_id)
            documents_map[doc_id] = item

        return documents_map

    def close(self):
        """Close database connection"""
        if hasattr(self, 'connection') and self.connection and not self.connection.closed:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

