using Godot;
using System;
using System.Runtime.InteropServices;

public partial class WinHitTest : Node
{
	[Export] public float UpdateInterval = 0.15f;
	[Export] public byte AlphaThreshold = 10;

	private float _accum = 0f;
	private IntPtr _hwnd = IntPtr.Zero;

	public override void _Ready()
	{
		_hwnd = GetWindowHandle();
		if (_hwnd == IntPtr.Zero)
		{
			GD.PrintErr("[WinHitTest] Failed to get window handle.");
		}
	}

	public override void _Process(double delta)
	{
		_accum += (float)delta;
		if (_accum < UpdateInterval)
			return;
		_accum = 0f;

		if (_hwnd == IntPtr.Zero)
			_hwnd = GetWindowHandle();
		if (_hwnd == IntPtr.Zero)
			return;

		UpdateWindowRegion();
	}

	private void UpdateWindowRegion()
	{
		var viewport = GetViewport();
		var tex = viewport.GetTexture();
		if (tex == null)
			return;

		var img = tex.GetImage();
		if (img == null)
			return;

		if (img.GetFormat() != Image.Format.Rgba8)
			img.Convert(Image.Format.Rgba8);

		int w = img.GetWidth();
		int h = img.GetHeight();
		if (w <= 0 || h <= 0)
			return;

		byte[] data = img.GetData();
		if (data.Length < w * h * 4)
			return;

		IntPtr region = CreateRectRgn(0, 0, 0, 0);

		for (int y = 0; y < h; y++)
		{
			int rowStart = y * w * 4;
			int x = 0;
			while (x < w)
			{
				int idx = rowStart + x * 4 + 3;
				bool opaque = data[idx] > AlphaThreshold;
				if (!opaque)
				{
					x++;
					continue;
				}

				int x0 = x;
				x++;
				while (x < w)
				{
					idx = rowStart + x * 4 + 3;
					if (data[idx] <= AlphaThreshold)
						break;
					x++;
				}

				IntPtr run = CreateRectRgn(x0, y, x, y + 1);
				CombineRgn(region, region, run, RGN_OR);
				DeleteObject(run);
			}
		}

		SetWindowRgn(_hwnd, region, true);
	}

	private IntPtr GetWindowHandle()
	{
		long handle = DisplayServer.WindowGetNativeHandle(DisplayServer.HandleType.WindowHandle, 0);
		return new IntPtr(handle);
	}

	private const int RGN_OR = 2;

	[DllImport("user32.dll")]
	private static extern int SetWindowRgn(IntPtr hWnd, IntPtr hRgn, bool bRedraw);

	[DllImport("gdi32.dll")]
	private static extern IntPtr CreateRectRgn(int nLeftRect, int nTopRect, int nRightRect, int nBottomRect);

	[DllImport("gdi32.dll")]
	private static extern int CombineRgn(IntPtr hrgnDest, IntPtr hrgnSrc1, IntPtr hrgnSrc2, int fnCombineMode);

	[DllImport("gdi32.dll")]
	private static extern bool DeleteObject(IntPtr hObject);
}
