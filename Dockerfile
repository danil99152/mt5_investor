# first layer is our python base image enabling us to run pip
FROM python:3.10-windowsservercore-ltsc2022

# create directory in the container for adding your files
WORKDIR /user/src/app

# copy over the requirements file and run pip install to install the packages into your container at the directory defined above
COPY ./mt5_investor/requirements.txt ./
RUN python.exe -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./mt5_investor/ ./mt5_investor/
COPY ["./MetaTrader 5/", "./MetaTrader 5/"]
# enter entry point parameters executing the container
ENTRYPOINT ["powershell.exe"]

# exposing the port to match the port in the runserver.py file
EXPOSE 8000
CMD ["python", "mt5_investor/main.py"]

# build
# docker build -t mt5_investor .
# run
# docker run -p 8000:8000 <image_id>