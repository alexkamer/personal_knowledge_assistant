"""
Chat endpoints for RAG-powered question answering.
"""
import json
import logging
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
)
from app.services.conversation_service import ConversationService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


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

        # Retrieve relevant context using RAG
        rag_service = get_rag_service()
        context, citations = await rag_service.retrieve_and_assemble(
            db=db,
            query=request.message,
            top_k=request.top_k,
            include_web_search=request.include_web_search,
        )

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

        return ChatResponse(
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id),
            response=response_text,
            sources=citations,
            model_used=assistant_message.model_used or "",
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
                title = request.conversation_title or f"Chat about: {request.message[:50]}"
                conversation_data = ConversationCreate(title=title)
                conversation = await ConversationService.create_conversation(
                    db, conversation_data
                )

            # Send conversation ID immediately
            yield f'data: {json.dumps({"type": "conversation_id", "conversation_id": str(conversation.id)})}\n\n'

            # Add user message
            user_message = await ConversationService.add_message(
                db=db,
                conversation_id=str(conversation.id),
                role="user",
                content=request.message,
            )

            # Retrieve relevant context using RAG
            rag_service = get_rag_service()
            context, citations = await rag_service.retrieve_and_assemble(
                db=db,
                query=request.message,
                top_k=request.top_k,
                include_web_search=request.include_web_search,
            )

            # Send sources
            yield f'data: {json.dumps({"type": "sources", "sources": citations})}\n\n'

            # Get conversation history
            messages = await ConversationService.get_conversation_messages(
                db, str(conversation.id)
            )
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages[:-1]  # Exclude the message we just added
            ]

            # Generate streaming response
            llm_service = get_llm_service()
            stream = await llm_service.generate_answer(
                query=request.message,
                context=context,
                conversation_history=conversation_history,
                model=request.model,
                stream=True,
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
    List all conversations with pagination.
    """
    conversations, total = await ConversationService.list_conversations(
        db, skip=skip, limit=limit
    )

    return ConversationListResponse(
        conversations=[
            ConversationResponse.model_validate(conv) for conv in conversations
        ],
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

    # Parse sources from retrieved_chunks
    message_responses = []
    for msg in messages:
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
