# © 2025 NTT DATA Japan Co., Ltd. & NTT InfraNet All Rights Reserved.

import sys
import os

from fastapi.exceptions import RequestValidationError
# api フォルダをパスに追加（api/SpatialIdが含まれるディレクトリまで）
sys.path.append(os.path.join(os.path.dirname(__file__)))
import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import bindparam
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from SpatialId.shape.polygons import f_get_spatial_ids_on_polygons
from SpatialId.common.object.point import Point as SpatialPoint
from SpatialId.common.object.point import Triangle as SpatialTriangle
from SpatialId.shape.polygons import Triangle
from logging_config import setup_logging

app = FastAPI()

setup_logging()

logging.info("This is an info message in main.py")
logging.warning("This is a warning messeage in main.py")

# TIN のヘッダーとフッターの長さ
# TIN_START = 4
# TIN_END = -2
TIN_START = 6
TIN_END = -4

#三角形の3点の座標
TRIANGLE_POINT = 3

# ステータスコード
STATUS_OK = 200
STATUS_INTERNAL_ERROR = 500
STATUS_BAD_REQUEST = 400

#エラータイプを識別する定数
PSYCOPG2_ERROR = "psycopg2"
PSYCOPG2_CONNECTION_ERROR = "Connection refused"

app = FastAPI()

# データベースセッションの取得
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#座標→空間ID変換APIリクエストデータ
class PolygonRequest(BaseModel):
    polygon: str = Field(..., description="ポリゴン座標", min_length=1)
    epsg: int = Field(..., description="EPSGコード", gt=0)
    zoomLevel: int = Field(..., description="ズームレベル", gt=0)

#ポリゴン面積取得APIリクエストデータ
class AreaRequest(BaseModel):
    polygon: str = Field(..., description="ポリゴン座標", min_length=1)
    epsg: int  =  Field(..., description="EPSGコード", gt=0)

#リクエストデータの例外ハンドラ
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, e: RequestValidationError):
    return JSONResponse(
        status_code=STATUS_BAD_REQUEST,
        content={
            "detail":"Invalid input data",
            "error":e.errors()
        }
    )

#ポリゴン面積取得API
@app.post("/gen/api/polygon/v1/get-area")
def get_calculate_area(request: AreaRequest, db: Session = Depends(get_db)):

    # リクエストデータの受け取り
    polygon = request.polygon
    epsg = request.epsg

    logging.info("疎通OK")
    logging.info("request : " + str(request))

    try:
        logging.info("DB接続開始")
        #リクエストデータを基にクエリを実行
        query = text("select ST_Area(geo) from ST_GeogFromText(:geo_text) as geo;")
        result = db.execute(query, {"geo_text": f"SRID={epsg};{polygon}"}).one()

        logging.info("result : " + str(result))
        logging.info("DB接続完了")

        #クエリ結果の面積だけを取得
        area = result[0]

        #レスポンスデータの返却
        return JSONResponse(
                content={
                    "area": area
                }
            )
    #エラー内容に基づいてHTTPステータスを設定
    except Exception as e:
        detail = str(e)

    if PSYCOPG2_ERROR in detail:
        # OperationalErrorの場合は500、その他は400
        if PSYCOPG2_CONNECTION_ERROR in detail:
            status = STATUS_INTERNAL_ERROR
        else:
            status = STATUS_BAD_REQUEST
    # その他のエラーは500
    else:
        status = STATUS_INTERNAL_ERROR

    raise HTTPException(status_code=status, detail=detail)

#座標→空間ID変換API
@app.post("/gen/api/polygon/v1/get-spatialid")
def polygon_spatial_id_converter(request: PolygonRequest, db: Session = Depends(get_db)):

    # リクエストデータの受け取り
    polygon = request.polygon
    epsg = request.epsg
    zoomLevel = request.zoomLevel

    logging.info("疎通OK")
    logging.info("request : " + str(request))

    try:
        logging.info("DB接続開始")
        #リクエストデータを基にクエリ作成し実行
        query = text("SELECT ST_AsText(ST_Tesselate(:polygon));")
        result = db.execute(query, {"polygon": polygon}).one()

        logging.info("query : " + str(query))
        logging.info("result : " + str(result))
        logging.info("DB接続完了")

        polygon_str = result[0]
        # 先頭の "TIN(" と最後の ")" を除去
        polygon_core = polygon_str[TIN_START:TIN_END]

        # "),(" で分割
        split_polygon_list = polygon_core.split("),(")

        # 各ポリゴンのリストから、前後の括弧を除去
        cleaned_polygon_list = [polygon.strip("()")
                                for polygon in split_polygon_list]

        # 各種ポリゴンの座標をカンマ分割し空白を除去
        all_coordinates_list = []
        for polygon in cleaned_polygon_list:
            coordinates = polygon.split(",")
            # 最大3回までループする
            for i, coord in enumerate(coordinates):
                if TRIANGLE_POINT <= i:
                    break
                lon, lat = coord.split()
                all_coordinates_list.append({
                    "lon": float(lon),
                    "lat": float(lat),
                    "alt": 0
                })
        #各三角形の座標を格納
        Triangle_dict = []
        num_triangles = len(all_coordinates_list)

        for i in range(num_triangles):
            if i * 3 + 2 < len(all_coordinates_list):
                p1 = all_coordinates_list[i * 3]
                p2 = all_coordinates_list[i * 3 + 1]
                p3 = all_coordinates_list[i * 3 + 2]

                Triangle_dict.append({
                    "p1": p1,
                    "p2": p2,
                    "p3": p3
                })
            else:
                break

        #共通ライブラリの関数に渡せるようにインプット情報に設定
        barrier_triangles_list = []
        for barrier_triangle in Triangle_dict:
            barrier_triangles_list.append(
                    SpatialTriangle(
                        p1=SpatialPoint(
                            lon=barrier_triangle["p1"]["lon"],
                            lat=barrier_triangle["p1"]["lat"],
                            alt=barrier_triangle["p1"]["alt"],
                        ),
                        p2=SpatialPoint(
                            lon=barrier_triangle["p2"]["lon"],
                            lat=barrier_triangle["p2"]["lat"],
                            alt=barrier_triangle["p2"]["alt"],
                        ),
                        p3=SpatialPoint(
                            lon=barrier_triangle["p3"]["lon"],
                            lat=barrier_triangle["p3"]["lat"],
                            alt=barrier_triangle["p3"]["alt"],
                        ),
                    )
            )

        #インプット情報とリクエストデータを基に共通ライブラリ実行
        param_return = f_get_spatial_ids_on_polygons(
            barrier_triangles=barrier_triangles_list,
            space_triangles=[],
            zoom=zoomLevel ,
            crs=epsg,
            needs_closed_checking=False,
        )
        param_dict = {}
        param_dict["spatialIds"] = param_return

        #レスポンスデータの返却
        return JSONResponse(
            content={
                "sidList": param_dict["spatialIds"]
            }
        )
    #エラー内容に基づいてHTTPステータスを設定
    except Exception as e:
        detail = str(e)

    if PSYCOPG2_ERROR in detail:
        # OperationalErrorの場合は500、その他は400
        if PSYCOPG2_CONNECTION_ERROR in detail:
            status = STATUS_INTERNAL_ERROR
        else:
            status = STATUS_BAD_REQUEST
    # その他のエラーは500
    else:
        status = STATUS_INTERNAL_ERROR

    raise HTTPException(status_code=status, detail=detail)

@app.get("/health")
def read_health():
    return {"status": "UP"}