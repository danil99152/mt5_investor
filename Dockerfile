FROM tobix/pywine:3.10

ADD ./mt5_investor ./mt5_investor
ADD ./MetaTrader5 ./MetaTrader5

RUN cd / && apt update && apt install -y xvfb && \
    wine python -m pip install --upgrade pip setuptools && \
    wine python -m pip install -r ./mt5_investor/requirements.txt

CMD xvfb-run wine python -u ./mt5_investor/investor.py

# build
# docker build -t mt5-investor .
#
# run
# docker run --name mt5-investor <image_id> --env ACCOUNT_ID=<account_pk>
