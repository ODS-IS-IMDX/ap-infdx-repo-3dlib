# © 2025 NTT DATA Japan Co., Ltd. & NTT InfraNet All Rights Reserved.

####ビルドステージ
FROM python:3.12.4-bookworm AS builder

# PostgreSQL/PostGIS/supervisorをインストール

###Pythonの設定

WORKDIR /usr/local/app

# pip アップグレード
RUN pip install --upgrade pip

COPY requirements.txt .

# Pythonライブラリのインストール（SSL証明書の検証無視対応）
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --timeout=150 -r requirements.txt



####メインステージ
FROM python:3.12.4-slim-bookworm

EXPOSE 8000

# PostgreSQL/PostGIS/supervisor/その他ツールをインストール
RUN apt update && \
    apt -y upgrade && \
    apt install -y postgresql postgresql-contrib postgis supervisor curl && \
    apt clean
    
###Postgresqlの設定

#Postgresqlの実行ユーザーに切り替え
USER postgres

#Postgresqlの保存先
ENV PGDATA=/var/lib/postgresql/15/data/

#初期化SQL
ARG PGINIT_USER_SQL=/var/lib/postgresql/15/init/init_user.sql
ARG PGINIT_EXTENTION_SQL=/var/lib/postgresql/15/init/init_postgis.sql

COPY build-resources/init/ /var/lib/postgresql/15/init/

#Postgresqlの初期化処理
RUN mkdir $PGDATA \
    && /usr/lib/postgresql/15/bin/pg_ctl init

COPY build-resources/conf/postgresql/ $PGDATA

#拡張機能有効化(Postgis)
RUN /usr/lib/postgresql/15/bin/pg_ctl start \
    && /usr/bin/psql -h localhost -U postgres -f $PGINIT_USER_SQL \
    && /usr/bin/psql -h localhost -U postgres -f $PGINIT_EXTENTION_SQL \
    && /usr/lib/postgresql/15/bin/pg_ctl stop

#ルートユーザーに戻す
USER root

###Pythonの設定

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# アプリケーションコードをコピー
COPY api/ api/

###supervisorの設定ファイルを配置
COPY build-resources/conf/supervisor/ /etc/supervisor/

CMD ["/bin/bash","-c","/usr/bin/supervisord","-c","/etc/supervisor/supervisord.conf"]