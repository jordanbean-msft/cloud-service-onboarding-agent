import asyncio
import contextvars

# Create a context variable to store request-specific data
chat_context_var = contextvars.ContextVar("chat_context")

# Function to initialize the context (per request)


def build_chat_context():
    queue = asyncio.Queue()

    async def emit_event(event):
        await queue.put(event)

    async def close():
        await queue.put(None)  # Signals to close the stream

    return emit_event, close, queue


__all__ = [
    "chat_context_var",
    "build_chat_context",
]
