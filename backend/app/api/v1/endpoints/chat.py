"""
Chat endpoints for RAG-powered question answering.
"""
import json
import logging
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageResponse,
    MessageFeedbackCreate,
    MessageFeedbackResponse,
)
from app.services.conversation_service import ConversationService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.services.rag_orchestrator import get_rag_orchestrator
from app.services.agent_service import get_agent_service
from app.utils.token_counter import get_token_counter

logger = logging.getLogger(__name__)
router = APIRouter()


def _is_conversational_query(query: str) -> bool:
    """
    Detect if a query is conversational (referencing previous context)
    rather than a new information request.

    Args:
        query: User's query text

    Returns:
        True if query appears to be conversational, False otherwise
    """
    query_lower = query.lower().strip()

    # Very short queries are likely conversational
    if len(query_lower.split()) <= 3:
        # Check for conversational patterns
        conversational_patterns = [
            r'\bthat\b',
            r'\bit\b',
            r'\bthis\b',
            r'\bthese\b',
            r'\bthose\b',
            r'^(and|but|so|also|then|now|plus|minus|add|subtract|multiply|divide)',
            r'\b(more|tell me more|continue|go on|what about|how about)\b',
            r'^(what|where|when|who|why|how).*\b(it|that|this|they|them)\b',
            r'\bmy\s+(name|age|job|profession)\b',
            r'(what|who).*\b(am i|is my|are my)\b',
        ]

        for pattern in conversational_patterns:
            if re.search(pattern, query_lower):
                return True

    return False


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send a message and get an AI-powered response using RAG.

    Creates a new conversation if conversation_id is not provided.
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = await ConversationService.get_conversation(
                db, request.conversation_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )
        else:
            # Create new conversation
            title = request.conversation_title or f"Chat about: {request.message[:50]}"
            conversation_data = ConversationCreate(title=title)
            conversation = await ConversationService.create_conversation(
                db, conversation_data
            )

        # Add user message
        user_message = await ConversationService.add_message(
            db=db,
            conversation_id=str(conversation.id),
            role="user",
            content=request.message,
        )

        # Calculate and store token count for user message
        token_counter = get_token_counter()
        user_message.token_count = token_counter.count_tokens(request.message)
        await db.commit()
        await db.refresh(user_message)

        # Check if this is a conversational follow-up query
        is_conversational = _is_conversational_query(request.message)

        # Retrieve relevant context using RAG (skip for conversational queries)
        context = ""
        citations = []
        if not is_conversational:
            rag_service = get_rag_service()
            context, citations = await rag_service.retrieve_and_assemble(
                db=db,
                query=request.message,
                top_k=request.top_k,
                include_web_search=request.include_web_search,
            )
        else:
            logger.info("Detected conversational query, skipping RAG retrieval")

        # Get conversation history
        messages = await ConversationService.get_conversation_messages(
            db, str(conversation.id)
        )
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]  # Exclude the message we just added
        ]

        # Generate response using LLM
        llm_service = get_llm_service()
        response_text = await llm_service.generate_answer(
            query=request.message,
            context=context,
            conversation_history=conversation_history,
            model=request.model,
            stream=False,
        )

        # Add assistant message with citations
        assistant_message = await ConversationService.add_message(
            db=db,
            conversation_id=str(conversation.id),
            role="assistant",
            content=response_text,
            retrieved_chunks=citations,
            model_used=request.model or llm_service.primary_model,
        )

        # Generate suggested follow-up questions
        suggested_questions = await llm_service.generate_follow_up_questions(
            query=request.message,
            answer=response_text,
            context=context,
            model=request.model,
        )

        # Calculate and store token count for assistant message
        assistant_message.token_count = token_counter.count_tokens(response_text)

        # Update the message with suggested questions and token count
        if suggested_questions:
            assistant_message.suggested_questions = suggested_questions

        await db.commit()
        await db.refresh(assistant_message)

        return ChatResponse(
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id),
            response=response_text,
            sources=citations,
            model_used=assistant_message.model_used or "",
            suggested_questions=suggested_questions if suggested_questions else None,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)}",
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Send a message and get a streaming AI-powered response using RAG.

    Returns Server-Sent Events (SSE) stream with chunks of the response.
    """

    async def generate_stream():
        """Generator function for streaming response."""
        try:
            # Parse agent mention from message
            agent_service = get_agent_service()
            agent_name, clean_message = agent_service.parse_agent_mention(request.message)
            agent_config = agent_service.get_agent(agent_name)

            # Get or create conversation
            if request.conversation_id:
                conversation = await ConversationService.get_conversation(
                    db, request.conversation_id
                )
                if not conversation:
                    yield f'data: {json.dumps({"error": "Conversation not found"})}\n\n'
                    return
            else:
                # Create new conversation
                title = request.conversation_title or f"Chat about: {clean_message[:50]}"
                conversation_data = ConversationCreate(title=title)
                conversation = await ConversationService.create_conversation(
                    db, conversation_data
                )

            # Send conversation ID immediately
            yield f'data: {json.dumps({"type": "conversation_id", "conversation_id": str(conversation.id)})}\n\n'

            # Send agent info
            yield f'data: {json.dumps({"type": "agent", "agent": {"name": agent_config.name, "display_name": agent_config.display_name, "description": agent_config.description}})}\n\n'

            # Add user message (with original message including @ mention)
            user_message = await ConversationService.add_message(
                db=db,
                conversation_id=str(conversation.id),
                role="user",
                content=request.message,  # Keep original with @ mention
            )

            # Calculate and store token count for user message
            token_counter = get_token_counter()
            user_message.token_count = token_counter.count_tokens(request.message)
            await db.commit()
            await db.refresh(user_message)

            # Check if this is a conversational follow-up query
            is_conversational = _is_conversational_query(clean_message)

            # Retrieve relevant context using RAG Orchestrator (skip for conversational queries)
            context = ""
            citations = []
            metadata = {}
            if not is_conversational and agent_config.use_rag:
                orchestrator = get_rag_orchestrator()
                context, citations, metadata = await orchestrator.process_query(
                    db=db,
                    query=clean_message,  # Use clean message without @ mention
                    force_web_search=request.include_web_search if request.include_web_search is not None else None,
                    top_k=agent_config.rag_top_k,  # Use agent's RAG settings
                )
            else:
                if is_conversational:
                    logger.info("Detected conversational query, skipping RAG retrieval")
                    metadata = {"query_type": "conversational"}
                else:
                    logger.info(f"Agent {agent_config.name} has RAG disabled")
                    metadata = {"query_type": "no_rag"}

            # Send sources with metadata
            sources_data = {
                "type": "sources",
                "sources": citations,
                "metadata": metadata  # Include query type, complexity, etc.
            }
            yield f'data: {json.dumps(sources_data)}\n\n'

            # Get conversation history (limit based on agent config)
            messages = await ConversationService.get_conversation_messages(
                db, str(conversation.id)
            )
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages[:-1]  # Exclude the message we just added
            ][-agent_config.max_conversation_history:]  # Limit based on agent

            # Generate streaming response using agent config
            llm_service = get_llm_service()
            stream = await llm_service.generate_answer(
                query=clean_message,  # Use clean message without @ mention
                context=context,
                conversation_history=conversation_history,
                model=request.model or agent_config.model,  # Use agent's model if not specified
                stream=True,
                temperature=agent_config.temperature,  # Use agent's temperature
                system_prompt=agent_config.system_prompt,  # Use agent's system prompt
            )

            # Collect full response while streaming
            full_response = []
            async for chunk in stream:
                if chunk:
                    full_response.append(chunk)
                    yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'

            # Save complete message to database
            complete_response = "".join(full_response)
            assistant_message = await ConversationService.add_message(
                db=db,
                conversation_id=str(conversation.id),
                role="assistant",
                content=complete_response,
                retrieved_chunks=citations,
                model_used=request.model or llm_service.primary_model,
            )

            # Generate suggested follow-up questions
            suggested_questions = await llm_service.generate_follow_up_questions(
                query=request.message,
                answer=complete_response,
                context=context,
                model=request.model,
            )

            # Calculate and store token count for assistant message
            assistant_message.token_count = token_counter.count_tokens(complete_response)

            # Update the message with suggested questions and token count
            if suggested_questions:
                assistant_message.suggested_questions = suggested_questions

            await db.commit()
            await db.refresh(assistant_message)

            # Send suggested questions to client
            if suggested_questions:
                yield f'data: {json.dumps({"type": "suggested_questions", "questions": suggested_questions})}\n\n'

            # Send completion event
            yield f'data: {json.dumps({"type": "done", "message_id": str(assistant_message.id)})}\n\n'

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/conversations/", response_model=ConversationListResponse)
async def list_conversations(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    List all conversations with pagination, including message counts.
    """
    conversations_with_counts, total = await ConversationService.list_conversations(
        db, skip=skip, limit=limit
    )

    conversation_responses = []
    for conv, message_count in conversations_with_counts:
        conv_response = ConversationResponse.model_validate(conv)
        conv_response.message_count = message_count
        conversation_responses.append(conv_response)

    return ConversationListResponse(
        conversations=conversation_responses,
        total=total,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationWithMessages:
    """
    Get a conversation with its full message history.
    """
    conversation = await ConversationService.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = await ConversationService.get_conversation_messages(db, conversation_id)

    # Eagerly load feedback for each message
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.conversation import Message

    # Reload messages with feedback eagerly loaded
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.feedback))
        .order_by(Message.created_at)
    )
    messages_with_feedback = result.scalars().all()

    # Parse sources from retrieved_chunks
    message_responses = []
    for msg in messages_with_feedback:
        sources = None
        if msg.retrieved_chunks:
            try:
                sources = json.loads(msg.retrieved_chunks)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse retrieved_chunks for message {msg.id}")

        message_response = MessageResponse.model_validate(msg)
        message_response.sources = sources
        message_responses.append(message_response)

    # Create response dict manually to avoid lazy loading issues
    response = ConversationWithMessages(
        id=str(conversation.id),
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(messages),
        messages=message_responses,
    )

    return response


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """
    Update a conversation (title or summary).
    """
    conversation = await ConversationService.update_conversation(
        db, conversation_id, conversation_data
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a conversation and all its messages.
    """
    deleted = await ConversationService.delete_conversation(db, conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.get("/chunks/{chunk_id}")
async def get_chunk(
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get chunk content and metadata by chunk ID.
    """
    from sqlalchemy import select
    from app.models.chunk import Chunk
    from app.models.note import Note
    from app.models.document import Document

    # Get the chunk
    result = await db.execute(select(Chunk).where(Chunk.id == chunk_id))
    chunk = result.scalar_one_or_none()

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found",
        )

    # Get source information
    source_title = ""
    source_type = ""
    metadata = {}

    if chunk.note_id:
        result = await db.execute(select(Note).where(Note.id == chunk.note_id))
        note = result.scalar_one_or_none()
        if note:
            source_title = note.title
            source_type = "note"
            metadata = {
                "note_id": str(note.id),
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            }
    elif chunk.document_id:
        result = await db.execute(select(Document).where(Document.id == chunk.document_id))
        document = result.scalar_one_or_none()
        if document:
            source_title = document.title
            source_type = "document"
            metadata = {
                "document_id": str(document.id),
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "created_at": document.created_at.isoformat(),
            }

    return {
        "id": str(chunk.id),
        "content": chunk.content,
        "chunk_index": chunk.chunk_index,
        "token_count": chunk.token_count,
        "source_title": source_title,
        "source_type": source_type,
        "metadata": metadata,
    }


@router.post("/messages/{message_id}/feedback", response_model=MessageFeedbackResponse)
async def submit_message_feedback(
    message_id: str,
    feedback: MessageFeedbackCreate,
    db: AsyncSession = Depends(get_db),
) -> MessageFeedbackResponse:
    """
    Submit feedback (thumbs up/down) for a message.
    """
    from sqlalchemy import select
    from app.models.conversation import Message
    from app.models.message_feedback import MessageFeedback

    # Check if message exists
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Check if feedback already exists
    result = await db.execute(
        select(MessageFeedback).where(MessageFeedback.message_id == message_id)
    )
    existing_feedback = result.scalar_one_or_none()

    if existing_feedback:
        # Update existing feedback
        existing_feedback.is_positive = feedback.is_positive
        existing_feedback.comment = feedback.comment
        await db.commit()
        await db.refresh(existing_feedback)
        return MessageFeedbackResponse.model_validate(existing_feedback)
    else:
        # Create new feedback
        new_feedback = MessageFeedback(
            message_id=message_id,
            is_positive=feedback.is_positive,
            comment=feedback.comment,
        )
        db.add(new_feedback)
        await db.commit()
        await db.refresh(new_feedback)
        return MessageFeedbackResponse.model_validate(new_feedback)


@router.get("/agents")
async def list_agents() -> list[dict]:
    """
    List available AI agents with their configurations.
    """
    agent_service = get_agent_service()
    return agent_service.list_available_agents()


@router.get("/conversations/{conversation_id}/token-usage")
async def get_conversation_token_usage(
    conversation_id: str,
    model: str = Query(default="qwen2.5:14b", description="Model to calculate context limits for"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get token usage statistics for a conversation.

    Returns:
        - total_tokens: Total tokens used in conversation
        - messages_count: Number of messages
        - limit: Model's context window limit
        - usage_percent: Percentage of context used
        - remaining: Tokens remaining
        - is_warning: True if > 70% used
        - is_critical: True if > 90% used
        - message_tokens: List of token counts per message
    """
    # Get conversation messages
    messages = await ConversationService.get_conversation_messages(db, conversation_id)

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or has no messages",
        )

    # Calculate token usage
    token_counter = get_token_counter()

    # Get individual message token counts
    message_tokens = []
    total_tokens = 0

    for msg in messages:
        # Use stored token count if available, otherwise calculate
        tokens = msg.token_count if msg.token_count else token_counter.count_tokens(msg.content)
        message_tokens.append({
            "message_id": str(msg.id),
            "role": msg.role,
            "tokens": tokens,
            "created_at": msg.created_at.isoformat(),
        })
        total_tokens += tokens

    # Get usage statistics
    usage_stats = token_counter.estimate_context_usage(
        messages=[{"role": msg.role, "content": msg.content} for msg in messages],
        model=model,
    )

    return {
        **usage_stats,
        "messages_count": len(messages),
        "message_tokens": message_tokens,
    }
