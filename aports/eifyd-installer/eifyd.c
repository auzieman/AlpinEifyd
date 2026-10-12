#define _GNU_SOURCE
#include <Elementary.h>
#include <Ecore.h>
#include <Eina.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <sys/stat.h>

/* Native EFL presentation; all installation semantics live in the Python API. */
#define BACKEND "/usr/libexec/eifyd-install"
#define MAX_ITEMS 256
typedef struct { char kind[16], path[128], parent[128], label[256]; double gib; } Device;
typedef struct { char group[96], kind[16], name[128]; Evas_Object *check; } Package;
typedef struct {
    Evas_Object *win, *body, *pages[6], *nav[5], *back, *next, *status;
    Evas_Object *disk, *mode, *root_size, *size_slider, *layout_text;
    Evas_Object *root, *home, *bootpart, *esp, *format_root, *format_home, *format_boot;
    Evas_Object *layout_holder, *new_box, *existing_box, *host, *user, *zone, *password, *repeat;
    Evas_Object *review, *progress, *popup, *save_path;
    Device devices[MAX_ITEMS]; int device_count;
    Evas_Object *selectors[5]; int selector_count;
    Package packages[MAX_ITEMS]; int package_count;
    int page, busy, installing, syncing;
    double min_root;
    char firmware[16], token[65];
    pid_t child; int fd, eof;
    Ecore_Fd_Handler *handler; Ecore_Timer *timer;
    Eina_Strbuf *output;
} UI;
static UI ui;
static void show_page(int page);
static void launch_api(int install);
static void refresh_selectors(void);
static void selectors_later(void *data) { (void)data; refresh_selectors(); }

static void expand(Evas_Object *o) {
    evas_object_size_hint_weight_set(o, EVAS_HINT_EXPAND, 0.0);
    evas_object_size_hint_align_set(o, EVAS_HINT_FILL, 0.5);
}
static void pack(Evas_Object *box, Evas_Object *o) {
    elm_box_pack_end(box, o); evas_object_show(o);
}
static Evas_Object *box(Evas_Object *parent, int horizontal) {
    Evas_Object *o = elm_box_add(parent);
    elm_box_horizontal_set(o, horizontal);
    elm_box_padding_set(o, 12, 10);
    expand(o); return o;
}
static Evas_Object *label(Evas_Object *parent, const char *text) {
    Evas_Object *o = elm_label_add(parent);
    elm_label_line_wrap_set(o, ELM_WRAP_WORD);
    elm_object_text_set(o, text); expand(o); pack(parent, o); return o;
}
static Evas_Object *entry(Evas_Object *parent, const char *title, const char *value, int secret) {
    label(parent, title);
    Evas_Object *o = elm_entry_add(parent);
    elm_entry_single_line_set(o, EINA_TRUE);
    elm_entry_scrollable_set(o, EINA_TRUE);
    elm_entry_password_set(o, secret);
    elm_object_text_set(o, value); expand(o); pack(parent, o);
    return o;
}
static char *value(Evas_Object *o) { return elm_entry_markup_to_utf8(elm_object_text_get(o)); }
static Evas_Object *button(Evas_Object *parent, const char *text, Evas_Smart_Cb cb, void *data) {
    Evas_Object *o = elm_button_add(parent);
    elm_object_text_set(o, text);
    evas_object_smart_callback_add(o, "clicked", cb, data);
    pack(parent, o); return o;
}
static Evas_Object *check(Evas_Object *parent, const char *text, int enabled) {
    Evas_Object *o = elm_check_add(parent);
    elm_object_text_set(o, text); elm_check_state_set(o, enabled);
    expand(o); pack(parent, o); return o;
}
static Evas_Object *section(Evas_Object *parent, const char *title) {
    Evas_Object *frame = elm_frame_add(parent);
    elm_object_text_set(frame, title);
    elm_frame_autocollapse_set(frame, EINA_TRUE);
    Evas_Object *content = box(frame, 0);
    elm_object_content_set(frame, content); expand(frame); pack(parent, frame);
    evas_object_show(content);
    return content;
}
static Evas_Object *textview(Evas_Object *parent) {
    Evas_Object *o = elm_entry_add(parent);
    elm_entry_editable_set(o, EINA_FALSE);
    elm_entry_line_wrap_set(o, ELM_WRAP_WORD);
    expand(o); pack(parent, o); return o;
}
static void plain(Evas_Object *o, const char *text) {
    char *markup = elm_entry_utf8_to_markup(text);
    elm_object_text_set(o, markup ? markup : ""); free(markup);
}
static void popup_close(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev;
    if (ui.popup) evas_object_del(ui.popup);
    ui.popup = NULL;
}
static void message(const char *title, const char *text) {
    popup_close(NULL, NULL, NULL);
    ui.popup = elm_popup_add(ui.win);
    elm_object_part_text_set(ui.popup, "title,text", title);
    char *markup = elm_entry_utf8_to_markup(text);
    elm_object_text_set(ui.popup, markup); free(markup);
    Evas_Object *b = elm_button_add(ui.popup);
    elm_object_text_set(b, "OK");
    evas_object_smart_callback_add(b, "clicked", popup_close, NULL);
    elm_object_part_content_set(ui.popup, "button1", b);
    evas_object_show(ui.popup);
}
static void json_string(Eina_Strbuf *s, const char *v) {
    eina_strbuf_append_char(s, '"');
    for (const unsigned char *p = (const unsigned char *)(v ? v : ""); *p; p++) {
        if (*p == '"' || *p == '\\') { eina_strbuf_append_char(s, '\\'); eina_strbuf_append_char(s, *p); }
        else if (*p < 32) eina_strbuf_append_printf(s, "\\u%04x", *p);
        else eina_strbuf_append_char(s, *p);
    }
    eina_strbuf_append_char(s, '"');
}
static void json_field(Eina_Strbuf *s, const char *key, Evas_Object *o) {
    char *v = value(o); eina_strbuf_append_printf(s, ",\"%s\":", key);
    json_string(s, v); free(v);
}
static int existing(void) { return elm_radio_value_get(ui.mode) == 1; }
static Eina_Strbuf *request(int install) {
    Eina_Strbuf *s = eina_strbuf_new();
    eina_strbuf_append(s, "{\"plan\":{\"format\":\"eifyd-install-v2\",\"boot\":\"auto\"");
    json_field(s, "disk", ui.disk); json_field(s, "hostname", ui.host);
    json_field(s, "username", ui.user); json_field(s, "timezone", ui.zone);
    eina_strbuf_append_printf(s, ",\"mode\":\"%s\",\"root_gib\":%.0f", existing() ? "existing" : "new",
                             elm_slider_value_get(ui.size_slider));
    if (existing()) {
        json_field(s, "root", ui.root); json_field(s, "home", ui.home);
        json_field(s, "boot_partition", ui.bootpart); json_field(s, "esp", ui.esp);
    }
    eina_strbuf_append_printf(s, ",\"format_root\":%s,\"format_home\":%s,\"format_boot\":%s",
                             elm_check_state_get(ui.format_root) ? "true" : "false",
                             elm_check_state_get(ui.format_home) ? "true" : "false",
                             elm_check_state_get(ui.format_boot) ? "true" : "false");
    const char *kinds[] = {"apk", "flatpak"};
    for (int k = 0; k < 2; k++) {
        eina_strbuf_append_printf(s, ",\"%s\":[", kinds[k]); int comma = 0;
        for (int i = 0; i < ui.package_count; i++)
            if (!strcmp(ui.packages[i].kind, kinds[k]) && elm_check_state_get(ui.packages[i].check)) {
                if (comma++) eina_strbuf_append_char(s, ',');
                json_string(s, ui.packages[i].name);
            }
        eina_strbuf_append_char(s, ']');
    }
    eina_strbuf_append_char(s, '}');
    if (install) {
        eina_strbuf_append(s, ",\"token\":"); json_string(s, ui.token);
        char *password = value(ui.password);
        eina_strbuf_append(s, ",\"password\":"); json_string(s, password);
        if (password) { memset(password, 0, strlen(password)); free(password); }
    }
    eina_strbuf_append(s, "}\n"); return s;
}
static char *read_backend(const char *action) {
    int fds[2]; if (pipe(fds)) return strdup("");
    pid_t pid = fork();
    if (!pid) {
        close(fds[0]); dup2(fds[1], STDOUT_FILENO); close(fds[1]);
        execl(BACKEND, BACKEND, action, (char *)NULL); _exit(127);
    }
    close(fds[1]);
    if (pid < 0) { close(fds[0]); return strdup(""); }
    Eina_Strbuf *s = eina_strbuf_new(); char buf[4096]; ssize_t n;
    while ((n = read(fds[0], buf, sizeof(buf))) > 0) eina_strbuf_append_length(s, buf, n);
    close(fds[0]); int status; waitpid(pid, &status, 0);
    char *result = strdup(eina_strbuf_string_get(s)); eina_strbuf_free(s);
    return result;
}
static void load_inventory(void) {
    char *inventory = read_backend("inventory"), *save;
    ui.device_count = 0;
    for (char *line = strtok_r(inventory, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
        if (!strncmp(line, "INFO\t", 5)) {
            sscanf(line, "INFO\t%lf\t%15s", &ui.min_root, ui.firmware); continue;
        }
        if (ui.device_count >= MAX_ITEMS) break;
        Device *d = &ui.devices[ui.device_count]; double bytes;
        if (sscanf(line, "%15[^\t]\t%127[^\t]\t%127[^\t]\t%lf\t%255[^\n]", d->kind, d->path, d->parent, &bytes, d->label) == 5) {
            d->gib = bytes / (1024.0 * 1024 * 1024); ui.device_count++;
        }
    }
    free(inventory);
}
static void update_layout(void) {
    char *disk = value(ui.disk); double size = 0;
    for (int i = 0; i < ui.device_count; i++)
        if (!strcmp(disk, ui.devices[i].path)) size = ui.devices[i].gib;
    free(disk);
    double root = elm_slider_value_get(ui.size_slider);
    char text[512];
    snprintf(text, sizeof(text),
             "%s / GRUB • ext4\nBoot: 1 GiB  |  Root: %.0f GiB  |  Home: %.1f GiB\n"
             "A new layout replaces all partitions on the selected disk.",
             ui.firmware, root, size > root + 1.6 ? size - root - 1.6 : 0);
    plain(ui.layout_text, text);
}
static void slider_changed(void *d, Evas_Object *o, void *ev) {
    (void)d; (void)o; (void)ev; if (ui.syncing) return;
    ui.syncing = 1; char text[32];
    snprintf(text, sizeof(text), "%.0f", elm_slider_value_get(ui.size_slider));
    elm_object_text_set(ui.root_size, text); ui.syncing = 0; update_layout();
}
static void size_changed(void *d, Evas_Object *o, void *ev) {
    (void)d; (void)o; (void)ev; if (ui.syncing) return;
    char *s = value(ui.root_size), *end; double n = strtod(s, &end);
    if (*s && !*end) { ui.syncing = 1; elm_slider_value_set(ui.size_slider, n); ui.syncing = 0; update_layout(); }
    free(s); slider_changed(NULL, NULL, NULL);
}
static void save_plan(void *d, Evas_Object *o, void *ev) {
    (void)d; (void)o; (void)ev;
    char *path = value(ui.save_path);
    FILE *file = fopen(path, "wx"); free(path);
    if (!file) { message("Cannot save plan", strerror(errno)); return; }
    fchmod(fileno(file), 0600);
    Eina_Strbuf *payload = request(0);
    /* Save only the plan object, without its API envelope or any password. */
    size_t length = eina_strbuf_length_get(payload) - 10;
    int ok = fwrite(eina_strbuf_string_get(payload) + 8, 1, length, file) == length;
    if (fputc('\n', file) == EOF) ok = 0;
    if (fclose(file)) ok = 0;
    eina_strbuf_free(payload);
    message(ok ? "Plan saved" : "Could not finish saving", ok ? "The plan contains no password. Review it again before unattended installation." : "Check available space and file permissions.");
}
static void device_selected(void *data, Evas_Object *o, void *ev) {
    (void)ev;
    Evas_Object *field = evas_object_data_get(o, "entry");
    Device *d = data; elm_object_text_set(field, d->path);
    if (field == ui.disk) {
        double max = d->gib - 10; if (max < ui.min_root) max = ui.min_root;
        elm_slider_min_max_set(ui.size_slider, ui.min_root, max);
        slider_changed(NULL, NULL, NULL);
        ecore_job_add(selectors_later, NULL);
    }
}
static void refresh_selectors(void) {
    char *target = ui.disk ? value(ui.disk) : strdup("");
    for (int s = 0; s < ui.selector_count; s++) {
        Evas_Object *selector = ui.selectors[s];
        int disks_only = (int)(intptr_t)evas_object_data_get(selector, "disks-only");
        elm_hoversel_clear(selector); int count = 0;
        for (int i = 0; i < ui.device_count; i++) {
            Device *d = &ui.devices[i];
            if (((!strcmp(d->kind, "disk")) != disks_only) || strstr(d->label, "[in use]")) continue;
            if (!disks_only && *target && strcmp(d->parent, target)) continue;
            elm_hoversel_item_add(selector, d->label, NULL, ELM_ICON_NONE, device_selected, d); count++;
        }
        elm_object_text_set(selector, count ? "Choose from detected devices" :
                            disks_only ? "No idle target disk detected" : "No idle partitions on this target");
        elm_object_disabled_set(selector, !count);
    }
    free(target);
}
static void refresh_disks(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev;
    load_inventory(); refresh_selectors(); update_layout(); ui.token[0] = 0;
}
static Evas_Object *device_field(Evas_Object *parent, const char *title, int disks_only) {
    Evas_Object *field = entry(parent, title, "", 0);
    Evas_Object *selector = elm_hoversel_add(parent);
    elm_object_text_set(selector, "Choose from detected devices");
    elm_hoversel_hover_parent_set(selector, ui.win);
    evas_object_data_set(selector, "entry", field);
    evas_object_data_set(selector, "disks-only", (void *)(intptr_t)disks_only);
    ui.selectors[ui.selector_count++] = selector;
    pack(parent, selector); return field;
}
static void mode_changed(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev;
    elm_box_unpack(ui.layout_holder, ui.new_box);
    elm_box_unpack(ui.layout_holder, ui.existing_box);
    evas_object_hide(ui.new_box); evas_object_hide(ui.existing_box);
    pack(ui.layout_holder, existing() ? ui.existing_box : ui.new_box);
}
static void external(void *data, Evas_Object *o, void *ev) {
    (void)o; (void)ev;
    if (fork() == 0) {
        if (!strcmp(data, "gparted")) execlp("sudo", "sudo", "-n", "gparted", (char *)NULL);
        else execlp("terminology", "terminology", "-e", "sudo", BACKEND, "tui", (char *)NULL);
        _exit(127);
    }
}
static void group_changed(void *data, Evas_Object *o, void *ev) {
    (void)ev; const char *group = data;
    for (int i = 0; i < ui.package_count; i++)
        if (!strcmp(group, ui.packages[i].group))
            elm_check_state_set(ui.packages[i].check, elm_check_state_get(o));
}
static void busy(int state) {
    ui.busy = state;
    for (int i = 0; i < 5; i++) elm_object_disabled_set(ui.nav[i], state);
    elm_object_disabled_set(ui.back, state || ui.page == 0);
    elm_object_disabled_set(ui.next, state || ui.page == 5 || (ui.page == 4 && !*ui.token));
}
static Eina_Bool read_output(void *data, Ecore_Fd_Handler *handler) {
    (void)data;
    char buf[8192]; ssize_t n = read(ecore_main_fd_handler_fd_get(handler), buf, sizeof(buf));
    if (n > 0) {
        eina_strbuf_append_length(ui.output, buf, n);
        plain(ui.installing ? ui.progress : ui.review, eina_strbuf_string_get(ui.output));
        return ECORE_CALLBACK_RENEW;
    }
    if (n < 0 && errno == EINTR) return ECORE_CALLBACK_RENEW;
    ui.eof = 1; ui.handler = NULL; close(ui.fd); ui.fd = -1;
    return ECORE_CALLBACK_CANCEL;
}
static Eina_Bool completed(void *data) {
    (void)data; int status;
    if (!ui.eof || waitpid(ui.child, &status, WNOHANG) == 0) return ECORE_CALLBACK_RENEW;
    const char *output = eina_strbuf_string_get(ui.output);
    int ok = WIFEXITED(status) && WEXITSTATUS(status) == 0;
    if (!ui.installing && ok && !strncmp(output, "REVIEW_ID=", 10)) {
        memcpy(ui.token, output + 10, 64); ui.token[64] = 0;
        const char *body = strchr(output, '\n'); plain(ui.review, body ? body + 1 : output);
    }
    if (ui.installing) {
        elm_object_text_set(ui.status, ok ? "Installation complete. You can close this window and shut down."
                                        : "Installation stopped. Read the log below before retrying.");
        elm_object_text_set(ui.password, ""); elm_object_text_set(ui.repeat, "");
    } else elm_object_text_set(ui.status, ok ? "Review the actions below, then choose Install."
                                             : "Review needs attention. Go back and correct the reported settings.");
    busy(0);
    if (ui.installing) {
        for (int i = 0; i < 5; i++) elm_object_disabled_set(ui.nav[i], EINA_TRUE);
        elm_object_disabled_set(ui.back, EINA_TRUE);
    }
    ui.timer = NULL; return ECORE_CALLBACK_CANCEL;
}
static void launch_api(int install) {
    if (ui.busy) return;
    if (!install) ui.token[0] = 0;
    Eina_Strbuf *payload = request(install);
    int input[2], output[2];
    if (pipe(input)) { eina_strbuf_free(payload); message("Cannot start", strerror(errno)); return; }
    if (pipe(output)) { close(input[0]); close(input[1]); eina_strbuf_free(payload); return; }
    pid_t child = fork();
    if (!child) {
        close(input[1]); close(output[0]);
        dup2(input[0], STDIN_FILENO); dup2(output[1], STDOUT_FILENO); dup2(output[1], STDERR_FILENO);
        close(input[0]); close(output[1]);
        setenv("PYTHONUNBUFFERED", "1", 1);
        if (install) execlp("sudo", "sudo", "-n", BACKEND, "install", (char *)NULL);
        else execl(BACKEND, BACKEND, "review", (char *)NULL);
        _exit(127);
    }
    close(input[0]); close(output[1]);
    if (child < 0) { close(input[1]); close(output[0]); eina_strbuf_free(payload); return; }
    const char *s = eina_strbuf_string_get(payload); size_t left = eina_strbuf_length_get(payload);
    while (left) { ssize_t n = write(input[1], s, left); if (n < 0) { if (errno == EINTR) continue; break; } left -= n; s += n; }
    close(input[1]);
    /* Password travels only over the private pipe, never argv, a file or the log. */
    if (install) memset((char *)eina_strbuf_string_get(payload), 0, eina_strbuf_length_get(payload));
    eina_strbuf_free(payload);
    if (ui.output) eina_strbuf_free(ui.output);
    ui.output = eina_strbuf_new(); ui.child = child; ui.fd = output[0]; ui.eof = 0; ui.installing = install;
    busy(1);
    elm_object_text_set(ui.status, install ? "Installing — progress from the native tools appears below."
                                         : "Inspecting the selected layout...");
    ui.handler = ecore_main_fd_handler_add(ui.fd, ECORE_FD_READ, read_output, NULL, NULL, NULL);
    ui.timer = ecore_timer_add(.1, completed, NULL);
}
static void confirmed(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev; popup_close(NULL, NULL, NULL);
    show_page(5); launch_api(1);
}
static void confirm(void) {
    char *a = value(ui.password), *b = value(ui.repeat);
    int valid = a && b && strlen(a) >= 8 && !strcmp(a, b);
    if (a) { memset(a, 0, strlen(a)); free(a); }
    if (b) { memset(b, 0, strlen(b)); free(b); }
    if (!valid) { message("Account password", "Return to Your account. Passwords must match and contain at least eight characters."); return; }
    ui.popup = elm_popup_add(ui.win);
    elm_object_part_text_set(ui.popup, "title,text", "Apply this installation plan?");
    elm_object_text_set(ui.popup, "This will alter the reviewed disk and format the partitions marked FORMAT.<br/>Files on those filesystems will be lost. Keep a backup.");
    Evas_Object *yes = elm_button_add(ui.popup), *no = elm_button_add(ui.popup);
    elm_object_text_set(yes, "Install"); elm_object_text_set(no, "Cancel");
    evas_object_smart_callback_add(yes, "clicked", confirmed, NULL);
    evas_object_smart_callback_add(no, "clicked", popup_close, NULL);
    elm_object_part_content_set(ui.popup, "button1", yes); elm_object_part_content_set(ui.popup, "button2", no);
    evas_object_show(ui.popup);
}
static void show_page(int page) {
    Evas_Object *old = elm_object_content_unset(ui.body);
    if (old) evas_object_hide(old);
    ui.page = page;
    elm_object_content_set(ui.body, ui.pages[page]); evas_object_show(ui.pages[page]);
    elm_object_text_set(ui.next, page == 4 ? "Install..." : "Next");
    elm_object_text_set(ui.status, "");
    busy(0);
    if (page == 4) launch_api(0);
}
static void navigate(void *data, Evas_Object *o, void *ev) {
    (void)o; (void)ev; if (!ui.busy) show_page((int)(intptr_t)data);
}
static void next(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev;
    if (ui.page == 4) confirm(); else if (ui.page < 4) show_page(ui.page + 1);
}
static void back(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev; if (ui.page > 0) show_page(ui.page - 1);
}
static void close_window(void *data, Evas_Object *o, void *ev) {
    (void)data; (void)o; (void)ev;
    if (ui.busy) message("Operation in progress", "Wait for the current operation to finish. Installation may be writing the disk.");
    else elm_exit();
}
EAPI_MAIN int elm_main(int argc, char **argv) {
    (void)argc; (void)argv;
    signal(SIGPIPE, SIG_IGN);
    elm_policy_set(ELM_POLICY_QUIT, ELM_POLICY_QUIT_LAST_WINDOW_CLOSED);
    char *save;
    ui.min_root = 24; snprintf(ui.firmware, sizeof(ui.firmware), "BIOS");
    load_inventory();
    char *catalog = read_backend("catalog");
    for (char *line = strtok_r(catalog, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
        if (ui.package_count >= MAX_ITEMS) break;
        Package *p = &ui.packages[ui.package_count];
        if (sscanf(line, "%95[^\t]\t%15[^\t]\t%127[^\n]", p->group, p->kind, p->name) == 3) ui.package_count++;
    }
    free(catalog);
    ui.win = elm_win_util_standard_add("eifyd-installer", "Get E’ifyd — Install AlpinE");
    evas_object_smart_callback_add(ui.win, "delete,request", close_window, NULL);
    Evas_Object *bg = elm_bg_add(ui.win); elm_bg_color_set(bg, 7, 17, 31);
    evas_object_size_hint_weight_set(bg, EVAS_HINT_EXPAND, EVAS_HINT_EXPAND);
    elm_win_resize_object_add(ui.win, bg); evas_object_show(bg);
    Evas_Object *outer = box(ui.win, 0);
    evas_object_size_hint_weight_set(outer, EVAS_HINT_EXPAND, EVAS_HINT_EXPAND);
    elm_win_resize_object_add(ui.win, outer); evas_object_show(outer);
    label(outer, "<font_size=24><color=#62d9ef><b>GET E’IFYD</b></color></font_size>  AlpinE by Auzietek");
    Evas_Object *nav = box(outer, 1); pack(outer, nav);
    const char *titles[] = {"Welcome", "Disks & boot", "Your account", "Software", "Review"};
    for (int i = 0; i < 5; i++) ui.nav[i] = button(nav, titles[i], navigate, (void *)(intptr_t)i);
    ui.body = elm_scroller_add(outer);
    evas_object_size_hint_weight_set(ui.body, EVAS_HINT_EXPAND, EVAS_HINT_EXPAND);
    evas_object_size_hint_align_set(ui.body, EVAS_HINT_FILL, EVAS_HINT_FILL);
    pack(outer, ui.body);
    for (int i = 0; i < 6; i++) {
        ui.pages[i] = box(ui.win, 0);
        elm_box_align_set(ui.pages[i], 0.5, 0.0);
        evas_object_size_hint_weight_set(ui.pages[i], EVAS_HINT_EXPAND, EVAS_HINT_EXPAND);
        evas_object_size_hint_align_set(ui.pages[i], EVAS_HINT_FILL, EVAS_HINT_FILL);
    }
    Evas_Object *p = ui.pages[0];
    Evas_Object *mark = elm_image_add(p);
    elm_image_file_set(mark, "/usr/share/eifyd/mark-shield-swords.png", NULL);
    /* A child's finite maximum width propagates to the entire Elementary box. */
    evas_object_size_hint_min_set(mark, 150, 150); evas_object_size_hint_max_set(mark, -1, 150); pack(p, mark);
    label(p, "<font_size=22><b>Your workstation. Enlightened.</b></font_size>");
    label(p, "A native Alpine system with Enlightenment, your themes and the applications you choose.");
    label(p, "Choose a new split root/home layout or reuse existing partitions.<br/>Nothing is written until you review the plan and press Install.");
    label(p, "Back up files you want to keep. Migration is separate from installation; no Windows folders are copied automatically.");
    label(p, "AlpinE combines independently licensed software. Alpine is open source; component licenses remain in effect.<br/>This installer does not introduce an Alpine EULA.");
    button(p, "Open the console installer", external, "tui");
    p = ui.pages[1];
    label(p, "<b>Storage and boot</b> — ext4 root and home; native GRUB");
    Evas_Object *destination = section(p, "Destination disk");
    ui.disk = device_field(destination, "Target disk (or enter its device path)", 1);
    evas_object_smart_callback_add(ui.disk, "unfocused", refresh_disks, NULL);
    button(destination, "Refresh disks and partitions", refresh_disks, NULL);
    ui.mode = elm_radio_add(p);
    elm_object_text_set(ui.mode, "Guided — create a new root and home layout");
    elm_radio_state_value_set(ui.mode, 0); expand(ui.mode); pack(p, ui.mode);
    Evas_Object *manual = elm_radio_add(p);
    elm_object_text_set(manual, "Manual — assign existing partitions and choose what to format");
    elm_radio_state_value_set(manual, 1); elm_radio_group_add(manual, ui.mode);
    expand(manual); pack(p, manual); elm_radio_value_set(ui.mode, 0);
    evas_object_smart_callback_add(ui.mode, "changed", mode_changed, NULL);
    evas_object_smart_callback_add(manual, "changed", mode_changed, NULL);
    label(p, "Only idle writable disks appear in the chooser; the running live disk is excluded.");
    ui.layout_holder = box(p, 0); pack(p, ui.layout_holder);
    ui.new_box = box(ui.layout_holder, 0);
    ui.root_size = entry(ui.new_box, "New root size (GiB); the rest becomes /home", "48", 0);
    ui.size_slider = elm_slider_add(ui.new_box);
    elm_slider_min_max_set(ui.size_slider, ui.min_root, 256);
    elm_slider_value_set(ui.size_slider, ui.min_root > 48 ? ui.min_root : 48);
    elm_slider_unit_format_set(ui.size_slider, "%.0f GiB"); expand(ui.size_slider); pack(ui.new_box, ui.size_slider);
    evas_object_smart_callback_add(ui.size_slider, "changed", slider_changed, NULL);
    evas_object_smart_callback_add(ui.root_size, "unfocused", size_changed, NULL);
    ui.layout_text = textview(ui.new_box);
    ui.existing_box = box(ui.layout_holder, 0);
    Evas_Object *root_section = section(ui.existing_box, "System — / — ext4");
    ui.root = device_field(root_section, "Root partition", 0);
    ui.format_root = check(root_section, "Format root — required for a clean installation", 1);
    Evas_Object *home_section = section(ui.existing_box, "Personal files — /home — ext4");
    ui.home = device_field(home_section, "Home partition", 0);
    ui.format_home = check(home_section, "Format home — ERASES personal files (leave off to preserve)", 0);
    Evas_Object *boot_section = section(ui.existing_box, "Boot and firmware");
    ui.bootpart = device_field(boot_section, "Boot partition → /boot (optional, ext4)", 0);
    ui.format_boot = check(boot_section, "Format the selected boot partition", 0);
    ui.esp = device_field(boot_section, "EFI system partition → /boot/efi (UEFI only, kept without formatting)", 0);
    label(p, "Boot mode follows the live session. GRUB targets the selected disk.<br/>For resizing or advanced layouts, prepare partitions in GParted, then Refresh disks and partitions.");
    button(p, "Open GParted", external, "gparted");
    p = ui.pages[2];
    label(p, "<b>Your account</b> — administrator access through sudo, with your password");
    ui.host = entry(p, "Computer name", "alpine-workstation", 0);
    ui.user = entry(p, "Account name (not root or alpine)", "", 0);
    ui.zone = entry(p, "Timezone", "America/Los_Angeles", 0);
    ui.password = entry(p, "Password (at least eight characters)", "", 1);
    ui.repeat = entry(p, "Repeat password", "", 1);
    label(p, "The installed system will ask you to log in. Root login remains locked.<br/>Keyboard and desktop defaults follow this live image. A preserved home keeps its own settings.");
    p = ui.pages[3];
    label(p, "<b>Choose your software</b>");
    label(p, "The Alpine/E desktop, networking, sound, hardware support and recovery tools stay installed.<br/>Expand groups to choose individual applications. APK resolves their dependencies.");
    char previous[96] = ""; Evas_Object *groupbox = NULL;
    for (int i = 0; i < ui.package_count; i++) {
        Package *item = &ui.packages[i];
        if (strcmp(previous, item->group)) {
            snprintf(previous, sizeof(previous), "%s", item->group);
            Evas_Object *frame = elm_frame_add(p);
            elm_object_text_set(frame, item->group); elm_frame_autocollapse_set(frame, EINA_TRUE);
            groupbox = box(frame, 0);
            Evas_Object *all = check(groupbox, "Include all in this group", 1);
            evas_object_smart_callback_add(all, "changed", group_changed, item->group);
            elm_object_content_set(frame, groupbox); expand(frame); pack(p, frame);
            elm_frame_collapse_set(frame, EINA_TRUE);
        }
        char name[180]; snprintf(name, sizeof(name), "%s (%s)", item->name, item->kind);
        item->check = check(groupbox, name, 1);
    }
    ui.review = textview(ui.pages[4]);
    char saved[512]; snprintf(saved, sizeof(saved), "%s/eifyd-install-plan.json", getenv("HOME") ? getenv("HOME") : "/tmp");
    ui.save_path = entry(ui.pages[4], "Save this plan for console/BKC use (optional)", saved, 0);
    button(ui.pages[4], "Save plan", save_plan, NULL);
    ui.progress = textview(ui.pages[5]);
    ui.status = label(outer, "");
    Evas_Object *footer = box(outer, 1); pack(outer, footer);
    ui.back = button(footer, "Back", back, NULL);
    ui.next = button(footer, "Next", next, NULL);
    mode_changed(NULL, NULL, NULL); refresh_selectors(); update_layout(); show_page(0);
    evas_object_resize(ui.win, 920, 760); elm_win_center(ui.win, EINA_TRUE, EINA_TRUE);
    evas_object_show(ui.win); elm_run(); return 0;
}
ELM_MAIN()
