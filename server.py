import os
import math
import time
import secrets
from collections import defaultdict, deque
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

MAX_PLAYERS = 16
ARENA_LIMIT = 29.0
MOVE_SPEED = 10.5
PLAYER_RADIUS = 0.55
SHOT_RANGE = 45.0
SHOT_ANGLE_COS = math.cos(math.radians(5.0))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
allowed = os.environ.get("ALLOWED_ORIGINS", "*")
origins = "*" if allowed == "*" else [x.strip() for x in allowed.split(",") if x.strip()]
socketio = SocketIO(app, cors_allowed_origins=origins, async_mode="threading",
                    ping_interval=25, ping_timeout=60, max_http_buffer_size=10_000)
players = {}
rate = defaultdict(deque)
scores = {"blue": 0, "red": 0}
match_started = time.time()

def limited(sid, event, max_count, window=1.0):
    now = time.monotonic()
    q = rate[(sid, event)]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= max_count:
        return True
    q.append(now)
    return False

def clean_name(value):
    name = "".join(c for c in str(value or "Player") if c.isalnum() or c in " _-")[:18].strip()
    return name or "Player"

def snapshot():
    return [{"id": sid, "name": p["name"], "team": p["team"],
             "x": p["x"], "y": p["y"], "z": p["z"], "yaw": p["yaw"],
             "health": p["health"]} for sid, p in players.items()]

def broadcast_state():
    socketio.emit("state", {"players": snapshot(), "scores": scores}, to="arena")

@app.get("/")
def health():
    return jsonify(status="online", game="NEON ARENA FPS", players=len(players), capacity=MAX_PLAYERS)

@socketio.on("join")
def on_join(data):
    if request.sid in players:
        emit("joined", {"ok": True, "id": request.sid, "team": players[request.sid]["team"]})
        return
    if len(players) >= MAX_PLAYERS:
        emit("join_error", {"message": "방이 가득 찼습니다. 최대 16명입니다."})
        return
    data = data if isinstance(data, dict) else {}
    blue_count = sum(p["team"] == "blue" for p in players.values())
    red_count = len(players) - blue_count
    team = "blue" if blue_count <= red_count else "red"
    players[request.sid] = {
        "name": clean_name(data.get("name")), "team": team,
        "x": -12.0 if team == "blue" else 12.0, "y": 1.7,
        "z": secrets.choice([-8.0, -4.0, 4.0, 8.0]),
        "yaw": 0.0 if team == "blue" else math.pi,
        "health": 100, "last_move": time.monotonic(),
        "last_shot": 0.0, "last_damage": 0.0
    }
    emit("joined", {"ok": True, "id": request.sid, "team": team})
    emit("feed", {"text": players[request.sid]["name"] + " 입장", "kind": "info"}, to="arena")
    broadcast_state()

@socketio.on("move")
def on_move(data):
    p = players.get(request.sid)
    if not p or not isinstance(data, dict) or limited(request.sid, "move", 25):
        return
    now = time.monotonic()
    dt = max(0.01, min(now - p["last_move"], 0.25))
    try:
        nx = float(data.get("x", p["x"]))
        nz = float(data.get("z", p["z"]))
        ny = float(data.get("y", p["y"]))
        yaw = float(data.get("yaw", p["yaw"]))
    except (TypeError, ValueError):
        return
    if not all(math.isfinite(v) for v in (nx, nz, ny, yaw)):
        return
    dx, dz = nx - p["x"], nz - p["z"]
    max_step = MOVE_SPEED * dt + 0.9
    distance = math.hypot(dx, dz)
    if distance > max_step:
        scale = max_step / distance
        nx, nz = p["x"] + dx * scale, p["z"] + dz * scale
    p["x"] = max(-ARENA_LIMIT, min(ARENA_LIMIT, nx))
    p["z"] = max(-ARENA_LIMIT, min(ARENA_LIMIT, nz))
    p["y"] = max(1.2, min(4.8, ny))
    p["yaw"] = ((yaw + math.pi) % (2 * math.pi)) - math.pi
    p["last_move"] = now
    socketio.emit("player_moved", {"id": request.sid, **{k:p[k] for k in ("x","y","z","yaw","health","team","name")}},
                  to="arena", include_self=False)

@socketio.on("shoot")
def on_shoot(data):
    global scores
    shooter = players.get(request.sid)
    if not shooter or not isinstance(data, dict) or limited(request.sid, "shoot", 8):
        return
    now = time.monotonic()
    if now - shooter["last_shot"] < 0.12:
        return
    shooter["last_shot"] = now
    try:
        yaw = float(data.get("yaw", shooter["yaw"]))
        pitch = float(data.get("pitch", 0.0))
    except (TypeError, ValueError):
        return
    if not math.isfinite(yaw) or not math.isfinite(pitch):
        return
    # Server validates target proximity and aim direction; client cannot simply name a target.
    dx_dir = -math.sin(yaw) * math.cos(pitch)
    dy_dir = math.sin(pitch)
    dz_dir = -math.cos(yaw) * math.cos(pitch)
    candidates = []
    for sid, target in players.items():
        if sid == request.sid or target["team"] == shooter["team"] or target["health"] <= 0:
            continue
        dx = target["x"] - shooter["x"]
        dy = (target["y"] + 0.1) - shooter["y"]
        dz = target["z"] - shooter["z"]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist > SHOT_RANGE or dist < 0.1:
            continue
        dot = (dx*dx_dir + dy*dy_dir + dz*dz_dir) / dist
        if dot < SHOT_ANGLE_COS:
            continue
        perp = math.sqrt(max(0.0, dist*dist - (dx*dx_dir + dy*dy_dir + dz*dz_dir)**2))
        if perp <= PLAYER_RADIUS + 0.18:
            candidates.append((dist, sid))
    socketio.emit("shot", {"id": request.sid, "name": shooter["name"], "x": shooter["x"], "z": shooter["z"]}, to="arena")
    if candidates:
        _, target_id = min(candidates)
        target = players[target_id]
        target["health"] -= 34
        socketio.emit("damage", {"target": target_id, "health": target["health"]}, to="arena")
        if target["health"] <= 0:
            scores[shooter["team"]] += 1
            socketio.emit("feed", {"text": shooter["name"] + " 처치!", "kind": shooter["team"]}, to="arena")
            target["health"] = 100
            target["x"] = -12.0 if target["team"] == "blue" else 12.0
            target["z"] = secrets.choice([-8.0, -4.0, 4.0, 8.0])
            socketio.emit("respawn", {"id": target_id, "x": target["x"], "z": target["z"], "health": 100}, to="arena")
            socketio.emit("scores", scores, to="arena")

@socketio.on("disconnect")
def on_disconnect():
    p = players.pop(request.sid, None)
    rate.pop((request.sid, "move"), None)
    rate.pop((request.sid, "shoot"), None)
    if p:
        socketio.emit("feed", {"text": p["name"] + " 퇴장", "kind": "info"}, to="arena")
        broadcast_state()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
