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

    wchar_t local_py[MAX_PATH];
    wsprintfW(local_py, L"%s\\python\\pythonw.exe", dir_path);

    const wchar_t* py_candidates[] = {
        local_py,
        L"D:\\MSYS2\\clang64\\bin\\python3w.exe",
        L"D:\\MSYS2\\clang64\\bin\\pythonw.exe",
        L"D:\\MSYS2\\clang64\\bin\\python3.exe",
        L"pythonw.exe",
        L"python3w.exe",
        L"python.exe",
        L"py.exe",
    };

    int candidate_count = (int)(sizeof(py_candidates) / sizeof(py_candidates[0]));
    PROCESS_INFORMATION pi;

    for (int i = 0; i < candidate_count; ++i) {
        STARTUPINFOW si;
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        ZeroMemory(&pi, sizeof(pi));

        wchar_t cmd_line[MAX_PATH * 3];
        wsprintfW(cmd_line, L"\"%s\" \"%s\"", py_candidates[i], script_path);

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
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            return 0;
        }
    }

    MessageBoxW(NULL,
        L"Para iniciar el Launcher de PES 2017 se requiere tener instalado Python 3.\n\n"
        L"Puedes descargarlo e instalarlo gratis desde python.org o la Microsoft Store.",
        L"Pro Evolution Soccer 2017", MB_ICONINFORMATION | MB_OK);

    return 1;
}
