from functools import wraps
from typing import Optional
from pathlib import Path
import shutil
from typing import List

from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
import identity
import identity.web

from db import (
    get_current_user_by_email, insert_new_user, insert_new_question, get_questions, get_questions_by_doc,
    get_current_user, create_access_token, get_conn, close_conn, get_current_user_email, delete_question,
    insert_bulk_questions, get_system_prompt, get_dummy_message_data,get_empty_questions,get_empty_system_prompt,insert_default_bulk_questions
)
from config import (
    MICROSOFT_AUTHORITY, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_SCOPE,
    MICROSOFT_REDIRECT_URI, FRONTEND_URL, SECRET_KEY, BUILD_PATH,ALLOWED_TENANTS,BATCH_SIZE,OPENAI_RESOURCES
)
from file_handler import save_file_to_search
from search import call_large_model, search_documents, delete_documents_by_request_id

# initialize API
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=f"{BUILD_PATH}/static"), name="static")
app.mount("/assets", StaticFiles(directory=f"{BUILD_PATH}/assets"), name="assets")
templates = Jinja2Templates(directory=BUILD_PATH)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


class UsersInput(BaseModel):
    user_fullname: Optional[str]
    user_email: str

class PromptInput(BaseModel):
    question_id: Optional[int]
    doc_type: int
    question: str

class BulkPromptInput(BaseModel):
    questions: list[PromptInput]
    system_prompt: str
    system_prompt_two: str

def auth_required(func):
    @wraps(func)
    def wrapper(request: Request, *args, **kwargs):
        usr_email = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
        if usr_email:
            return func(request=request, *args, **kwargs)
    return wrapper

@app.get('/api/')
def get_func():
    return {'text': 'hello world'}, 200

# Dictionary to store file counts for each request ID
file_counts = {}
@app.post('/api/upload/{request_id}')
async def upload_files(file: List[UploadFile] = File(...), request_id: str = None):
    """
    Upload files to the server and keep track of the number of files uploaded for each request ID.
    """
    if request_id not in file_counts:
        file_counts[request_id] = 0
    Path(f"uploads/{request_id}").mkdir(parents=True, exist_ok=True)
    for i in file:
        file_counts[request_id] += 1
        print(f"Request ID: {request_id}, File Count: {file_counts[request_id]}, File Name: {i.filename}")
        with open(Path(f"uploads/{request_id}") / i.filename, "wb") as buffer:
            shutil.copyfileobj(i.file, buffer)
        save_file_to_search(f"uploads/{request_id}/{i.filename}", request_id)
    return {"message": "files uploaded successfully", "file_count": file_counts[request_id]}

@app.get('/api/prompt')
# @auth_required
async def get_prompt_for_user(request: Request):
    """
    get prompt for the user
    curl -X GET "http://localhost:8000/api/prompt" -H  "Content-Type: application/json" -H  ""
    """
    usr_email = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
    conn, cursor = get_conn()
    questions = get_questions(cursor, usr_email)
    system_prompt = get_system_prompt(cursor, usr_email)
    close_conn(conn, cursor)
    return {"result": questions if len(questions) > 0 else get_dummy_message_data(), "system_prompt": system_prompt}

@app.post('/api/prompt')
# @auth_required
async def post_prompt_for_user(request: Request, question: PromptInput):
    """
    post prompt for the user
    curl -X POST "http://localhost:8000/api/prompt" -H  "Content-Type: application/json" -H  "Authorization" -d '{"question_id": 0, "doc_type":1, "question":"What is the purpose of the document?"}'
    """
    usr_email:str = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
    conn, cursor = get_conn()
    questions = insert_new_question(cursor, usr_email, question.doc_type, question.question, question.question_id)
    close_conn(conn, cursor)
    return {"result": questions}

@app.post('/api/prompt/bulk')
# @auth_required
async def post_bulk_prompt_for_user(request: Request, input: BulkPromptInput):
    """
    post prompt for the user
    curl -X POST "http://localhost:8000/api/prompt/bulk" -H  "Content-Type: application/json" -H  "" -d '{"questions": [{"question_id": 0, "doc_type":1, "question":"What is the purpose of the document?"}], "system_prompt": "What is the purpose of the document?"}'
    """
    usr_email:str = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
    conn, cursor = get_conn()
    result = insert_bulk_questions(cursor, usr_email, input.questions, input.system_prompt, input.system_prompt_two)
    close_conn(conn, cursor)
    return {"result": result[0], "system_prompt": result[1]}

@app.delete('/api/prompt/{question_id}')
# @auth_required
async def delete_prompt_for_user(request: Request, question_id: int = None):
    """
    delete prompt for the user
    """
    usr_email = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
    conn, cursor = get_conn()
    questions = delete_question(cursor, usr_email, question_id)
    close_conn(conn, cursor)
    return {"result": questions}

@app.get('/api/summary')
# @auth_required
async def get_summary(request: Request, request_id: str = None, document_type: str = None, language: str = None):
   
    usr_email = get_current_user_email(request.headers.get('Authorization').split(' ')[1])
    conn, cursor = get_conn()
    questions = get_questions_by_doc(cursor, usr_email, document_type)
    system_prompt = get_system_prompt(cursor, usr_email)
    system_prompt = system_prompt[0]["Prompt"] if document_type == "1" else system_prompt[0]["PromptTwo"]
    questions = questions if len(questions) > 0 else get_dummy_message_data([document_type])
    close_conn(conn, cursor)

    my_questions = [x["Question"] for x in questions if x["Question"].strip() != '']
    if not my_questions:
        return {"result": [{}]}
    summary = []
    batch_size = BATCH_SIZE
    num_resources = len(OPENAI_RESOURCES)
    # Process each batch with respective OpenAI resource
    for batch_index in range(0, len(my_questions), batch_size):
        query_context = ''
        batch = my_questions[batch_index:batch_index + batch_size]
        resource_index = (batch_index // batch_size) % num_resources  # Get resource index in a round-robin manner
        resource = OPENAI_RESOURCES[resource_index]
        for question in batch:
            print(f"Question: {question}")
            results = search_documents(request_id, question)
            for result in results:
                page_number = result['Seitenzahl']
                query_context += f"Question {question}:\n```\nSeitenzahl: {page_number}\nDateiname: {result['Dateiname']}\n{result['text']}\n```\n"
        messages = [
            {"role": "system", "content": f"Bitte befolgen Sie unbedingt die Anweisungen zu jeder Frage:\n{system_prompt}\n\nCONTENT:\n{query_context}\nEND OF CONTENT\n"}
        ]

        answer = call_large_model(messages, resource)
        summary.append({"answer": answer})
    delete_documents_by_request_id(request_id)
    return {"result": summary}

@app.get('/api/me',status_code=200)
@auth_required
def get_my_info(request: Request):
    """
    returns the current user details
    """
    current_user: UsersInput = get_current_user(request.headers.get('Authorization').split(' ')[1])
    return {"user": current_user}

def get_auth_instance(session):
    auth = identity.web.Auth(
        session=session,
        authority=MICROSOFT_AUTHORITY,
        client_id=MICROSOFT_CLIENT_ID,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )
    return auth

@app.route('/api/microsoft/login')
def microsoft_login(request: Request):
    auth_instance = get_auth_instance(request.session)
    auth_object = auth_instance.log_in(
        scopes=MICROSOFT_SCOPE,
        redirect_uri=MICROSOFT_REDIRECT_URI
    )
    return RedirectResponse(auth_object["auth_uri"])

@app.route('/api/microsoft/callback')
def microsoft_callback(request: Request):
    auth_instance = get_auth_instance(request.session)
    user_info = auth_instance.complete_log_in(dict(request.query_params))
    # Extract tenant ID from the user info
    tenant_id = user_info["tid"]
    if "preferred_username" not in user_info:
        return JSONResponse({"error": "User info not found"}, status_code=400)
    # Validate the user's tenant
    if tenant_id not in ALLOWED_TENANTS:
        raise HTTPException(status_code=403, detail="Access to this tenant is not allowed")
    conn, cursor = get_conn()
    # check if user exists in the database
    our_user = get_current_user_by_email(cursor, user_info["preferred_username"])
    if our_user is None:
        insert_new_user(cursor, user_info["name"], user_info["preferred_username"])
    usr_email = user_info['preferred_username']
    conn, cursor = get_conn()
    questions = get_questions(cursor, usr_email)
    system_prompt = get_system_prompt(cursor, usr_email)
    if not questions and not system_prompt:
        questions = get_empty_questions(cursor, usr_email)
        system_prompt = get_empty_system_prompt(cursor, usr_email)
        for item in system_prompt:
            prompt= item["Prompt"]
            promptTwo = item["PromptTwo"]
        result = insert_default_bulk_questions(cursor, usr_email, questions, prompt, promptTwo)
    # Close database connection
    close_conn(conn, cursor)
    # get access token
    access_token = create_access_token(data={"sub": user_info["preferred_username"]})
    return RedirectResponse(f'{FRONTEND_URL}?token={access_token}&email={user_info["preferred_username"]}&name={user_info["name"]}')

@app.get("/")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/c/new")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/c/settings")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
