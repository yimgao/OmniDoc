"""Helpers for loading and working with the document catalog configuration."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import json
import logging
import os

from fastapi import HTTPException

logger = logging.getLogger(__name__)

DOCUMENT_CONFIG_ENV = "DOCUMENT_CONFIG_PATH"
# Default path: backend/config/document_definitions.json (relative to project root)
DEFAULT_CATALOG_PATH = Path("backend/config/document_definitions.json")
QUALITY_RULES_PATH = Path("src/config/quality_rules.json")


@dataclass(frozen=True)
class DocumentDefinition:
    """Typed representation of a single document definition."""

    id: str
    name: str
    prompt_key: Optional[str]
    agent_class: str
    dependencies: List[str]
    category: Optional[str]
    description: Optional[str]
    priority: Optional[str]
    owner: Optional[str]
    status: Optional[str]
    audience: Optional[str]
    stage_label: Optional[str]
    stage_notes: Optional[str]
    must_have: Optional[str]
    usage_frequency: Optional[str]
    notes: Optional[str]
    special_key: Optional[str] = None


def _catalog_path() -> Path:
    """
    Get the path to the document definitions catalog.
    
    Checks in order:
    1. DOCUMENT_CONFIG_PATH environment variable (absolute or relative)
    2. Default path: backend/config/document_definitions.json (relative to project root)
    3. Fallback: config/document_definitions.json (for backward compatibility)
    """
    # Get project root (consistent for all path resolution)
    current_file = Path(__file__)
    # From backend/src/config/document_catalog.py -> backend/
    backend_dir = current_file.parent.parent.parent
    # From backend/ -> project root
    project_root = backend_dir.parent
    
    env_path = os.getenv(DOCUMENT_CONFIG_ENV)
    if env_path:
        path = Path(env_path)
        # If absolute path, use as-is
        if path.is_absolute():
            return path
        
        # For relative paths, try multiple locations
        # 1. Resolve from project root (most common case)
        resolved_from_root = project_root / path
        if resolved_from_root.exists():
            return resolved_from_root
        
        # 2. Handle old-style paths like "config/document_definitions.json"
        # Try new location: backend/config/document_definitions.json
        if len(path.parts) > 0 and path.parts[0] == "config":
            new_location = project_root / "backend" / path
            if new_location.exists():
                return new_location
        
        # 3. Try as-is from current working directory (for backward compatibility)
        if path.exists():
            return path
        
        # 4. Return the resolved path from project root (will fail with clear error)
        return resolved_from_root
    
    # Default: try backend/config/document_definitions.json from project root
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent.parent
    project_root = backend_dir.parent
    default_path = project_root / DEFAULT_CATALOG_PATH
    if default_path.exists():
        return default_path
    
    # Fallback: try old location for backward compatibility
    fallback = project_root / "config" / "document_definitions.json"
    if fallback.exists():
        return fallback
    
    # Last resort: return default (will fail with clear error message)
    return project_root / DEFAULT_CATALOG_PATH


# Cache at module level to avoid reloading on every call
_document_definitions_cache: Optional[Dict[str, DocumentDefinition]] = None

def load_document_definitions() -> Dict[str, DocumentDefinition]:
    """Load and cache document definitions keyed by ID."""
    global _document_definitions_cache
    
    # Return cached version if available
    if _document_definitions_cache is not None:
        return _document_definitions_cache
    
    catalog_file = _catalog_path()
    
    # Double-check: if file doesn't exist, try to find it in common locations
    if not catalog_file.exists():
        current_file = Path(__file__)
        backend_dir = current_file.parent.parent.parent
        project_root = backend_dir.parent
        
        # Try all possible locations
        possible_paths = [
            catalog_file,  # The resolved path
            project_root / "backend" / "config" / "document_definitions.json",  # New location
            project_root / "config" / "document_definitions.json",  # Old location
            Path("backend/config/document_definitions.json"),  # Relative from cwd
            Path("config/document_definitions.json"),  # Relative from cwd (old)
        ]
        
        # Check if any of these exist
        for possible_path in possible_paths:
            if possible_path.exists():
                logger.warning(
                    f"Document catalog found at {possible_path} but was looking at {catalog_file}. "
                    f"Using found path."
                )
                catalog_file = possible_path
                break
        
        # If still not found, raise error with helpful message
        if not catalog_file.exists():
            env_path = os.getenv(DOCUMENT_CONFIG_ENV, "not set")
            attempted_paths = [str(p) for p in possible_paths]
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Document catalog not found.\n"
                    f"  Attempted paths:\n"
                    + "\n".join(f"    - {p}" for p in attempted_paths)
                    + f"\n  DOCUMENT_CONFIG_PATH env var: {env_path}\n"
                    f"  Current working directory: {Path.cwd()}\n"
                    f"  Project root (detected): {project_root}\n"
                    f"  Please ensure document_definitions.json exists in backend/config/\n"
                    f"  Or update DOCUMENT_CONFIG_PATH in .env file to: backend/config/document_definitions.json"
                ),
            )

    payload = json.loads(catalog_file.read_text(encoding="utf-8"))
    documents = payload.get("documents", [])
    definitions: Dict[str, DocumentDefinition] = {}

    for raw in documents:
        doc_id = raw.get("id")
        if not doc_id:
            continue

        # Handle stage field: can be either a dict or a string
        stage_raw = raw.get("stage")
        if isinstance(stage_raw, str):
            # If stage is a string, convert it to dict format
            stage = {"label": stage_raw, "notes": ""}
        elif isinstance(stage_raw, dict):
            stage = stage_raw
        else:
            stage = {}

        definitions[doc_id] = DocumentDefinition(
            id=doc_id,
            name=raw.get("name", doc_id.title()),
            prompt_key=raw.get("prompt_key"),
            agent_class=raw.get("agent_class", "generic"),
            dependencies=list({dep for dep in raw.get("dependencies", []) if dep}),
            category=raw.get("category"),
            description=raw.get("description"),
            priority=raw.get("priority"),
            owner=raw.get("owner"),
            status=raw.get("status"),
            audience=raw.get("audience"),
            stage_label=stage.get("label"),
            stage_notes=stage.get("notes"),
            must_have=raw.get("must_have"),
            usage_frequency=raw.get("usage_frequency"),
            notes=raw.get("notes"),
            special_key=raw.get("special_key"),
        )

    # Cache the result
    _document_definitions_cache = definitions
    return definitions


def get_document_by_id(document_id: str) -> Optional[DocumentDefinition]:
    """Return a single document definition, if present."""
    return load_document_definitions().get(document_id)


def reload_catalog() -> None:
    """Clear the cached definitions (useful for tests or when the file changes)."""
    load_document_definitions.cache_clear()  # type: ignore[attr-defined]
    _load_quality_rules_dependencies.cache_clear()  # type: ignore[attr-defined]


@lru_cache(maxsize=1)
def _load_quality_rules_dependencies() -> Dict[str, List[str]]:
    """
    Load dependencies from quality_rules.json and map document names to document IDs.
    
    Returns:
        Dict mapping document ID to list of dependency document IDs
    """
    dependencies_map: Dict[str, List[str]] = {}
    
    # Load quality rules
    if not QUALITY_RULES_PATH.exists():
        return dependencies_map
    
    try:
        with open(QUALITY_RULES_PATH, 'r', encoding='utf-8') as f:
            quality_rules = json.load(f)
    except Exception:
        return dependencies_map
    
    # Load document definitions to create name -> id mapping
    definitions = load_document_definitions()
    name_to_id: Dict[str, str] = {}
    for doc_id, definition in definitions.items():
        name_to_id[definition.name] = doc_id
        # Also map normalized names (lowercase, no special chars)
        normalized_name = definition.name.lower().replace('(', '').replace(')', '').strip()
        name_to_id[normalized_name] = doc_id
    
    # Process quality rules
    for rule_name, rules in quality_rules.items():
        if "dependencies" not in rules:
            continue
        
        # Find document ID for this rule name
        doc_id = None
        # Try exact match first
        if rule_name in name_to_id:
            doc_id = name_to_id[rule_name]
        else:
            # Try normalized match
            normalized_rule = rule_name.lower().replace('(', '').replace(')', '').strip()
            if normalized_rule in name_to_id:
                doc_id = name_to_id[normalized_rule]
            else:
                # Try fuzzy match by checking all document names
                for doc_name, doc_id_candidate in name_to_id.items():
                    if rule_name.lower() in doc_name.lower() or doc_name.lower() in rule_name.lower():
                        doc_id = doc_id_candidate
                        break
        
        if not doc_id:
            continue
        
        # Map dependency names to IDs
        dep_ids: List[str] = []
        for dep_name in rules.get("dependencies", []):
            # Try exact match
            if dep_name in name_to_id:
                dep_ids.append(name_to_id[dep_name])
            else:
                # Try normalized match
                normalized_dep = dep_name.lower().replace('(', '').replace(')', '').strip()
                if normalized_dep in name_to_id:
                    dep_ids.append(name_to_id[normalized_dep])
                else:
                    # Try fuzzy match
                    for doc_name, dep_id_candidate in name_to_id.items():
                        if dep_name.lower() in doc_name.lower() or doc_name.lower() in dep_name.lower():
                            dep_ids.append(dep_id_candidate)
                            break
        
        if dep_ids:
            dependencies_map[doc_id] = dep_ids
    
    return dependencies_map


def get_all_dependencies(doc_id: str) -> List[str]:
    """
    Get all dependencies for a document ID, combining dependencies from:
    1. document_definitions.json
    2. quality_rules.json
    
    Returns:
        List of unique dependency document IDs
    """
    definitions = load_document_definitions()
    definition = definitions.get(doc_id)
    
    # Start with dependencies from document_definitions.json
    deps_from_definitions: List[str] = []
    if definition:
        deps_from_definitions = list(definition.dependencies)
    
    # Add dependencies from quality_rules.json
    quality_deps = _load_quality_rules_dependencies().get(doc_id, [])
    
    # Combine and deduplicate
    all_deps = list(dict.fromkeys(deps_from_definitions + quality_deps))
    
    return all_deps


def resolve_dependencies(selected_ids: Iterable[str]) -> List[str]:
    """
    Resolve dependencies for the given document IDs with topological ordering.
    Combines dependencies from both document_definitions.json and quality_rules.json.
    
    Enhanced features:
    - Circular dependency detection with detailed error messages
    - Optional dependency handling (warnings instead of errors)
    - Missing dependency detection
    
    Args:
        selected_ids: Iterable of document IDs to resolve
        
    Returns:
        List of document IDs in topological order
        
    Raises:
        ValueError: If circular dependency detected or unknown document ID found
    """
    definitions = load_document_definitions()
    order: List[str] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()
    cycle_path: List[str] = []  # Track cycle path for better error messages

    def visit(doc_id: str, path: List[str] = None) -> None:
        """Visit a document and its dependencies recursively."""
        if path is None:
            path = []
        
        if doc_id in visited:
            return
        if doc_id in visiting:
            # Circular dependency detected - build detailed error message
            cycle_start = path.index(doc_id) if doc_id in path else 0
            cycle = path[cycle_start:] + [doc_id]
            raise ValueError(
                f"Circular dependency detected: {' -> '.join(cycle)}. "
                f"Please check dependencies in document_definitions.json and quality_rules.json."
            )
        
        definition = definitions.get(doc_id)
        if not definition:
            raise ValueError(
                f"Unknown document id '{doc_id}'. "
                f"Available document IDs: {', '.join(sorted(definitions.keys()))}"
            )

        visiting.add(doc_id)
        current_path = path + [doc_id]
        
        # Use get_all_dependencies to get combined dependencies
        all_deps = get_all_dependencies(doc_id)
        missing_deps = [dep for dep in all_deps if dep not in definitions]
        
        if missing_deps:
            # Log warning but continue (optional dependencies)
            logger.warning(
                "Document '%s' has dependencies that don't exist in catalog: %s. "
                "These will be skipped.",
                doc_id,
                missing_deps
            )
        
        # Visit only valid dependencies
        for dep_id in all_deps:
            if dep_id in definitions:
                visit(dep_id, current_path)
        
        visiting.remove(doc_id)
        visited.add(doc_id)
        order.append(doc_id)

    # Validate all selected IDs exist before processing
    selected_list = list(dict.fromkeys(selected_ids))
    invalid_ids = [doc_id for doc_id in selected_list if doc_id not in definitions]
    if invalid_ids:
        raise ValueError(
            f"Unknown document IDs in selection: {', '.join(invalid_ids)}. "
            f"Available document IDs: {', '.join(sorted(definitions.keys()))}"
        )

    for doc_id in selected_list:
        visit(doc_id)

    return order


def list_document_ids() -> List[str]:
    """Return all document IDs in the catalog."""
    return list(load_document_definitions().keys())


