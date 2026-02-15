import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import firestore

app = FastAPI()
db = firestore.Client()

@app.get("/")
async def root():
    return {"message": "WebSocket Server is running"}

@app.websocket("/ws/{id_menor}")
async def websocket_endpoint(websocket: WebSocket, id_menor: str):
    await websocket.accept()
    print(f"Nueva conexión para el niño: {id_menor}")

    # Esta función se activa cada vez que Firestore cambia
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name in ['ADDED', 'MODIFIED']:
                data = change.document.to_dict()
                # Enviamos el dato al móvil del padre/reloj
                asyncio.run_coroutine_thread_safe(
                    websocket.send_json(data), asyncio.get_running_loop()
                )

    # 1. Vigilar Ubicación
    doc_ref = db.collection("ubicaciones_actualizadas").document(id_menor)
    watch_ubicacion = doc_ref.on_snapshot(on_snapshot)

    # 2. Vigilar Alertas (Peligro/Advertencia)
    # Buscamos alertas recientes para este niño específico
    query_alertas_padre = db.collection("alertas_padre").where("id_menor", "==", id_menor)
    watch_alertas_padre = query_alertas_padre.on_snapshot(on_snapshot)

    query_alertas_niño = db.collection("alertas_niño").where("id_menor", "==", id_menor)
    watch_alertas_niño = query_alertas_niño.on_snapshot(on_snapshot)

    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        print(f"El usuario {id_menor} se ha desconectado")
        watch_ubicacion.unsubscribe()
        watch_alertas_padre.unsubscribe()
        watch_alertas_niño.unsubscribe()