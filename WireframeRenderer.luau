local HttpService = game:GetService("HttpService")
local EncodingService = game:GetService("EncodingService")
local StarterGui = game:GetService("StarterGui")
local WireframeRenderer = {}

local function notify(title, text, duration)
	pcall(function()
		StarterGui:SetCore("SendNotification", {
			Title = title,
			Text = text,
			Duration = duration or 3
		})
	end)
end
local function getFaceMapping(face, size)
	local pw, ph, zOffset
	if face == Enum.NormalId.Front then
		pw, ph = size.X, size.Y
		zOffset = size.Z/2 + 0.05
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(x1, yc, zOffset), Vector3.new(x2, yc, zOffset) end
	elseif face == Enum.NormalId.Back then
		pw, ph = size.X, size.Y
		zOffset = -(size.Z/2 + 0.05)
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(-x1, yc, zOffset), Vector3.new(-x2, yc, zOffset) end
	elseif face == Enum.NormalId.Right then
		pw, ph = size.Z, size.Y
		zOffset = size.X/2 + 0.05
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(zOffset, yc, -x1), Vector3.new(zOffset, yc, -x2) end
	elseif face == Enum.NormalId.Left then
		pw, ph = size.Z, size.Y
		zOffset = -(size.X/2 + 0.05)
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(zOffset, yc, x1), Vector3.new(zOffset, yc, x2) end
	elseif face == Enum.NormalId.Top then
		pw, ph = size.X, size.Z
		zOffset = size.Y/2 + 0.05
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(x1, zOffset, -yc), Vector3.new(x2, zOffset, -yc) end
	elseif face == Enum.NormalId.Bottom then
		pw, ph = size.X, size.Z
		zOffset = -(size.Y/2 + 0.05)
		return pw, ph, zOffset, function(x1, yc, x2) return Vector3.new(x1, zOffset, yc), Vector3.new(x2, zOffset, yc) end
	end
end
function WireframeRenderer.Draw(targetPart, imageData, face)
	face = face or Enum.NormalId.Front

	if type(imageData) == "string" then
		imageData = HttpService:JSONDecode(imageData)
	end

	if not imageData or not imageData.p then return end
	local w, h, isAnimated, durations, pixels = imageData.w, imageData.h, imageData.a, imageData.d, imageData.p

	for _, child in pairs(targetPart:GetChildren()) do
		if child:IsA("Folder") and child.Name == "WireframeImageRender" then child:Destroy() end
	end

	local renderFolder = Instance.new("Folder")
	renderFolder.Name = "WireframeImageRender"
	renderFolder.Parent = targetPart

	local pw, ph, zOffset, coordFunc = getFaceMapping(face, targetPart.Size)
	local spanw = pw / w
	local spanh = ph / h
	local halfw = pw / 2
	local halfh = ph / 2

	local function processFrame(frameData)
		local frameFolder = Instance.new("Folder")
		frameFolder.Name = "Frame"
		frameFolder.Parent = renderFolder
		local colorBuckets = {}
		for y_key, row in pairs(frameData) do
			local y = tonumber(y_key)
			if not y then continue end
			local cx = 0
			for _, span in ipairs(row) do
				local slen, r, g, b = span[1], span[2], span[3], span[4]
				local key = r * 65536 + g * 256 + b
				if not colorBuckets[key] then colorBuckets[key] = { color = Color3.fromRGB(r, g, b), pts = {} } end
				local x1 = (cx * spanw) - halfw
				local x2 = ((cx + slen) * spanw) - halfw
				local yc = halfh - (y - 0.5) * spanh
				local p1, p2 = coordFunc(x1, yc, x2)
				table.insert(colorBuckets[key].pts, p1)
				table.insert(colorBuckets[key].pts, p2)
				cx += slen
			end
		end
		for _, bucket in pairs(colorBuckets) do
			local wire = Instance.new("WireframeHandleAdornment")
			wire.Adornee = targetPart
			wire.AlwaysOnTop = false
			wire.Visible = false
			wire.Color3 = bucket.color
			wire.Parent = frameFolder
			wire:AddLines(bucket.pts)
		end
		return frameFolder
	end

	local frames = {}
	if isAnimated then
		for _, frameData in ipairs(pixels) do table.insert(frames, processFrame(frameData)) task.wait() end
	else
		table.insert(frames, processFrame(pixels))
	end

	local function isPartVisible(part)
		local camera = workspace.CurrentCamera
		if not camera then return true end
		local cf, sz = part.CFrame, part.Size / 2
		if math.abs(cf:PointToObjectSpace(camera.CFrame.Position).X) < sz.X then return true end
		for _, p in ipairs({cf.Position, cf * Vector3.new(sz.X, sz.Y, sz.Z), cf * Vector3.new(-sz.X, -sz.Y, -sz.Z)}) do
			if camera:WorldToViewportPoint(p) then return true end
		end
		return false
	end

	task.spawn(function()
		local current = 1
		local function setVis(f, v) if f then for _, w in f:GetChildren() do w.Visible = v end end end
		setVis(frames[1], true)
		while renderFolder.Parent == targetPart do
			local vis = isPartVisible(targetPart)
			if vis then
				if isAnimated and #frames > 1 then
					task.wait((durations[current] or 100) / 1000)
					setVis(frames[current], false)
					current = (current % #frames) + 1
					setVis(frames[current], true)
				else task.wait(0.2) end
			else
				for _, f in ipairs(frames) do setVis(f, false) end
				task.wait(0.5)
			end
		end
	end)
end

function WireframeRenderer.DrawFromFolder(targetPart, folder, face)
	face = face or Enum.NormalId.Front
	if not folder or not folder:IsA("Folder") then return end

	notify("Image Renderer", "Reading data chunks...", 3)

	local width = tonumber(folder:WaitForChild("Width", 5).Value)
	local height = tonumber(folder:WaitForChild("Height", 5).Value)
	local animated = folder:WaitForChild("Animated", 5).Value == "true"

	local durations = {}
	local durationsStr = folder:WaitForChild("Durations", 5).Value
	if durationsStr and durationsStr ~= "" then
		for d in string.gmatch(durationsStr, "%d+") do table.insert(durations, tonumber(d)) end
	end

	local totalChunks = tonumber(folder:WaitForChild("TotalChunks", 5).Value)
	local chunks = {}
	for i = 1, totalChunks do
		local chunkVal = folder:WaitForChild(tostring(i), 5)
		if chunkVal then chunks[i] = chunkVal.Value else return end
	end

	notify("Image Renderer", "Decoding Base64...", 3)
	local decoded_buf = EncodingService:Base64Decode(buffer.fromstring(table.concat(chunks)))
	local len = buffer.len(decoded_buf)

	local frames_info = {}
	local pos = 0
	while pos < len do
		local num_spans = buffer.readu32(decoded_buf, pos)
		pos += 4
		table.insert(frames_info, { start = pos, count = num_spans })
		pos += num_spans * 7
	end

	local totalFrames = #frames_info
	notify("Image Renderer", string.format("Loading %s (%d frames)...", animated and "GIF" or "Image", totalFrames), 4)

	for _, child in pairs(targetPart:GetChildren()) do
		if child:IsA("Folder") and child.Name == "WireframeImageRender" then child:Destroy() end
	end
	local renderFolder = Instance.new("Folder")
	renderFolder.Name = "WireframeImageRender"
	renderFolder.Parent = targetPart

	local pw, ph, zOffset, coordFunc = getFaceMapping(face, targetPart.Size)
	local spanw = pw / width
	local spanh = ph / height
	local halfw = pw / 2
	local halfh = ph / 2

	local frames = {}
	local done_count = 0
	local active_count = 0
	local max_concurrent = 30
	local batch_size = 5000

	local function processFrame(idx)
		local info = frames_info[idx]
		local frameFolder = Instance.new("Folder")
		frameFolder.Name = "Frame"
		frameFolder.Parent = renderFolder

		local colorBuckets = {}
		local pos = info.start
		local current_y = -1
		local cx = 0

		for i = 1, info.count do
			local y = buffer.readu16(decoded_buf, pos)
			local slen = buffer.readu16(decoded_buf, pos + 2)
			local r = buffer.readu8(decoded_buf, pos + 4)
			local g = buffer.readu8(decoded_buf, pos + 5)
			local b = buffer.readu8(decoded_buf, pos + 6)
			pos += 7

			if y ~= current_y then
				current_y = y
				cx = 0
			end

			local key = r * 65536 + g * 256 + b
			if not colorBuckets[key] then colorBuckets[key] = { color = Color3.fromRGB(r, g, b), pts = {} } end

			local x1 = (cx * spanw) - halfw
			local x2 = ((cx + slen) * spanw) - halfw
			local yc = halfh - (y - 0.5) * spanh

			local p1, p2 = coordFunc(x1, yc, x2)
			table.insert(colorBuckets[key].pts, p1)
			table.insert(colorBuckets[key].pts, p2)
			cx += slen
		end

		local lastYield = os.clock()
		local MAX_FRAME_TIME = 1/30

		for _, bucket in pairs(colorBuckets) do
			local wire = Instance.new("WireframeHandleAdornment")
			wire.Adornee = targetPart
			wire.AlwaysOnTop = false
			wire.Visible = false
			wire.Color3 = bucket.color
			wire.Parent = frameFolder

			local processed = 0
			while processed < #bucket.pts do
				local batch_count = math.min(batch_size, #bucket.pts - processed)
				local pts = {}
				for j = 1, batch_count do
					pts[#pts + 1] = bucket.pts[processed + j]
				end
				wire:AddLines(pts)
				processed += batch_count
				if os.clock() - lastYield > MAX_FRAME_TIME then
					task.wait()
					lastYield = os.clock()
				end
			end
		end
		table.insert(frames, frameFolder)
	end

	for idx = 1, totalFrames do
		while active_count >= max_concurrent do task.wait() end
		active_count += 1
		coroutine.wrap(function()
			processFrame(idx)
			done_count += 1
			active_count -= 1

			local currentTenth = math.floor((done_count / totalFrames) * 10)
			if totalFrames > 1 and done_count % math.max(1, math.floor(totalFrames / 10)) == 0 then
				notify("Image Renderer", string.format("Progress: %d/%d frames", done_count, totalFrames), 2)
			end
		end)()
	end

	while done_count < totalFrames do task.wait() end
	notify("Image Renderer", "Image loaded successfully!", 3)

	local function isPartVisible(part)
		local camera = workspace.CurrentCamera
		if not camera then return true end
		local cf = part.CFrame
		local sz = part.Size / 2
		local localCamPos = cf:PointToObjectSpace(camera.CFrame.Position)
		if math.abs(localCamPos.X) < sz.X and math.abs(localCamPos.Y) < sz.Y and math.abs(localCamPos.Z) < sz.Z then return true end
		local points = {
			cf.Position,
			cf * Vector3.new(sz.X, sz.Y, sz.Z), cf * Vector3.new(sz.X, sz.Y, -sz.Z),
			cf * Vector3.new(sz.X, -sz.Y, sz.Z), cf * Vector3.new(sz.X, -sz.Y, -sz.Z),
			cf * Vector3.new(-sz.X, sz.Y, sz.Z), cf * Vector3.new(-sz.X, sz.Y, -sz.Z),
			cf * Vector3.new(-sz.X, -sz.Y, sz.Z), cf * Vector3.new(-sz.X, -sz.Y, -sz.Z)
		}
		for _, p in ipairs(points) do
			local _, onScreen = camera:WorldToViewportPoint(p)
			if onScreen then return true end
		end
		return false
	end

	task.spawn(function()
		local current = 1
		local function setFrameVisibility(frame, isVisible)
			if frame then for _, wire in frame:GetChildren() do wire.Visible = isVisible end end
		end
		local lastVisible = true
		setFrameVisibility(frames[1], true)

		while renderFolder.Parent == targetPart do
			local isVisible = isPartVisible(targetPart)
			if isVisible ~= lastVisible then
				if not isVisible then
					for _, frame in ipairs(frames) do setFrameVisibility(frame, false) end
				else
					setFrameVisibility(frames[current], true)
				end
				lastVisible = isVisible
			end
			if isVisible then
				if animated and #frames > 1 then
					local waitTime = (durations[current] or 100) / 1000
					task.wait(waitTime)
					if renderFolder.Parent == targetPart and isPartVisible(targetPart) then
						setFrameVisibility(frames[current], false)
						current = (current % #frames) + 1
						setFrameVisibility(frames[current], true)
					end
				else task.wait(0.2) end
			else task.wait(0.5) end
		end
	end)
end

return WireframeRenderer