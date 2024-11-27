FROM python:3.9

# install nodejs 18
RUN apt-get update
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

RUN mkdir /code
RUN mkdir /code/front
WORKDIR /code/front
COPY ./front/package.json /code/front
COPY ./front/package-lock.json /code/front
RUN npm install
COPY ./front /code/front
RUN npm run build

RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18
# optional: for unixODBC development headers
RUN apt-get install -y unixodbc-dev

WORKDIR /code

RUN pip install --upgrade pip
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

EXPOSE 8000
# docker build -t spaces:latest .
# docker run -p 8000:8000 spaces:latest
# uvicorn api:app --host 0.0.0.0 --port 8000 --reload
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "5"]