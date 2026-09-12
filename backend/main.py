from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from threading import Lock

from database import get_connection, init_db
from schemas import ApplianceCreate

CAPACITY = 800

state_lock = Lock()

app = FastAPI(tittle="Inverter Load Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


def get_all_appliances(conn):
    return conn.execute("""
          SELECT id, name, wattage, priority, state, desired_on, shed_order
          FROM appliances
          ORDER BY id
    """). fetchall()


def calculate_load(conn):
    row = conn.execute("""
        SELECT COALESCE(SUM(wattage), 0) AS total
        FROM appliances
        WHERE state = 'RUNNING'
    """).fetchone()    

    return row["total"]


def get_next_shed_order(conn):    
    row = conn.execute("""
        SELECT COALESCE((MAX_order), 0) + 1 AS next_order
        FROM appliances
    """).fetchone()    

    return row["next_order"]

def restore_appliances(conn):
    currect_load = calculate_load(conn)

    shed_appliances = conn.execute("""
        SELECT *
        FROM appliances
        WHERE state = 'SHED'
        AND desired_on = 1
        ORDER BY priority ASC,shed_order ASC
    """).fetchall()
    
    for appliance in shed_appliances:
        if current_load + appliance["wattage"] > CAPACITY:
            continue

        conn.execute("""
            UPDATE appliances
            SET state = 'RUNNING', shed_order = NULL
            WHERE id = ?
        """, (appliance["id"],))
        current_load += appliance["wattage"]


@app.get("/api/appliances")
def list_appliances():
    with state_lock:
        conn = get_connection()

        appliances = get_all_appliances(conn)
        current_load = calculate_load(conn)

        result = [
            {
                "id": row["id"],
                "name": row["name"],
                "wattage": row["wattage"],
                "priority": row["priority"],
                "state": row["state"],
            }
            for row in appliances
        ]
    conn.close()

    return {
        "appliances": result,
        "current_load": current_load,
        "remaining_capacity": CAPACITY - current_load,
    }

app.post("/api/appliances")
def create_appliance(data: ApplianceCreate):
    name = data.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Appliance name cannot be empty.")

    if data.wattage > CAPACITY:
        pass

    with state_lock:
        conn = get_connection()

        try:
            cursor = conn.execute("""
                INSERT INTO appliances (name, wattage, priority, state, desired_on)
                VALUES (?, ?, ?, 'OFF', 0)
            """, (
                name,
                data.wattage, 
                data.priority
            ))

            conn.commit()  

            appliance_id = cursor.lastrowid

        except Exception as e:
            conn.rollback()
            conn.close()
            
            raise HTTPException(status_code=500, detail="Appliance name already exists")
        
        appliance = get_appliance(conn, appliance_id)

    return {
        "id": appliance["id"],
        "name": appliance["name"],
        "wattage": appliance["wattage"],
        "priority": appliance["priority"],
        "state": appliance["state"],
    }

    conn.close()

    return result


@app.delete("/api/appliances/{appliance_id}")
def delete_appliance(appliance_id: int):
    with state_lock:
        conn = get_connection()

        appliance = get_appliance(conn, appliance_id)

        if appliance is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Appliance not found")
        
        was_running = appliance["state"] == "RUNNING"

        conn.execute("""
            DELETE FROM appliances
            WHERE id = ?
        """, (appliance_id,))

        if was_running:
            restore_appliances(conn)

        conn.commit()

        current_load = calculate_load(conn)

        conn.close()

        return {
           "message": "Appliance deleted successfully.",
           "current_load": current_load,
           "remaining_capacity": CAPACITY - current_load,
        }

@app.post("/api/appliances/{appliance_id}/on")
def turn_on_appliance(appliance_id: int):
    with state_lock:
        conn = get_connection()

        appliance = get_appliance(conn, appliance_id)

        if appliance is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Appliance not found")

        if appliance["state"] == "RUNNING":
            conn.close()
            return {
                "message": "Appliance is already running.",
                }

        current_load = calculate_load(conn)

        if current_load + appliance["wattage"] <= CAPACITY:
            conn.execute("""
                UPDATE appliances
                SET state = 'RUNNING', desired_on = 1, shed_order = NULL
                WHERE id = ?
            """, (appliance_id,))

            conn.commit()
            conn.close()

            return {
               "message": "Appliance turned on successfully."
            }
        
        required = current_load + appliance["wattage"] - CAPACITY

        candidates = conn.execute("""
            SELECT * 
            FROM appliances
            WHERE state = 'RUNNING' AND priority < ?
            ORDER BY priority DESC, id ASC
        """, (appliance["priority"],)).fetchall()

        freed = 0
        to_shred = []

        for candidate in candidates:
            freed += candidate["wattage"]
            to_shred.append(candidate)

            if freed >= required:
                break
            
        if freed < required:
            conn.close()
            raise HTTPException(
                status_code=409, 
                detail=(
                    "Cannot turn on {appliance['name']}."
                    "There is not enough capacity even after"
                    "Shedding all lower-priority appliances."
                )
            )   
     
        next_order = get_next_shed_order(conn)

        for candidate in to_shred:
            conn.execute("""
                UPDATE appliances
                SET state = 'SHED', desired_on =1, shed_order = ?
                WHERE id = ?
            """, (next_order, candidate["id"]))

            next_order += 1
        
        conn.execute("""
            UPDATE appliances
            SET state = 'RUNNING', desired_on = 1, shed_order = NULL
            WHERE id = ?
        """, (appliance_id,))

        conn.commit()

        current_load = calculate_load(conn)

        conn.close()

        return {
            "message": "Appliance turned ON and lower-priority appliances were shed",
            "current_load": current_load,
            "remaining_capacity": CAPACITY - current_load,
        }

@app.post("/api/appliances/{appliance_id}/off")
def turn_off_appliance(appliance_id: int):
    with state_lock:
        conn = get_connection()

        appliance = get_appliance(conn, appliance_id)

        if appliance is None:
            conn.close()
            raise HTTPException(status_code=404, detail="Appliance not found")

        conn.execute("""
            UPDATE appliances
            SET state = 'OFF', desired_on = 0, shed_order = NULL
            WHERE id = ?
        """, (appliance_id,))

        restore_appliances(conn)

        conn.commit()

        current_load = calculate_load(conn)

        conn.close()

        return {
            "message": "Appliance turned OFF successfully.",
            "current_load": current_load,
            "remaining_capacity": CAPACITY - current_load,
        }