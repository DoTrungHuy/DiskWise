"""Pydantic models for the local DiskWise API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    path: str


class ExtractResponse(BaseModel):
    ok: bool
    content_type: str
    content_preview: str
    extractor: str
    error: str | None = None


class CategoryPlanRequest(BaseModel):
    target_root: str = Field(alias="targetRoot")


class ExecutePlanRequest(BaseModel):
    selected_item_ids: list[int] = Field(default_factory=list, alias="selectedItemIds")
    confirmation: str


class UndoOperationRequest(BaseModel):
    confirmation: str
