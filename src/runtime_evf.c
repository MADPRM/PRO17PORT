/* PS4 kernel event flags: a 64-bit pattern that threads set, clear and wait on.
 * Handles are zeroed low records (runtime_low_alloc) the guest sees by address, like the
 * rwlock and mutex handles. One registry lock guards lifetime and the pattern; each flag has
 * its own condition variable. */
#define _GNU_SOURCE
#include "runtime.h"
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <errno.h>

#define ERR(n) ((int32_t)(UINT32_C(0x80020000)|(n)))
#define EVF_ESRCH ERR(3)
#define EVF_EBUSY ERR(16)
#define EVF_EINVAL ERR(22)
#define EVF_ETIMEDOUT ERR(60)
#define EVF_ECANCELED ERR(85)
#define WAIT_AND 0x01u
#define WAIT_OR 0x02u
#define CLEAR_ALL 0x10u
#define CLEAR_PAT 0x20u
#define ATTR_MULTI 0x200u

typedef struct Evf {
    pthread_cond_t changed;
    uint64_t pattern;
    uint32_t attr;
    unsigned waiters;
    int deleting;
    char name[32];
    struct Evf *next;
} Evf;
static pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER;
static Evf *registry;
static size_t created, deleted, sets, waits_blocked;

static Evf *find_locked(Evf *handle) {
    for (Evf *e=registry; e; e=e->next) if (e==handle) return e;
    return NULL;
}
static ABI int32_t evf_create(Evf **out,const char *name,uint32_t attr,uint64_t initial,const void *opt) {
    (void)opt;
    if (!out || !name) return EVF_EINVAL;
    Evf *e=runtime_low_alloc(sizeof(*e));
    if (!e) return ERR(12);
    if (pthread_cond_init(&e->changed,NULL)) { runtime_low_free(e); return ERR(12); }
    e->pattern=initial; e->attr=attr;
    strncpy(e->name,name,sizeof(e->name)-1);
    pthread_mutex_lock(&lock);
    e->next=registry; registry=e; ++created;
    pthread_mutex_unlock(&lock);
    *out=e; return 0;
}
static ABI int32_t evf_delete(Evf *handle) {
    pthread_mutex_lock(&lock);
    Evf *e=find_locked(handle);
    if (!e) { pthread_mutex_unlock(&lock); return EVF_ESRCH; }
    e->deleting=1;
    pthread_cond_broadcast(&e->changed);
    while (e->waiters) pthread_cond_wait(&e->changed,&lock); /* woken waiters leave with ECANCELED */
    Evf **link=&registry;
    while (*link!=e) link=&(*link)->next;
    *link=e->next; ++deleted;
    pthread_mutex_unlock(&lock);
    pthread_cond_destroy(&e->changed);
    runtime_low_free(e);
    return 0;
}
static ABI int32_t evf_set(Evf *handle,uint64_t bits) {
    pthread_mutex_lock(&lock);
    Evf *e=find_locked(handle);
    if (!e || e->deleting) { pthread_mutex_unlock(&lock); return EVF_ESRCH; }
    e->pattern|=bits; ++sets;
    pthread_cond_broadcast(&e->changed);
    pthread_mutex_unlock(&lock);
    return 0;
}
static ABI int32_t evf_clear(Evf *handle,uint64_t bits) {
    pthread_mutex_lock(&lock);
    Evf *e=find_locked(handle);
    if (!e || e->deleting) { pthread_mutex_unlock(&lock); return EVF_ESRCH; }
    e->pattern&=bits; /* keeps only the bits set in the argument */
    pthread_mutex_unlock(&lock);
    return 0;
}
static int satisfied(const Evf *e,uint64_t want,uint32_t mode) {
    return (mode&WAIT_AND) ? (e->pattern&want)==want : (e->pattern&want)!=0;
}
static int32_t wait_locked(Evf *e,uint64_t want,uint32_t mode,uint64_t *result,uint32_t *timeout_us,int block) {
    struct timespec end={0,0};
    uint64_t start_us=0;
    if (block && timeout_us) {
        struct timespec now; clock_gettime(CLOCK_REALTIME,&now);
        start_us=(uint64_t)now.tv_sec*1000000u+(uint64_t)now.tv_nsec/1000u;
        uint64_t deadline=start_us+*timeout_us;
        end.tv_sec=(time_t)(deadline/1000000u); end.tv_nsec=(long)(deadline%1000000u*1000u);
    }
    int32_t r=0;
    ++e->waiters;
    while (!e->deleting && !satisfied(e,want,mode)) {
        if (!block) { r=EVF_EBUSY; break; }
        ++waits_blocked;
        int c=(timeout_us ? pthread_cond_timedwait(&e->changed,&lock,&end) : pthread_cond_wait(&e->changed,&lock));
        if (c==ETIMEDOUT && !satisfied(e,want,mode)) { r=EVF_ETIMEDOUT; break; }
    }
    if (!r && e->deleting) r=EVF_ECANCELED;
    if (result) *result=e->pattern;
    if (!r) {
        if (mode&CLEAR_ALL) e->pattern=0;
        else if (mode&CLEAR_PAT) e->pattern&=~want;
    }
    if (block && timeout_us) {
        struct timespec now; clock_gettime(CLOCK_REALTIME,&now);
        uint64_t used=(uint64_t)now.tv_sec*1000000u+(uint64_t)now.tv_nsec/1000u-start_us;
        *timeout_us = (r==EVF_ETIMEDOUT || used>=*timeout_us) ? 0 : (uint32_t)(*timeout_us-used);
    }
    --e->waiters;
    if (e->deleting) pthread_cond_broadcast(&e->changed); /* lets evf_delete finish */
    return r;
}
static int32_t do_wait(Evf *handle,uint64_t want,uint32_t mode,uint64_t *result,uint32_t *timeout_us,int block) {
    if (!want || !(mode&(WAIT_AND|WAIT_OR)) || ((mode&WAIT_AND) && (mode&WAIT_OR))) return EVF_EINVAL;
    pthread_mutex_lock(&lock);
    Evf *e=find_locked(handle);
    if (!e || e->deleting) { pthread_mutex_unlock(&lock); return EVF_ESRCH; }
    if (!(e->attr&ATTR_MULTI) && e->waiters) { pthread_mutex_unlock(&lock); return EVF_EBUSY; }
    int32_t r=wait_locked(e,want,mode,result,timeout_us,block);
    pthread_mutex_unlock(&lock);
    return r;
}
static ABI int32_t evf_wait(Evf *handle,uint64_t want,uint32_t mode,uint64_t *result,uint32_t *timeout_us) {
    return do_wait(handle,want,mode,result,timeout_us,1);
}
static ABI int32_t evf_poll(Evf *handle,uint64_t want,uint32_t mode,uint64_t *result) {
    return do_wait(handle,want,mode,result,NULL,0);
}
static const RuntimeExport exports[]={
    {"sceKernelCreateEventFlag",evf_create}, {"sceKernelDeleteEventFlag",evf_delete},
    {"sceKernelSetEventFlag",evf_set}, {"sceKernelClearEventFlag",evf_clear},
    {"sceKernelWaitEventFlag",evf_wait}, {"sceKernelPollEventFlag",evf_poll},
};
uintptr_t runtime_evf_resolve(const char *name) { return RUNTIME_LOOKUP(exports,name); }
void runtime_evf_report(void) {
    pthread_mutex_lock(&lock);
    printf("Runtime: event flags created=%zu, deleted=%zu, sets=%zu, blocked waits=%zu\n",created,deleted,sets,waits_blocked);
    pthread_mutex_unlock(&lock);
}
