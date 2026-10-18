"""Reject oversized bodies before JSON decoding, including chunked uploads."""
from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self, app, limit=150000):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            size += len(event.get('body', b''))
            if size > self.limit:
                return await JSONResponse({'detail': 'Request is too large.'}, status_code=413)(scope, receive, send)
            chunks.append(event)
            if not event.get('more_body'):
                break

        async def replay():
            if chunks:
                return chunks.pop(0)
            return await receive()
        await self.app(scope, replay, send)
