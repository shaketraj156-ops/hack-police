from fastapi import FastAPI

from pydantic import BaseModel
import psycopg

DB_HOST = "localhost"
DB_NAME = "cctv_registry"
DB_USER = "postgres"
DB_PASSWORD = "CCTV#26"
DB_PORT = 5432

def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
app = FastAPI()


class Camera(BaseModel):
    camera_name: str
    department: str
    latitude: float
    longitude: float
    camera_type: str


cameras = []


@app.get("/")
def home():
    return {
        "message": "CCTV Registry Backend is running!"
    }


@app.post("/cameras")
def add_camera(camera: Camera):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO cameras
        (camera_name, department, latitude, longitude, camera_type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING camera_id
        """,
        (
            camera.camera_name,
            camera.department,
            camera.latitude,
            camera.longitude,
            camera.camera_type
        )
    )

    camera_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Camera added successfully",
        "camera_id": camera_id
    }


@app.get("/cameras")
def get_cameras():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            camera_id,
            camera_name,
            department,
            latitude,
            longitude,
            camera_type
        FROM cameras
        ORDER BY camera_id
    """)

    cameras = cursor.fetchall()

    cursor.close()
    conn.close()

    return cameras



@app.put("/cameras/{camera_id}")
def update_camera(camera_id: int, camera: Camera):
    for existing_camera in cameras:
        if existing_camera["camera_id"] == camera_id:
            existing_camera["camera_name"] = camera.camera_name
            existing_camera["department"] = camera.department
            existing_camera["latitude"] = camera.latitude
            existing_camera["longitude"] = camera.longitude
            existing_camera["camera_type"] = camera.camera_type

            return {
                "message": "Camera updated successfully",
                "camera": existing_camera
            }

    return {
        "message": "Camera not found"
    }

@app.delete("/cameras/{camera_id}")
def delete_camera(camera_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM cameras
        WHERE camera_id = %s
        RETURNING camera_id
        """,
        (camera_id,)
    )

    deleted_camera = cursor.fetchone()

    conn.commit()

    cursor.close()
    conn.close()

    if deleted_camera is None:
        return {"message": "Camera not found"}

    return {
        "message": "Camera deleted successfully",
        "camera_id": deleted_camera[0]
    }