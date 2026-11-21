/* Offline PS4 services. This port runs without PSN, so online libraries (NP, HTTP, SSL), the
 * system dialogs and the platform telemetry hooks (coredump, share play, live streaming, screenshots,
 * video recording, voice chat, USB storage) answer as an offline console would:
 *  - dialogs and telemetry succeed and do nothing (UpdateStatus 0 = SCE_COMMON_DIALOG_STATUS_NONE),
 *  - NP calls report "signed out", HTTP/SSL report a network failure, NetCtl "not connected".
 * Calls with real semantics (save data, app content, RTC, trophies, kernel) are NOT stubbed here:
 * they stay unresolved so the probe stops at the first use instead of hiding it. */
#include "runtime.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#ifdef _WIN32
#include <direct.h>
#define usb_stat _stat64
#define usb_mkdir(p) _mkdir(p)
typedef struct _stat64 UsbStat;
#else
#include <unistd.h>
#define usb_stat stat
#define usb_mkdir(p) mkdir((p), 0755)
typedef struct stat UsbStat;
#endif
#define OFF_NP_SIGNED_OUT ((int32_t)0x80550006)
#define OFF_HTTP_NETWORK ((int32_t)0x80431063)
#define OFF_NET_CTL_NOT_CONNECTED ((int32_t)0x80412108)
#define OFF_NET_EINVAL ((int32_t)0x80410116)
static ABI int32_t off_ok(void) { return 0; }
static ABI int32_t off_np(void) { return OFF_NP_SIGNED_OUT; }
static ABI int32_t off_http(void) { return OFF_HTTP_NETWORK; }
static ABI int32_t off_netctl(void) { return OFF_NET_CTL_NOT_CONNECTED; }
static ABI int32_t off_net_inval(void) { return OFF_NET_EINVAL; }
/* libScePosix sockets: no network, every call fails with ENETUNREACH (51 on the PS4). */
static ABI int64_t off_posix_net(void) { *runtime_errno()=51; return -1; }

/* Virtual USB storage (/usb0 -> ./WEPES or <user>/WEPES) for PES 2017 Option Files. */
static int usb_dialog_status = 0;
static int usb_is_dir(const char *path) {
    UsbStat st;
    return usb_stat(path, &st) == 0 && (st.st_mode & S_IFDIR) != 0;
}
static void usb_resolve_wepes(char *out, size_t size) {
    if (usb_is_dir("WEPES")) { snprintf(out, size, "WEPES"); return; }
    char user_wepes[512];
    snprintf(user_wepes, sizeof(user_wepes), "%s/WEPES", runtime_file_user_dir());
    if (usb_is_dir(user_wepes)) { snprintf(out, size, "%s", user_wepes); return; }
    usb_mkdir("WEPES");
    if (usb_is_dir("WEPES")) { snprintf(out, size, "WEPES"); return; }
    usb_mkdir(user_wepes);
    snprintf(out, size, "%s", user_wepes);
}
static const char *usb_strip_wepes(const char *path) {
    if (!path) return "";
    while (*path == '/' || *path == '\\') ++path;
    if ((path[0] == 'W' || path[0] == 'w') && (path[1] == 'E' || path[1] == 'e') &&
        (path[2] == 'P' || path[2] == 'p') && (path[3] == 'E' || path[3] == 'e') &&
        (path[4] == 'S' || path[4] == 's') &&
        (path[5] == '\0' || path[5] == '/' || path[5] == '\\')) {
        path += 5;
        while (*path == '/' || *path == '\\') ++path;
    }
    return path;
}
static ABI int32_t usb_init(void *param) { (void)param; return 0; }
static ABI int32_t usb_term(void) { return 0; }
static ABI int32_t usb_get_device_list(uint32_t *list, int32_t *num) {
    if (list) list[0] = 1;
    if (num) *num = 1;
    return 0;
}
static ABI int32_t usb_get_device_info(uint32_t dev_id, void *info) {
    (void)dev_id;
    if (info) {
        uint64_t *u64 = (uint64_t *)info;
        u64[0] = 16ULL * 1024ULL * 1024ULL * 1024ULL;
        u64[1] = 16ULL * 1024ULL * 1024ULL * 1024ULL;
    }
    return 0;
}
static ABI int32_t usb_is_exist(uint32_t dev_id, const char *path, int32_t *exist) {
    (void)dev_id;
    char wepes[512], full[768];
    usb_resolve_wepes(wepes, sizeof(wepes));
    const char *sub = usb_strip_wepes(path);
    if (sub[0]) snprintf(full, sizeof(full), "%s/%s", wepes, sub);
    else snprintf(full, sizeof(full), "%s", wepes);
    size_t len = strlen(full);
    while (len > 1 && (full[len - 1] == '/' || full[len - 1] == '\\')) full[--len] = '\0';
    UsbStat st;
    int found = (usb_stat(full, &st) == 0) ? 1 : 0;
    if (exist) *exist = found;
    return found;
}
static ABI int32_t usb_request_map(uint32_t dev_id, const char *target_dir, uint32_t access_mode,
                                   uint32_t options, char *mount_point, uint64_t *avail_size) {
    (void)dev_id; (void)access_mode; (void)options;
    char wepes[512], host[768];
    usb_resolve_wepes(wepes, sizeof(wepes));
    const char *sub = usb_strip_wepes(target_dir);
    if (sub[0]) snprintf(host, sizeof(host), "%s/%s", wepes, sub);
    else snprintf(host, sizeof(host), "%s", wepes);
    runtime_file_mount("/usb0", host);
    if (mount_point) snprintf(mount_point, 16, "/usb0");
    if (avail_size) *avail_size = 16ULL * 1024ULL * 1024ULL * 1024ULL;
    printf("Runtime: UsbStorage mounted /usb0 -> %s (target=%s)\n", host, target_dir ? target_dir : "");
    return 0;
}
static ABI int32_t usb_request_unmap(uint32_t dev_id, const char *mount_point) {
    (void)dev_id;
    runtime_file_unmount((mount_point && mount_point[0]) ? mount_point : "/usb0");
    return 0;
}
static ABI int32_t usb_dialog_init(void) { usb_dialog_status = 0; return 0; }
static ABI int32_t usb_dialog_term(void) { usb_dialog_status = 0; return 0; }
static ABI int32_t usb_dialog_open(const void *param) { (void)param; usb_dialog_status = 3; return 0; }
static ABI int32_t usb_dialog_update_status(void) { return usb_dialog_status; }
static ABI int32_t usb_dialog_get_result(void *result) {
    if (result) {
        *(int32_t *)((char *)result + 8) = 0;
        *(uint32_t *)((char *)result + 12) = 1;
    }
    return 0;
}
static ABI int32_t usb_dialog_close(void) { usb_dialog_status = 0; return 0; }
static const RuntimeExport exports[]={
    {"socket",off_posix_net}, {"bind",off_posix_net}, {"listen",off_posix_net}, {"accept",off_posix_net},
    {"connect",off_posix_net}, {"send",off_posix_net}, {"sendto",off_posix_net}, {"recv",off_posix_net},
    {"recvfrom",off_posix_net}, {"setsockopt",off_posix_net}, {"getsockopt",off_posix_net},
    {"getsockname",off_posix_net}, {"getpeername",off_posix_net}, {"select",off_posix_net},
    {"inet_pton",off_posix_net}, {"inet_ntop",off_posix_net},
    {"sceNpRegisterStateCallbackForToolkit",off_ok},
    {"sceInvitationDialogOpen",off_ok},
    {"sceScreenShotEnable",off_ok},
    {"sceCoredumpAttachUserFile",off_ok},
    {"sceGameCustomDataDialogOpen",off_ok},
    {"sceInvitationDialogGetResult",off_ok},
    {"sceInvitationDialogUpdateStatus",off_ok},
    {"sceErrorDialogTerminate",off_ok},
    {"sceGameLiveStreamingTerminate",off_ok},
    {"sceNpSnsFacebookDialogGetResult",off_ok},
    {"sceNetResolverAbort",off_ok},
    {"sceInvitationDialogTerminate",off_ok},
    {"sceUsbStorageInit",usb_init},
    {"sceSigninDialogUpdateStatus",off_ok},
    {"sceNpSnsFacebookDialogTerminate",off_ok},
    {"sceUsbStorageDialogOpen",usb_dialog_open},
    {"sceSharePlaySetProhibition",off_ok},
    {"sceCoredumpWriteUserData",off_ok},
    {"sceVoicePausePortAll",off_ok},
    {"sceGameLiveStreamingEnableLiveStreaming",off_ok},
    {"sceErrorDialogClose",off_ok},
    {"sceVideoRecordingSetInfo",off_ok},
    {"sceNpSnsFacebookDialogUpdateStatus",off_ok},
    {"sceUsbStorageRequestUnmap",usb_request_unmap},
    {"sceWebBrowserDialogOpen",off_ok},
    {"sceUsbStorageGetDeviceInfo",usb_get_device_info},
    {"sceWebBrowserDialogUpdateStatus",off_ok},
    {"sceNpSnsFacebookDialogOpen",off_ok},
    {"sceGameCustomDataDialogTerminate",off_ok},
    {"sceUsbStorageRequestMap",usb_request_map},
    {"sceUsbStorageDialogInitialize",usb_dialog_init},
    {"sceVoiceResumePortAll",off_ok},
    {"sceNpCheckCallbackForLib",off_ok},
    {"sceSigninDialogOpen",off_ok},
    {"sceWebBrowserDialogInitialize",off_ok},
    {"sceUsbStorageDialogClose",usb_dialog_close},
    {"sceCoredumpGetStopInfoCpu",off_ok},
    {"sceSigninDialogTerminate",off_ok},
    {"sceErrorDialogOpen",off_ok},
    {"sceSigninDialogClose",off_ok},
    {"sceCoredumpAttachMemoryRegionAsUserFile",off_ok},
    {"sceSigninDialogInitialize",off_ok},
    {"sceUsbStorageDialogUpdateStatus",usb_dialog_update_status},
    {"sceUsbStorageGetDeviceList",usb_get_device_list},
    {"sceSigninDialogGetResult",off_ok},
    {"sceCoredumpGetStopInfoGpu",off_ok},
    {"sceNpCommerceDialogClose",off_ok},
    {"sceUsbStorageDialogTerminate",usb_dialog_term},
    {"sceWebBrowserDialogTerminate",off_ok},
    {"sceSharePlayGetCurrentConnectionInfo",off_ok},
    {"sceGameCustomDataDialogUpdateStatus",off_ok},
    {"sceWebBrowserDialogClose",off_ok},
    {"sceNpCommerceDialogGetResult",off_ok},
    {"sceCoredumpGetThreadContextInfo",off_ok},
    {"sceGameCustomDataDialogGetResult",off_ok},
    {"sceNpSnsFacebookDialogInitialize",off_ok},
    {"sceScreenShotDisable",off_ok},
    {"sceUsbStorageIsExist",usb_is_exist},
    {"sceSharePlayTerminate",off_ok},
    {"sceUsbStorageDialogGetResult",usb_dialog_get_result},
    {"sceWebBrowserDialogGetResult",off_ok},
    {"sceNpProfileDialogClose",off_ok},
    {"sceUsbStorageTerm",usb_term},
    {"sceImeDialogGetPanelSize",off_ok},
    {"sceErrorDialogUpdateStatus",off_ok},
    {"sceInvitationDialogClose",off_ok},
    {"sceGameCustomDataDialogInitialize",off_ok},
    {"sceInvitationDialogInitialize",off_ok},
    {"sceNpUnregisterStateCallbackForToolkit",off_ok},
    {"sceNetCtlTerm",off_ok},
    {"sceNpInGameMessageDeleteHandle",off_np},
    {"sceNpTusSetDataVUser",off_np},
    {"sceNpTusDeleteMultiSlotData",off_np},
    {"sceNpTusSetMultiSlotVariableVUser",off_np},
    {"sceNpWordFilterCensorComment",off_np},
    {"sceNpScoreRecordGameDataAsync",off_np},
    {"sceNpMatching2GetRoomDataExternalList",off_np},
    {"sceNpWebApiUnregisterServicePushEventCallback",off_np},
    {"sceNpTusCreateRequest",off_np},
    {"sceNpTusSetData",off_np},
    {"sceNpMatching2GetRoomMemberDataInternal",off_np},
    {"sceNpWebApiDeleteHandle",off_np},
    {"sceNpAuthCreateRequest",off_np},
    {"sceNpWebApiCreateHandle",off_np},
    {"sceNpScoreGetFriendsRankingAsync",off_np},
    {"sceNpScoreGetFriendsRanking",off_np},
    {"sceNpScoreGetRankingByNpId",off_np},
    {"sceNpGetAccountId",off_np},
    {"sceNpScoreRecordScoreAsync",off_np},
    {"sceNpTusCreateNpTitleCtx",off_np},
    {"sceNpInGameMessageTerminate",off_np},
    {"sceNpBandwidthTestGetStatus",off_np},
    {"sceNpTusSetMultiSlotVariable",off_np},
    {"sceNpTusDeleteRequest",off_np},
    {"sceNpAuthAbortRequest",off_np},
    {"sceNpTusAddAndGetVariable",off_np},
    {"sceNpCommerceShowPsStoreIcon",off_np},
    {"sceNpCommerceHidePsStoreIcon",off_np},
    {"sceNpTusGetMultiSlotVariable",off_np},
    {"sceNpInGameMessageInitialize",off_np},
    {"sceNpCreateRequest",off_np},
    {"sceNpTusGetDataVUser",off_np},
    {"sceNpTusDeleteNpTitleCtx",off_np},
    {"sceNpWordFilterCreateRequest",off_np},
    {"sceNpWordFilterCreateAsyncRequest",off_np},
    {"sceNpLookupCreateRequest",off_np},
    {"sceNpMatching2SendRoomMessage",off_np},
    {"sceNpWordFilterSanitizeComment",off_np},
    {"sceNpScoreGetGameDataAsync",off_np},
    {"sceNpBandwidthTestInitStart",off_np},
    {"sceNpMatching2GetRoomDataInternal",off_np},
    {"sceNpWebApiSendRequest2",off_np},
    {"sceNpWebApiRegisterServicePushEventCallback",off_np},
    {"sceNpScorePollAsync",off_np},
    {"sceNpMatching2SetUserInfo",off_np},
    {"sceNpInGameMessageSendData",off_np},
    {"sceNpSnsFacebookCreateRequest",off_np},
    {"sceNpMatching2SendRoomChatMessage",off_np},
    {"sceNpWebApiDeleteServicePushEventFilter",off_np},
    {"sceNpBandwidthTestShutdown",off_np},
    {"sceNpSnsFacebookDeleteRequest",off_np},
    {"sceNpWordFilterDeleteRequest",off_np},
    {"sceNpMatching2GetUserInfoList",off_np},
    {"sceNpWordFilterCreateTitleCtx",off_np},
    {"sceNpWordFilterAbortRequest",off_np},
    {"sceNpScoreGetRankingByNpIdAsync",off_np},
    {"sceNpScoreGetRankingByRangeAsync",off_np},
    {"sceNpInGameMessageCreateHandle",off_np},
    {"sceNpWebApiCreateServicePushEventFilter",off_np},
    {"sceNpTssGetData",off_np},
    {"sceNpWordFilterDeleteTitleCtx",off_np},
    {"sceNpMatching2SignalingGetConnectionInfo",off_np},
    {"sceNpMatching2RegisterRoomMessageCallback",off_np},
    {"sceNpTusGetMultiSlotVariableVUser",off_np},
    {"sceNpTusAddAndGetVariableVUser",off_np},
    {"sceNpWordFilterPollAsync",off_np},
    {"sceNpInGameMessagePrepare",off_np},
    {"sceNpSnsFacebookGetAccessToken",off_np},
    {"sceNpTusGetData",off_np},
    {"sceNpTusDeleteMultiSlotDataVUser",off_np},
    {"sceSslGetSerialNumber",off_http},
    {"sceHttpsSetSslCallback",off_http},
    {"sceHttpAbortRequest",off_http},
    {"sceHttpUriParse",off_http},
    {"sceHttpCreateConnection",off_http},
    {"sceSslFreeCaCerts",off_http},
    {"sceHttpCreateRequest",off_http},
    {"sceHttpSetSendTimeOut",off_http},
    {"sceHttpSetRecvTimeOut",off_http},
    {"sceHttpUriEscape",off_http},
    {"sceHttpsUnloadCert",off_http},
    {"sceNetCtlGetResult",off_netctl},
    {"sceNetGetMacAddress",off_net_inval},
};
uintptr_t runtime_offline_resolve(const char *name) { return RUNTIME_LOOKUP(exports,name); }
