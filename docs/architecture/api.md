# API層（FastAPI バックエンド）

**役割**: GUIアプリケーションのためのREST APIを提供

## app.py (アプリケーションファクトリ)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    app = FastAPI(
        title="GenGlossary API",
        description="API for GenGlossary",
        version=__version__,
    )

    # CORS設定（localhost:3000, 5173など）
    app.add_middleware(CORSMiddleware, ...)

    # カスタムミドルウェア
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)

    # ルーター登録
    app.include_router(health_router)

    return app
```

## schemas/ (APIスキーマ)

スキーマはエンティティごとにモジュール化されています。

### common.py (共通スキーマ)
```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from genglossary.models.term import TermOccurrence


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")


class VersionResponse(BaseModel):
    """Version information response."""
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


class GlossaryTermResponse(BaseModel):
    """Common schema for glossary terms (provisional and refined)."""
    id: int = Field(..., description="Term ID")
    term_name: str = Field(..., description="Term name")
    definition: str = Field(..., description="Term definition")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    occurrences: list[TermOccurrence] = Field(
        ..., description="List of term occurrences"
    )

    @classmethod
    def from_db_row(cls, row: Any) -> "GlossaryTermResponse":
        """Create from database row.

        Args:
            row: Database row (GlossaryTermRow or dict-like) with deserialized occurrences.

        Returns:
            GlossaryTermResponse: Response instance.
        """
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            definition=row["definition"],
            confidence=row["confidence"],
            occurrences=row["occurrences"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["GlossaryTermResponse"]:
        """Create list from database rows.

        Args:
            rows: List of database rows (GlossaryTermRow or dict-like).

        Returns:
            list[GlossaryTermResponse]: List of response instances.
        """
        return [cls.from_db_row(row) for row in rows]
```

### term_schemas.py (Terms用スキーマ)
```python
class TermResponse(BaseModel):
    """Response schema for a term."""
    id: int = Field(..., description="Term ID")
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")

    @classmethod
    def from_db_row(cls, row: Any) -> "TermResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_text=row["term_text"],
            category=row["category"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["TermResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]


class TermMutationRequest(BaseModel):
    """Request schema for creating or updating a term."""
    term_text: str = Field(..., description="Term text")
    category: str | None = Field(None, description="Term category")


# Aliases for clarity
TermCreateRequest = TermMutationRequest
TermUpdateRequest = TermMutationRequest
```

### provisional_schemas.py / refined_schemas.py
```python
# GlossaryTermResponseを継承またはエイリアス
from genglossary.api.schemas.common import GlossaryTermResponse

ProvisionalResponse = GlossaryTermResponse  # Provisional用
RefinedResponse = GlossaryTermResponse      # Refined用
```

### issue_schemas.py (Issues用スキーマ)
```python
class IssueResponse(BaseModel):
    """Response schema for a glossary issue."""
    id: int = Field(..., description="Issue ID")
    term_name: str = Field(..., description="Term name this issue relates to")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Description of the issue")

    @classmethod
    def from_db_row(cls, row: Any) -> "IssueResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_name=row["term_name"],
            issue_type=row["issue_type"],
            description=row["description"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["IssueResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]
```

### project_schemas.py (Projects用スキーマ)
```python
def _validate_project_name(v: str) -> str:
    """Validate project name is not empty.

    共通バリデーション関数。ProjectCreateRequestとProjectCloneRequestで共有。
    """
    stripped = v.strip()
    if not stripped:
        raise ValueError("Project name cannot be empty")
    return stripped


class ProjectResponse(BaseModel):
    """Response schema for a project."""
    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    doc_root: str = Field(..., description="Document root path")
    llm_provider: str = Field(..., description="LLM provider name")
    llm_model: str = Field(..., description="LLM model name")
    llm_base_url: str = Field(..., description="LLM base URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_run_at: datetime | None = Field(None, description="Last run timestamp")
    status: ProjectStatus = Field(..., description="Project status")

    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        """Create from Project model using Pydantic model_validate."""
        return cls.model_validate(project, from_attributes=True)


class ProjectCreateRequest(BaseModel):
    """Request schema for creating a project."""
    name: str = Field(..., description="Project name (must be unique)")
    doc_root: str | None = Field(
        default=None, description="Document directory (auto-generated if not provided)"
    )
    llm_provider: str = Field(default="ollama", description="LLM provider name")
    llm_model: str = Field(default="", description="LLM model name")
    llm_base_url: str = Field(default="", description="LLM base URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty."""
        return _validate_project_name(v)  # 共通関数を使用

    @field_validator("doc_root")
    @classmethod
    def validate_doc_root(cls, v: str | None) -> str | None:
        """Validate document root path if provided."""
        return _validate_doc_root(v)  # 空白をNoneに変換

    @field_validator("llm_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate LLM base URL format (http/https only)."""
        return _validate_llm_base_url(v)


class ProjectCloneRequest(BaseModel):
    """Request schema for cloning a project."""
    new_name: str = Field(..., description="Name for the cloned project")

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty."""
        return _validate_project_name(v)  # 共通関数を使用


class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project."""
    name: str | None = Field(None, description="New project name")
    llm_provider: str | None = Field(None, description="New LLM provider name")
    llm_model: str | None = Field(None, description="New LLM model name")
    llm_base_url: str | None = Field(None, description="New LLM base URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate project name if provided."""
        if v is None:
            return None
        return _validate_project_name(v)

    @field_validator("llm_base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        """Validate LLM base URL format if provided (http/https only)."""
        return _validate_llm_base_url(v)
```

**スキーマ設計のポイント:**
- `_validate_project_name()` を共通関数として抽出し、重複を排除
- `from_project()` でProjectモデルからレスポンスへの変換を統一

### file_schemas.py (Files用スキーマ)
```python
class FileResponse(BaseModel):
    """Response schema for a document file."""
    id: int = Field(..., description="Document ID")
    file_path: str = Field(..., description="File path")
    content_hash: str = Field(..., description="Content hash")

    @classmethod
    def from_db_row(cls, row: Any) -> "FileResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            file_path=row["file_path"],
            content_hash=row["content_hash"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["FileResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]


class FileCreateRequest(BaseModel):
    """Request schema for creating a document file."""
    file_path: str = Field(..., description="File path relative to doc_root")


class DiffScanResponse(BaseModel):
    """Response schema for diff scan operation."""
    added: list[str] = Field(..., description="List of newly added file paths")
    modified: list[str] = Field(..., description="List of modified file paths")
    deleted: list[str] = Field(..., description="List of deleted file paths")
```

**スキーマ設計のポイント:**
- `from_db_row()` / `from_db_rows()` クラスメソッドでDB行からモデルへの変換を統一
- `GlossaryTermResponse` を基底クラスとしてProvisionalとRefinedで共有
- `TermMutationRequest` をCreateとUpdateで共有（DRY原則）
- `Field()` でOpenAPIドキュメントに説明を追加

## routers/ (APIエンドポイント)

### health.py (ヘルスチェックエンドポイント)
```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """ヘルスチェック"""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))

@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """バージョン情報"""
    return VersionResponse(name="genglossary", version=__version__)
```

### projects.py (Projects API - プロジェクト管理)

```python
router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_project_or_404(
    registry_conn: sqlite3.Connection,
    project_id: int,
) -> Project:
    """Get project or raise 404.

    プロジェクト取得 + 404チェックの共通ヘルパー。
    複数のエンドポイントで同一パターンが使われるため抽出。
    """
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def _cleanup_db_file(db_path: str) -> None:
    """Cleanup orphaned database file.

    プロジェクト作成/クローン失敗時のDBファイルクリーンアップ。
    IntegrityError発生時に呼び出される共通処理。
    """
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


@router.get("", response_model=list[ProjectResponse])
async def list_all_projects(
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> list[ProjectResponse]:
    """プロジェクト一覧を取得"""
    ...

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: int = PathParam(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """プロジェクトをIDで取得"""
    project = _get_project_or_404(registry_conn, project_id)
    return ProjectResponse.from_project(project)

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    request: ProjectCreateRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """新しいプロジェクトを作成

    doc_rootが未指定の場合、{data_dir}/projects/{project_name}/に自動生成される。
    """
    db_path = _generate_db_path(request.name)
    doc_root = request.doc_root or _generate_doc_root(request.name)
    try:
        project_id = create_project(registry_conn, ...)
    except sqlite3.IntegrityError:
        _cleanup_db_file(db_path)  # 共通ヘルパーでクリーンアップ
        _cleanup_doc_root(doc_root)  # 自動生成したdoc_rootもクリーンアップ
        raise HTTPException(status_code=409, detail="Project name already exists")
    ...

@router.post("/{project_id}/clone", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def clone_existing_project(
    project_id: int = PathParam(...),
    request: ProjectCloneRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """プロジェクトをクローン"""
    ...

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_project(
    project_id: int = PathParam(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> None:
    """プロジェクトを削除"""
    _get_project_or_404(registry_conn, project_id)  # 存在確認
    delete_project(registry_conn, project_id)

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_existing_project(
    project_id: int = PathParam(...),
    request: ProjectUpdateRequest = Body(...),
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> ProjectResponse:
    """プロジェクト設定を更新"""
    _get_project_or_404(registry_conn, project_id)  # 存在確認
    update_project(registry_conn, project_id, ...)
    updated_project = _get_project_or_404(registry_conn, project_id)
    return ProjectResponse.from_project(updated_project)
```

**ヘルパー関数の設計:**
- `_get_project_or_404()`: プロジェクト取得と404チェックを一元化。GET/DELETE/PATCHで使用
- `_cleanup_db_file()`: DBファイルの孤立防止。create/clone失敗時に使用

### terms.py (Terms API - 抽出用語の管理)
```python
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

router = APIRouter(prefix="/api/projects/{project_id}/terms", tags=["terms"])

@router.get("", response_model=list[TermResponse])
async def list_all_terms_endpoint(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[TermResponse]:
    """抽出用語の一覧を取得"""
    rows = list_all_terms(project_db)
    return TermResponse.from_db_rows(rows)

@router.get("/{term_id}", response_model=TermResponse)
async def get_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """指定IDの用語を取得"""
    row = get_term(project_db, term_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return TermResponse.from_db_row(row)

@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
async def create_new_term(
    project_id: int = Path(...),
    request: TermCreateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """新しい用語を作成"""
    term_id = create_term(project_db, request.term_text, request.category)
    row = get_term(project_db, term_id)
    assert row is not None
    return TermResponse.from_db_row(row)

@router.patch("/{term_id}", response_model=TermResponse)
async def update_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    request: TermUpdateRequest = Body(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    """用語を更新"""
    update_term(project_db, term_id, request.term_text, request.category)
    row = get_term(project_db, term_id)
    assert row is not None
    return TermResponse.from_db_row(row)

@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term_endpoint(
    project_id: int = Path(...),
    term_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> None:
    """用語を削除"""
    delete_term(project_db, term_id)
```

### provisional.py (Provisional API - 暫定用語集)
```python
router = APIRouter(prefix="/api/projects/{project_id}/provisional", tags=["provisional"])

# GET /api/projects/{project_id}/provisional - 一覧取得
# GET /api/projects/{project_id}/provisional/{entry_id} - 詳細取得
# PATCH /api/projects/{project_id}/provisional/{entry_id} - 更新
# DELETE /api/projects/{project_id}/provisional/{entry_id} - 削除
# POST /api/projects/{project_id}/provisional/{entry_id}/regenerate - 単一エントリの再生成（LLM）
```

**regenerate エンドポイントの実装詳細:**

```python
@router.post("/{entry_id}/regenerate", response_model=ProvisionalResponse)
async def regenerate_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    """Regenerate definition for a provisional term using LLM.

    処理フロー:
    1. 用語の存在確認（get_provisional_term）
    2. プロジェクトのLLM設定からLLMクライアント作成
    3. DocumentLoaderでドキュメントロード
    4. GlossaryGeneratorで用語の出現箇所検索と定義再生成
    5. 新しい定義とconfidenceでDB更新
    6. 更新後の用語を返却

    エラーハンドリング:
    - 404: 用語が見つからない場合
    - 503: LLMタイムアウト (httpx.TimeoutException)
    - 503: LLM接続エラー (httpx.HTTPError)

    Returns:
        ProvisionalResponse: 再生成された用語（新しい定義とconfidence）
    """
    # 用語の存在確認
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    try:
        # LLMクライアント作成
        llm_client = create_llm_client(project.llm_provider, project.llm_model or None)

        # ドキュメントロード
        loader = DocumentLoader()
        documents = loader.load_directory(project.doc_root)

        # 定義再生成
        generator = GlossaryGenerator(llm_client=llm_client)
        occurrences = generator._find_term_occurrences(row["term_name"], documents)
        if not occurrences:
            occurrences = row["occurrences"]  # 既存のoccurrencesを使用

        definition, confidence = generator._generate_definition(
            row["term_name"], occurrences
        )

        # DB更新
        update_provisional_term(project_db, entry_id, definition, confidence)

        # 更新後の用語を返却
        updated_row = get_provisional_term(project_db, entry_id)
        return ProvisionalResponse.from_db_row(updated_row)

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="LLM service timeout")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
```

**LLM統合のポイント:**
- プロジェクトの `llm_provider` と `llm_model` 設定を使用
- `GlossaryGenerator._find_term_occurrences()` でドキュメント内の用語出現箇所を検索
- `GlossaryGenerator._generate_definition()` でLLMを使用して定義と信頼度を生成
- 既存のoccurrencesが見つからない場合は、DBに保存されているoccurrencesを使用

### issues.py (Issues API - 精査結果)
```python
router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])

@router.get("", response_model=list[IssueResponse])
async def list_all_issues_endpoint(
    project_id: int = Path(...),
    issue_type: str | None = Query(None, description="Filter by issue type"),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[IssueResponse]:
    """精査結果の一覧を取得（issue_typeフィルタ対応）"""
    if issue_type:
        rows = list_issues_by_type(project_db, issue_type)
    else:
        rows = list_all_issues(project_db)
    return IssueResponse.from_db_rows(rows)

# GET /api/projects/{project_id}/issues/{issue_id} - 詳細取得
```

### refined.py (Refined API - 最終用語集)
```python
router = APIRouter(prefix="/api/projects/{project_id}/refined", tags=["refined"])

# GET /api/projects/{project_id}/refined - 一覧取得
# GET /api/projects/{project_id}/refined/{term_id} - 詳細取得
# GET /api/projects/{project_id}/refined/export-md - Markdownエクスポート
# PATCH /api/projects/{project_id}/refined/{term_id} - 更新
# DELETE /api/projects/{project_id}/refined/{term_id} - 削除

@router.get("/export-md", response_class=PlainTextResponse)
async def export_markdown(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> PlainTextResponse:
    """最終用語集をMarkdown形式でエクスポート"""
    rows = list_all_refined(project_db)
    lines = ["# 用語集\n"]
    for row in rows:
        lines.append(f"## {row['term_name']}\n")
        lines.append(f"{row['definition']}\n\n")
        # ... 出現箇所の追加
    return PlainTextResponse(
        content="".join(lines),
        media_type="text/markdown; charset=utf-8"
    )
```

**重要な実装ポイント:**
- `export-md` のような固定パスは `/{term_id}` より先に定義する（FastAPIのルーティング順序）
- `Body(...)` アノテーションでリクエストボディを明示
- プロジェクトIDの検証は `get_project_by_id` が自動的に404を返す

### files.py (Files API - ドキュメント管理)
```python
router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])

# GET /api/projects/{project_id}/files - ファイル一覧取得
# GET /api/projects/{project_id}/files/{file_id} - ファイル詳細取得
# POST /api/projects/{project_id}/files - ファイル追加
# DELETE /api/projects/{project_id}/files/{file_id} - ファイル削除

@router.post("/diff-scan", response_model=DiffScanResponse)
async def scan_file_diff(
    project_id: int = Path(...),
    project: Project = Depends(get_project_by_id),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> DiffScanResponse:
    """ファイルシステムとDBの差分をスキャン"""
    db_files = {row["file_path"]: row for row in list_all_documents(project_db)}
    fs_files = {}

    doc_root = Path(project.doc_root)
    if doc_root.exists():
        for file_path in doc_root.rglob("*.txt"):
            rel_path = str(file_path.relative_to(doc_root))
            fs_files[rel_path] = _compute_file_hash(file_path)

    added = [path for path in fs_files if path not in db_files]
    deleted = [path for path in db_files if path not in fs_files]
    modified = [
        path for path in fs_files
        if path in db_files and fs_files[path] != db_files[path]["content_hash"]
    ]

    return DiffScanResponse(added=added, modified=modified, deleted=deleted)
```

**diff-scanのロジック:**
- ファイルシステム上の `.txt` ファイルをスキャン
- SHA256ハッシュで変更を検出
- added / modified / deleted を返却

## middleware/

### request_id.py (リクエストIDミドルウェア)
```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """すべてのレスポンスにX-Request-IDヘッダーを付与"""
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### logging.py (構造化ログミドルウェア)
```python
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """リクエスト/レスポンスを構造化ログとして出力"""
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info("HTTP request", extra={
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
        })
        return response
```

## dependencies.py (依存性注入)
```python
import os
import sqlite3
from pathlib import Path
from typing import Generator

from fastapi import Depends, HTTPException

from genglossary.config import Config
from genglossary.db.connection import get_connection
from genglossary.db.project_repository import get_project
from genglossary.db.registry_schema import initialize_registry
from genglossary.models.project import Project


def get_config() -> Config:
    """Get application configuration.

    Returns:
        Config: Application configuration instance
    """
    return Config()


def get_registry_db(
    registry_path: str | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Get registry database connection.

    Args:
        registry_path: Optional path to registry database.
            If None, uses GENGLOSSARY_REGISTRY_PATH env var or default.

    Yields:
        sqlite3.Connection: Registry database connection.
    """
    if registry_path is None:
        registry_path = os.getenv(
            "GENGLOSSARY_REGISTRY_PATH",
            str(Path.home() / ".genglossary" / "registry.db"),
        )

    conn = get_connection(registry_path)
    initialize_registry(conn)

    try:
        yield conn
    finally:
        conn.close()


def get_project_by_id(
    project_id: int,
    registry_conn: sqlite3.Connection = Depends(get_registry_db),
) -> Project:
    """Get project by ID or raise 404.

    Args:
        project_id: Project ID to retrieve.
        registry_conn: Registry database connection.

    Returns:
        Project: The requested project.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def get_project_db(
    project: Project = Depends(get_project_by_id),
) -> Generator[sqlite3.Connection, None, None]:
    """Get project-specific database connection.

    Args:
        project: Project instance from get_project_by_id.

    Yields:
        sqlite3.Connection: Project database connection.
    """
    conn = get_connection(project.db_path)
    try:
        yield conn
    finally:
        conn.close()
```

**依存性注入のパターン:**
- `get_registry_db()` - レジストリDB接続をyieldするジェネレーター
- `get_project_by_id()` - プロジェクトIDからProjectを取得、存在しない場合は404
- `get_project_db()` - プロジェクト固有のDB接続を取得（`get_project_by_id`に依存）

**使用例:**
```python
@router.get("/{project_id}/terms")
async def list_terms(
    project_id: int = Path(...),
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> list[TermResponse]:
    rows = list_all_terms(project_db)
    return TermResponse.from_db_rows(rows)
```

## APIエンドポイント一覧

**システムエンドポイント:**
- `GET /health` - ヘルスチェック
- `GET /version` - バージョン情報
- `GET /docs` - OpenAPI ドキュメント（Swagger UI）
- `GET /redoc` - ReDoc ドキュメント

**Terms API (抽出用語の管理) - 5エンドポイント:**
- `GET /api/projects/{project_id}/terms` - 用語一覧取得
- `GET /api/projects/{project_id}/terms/{term_id}` - 用語詳細取得
- `POST /api/projects/{project_id}/terms` - 用語作成
- `PATCH /api/projects/{project_id}/terms/{term_id}` - 用語更新
- `DELETE /api/projects/{project_id}/terms/{term_id}` - 用語削除

**Provisional API (暫定用語集) - 5エンドポイント:**
- `GET /api/projects/{project_id}/provisional` - 暫定用語集一覧取得
- `GET /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語詳細取得
- `PATCH /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語更新（定義・confidence編集）
- `DELETE /api/projects/{project_id}/provisional/{entry_id}` - 暫定用語削除
- `POST /api/projects/{project_id}/provisional/{entry_id}/regenerate` - 単一エントリの再生成（LLM）

**Issues API (精査結果) - 2エンドポイント:**
- `GET /api/projects/{project_id}/issues` - 精査結果一覧取得（`issue_type` クエリパラメータでフィルタ可能）
- `GET /api/projects/{project_id}/issues/{issue_id}` - 精査結果詳細取得

**Refined API (最終用語集) - 5エンドポイント:**
- `GET /api/projects/{project_id}/refined` - 最終用語集一覧取得
- `GET /api/projects/{project_id}/refined/{term_id}` - 最終用語詳細取得
- `GET /api/projects/{project_id}/refined/export-md` - Markdownエクスポート
- `PATCH /api/projects/{project_id}/refined/{term_id}` - 最終用語更新
- `DELETE /api/projects/{project_id}/refined/{term_id}` - 最終用語削除

**Files API (ドキュメント管理) - 5エンドポイント:**
- `GET /api/projects/{project_id}/files` - ファイル一覧取得
- `GET /api/projects/{project_id}/files/{file_id}` - ファイル詳細取得
- `POST /api/projects/{project_id}/files` - ファイル追加
- `DELETE /api/projects/{project_id}/files/{file_id}` - ファイル削除
- `POST /api/projects/{project_id}/files/diff-scan` - ファイルシステムとDBの差分スキャン

**Projects API (プロジェクト管理) - 6エンドポイント:**
- `GET /api/projects` - プロジェクト一覧取得
- `GET /api/projects/{project_id}` - プロジェクト詳細取得
- `POST /api/projects` - プロジェクト作成
- `POST /api/projects/{project_id}/clone` - プロジェクトクローン
- `PATCH /api/projects/{project_id}` - プロジェクト設定更新
- `DELETE /api/projects/{project_id}` - プロジェクト削除

**Runs API (パイプライン実行管理) - 6エンドポイント:**
- `POST /api/projects/{project_id}/runs` - Run開始
- `DELETE /api/projects/{project_id}/runs/{run_id}` - Run キャンセル
- `GET /api/projects/{project_id}/runs` - Run履歴一覧
- `GET /api/projects/{project_id}/runs/{run_id}` - Run詳細取得
- `GET /api/projects/{project_id}/runs/current` - アクティブRun取得
- `GET /api/projects/{project_id}/runs/{run_id}/logs` - SSEログストリーミング

**合計: 38エンドポイント** (システム4 + Projects API 6 + データAPI 28)

## API実装のポイント

### 1. SQLiteスレッド安全性

FastAPIは非同期処理で複数のスレッドを使用するため、SQLite接続時に `check_same_thread=False` を指定しています。

```python
# db/connection.py
def get_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

### 2. 依存性注入の階層化

プロジェクト固有のDB接続は、レジストリDB接続とプロジェクト取得に依存する3段階の依存関係を構成しています。

```
get_registry_db()
    ↓ Depends
get_project_by_id(registry_conn)
    ↓ Depends
get_project_db(project)
```

### 3. スキーマのファクトリーメソッド

全てのレスポンススキーマに `from_db_row()` / `from_db_rows()` クラスメソッドを実装し、DB行からモデルへの変換ロジックを統一しています。

```python
class TermResponse(BaseModel):
    @classmethod
    def from_db_row(cls, row: Any) -> "TermResponse":
        """Create from database row."""
        return cls(
            id=row["id"],
            term_text=row["term_text"],
            category=row["category"],
        )

    @classmethod
    def from_db_rows(cls, rows: list[Any]) -> list["TermResponse"]:
        """Create list from database rows."""
        return [cls.from_db_row(row) for row in rows]
```

### 4. 型注釈の工夫

DB行の型は `sqlite3.Row` と `TypedDict` (GlossaryTermRow) の両方があるため、`from_db_row()` のパラメータ型には `Any` を使用しています。

### 5. ルーティング順序

FastAPIは定義順にルートをマッチングするため、`/export-md` のような固定パスは `/{term_id}` のようなパス パラメータより先に定義する必要があります。

```python
# refined.py
@router.get("/export-md", ...)  # 先に定義
async def export_markdown(...):
    ...

@router.get("/{term_id}", ...)  # 後に定義
async def get_refined_by_id(...):
    ...
```

### 6. リクエストボディのアノテーション

FastAPIでは、パスパラメータとリクエストボディを組み合わせる場合、明示的に `Body()` アノテーションが必要です。

```python
async def create_new_term(
    project_id: int = Path(...),           # パスパラメータ
    request: TermCreateRequest = Body(...), # リクエストボディ（明示的）
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> TermResponse:
    ...
```

### 7. HTTPステータスコード

RESTful APIの慣習に従ったステータスコードを返却しています。

- `200 OK` - GETリクエストの成功、PATCH/PUTの成功
- `201 Created` - POSTでリソース作成成功
- `204 No Content` - DELETEでリソース削除成功
- `404 Not Found` - リソースが見つからない（`get_project_by_id` が自動的に返却）
