

import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from configuration import config
from web.schema import Question, Answer
from web.server import ChatService

app = FastAPI()
app.mount("/static", StaticFiles(directory=config.TEMPLATE_DIR), name="static")
service = ChatService()
@app.get('/')
def read_root():
    return RedirectResponse('/static/index.html')

@app.post('/chat')
def read_item(question:Question)->Answer:
    result = service.chat(question.message)
    return Answer(message=result)


def web_serve():
    uvicorn.run('web.app:app',host='0.0.0.0',port=8000)

if __name__ == '__main__':
    web_serve()