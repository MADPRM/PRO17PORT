#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

static int file_exists(const wchar_t* path) {
    DWORD attr = GetFileAttributesW(path);
    return (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY));
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {
    (void)hInstance;
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

    wchar_t exe_path[MAX_PATH];
    DWORD len = GetModuleFileNameW(NULL, exe_path, MAX_PATH);
    if (len == 0 || len >= MAX_PATH) {
        return 1;
    }

    wchar_t dir_path[MAX_PATH];
    wcscpy_s(dir_path, MAX_PATH, exe_path);
    wchar_t* last_slash = wcsrchr(dir_path, L'\\');
    if (last_slash) {
        *last_slash = L'\0';
    }

    wchar_t script_path[MAX_PATH];
    wsprintfW(script_path, L"%s\\launcher_pes2017.py", dir_path);
    if (!file_exists(script_path)) {
        wsprintfW(script_path, L"%s\\PRO17PORT\\launcher_pes2017.py", dir_path);
    }
    if (!file_exists(script_path)) {
        MessageBoxW(NULL, L"No se encontró launcher_pes2017.py junto a PES2017_Launcher.exe.",
                    L"Pro Evolution Soccer 2017", MB_ICONERROR | MB_OK);
        return 1;
    }

    // Prepend MSYS2 bin and local out folder to PATH so runtime DLLs are found
    wchar_t old_path[16384];
    wchar_t new_path[16384];
    if (GetEnvironmentVariableW(L"PATH", old_path, 16384) > 0) {
        wsprintfW(new_path, L"D:\\MSYS2\\clang64\\bin;%s\\out;%s\\PRO17PORT\\out;%s", dir_path, dir_path, old_path);
        SetEnvironmentVariableW(L"PATH", new_path);
    }

    wchar_t local_appdata[MAX_PATH];
    wchar_t prog_files[MAX_PATH];
    local_appdata[0] = L'\0';
    prog_files[0] = L'\0';
    GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata, MAX_PATH);
    GetEnvironmentVariableW(L"ProgramFiles", prog_files, MAX_PATH);

    wchar_t py_paths[20][MAX_PATH];
    int py_count = 0;

    // 1. Local embedded python folder next to launcher
    wsprintfW(py_paths[py_count++], L"%s\\python\\pythonw.exe", dir_path);
    wsprintfW(py_paths[py_count++], L"%s\\python\\python.exe", dir_path);

    // 2. MSYS2 clang64 developer binaries
    wsprintfW(py_paths[py_count++], L"D:\\MSYS2\\clang64\\bin\\python3w.exe");
    wsprintfW(py_paths[py_count++], L"D:\\MSYS2\\clang64\\bin\\pythonw.exe");
    wsprintfW(py_paths[py_count++], L"D:\\MSYS2\\clang64\\bin\\python3.exe");

    // 3. Common Windows Python install locations (Python 3.14 down to 3.8)
    const wchar_t* ver_tags[] = { L"314", L"313", L"312", L"311", L"310", L"39", L"38" };
    for (int v = 0; v < 7; ++v) {
        if (local_appdata[0]) {
            wchar_t cand[MAX_PATH];
            wsprintfW(cand, L"%s\\Programs\\Python\\Python%s\\pythonw.exe", local_appdata, ver_tags[v]);
            if (file_exists(cand)) {
                wcscpy_s(py_paths[py_count++], MAX_PATH, cand);
                break;
            }
        }
        if (prog_files[0]) {
            wchar_t cand[MAX_PATH];
            wsprintfW(cand, L"%s\\Python%s\\pythonw.exe", prog_files, ver_tags[v]);
            if (file_exists(cand)) {
                wcscpy_s(py_paths[py_count++], MAX_PATH, cand);
                break;
            }
        }
    }

    // 4. System PATH executables
    wsprintfW(py_paths[py_count++], L"pythonw.exe");
    wsprintfW(py_paths[py_count++], L"python3w.exe");
    wsprintfW(py_paths[py_count++], L"python.exe");
    wsprintfW(py_paths[py_count++], L"py.exe");

    PROCESS_INFORMATION pi;

    for (int i = 0; i < py_count; ++i) {
        // Discard dummy Windows Store execution aliases (WindowsApps)
        wchar_t resolved[MAX_PATH];
        if (SearchPathW(NULL, py_paths[i], L".exe", MAX_PATH, resolved, NULL) > 0) {
            if (wcsstr(resolved, L"WindowsApps") != NULL || wcsstr(resolved, L"windowsapps") != NULL) {
                continue;
            }
        }

        STARTUPINFOW si;
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        ZeroMemory(&pi, sizeof(pi));

        wchar_t cmd_line[MAX_PATH * 3];
        wsprintfW(cmd_line, L"\"%s\" \"%s\"", py_paths[i], script_path);

        BOOL ok = CreateProcessW(
            NULL,
            cmd_line,
            NULL,
            NULL,
            FALSE,
            CREATE_NO_WINDOW,
            NULL,
            dir_path,
            &si,
            &pi
        );

        if (ok) {
            // Verify if the process didn't die immediately (e.g. broken alias or launch error)
            DWORD wait_res = WaitForSingleObject(pi.hProcess, 350);
            if (wait_res == WAIT_OBJECT_0) {
                DWORD exit_code = 0;
                GetExitCodeProcess(pi.hProcess, &exit_code);
                CloseHandle(pi.hProcess);
                CloseHandle(pi.hThread);
                if (exit_code != 0) {
                    continue;
                }
                return 0;
            }
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            return 0;
        }
    }

    MessageBoxW(NULL,
        L"No se encontró Python 3 instalado en el sistema para ejecutar el Launcher de PES 2017.\n\n"
        L"Por favor descarga e instala Python 3 (marcando la opción 'Add python.exe to PATH'):\n"
        L"https://www.python.org/downloads/\n\n"
        L"Nota: Recuerda que también requieres tu carpeta del juego de PS4 (CUSA04957).\n\n"
        L"--------------------------------------------------\n\n"
        L"Python 3 was not found on your system to run the PES 2017 Launcher.\n\n"
        L"Please install Python 3 (make sure to check 'Add python.exe to PATH'):\n"
        L"https://www.python.org/downloads/\n\n"
        L"Note: You also need your PS4 game dump folder (CUSA04957).",
        L"Pro Evolution Soccer 2017 - Launcher", MB_ICONWARNING | MB_OK);

    return 1;
}
