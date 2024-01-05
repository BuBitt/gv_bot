FROM redhat/ubi8
FROM python
LABEL maintainer="38838323+BuBitt@users.noreply.github.com"

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
