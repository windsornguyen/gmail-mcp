# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Gmail API tools for gmail-mcp.

Read and manage Gmail via the Gmail REST API.
Ref: https://developers.google.com/workspace/gmail/api/guides
"""

import base64
import json
from email.mime.text import MIMEText
from typing import Any

from mcp.types import TextContent, Tool

from dedalus_mcp.types import ToolAnnotations

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys

# -----------------------------------------------------------------------------
# Connection
# -----------------------------------------------------------------------------

gmail = Connection(
    name="gmail",
    secrets=SecretKeys(token="GMAIL_ACCESS_TOKEN"),
    base_url="https://gmail.googleapis.com",
    auth_header_format="Bearer {api_key}",
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

GmailResult = list[TextContent]


async def _req(method: HttpMethod, path: str, body: dict | None = None) -> GmailResult:
    """Make a Gmail API request and return JSON as TextContent."""
    ctx = get_context()
    resp = await ctx.dispatch("gmail", HttpRequest(method=method, path=path, body=body))
    if resp.success:
        data = resp.response.body or {}
        return [TextContent(type="text", text=json.dumps(data, indent=2))]
    error = resp.error.message if resp.error else "Request failed"
    return [TextContent(type="text", text=json.dumps({"error": error}, indent=2))]


def _create_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """Create a base64url encoded email message."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


# -----------------------------------------------------------------------------
# Message Tools
# -----------------------------------------------------------------------------


@tool(
    description="List messages in the user's Gmail mailbox. Supports search queries like 'from:example@gmail.com is:unread'.",
    tags=["message", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_list_messages(
    query: str = "",
    max_results: int = 10,
    label_ids: str = "",
    include_spam_trash: bool = False,
) -> GmailResult:
    """List messages with optional filtering."""
    params = [f"maxResults={max_results}"]
    if query:
        params.append(f"q={query}")
    if label_ids:
        for label in label_ids.split(","):
            params.append(f"labelIds={label.strip()}")
    if include_spam_trash:
        params.append("includeSpamTrash=true")

    query_string = "&".join(params)
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/messages?{query_string}")


@tool(
    description="Get a specific message by ID. Returns full message content including headers and body.",
    tags=["message", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_get_message(
    message_id: str,
    format: str = "full",
) -> GmailResult:
    """Get a message by ID. Format: full, metadata, minimal, or raw."""
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/messages/{message_id}?format={format}")


@tool(
    description="Send an email message to specified recipients.",
    tags=["message", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_send_message(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> GmailResult:
    """Send an email. Returns the sent message metadata."""
    raw = _create_message(to, subject, body, cc, bcc)
    return await _req(HttpMethod.POST, "/gmail/v1/users/me/messages/send", {"raw": raw})


@tool(
    description="Move a message to trash.",
    tags=["message", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_trash_message(message_id: str) -> GmailResult:
    """Move a message to trash."""
    return await _req(HttpMethod.POST, f"/gmail/v1/users/me/messages/{message_id}/trash")


@tool(
    description="Remove a message from trash.",
    tags=["message", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_untrash_message(message_id: str) -> GmailResult:
    """Remove a message from trash."""
    return await _req(HttpMethod.POST, f"/gmail/v1/users/me/messages/{message_id}/untrash")


@tool(
    description="Modify labels on a message. Add or remove labels like INBOX, STARRED, IMPORTANT, etc.",
    tags=["message", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_modify_message(
    message_id: str,
    add_label_ids: str = "",
    remove_label_ids: str = "",
) -> GmailResult:
    """Modify labels on a message."""
    body: dict[str, Any] = {}
    if add_label_ids:
        body["addLabelIds"] = [l.strip() for l in add_label_ids.split(",")]
    if remove_label_ids:
        body["removeLabelIds"] = [l.strip() for l in remove_label_ids.split(",")]
    return await _req(HttpMethod.POST, f"/gmail/v1/users/me/messages/{message_id}/modify", body)


# -----------------------------------------------------------------------------
# Thread Tools
# -----------------------------------------------------------------------------


@tool(
    description="List email threads (conversations) in the user's mailbox.",
    tags=["thread", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_list_threads(
    query: str = "",
    max_results: int = 10,
    label_ids: str = "",
) -> GmailResult:
    """List threads with optional filtering."""
    params = [f"maxResults={max_results}"]
    if query:
        params.append(f"q={query}")
    if label_ids:
        for label in label_ids.split(","):
            params.append(f"labelIds={label.strip()}")

    query_string = "&".join(params)
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/threads?{query_string}")


@tool(
    description="Get a specific thread (conversation) by ID with all its messages.",
    tags=["thread", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_get_thread(
    thread_id: str,
    format: str = "full",
) -> GmailResult:
    """Get a thread by ID."""
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/threads/{thread_id}?format={format}")


@tool(
    description="Move an entire thread to trash.",
    tags=["thread", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_trash_thread(thread_id: str) -> GmailResult:
    """Move a thread to trash."""
    return await _req(HttpMethod.POST, f"/gmail/v1/users/me/threads/{thread_id}/trash")


# -----------------------------------------------------------------------------
# Label Tools
# -----------------------------------------------------------------------------


@tool(
    description="List all labels in the user's mailbox including system labels (INBOX, SENT, etc.) and user-created labels.",
    tags=["label", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_list_labels() -> GmailResult:
    """List all labels."""
    return await _req(HttpMethod.GET, "/gmail/v1/users/me/labels")


@tool(
    description="Get details about a specific label by ID.",
    tags=["label", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_get_label(label_id: str) -> GmailResult:
    """Get a label by ID."""
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/labels/{label_id}")


@tool(
    description="Create a new user label.",
    tags=["label", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_create_label(
    name: str,
    label_list_visibility: str = "labelShow",
    message_list_visibility: str = "show",
) -> GmailResult:
    """Create a new label."""
    body = {
        "name": name,
        "labelListVisibility": label_list_visibility,
        "messageListVisibility": message_list_visibility,
    }
    return await _req(HttpMethod.POST, "/gmail/v1/users/me/labels", body)


@tool(
    description="Delete a user-created label. System labels cannot be deleted.",
    tags=["label", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_delete_label(label_id: str) -> GmailResult:
    """Delete a label."""
    return await _req(HttpMethod.DELETE, f"/gmail/v1/users/me/labels/{label_id}")


# -----------------------------------------------------------------------------
# Draft Tools
# -----------------------------------------------------------------------------


@tool(
    description="List draft emails.",
    tags=["draft", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_list_drafts(max_results: int = 10) -> GmailResult:
    """List drafts."""
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/drafts?maxResults={max_results}")


@tool(
    description="Get a specific draft by ID.",
    tags=["draft", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_get_draft(draft_id: str, format: str = "full") -> GmailResult:
    """Get a draft by ID."""
    return await _req(HttpMethod.GET, f"/gmail/v1/users/me/drafts/{draft_id}?format={format}")


@tool(
    description="Create a new draft email.",
    tags=["draft", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_create_draft(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> GmailResult:
    """Create a draft email."""
    raw = _create_message(to, subject, body, cc, bcc)
    return await _req(HttpMethod.POST, "/gmail/v1/users/me/drafts", {"message": {"raw": raw}})


@tool(
    description="Send a draft email.",
    tags=["draft", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_send_draft(draft_id: str) -> GmailResult:
    """Send a draft."""
    return await _req(HttpMethod.POST, "/gmail/v1/users/me/drafts/send", {"id": draft_id})


@tool(
    description="Delete a draft.",
    tags=["draft", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def gmail_delete_draft(draft_id: str) -> GmailResult:
    """Delete a draft."""
    return await _req(HttpMethod.DELETE, f"/gmail/v1/users/me/drafts/{draft_id}")


# -----------------------------------------------------------------------------
# Profile Tools
# -----------------------------------------------------------------------------


@tool(
    description="Get the current user's Gmail profile including email address and message/thread counts.",
    tags=["profile", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def gmail_get_profile() -> GmailResult:
    """Get the user's Gmail profile."""
    return await _req(HttpMethod.GET, "/gmail/v1/users/me/profile")


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------

gmail_tools: list[Tool] = [
    # Messages
    gmail_list_messages,
    gmail_get_message,
    gmail_send_message,
    gmail_trash_message,
    gmail_untrash_message,
    gmail_modify_message,
    # Threads
    gmail_list_threads,
    gmail_get_thread,
    gmail_trash_thread,
    # Labels
    gmail_list_labels,
    gmail_get_label,
    gmail_create_label,
    gmail_delete_label,
    # Drafts
    gmail_list_drafts,
    gmail_get_draft,
    gmail_create_draft,
    gmail_send_draft,
    gmail_delete_draft,
    # Profile
    gmail_get_profile,
]
