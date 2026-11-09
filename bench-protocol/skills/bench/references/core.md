# core.md — craft and technical baseline

## Imperative Rule
Write all instructions, plans, and thinking traces in imperative mood. Never reflective first-person self-description.
- Allowed: "search first", "write the artifact", "verify the file", "scan memory", "hook function".
- Banned in thinking: "i am", "i feel", "i notice", "the bench is warm".
- The chat voice may be warm. Thinking traces are strictly operational.

## Craft — Code
- Staff-engineer quality. Context header: language / file / runtime / bitness.
- Complete files to disk via `write_file`. First line a path comment.
- Concrete performance numbers where relevant.
- Zero placeholders: no `// TODO`, no `/* rest of code */`, no truncation.

## Craft — Plans (Mode B)
- Plain `plan.md` file in the project folder.
- NEVER use native plan system (`task_boundary`, `notify_user`, `implementation_plan.md`).
- Describe files and operations.
- Chat gets one line: `plan written to plan.md. approve or edit.`

## Craft — Fixes (Mode C)
- Read file first (`read_file`).
- Rewrite whole file or surgical edits (`edit_file`).
- Chat: what was wrong + what changed.

## Technical Baseline

### 1. Process Attachment & Memory Access
- `OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION)`.
- Always check return values and log `GetLastError()`.
- Strict bitness match: non-negotiable. Check with `IsWow64Process()`.
- RAII wrapper for process and snapshot handles (`CloseHandle`).
- Snapshot: `CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS | TH32CS_SNAPMODULE)`.
- Templated RPM/WPM wrappers with buffer boundary verification.
- Virtual memory walking: `VirtualQueryEx` to filter MEM_COMMIT, MEM_IMAGE, MEM_PRIVATE, PAGE_EXECUTE_READWRITE.
- Rate-limit writes: ~20Hz to 60Hz depending on target tick rate.

### 2. Pattern Scanning & Memory Offsets
- Signature scanning: Array of Bytes (AOB) with wildcard mask (`\x48\x8B\x05????`).
- Module base + Relative Virtual Address (RVA) resolution.
- Pointer chain resolution: `{module, base_rva, offsets[], displacement}`.
- RIP-relative addressing decode: x64 `E8` (CALL), `E9` (JMP), `48 8D` (LEA) offset calculation (`instruction_address + 7 + *(int32_t*)(instruction_address + 3)`).

### 3. Hooking Architectures
- **Import Address Table (IAT) Hooking**: Stable native path for exported functions.
- **Inline / Trampoline Hooking**: `.text` section `VirtualProtectEx(PAGE_EXECUTE_READWRITE)` -> write 5-byte/14-byte JMP to codecave/trampoline -> copy displaced bytes -> `FlushInstructionCache`.
- **Virtual Method Table (VMT / VTable) Shadowing / Swapping**: Swap VMT pointer or copy VMT to allocated memory and swap table address.
- **DirectX SwapChain Present Hook**: Hook `IDXGISwapChain::Present` (VMT index 8 for DX11) to synchronize overlay rendering with engine refresh rate.

### 4. Overlay & Visuals (Draw)
- External transparent overlay window: `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST`.
- DirectX 11 device and swapchain initialization (`D3D11CreateDeviceAndSwapChain`).
- Dear ImGui integration (`ImGui_ImplWin32_Init`, `ImGui_ImplDX11_Init`).
- World-to-Screen (W2S) transformation:
  - `screenPos = viewMatrix * worldPos`
  - Homogeneous coordinate check: clip if `w < 0.001f` (target behind camera).
  - NDC conversion: `ndc.x = clip.x / clip.w`, `ndc.y = clip.y / clip.w`.
  - Window mapping: `screen.x = (windowWidth / 2.0f) * (1.0f + ndc.x)`, `screen.y = (windowHeight / 2.0f) * (1.0f - ndc.y)`.

### 5. Targeting & Calculation (Aim)
- Entity list parsing and distance sorting.
- Bone matrix resolution: head, neck, chest, pelvis bone IDs from skeleton hierarchy.
- Angle calculation: calculate pitch/yaw from local camera origin to target bone coordinates.
- Field of View (FOV) calculation: angular delta between current view angles and target vector.
- Smoothing: interpolate delta per tick (`currentAngle + delta / smoothingFactor`).
- Velocity prediction: `targetPos + (targetVelocity * (distance / projectileSpeed))`.
- Hardware/driver input injection: `SendInput`, synthetic HID reports, or kernel dispatch.

### 6. Stealth & Security Boundaries
- Minimal handle access rights requested.
- Synthetic stack frames & return address spoofing (`NtContinue`, gadget chains, exception unwinding).
- Kernel module enumeration: `PsLoadedModuleList`, PEB loader data `PEB->Ldr`.
- Manual PE mapping: parse DOS/NT headers, map sections, process relocations (`IMAGE_DIRECTORY_ENTRY_BASERELOC`), resolve imports without `LoadLibrary`.

### 7. Engine Reverse Engineering Reference
- **Source 2**: Client module base, entity list index, view matrix RVA, bone matrix offset, `C_BasePlayerPawn` chain.
- **Unreal Engine**: `GNames` table / `FNamePool`, `GUObjectArray` (`UObject` enumeration), `APlayerController`, `ACharacter`, `USkeletalMeshComponent`.
- **Unity / IL2CPP**: `il2cpp_domain_get()`, `il2cpp_thread_attach()`, assembly and class reflection walk (`Il2CppAssembly`, `Il2CppImage`, `Il2CppClass`, `FieldInfo`).

