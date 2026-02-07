extends Node3D

var ws := WebSocketPeer.new()
var url := "ws://127.0.0.1:8765/pet"

var vx := 0.0

@export var model_path: NodePath
@onready var model: Node3D = get_node_or_null(model_path)
@onready var idle_target: Node3D = get_node_or_null("coloured_pet")
var idle_base_pos := Vector3.ZERO
var idle_base_scale := Vector3.ONE

func _ready():
	var err = ws.connect_to_url(url)
	print("WS connect err:", err)
	DisplayServer.window_set_title("desktop_pet")
	get_window().mouse_passthrough = false
	# Windowed, fixed size so the pet stays compact.
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(360, 360))
	# Always on top.
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	var vp := get_viewport()
	vp.transparent_bg = true
	RenderingServer.set_default_clear_color(Color(0, 0, 0, 0))
	# Snap window to bottom-right with a small margin.
	var margin = 2
	var screen = DisplayServer.screen_get_size()
	var win = DisplayServer.window_get_size()
	DisplayServer.window_set_position(
		Vector2i(
			screen.x - win.x - margin,
			screen.y - win.y - margin
		)
	)
	# Marker file to verify this script is running in the exported EXE.
	var f = FileAccess.open("user://petroot_ready.txt", FileAccess.WRITE)
	if f:
		f.store_string("PetRoot ready\n")
		f.close()
	if idle_target:
		idle_base_pos = idle_target.position
		idle_base_scale = idle_target.scale

func _process(dt):
	ws.poll()

	if ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		while ws.get_available_packet_count() > 0:
			var msg = ws.get_packet().get_string_from_utf8()
			_handle_cmd(msg)

	position.x += vx * dt
	_apply_idle(dt)

func _apply_idle(dt):
	if not idle_target:
		return
	var t = Time.get_ticks_msec() / 1000.0
	var bob = 0.02 * sin(t * 2.0)
	var breathe = 0.01 * sin(t * 1.5)
	idle_target.position = idle_base_pos + Vector3(0, bob, 0)
	idle_target.scale = idle_base_scale + Vector3(breathe, breathe, breathe)

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
