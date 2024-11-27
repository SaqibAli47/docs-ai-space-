from datetime import datetime, timedelta

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
import pyodbc

from config import SECRET_KEY, SQL_SERVER, SQL_DATABASE, SQL_UID, SQL_PWD, USER_PASSWORD

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 200000

def get_conn():
    conn = pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SQL_SERVER},1433;"
        f"Database={SQL_DATABASE};"
        f"Uid={SQL_UID};"
        f"Pwd={SQL_PWD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    cursor = conn.cursor()
    return conn, cursor

def close_conn(conn, cursor):
    cursor.close()
    conn.close()

def get_dummy_message_data(doc_types=[1, 2]):
    results = []
    for doc_type in doc_types:
        for index in [1, 2, 3, 4, 5]:
            results.append({
                "ID": 0,
                "QuestionIndex": index,
                "DocType": doc_type,
                "Question": f"Question {index}",
                "UserEmail": "mail@example.com",
                "CreatedAt": "2024-05-01T20:50:02.993333"
            })
    return results

def create_chat_table(project_name='Proposal'):
    sql_create_table = f"""CREATE TABLE {project_name}_Chat (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UserName NVARCHAR(50),
        Title NVARCHAR(64),
        CreatedAt DATETIME2 DEFAULT CURRENT_TIMESTAMP
    );"""
    return sql_create_table

def create_users_table():
    sql_create_table = """CREATE TABLE [dbo].[Users] (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        user_fullname NVARCHAR(50),
        user_email NVARCHAR(50),
        user_password NVARCHAR(50),
        CreatedAt DATETIME2 DEFAULT CURRENT_TIMESTAMP
    );"""
    return sql_create_table

def create_prompts_table():
    sql_create_table = """CREATE TABLE [dbo].[Prompts] (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        DocType INT,
        Question NVARCHAR(1000),
        UserEmail NVARCHAR(50),
        CreatedAt DATETIME2 DEFAULT CURRENT_TIMESTAMP
    );"""
    return sql_create_table

def create_system_prompts_table():
    sql_create_table = """CREATE TABLE [dbo].[SystemPrompts] (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Prompt NVARCHAR(4000),
        PromptTwo NVARCHAR(4000),
        UserEmail NVARCHAR(50),
        CreatedAt DATETIME2 DEFAULT CURRENT_TIMESTAMP
    );"""
    return sql_create_table

def create_message_table(project_name='Proposal'):
    sql_create_table = f"""CREATE TABLE {project_name}_Message (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        ChatID INT,
        Role NVARCHAR(16),
        Content NVARCHAR(4000),
        CreatedAt DATETIME2 DEFAULT CURRENT_TIMESTAMP
    );"""
    return sql_create_table

def get_data_by_query(query):
    conn, cursor = get_conn()
    cursor.execute(query)
    # convert the data into a list of dictionaries
    results = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    close_conn(conn, cursor)
    return results

def get_chat_data(project_name='Proposal'):
    query = f'SELECT TOP (10) * FROM [dbo].[{project_name}_Chat]'
    results = get_data_by_query(query)
    return results

def save_message_data(cursor, chat_id, role, content, project_name='Proposal'):
    cursor.execute(f'INSERT INTO [dbo].[{project_name}_Message] (ChatID, Role, Content) VALUES (?, ?, ?)', chat_id, role, content)
    cursor.commit()

def insert_new_user(cursor, user_fullname, user_email):
    cursor.execute('INSERT INTO [dbo].[Users] (user_fullname, user_email, user_password) VALUES (?, ?, ?)', user_fullname, user_email, USER_PASSWORD)
    cursor.commit()

def get_questions(cursor, user_email):
    cursor.execute('SELECT * FROM [dbo].[Prompts] WHERE UserEmail = ?', user_email)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_empty_questions(cursor, user_email):
    cursor.execute('SELECT * FROM [dbo].[Prompts] WHERE UserEmail is null')
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_system_prompt(cursor, user_email):
    cursor.execute('SELECT * FROM [dbo].[SystemPrompts] WHERE UserEmail = ?', user_email)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_empty_system_prompt(cursor, user_email):
    cursor.execute('SELECT * FROM [dbo].[SystemPrompts] WHERE UserEmail is null')
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def insert_new_system_prompt(cursor, user_email, prompt, prompt_two=''):
    cursor.execute('UPDATE [dbo].[SystemPrompts] SET Prompt=?, PromptTwo=? WHERE UserEmail=? IF @@ROWCOUNT = 0 INSERT INTO [dbo].[SystemPrompts] (Prompt, PromptTwo, UserEmail) VALUES (?, ?, ?)', prompt, prompt_two, user_email, prompt, prompt_two, user_email)
    cursor.commit()
    results = get_system_prompt(cursor, user_email)
    return results

def just_insert_question(cursor, user_email, doc_type, question, question_id=0):
    if question_id:
        # Check if any questions exist for the user
        cursor.execute('SELECT COUNT(*) FROM [dbo].[Prompts] WHERE UserEmail = ?', (user_email,))
        count = cursor.fetchone()[0]
        if count == 0 or question_id == 0:
            # If no questions exist or question_id is 0, insert the new question
            cursor.execute('INSERT INTO [dbo].[Prompts] (DocType, Question, UserEmail) VALUES (?, ?, ?)', (doc_type, question, user_email))
        else:
            # Update the question
            cursor.execute('UPDATE [dbo].[Prompts] SET Question = ? WHERE ID = ? AND UserEmail = ?', (question, question_id, user_email))
    else:
        cursor.execute('INSERT INTO [dbo].[Prompts] (DocType, Question, UserEmail) VALUES (?, ?, ?)', doc_type, question, user_email)
    cursor.commit()

def insert_bulk_questions(cursor, user_email, questions, system_prompt, system_prompt_two):
    for question in questions:
        just_insert_question(cursor, user_email, question.doc_type, question.question, question.question_id)
    prompt_result = insert_new_system_prompt(cursor, user_email, system_prompt, system_prompt_two)
    results = get_questions(cursor, user_email)
    return [results, prompt_result]

def insert_default_bulk_questions(cursor, user_email, questions, system_prompt, system_prompt_two):
    for question in questions:
        just_insert_question(cursor, user_email, question["DocType"], question["Question"], 0)
    prompt_result = insert_new_system_prompt(cursor, user_email, system_prompt, system_prompt_two)
    results = get_questions(cursor, user_email)
    return [results, prompt_result]

def insert_new_question(cursor, user_email, doc_type, question, question_id=0):
    just_insert_question(cursor, user_email, doc_type, question, question_id)
    # get all the questions for the user
    results = get_questions(cursor, user_email)
    return results

def delete_question(cursor, user_email, question_id):
    cursor.execute('DELETE FROM [dbo].[Prompts] WHERE ID = ? AND UserEmail = ?', question_id, user_email)
    cursor.commit()
    results = get_questions(cursor, user_email)
    return results

def get_questions_by_doc(cursor, user_email, doc_type):
    cursor.execute('SELECT * FROM [dbo].[Prompts] WHERE UserEmail = ? AND DocType = ?', user_email, doc_type)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_user_data(cursor, user_email):
    cursor.execute('SELECT TOP (1) * FROM [dbo].[Users] WHERE user_email = ?', user_email)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_current_user_by_email(cursor, email: str):
    cursor.execute('SELECT TOP (1) * FROM [dbo].[Users] WHERE user_email = ?', email)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results[0] if results else {}

def save_chat_data(cursor, username, title="New Chat", project_name='Proposal'):
    cursor.execute(f'INSERT INTO [dbo].[{project_name}_Chat] (UserName, Title) VALUES (?, ?)', username, title)
    cursor.commit()
    cursor.execute(f'SELECT IDENT_CURRENT(\'{project_name}_Chat\')')
    chat_id = cursor.fetchone()[0]
    return chat_id

def get_message_data(cursor, chat_id, project_name='Proposal'):
    cursor.execute(f'SELECT TOP (100) * FROM [dbo].[{project_name}_Message] WHERE ChatID = ?', chat_id)
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def handle_message_data(chat_id, role, content, username='mkrnaqeebi', title='New Chat'):
    conn, cursor = get_conn()
    if chat_id == -1:
        chat_id = save_chat_data(cursor, username, title)
    save_message_data(cursor, chat_id, role, content)
    results = get_message_data(cursor, chat_id)
    close_conn(conn, cursor)
    return results

def create_access_token(data: dict ):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt    

def get_current_user_email(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usr_email: str = payload.get("sub")
        if usr_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return usr_email

def get_current_user(token: str):
    usr_email = get_current_user_email(token)
    conn, cursor = get_conn()
    user = get_current_user_by_email(cursor, usr_email)
    close_conn(conn, cursor)
    return user

def get_current_active_user(access_token: str=Header(None)):
    current_user = get_current_user(access_token)
    if not current_user.user_password:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

if __name__ == "__main__":
    conn, cursor = get_conn()
    create_query = create_chat_table('Legal')
    cursor.execute(create_query)
    cursor.commit()
    create_query_two = create_message_table('Legal')
    cursor.execute(create_query_two)
    cursor.commit()

    close_conn(conn, cursor)
