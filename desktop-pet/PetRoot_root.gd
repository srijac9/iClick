extends Node3D

var ws := WebSocketPeer.new()
var url := "ws://127.0.0.1:8765/pet"

var vx := 0.0

@export var model_path: NodePath
@onready var model: Node3D = get_node_or_null(model_path)

func _ready():
	var err = ws.connect_to_url(url)
	print("WS connect err:", err)
	DisplayServer.window_set_title("desktop_pet")
	get_window().mouse_passthrough = false
	RenderingServer.set_default_clear_color(Color(1, 0, 1, 1))

func _process(dt):
	ws.poll()

	if ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		while ws.get_available_packet_count() > 0:
			var msg = ws.get_packet().get_string_from_utf8()
			_handle_cmd(msg)

	position.x += vx * dt

func _handle_cmd(msg: String):
	var data = JSON.parse_string(msg)
	if typeof(data) != TYPE_DICTIONARY:
		return

	match data.get("type", ""):

		"set_speed":
			vx = float(data.get("vx", 0.0))

		"shutdown":
			get_tree().quit()

		"set_scale":
			if model:
				var s = float(data.get("s", 0.35))
				model.scale = Vector3(s, s, s)

		"set_window_pos":
			var x = int(data.get("x", 0))
			var y = int(data.get("y", 0))
			DisplayServer.window_set_position(Vector2i(x, y))

		"bottom_right":
			var margin = int(data.get("margin", 0))
			var screen = DisplayServer.screen_get_size()
			var win = DisplayServer.window_get_size()
			DisplayServer.window_set_position(
				Vector2i(
					screen.x - win.x - margin,
					screen.y - win.y - margin
				)
			)

		"always_on_top":
			var on = bool(data.get("on", true))
			DisplayServer.window_set_flag(
				DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP,
				on
			)

		"mouse_passthrough":
			var on = bool(data.get("on", true))
			get_window().mouse_passthrough = on
